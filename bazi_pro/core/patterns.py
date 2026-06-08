"""格局判定模块 — 四层筛查 + 破格检测

核心原理
========
《子平真诠》第八章"论用神"："用神专寻月令，以月令为先"。
格局判定的根本依据是月令（月支）所藏天干，看其是否透出天干，
透出则以该十神定格局名称，此即"用神从月令出"。

四层筛选架构 L0→L3
===================
按优先级从高到低逐层筛查，命中即返回，不再向下：

L0（特殊格局）：
  - 化气格：日主参与天干合化，化神五行占比≥60%
  - 专旺格（曲直/炎上/稼穑/从革/润下）：日主五行占绝对优势+方局/三合成局
  - 从强格/假从强格：印比合计≥80%且无强根
  - 从财格/从官杀格/从儿格/从势格：日主极弱，克泄耗成势
  - 两行成象格：克泄耗两行合计≥85%

L1（月令本气透干）：
  - 月支本气天干出现在四天干中，以该十神定格
  - 若本气为比劫，则转入建禄月劫格处理

L2（月令中气透干）：
  - 本气未透但中气透干，以中气十神定格
  - 中气为比劫同样转入建禄月劫格

L3（暗格/比劫月令）：
  - 月支本气不透干，取为暗格
  - 羊刃月令、比劫月令特殊处理

古籍依据
========
- 《子平真诠》沈孝瞻：格局分类、用神成败救应、破格条件
- 《滴天髓》任铁樵注：从格条件、化象论、旺衰极端判定
- 《渊海子平》徐升：根气论、建禄格
- 《神峰通考》张楠：伤官见官、枭神夺食

数据流
======
screen_pattern() ← full_analysis()
    → _screen_layer0() / _screen_layer1() / _screen_layer2() / _screen_layer3()
        → _check_formation() / _check_month_season() / _check_*_break()
    → _finalize_pattern()
    → 返回格局结果 dict（含 pattern, confidence, break_conditions 等）
"""

from bazi_pro.core.branches import (
    JIANLU_MAP,  # 建禄映射：天干→建禄地支，如 '甲'→'寅'
    SHIER_CHANGSHENG,  # 十二长生表：天干→{地支→长生状态}
    YANGREN_MAP,  # 羊刃映射：天干→羊刃地支，如 '甲'→'卯'
    ZHI_BANHE,  # 地支半合局：[(半合地支集合, 五行), ...]
    ZHI_CHONG,  # 地支六冲：[frozenset({地支1, 地支2}), ...]
    ZHI_HUIFANG,  # 地支会方：[(会方地支集合, 五行), ...]
    ZHI_SANHE,  # 地支三合局：[(三合地支集合, 五行), ...]
    ZHI_XING,  # 地支相刑：[frozenset({地支1, 地支2}), ...]
)
from bazi_pro.core.constants import GAN_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.stems import GAN_HE, KE_MAP, SHENG_MAP, WO_KE_MAP
from bazi_pro.core.ten_gods import _count_shishen_categories, _get_yongshen_direction

# 天干→合化伙伴映射（从 GAN_HE frozenset 键展开为单天干查找表）
# 《子平真诠》"甲己合土、乙庚合金、丙辛合水、丁壬合木、戊癸合火"
_GAN_HE_PARTNER: dict[str, str] = {}
for _pair, _wx in GAN_HE.items():
    _gans = sorted(_pair)
    _GAN_HE_PARTNER[_gans[0]] = _gans[1]
    _GAN_HE_PARTNER[_gans[1]] = _gans[0]


def _check_dm_root_in_branches(day_master: str, dm_wx: str, bazi_parts: list) -> dict:
    """检查日主在地支是否有根气

    《渊海子平》："命逢根气，命殞无猜" — 地支藏干中与日主同五行的天干即为根气。
    根气强度分三级：本气 > 中气 > 余气。从格判断中，本气根和中气根可破从格，
    余气根仅降低 confidence。

    Args:
        day_master: 日主天干，如 '甲'
        dm_wx: 日主五行，如 '木'
        bazi_parts: 四柱干支列表，如 ['甲子', '丙寅', '甲辰', '壬申']，
                    每个元素为天干+地支的字符串

    Returns:
        dict: {
            'has_benqi_root': bool,    # 是否有本气根（最强根，可破从格）
            'has_zhongqi_root': bool,  # 是否有中气根（较强根，可破从格）
            'has_weakqi_root': bool,   # 是否有余气根（弱根，仅降低confidence）
            'root_locations': list,    # 根气位置描述，如 ['辰（本气）', '寅（中气）']
        }
    """
    result = {
        'has_benqi_root': False,
        'has_zhongqi_root': False,
        'has_weakqi_root': False,
        'root_locations': []
    }

    for part in bazi_parts:
        if len(part) < 2:
            continue
        zhi = part[1]
        for cg, ql in get_canggan(zhi):
            # 藏干五行与日主五行相同即为根气
            if GAN_WUXING.get(cg, '') == dm_wx:
                if ql == '本气':
                    result['has_benqi_root'] = True
                    result['root_locations'].append(f'{zhi}（本气）')
                elif ql == '中气':
                    result['has_zhongqi_root'] = True
                    result['root_locations'].append(f'{zhi}（中气）')
                elif ql == '余气':
                    result['has_weakqi_root'] = True
                    result['root_locations'].append(f'{zhi}（余气）')

    return result


# 化气格月令当令判定表：五行→当令地支集合
# 《子平真诠·论杂格》"要化出之物，得时乘令"
# 土当令为辰戌丑未（四季土），金当令为申酉，余类推
HUA_SEASON_MAP = {
    '土': {'辰', '戌', '丑', '未'},
    '金': {'申', '酉'},
    '水': {'亥', '子'},
    '木': {'寅', '卯'},
    '火': {'巳', '午'},
}

# 天干争合/妒合查表
# key: 合化天干对的frozenset（如甲己合）
# value: {'争合': 争合天干, '妒合': 妒合天干}
# 争合：合化对方出现≥2个，如两己争甲
# 妒合：劫财天干同时有合对象在场，如甲己合+乙庚合
GAN_HE_DUO = {
    frozenset({'甲', '己'}): {'争合': '己', '妒合': '乙'},
    frozenset({'乙', '庚'}): {'争合': '庚', '妒合': '甲'},
    frozenset({'丙', '辛'}): {'争合': '辛', '妒合': '丁'},
    frozenset({'丁', '壬'}): {'争合': '壬', '妒合': '丙'},
    frozenset({'戊', '癸'}): {'争合': '癸', '妒合': '己'},
}

# 五行相克映射：被克五行→克者五行
# 用于化气格"克化神"检测和专旺格"官杀逆势"检测
WUXING_KE = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}


def _check_formation(bazi_parts, target_wx):
    """检查地支是否形成方局/三合/半会/半合

    《子平真诠·论杂格》："有取五行一方秀气者，取甲乙全亥卯未、寅卯辰"
    格局判定中，方局/三合是专旺格和从格成立的必要条件。

    检测优先级：会方 > 三合 > 同五行≥3 > 半会 > 半合局 > 四库土

    Args:
        bazi_parts: 四柱干支列表，如 ['甲子', '丙寅', '甲辰', '壬申']
        target_wx: 目标五行，如 '木'

    Returns:
        dict: {
            'has_formation': bool,   # 是否成局
            'type': str|None,        # 局类型：'会方'/'三合'/'半会'/'半合局'
            'branches': list,        # 参与成局的地支列表
            'element': str,          # 目标五行
        }
    """
    branches = []
    for part in bazi_parts:
        if len(part) >= 2:
            branches.append(part[1])
    branch_set = set(branches)

    # 优先级1：完整会方（如寅卯辰会木方）
    for fang_set, fang_wx in ZHI_HUIFANG:
        if fang_set.issubset(branch_set) and fang_wx == target_wx:
            return {
                'has_formation': True,
                'type': '会方',
                'branches': sorted(list(fang_set)),
                'element': target_wx,
            }

    # 优先级2：三合局（如亥卯未合木局）
    for he_set, he_wx in ZHI_SANHE:
        if he_set.issubset(branch_set) and he_wx == target_wx:
            return {
                'has_formation': True,
                'type': '三合',
                'branches': sorted(list(he_set)),
                'element': target_wx,
            }

    # 优先级3：同五行地支≥3：视为完整会方
    # 优先级3已移除：原"同五行地支≥3即视为会方"过度放宽
    # 《滴天髓》"方是方兮局是局，要得方，莫混局"
    # 会方要求严格的地支组合（寅卯辰、巳午未、申酉戌、亥子丑），
    # 不应将任意三个同五行地支混同为会方。
    # 三合局（申子辰等）已在优先级2中检测，无需重复。

    # 优先级4：半会（会方中2个地支）
    for fang_set, fang_wx in ZHI_HUIFANG:
        if fang_wx == target_wx:
            overlap = fang_set & branch_set
            if len(overlap) >= 2:
                return {
                    'has_formation': True,
                    'type': '半会',
                    'branches': sorted(list(overlap)),
                    'element': target_wx,
                }

    # 优先级5：半合局（三合中2个地支）
    for banhe_set, banhe_wx in ZHI_BANHE:
        if banhe_set.issubset(branch_set) and banhe_wx == target_wx:
            return {
                'has_formation': True,
                'type': '半合局',
                'branches': sorted(list(banhe_set)),
                'element': target_wx,
            }

    # 优先级6：四库土特殊处理（辰戌丑未中≥3个）
    if target_wx == '土':
        siku = {'辰', '戌', '丑', '未'}
        siku_present = siku & branch_set
        if len(siku_present) >= 3:
            return {
                'has_formation': True,
                'type': '会方',
                'branches': sorted(list(siku_present)),
                'element': target_wx,
            }

    return {
        'has_formation': False,
        'type': None,
        'branches': [],
        'element': target_wx,
    }


def _check_month_season(month_zhi, target_wx):
    """检查月支是否当令（月令是否属于目标五行的季节）

    《子平真诠·论杂格》"要化出之物，得时乘令" — 月令当令是格局成立的重要条件。
    专旺格要求月令当令，化气格用此区分真化/假化。

    Args:
        month_zhi: 月支地支，如 '寅'
        target_wx: 目标五行，如 '木'

    Returns:
        dict: {
            'is_season': bool,       # 月支是否当令
            'season_months': list,   # 该五行当令的地支列表
        }
    """
    SEASON_MAP = {
        '木': ['寅', '卯', '辰'],   # 春季：寅卯辰
        '火': ['巳', '午', '未'],   # 夏季：巳午未
        '金': ['申', '酉', '戌'],   # 秋季：申酉戌
        '水': ['亥', '子', '丑'],   # 冬季：亥子丑
        '土': ['辰', '戌', '丑', '未'],  # 四季土：辰戌丑未
    }
    season_months = SEASON_MAP.get(target_wx, [])
    return {
        'is_season': month_zhi in season_months,
        'season_months': season_months,
    }


def _check_zhuanwang_break(day_master, dm_wx, bazi_parts, gans):
    """专旺格破格检测

    《子平真诠·论杂格》专旺格破格条件：
    1. 官杀逆势（high）：天干出现克日主五行之天干，逆专旺之势
    2. 引至死绝（medium）：时支为日主死/绝/墓地，专旺气泄于时

    Args:
        day_master: 日主天干
        dm_wx: 日主五行
        bazi_parts: 四柱干支列表
        gans: 四天干列表（含日主）

    Returns:
        list[dict]: 破格条件列表，每项含 type/severity/detail
    """
    breaks = []
    KE_WUXING = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}
    ke_wx = KE_WUXING.get(dm_wx, '')
    if ke_wx:
        for g in gans:
            if GAN_WUXING.get(g, '') == ke_wx:
                ss = derive_shishen(day_master, g)
                breaks.append({
                    'type': '官杀逆势',
                    'severity': 'high',
                    'detail': f'天干{g}({ss})克日主{dm_wx}行，逆专旺之势',
                })

    # 检查时支是否为日主死绝之地
    hour_zhi = bazi_parts[3][1] if len(bazi_parts) >= 4 and len(bazi_parts[3]) >= 2 else ''
    if hour_zhi:
        cs_map = SHIER_CHANGSHENG.get(day_master, {})
        cs_status = cs_map.get(hour_zhi, '')
        # 死/绝/墓：日主气尽之地，专旺格忌之
        if cs_status in ('死', '绝', '墓'):
            breaks.append({
                'type': '引至死绝',
                'severity': 'medium',
                'detail': f'时支{hour_zhi}为日主{day_master}{cs_status}地，专旺气泄',
            })
    return breaks


def _check_hua_break(day_master, hua_wx, gans, bazi_parts):
    """化气格破格检测 — 《子平真诠》"论化气"

    破格条件及严重度：
    - 争合（high）：合化双方任一方≥2个天干，如两己争甲、两甲争己
    - 妒合（high）：劫财天干同时有合对象在场，形成竞争合化
    - 克化神（medium）：天干出现克化神五行之天干

    古籍原文：
    《子平真诠·论化气》："化得真者只论化，化不得真者，亦以化论"
    《子平真诠·论化气》："有争合妒合者，皆不能化"

    Args:
        day_master: 日主天干
        hua_wx: 化神五行，如 '土'（甲己化土）
        gans: 四天干列表（含日主）
        bazi_parts: 四柱干支列表

    Returns:
        list[dict]: 破格条件列表
    """
    breaks = []
    he_key = None
    for k in GAN_HE:
        if day_master in k:
            he_key = k
            break
    if he_key is None:
        return breaks

    # 争合检测：检查合化双方各自的数量，任一方≥2即为争合
    he_pair = list(he_key)
    other_gan = he_pair[0] if he_pair[1] == day_master else he_pair[1]

    # 对方天干数量≥2：争合日主（如两己争甲）
    other_count = sum(1 for g in gans if g == other_gan)
    if other_count >= 2:
        breaks.append({'type': '争合', 'severity': 'high',
                       'detail': f'天干出现{other_count}个{other_gan}争合{day_master}'})

    # 日主同类天干数量≥2：日主方争合对方（如两甲争己）
    dm_count = sum(1 for g in gans if g == day_master) - 1  # 减去日主自身
    if dm_count >= 2:
        breaks.append({'type': '争合', 'severity': 'high',
                       'detail': f'天干出现{dm_count+1}个{day_master}争合{other_gan}'})

    # 妒合检测：《子平真诠》"两丁合壬，两辛合丙"
    # 劫财天干（同五行异阴阳）同时有合对象在场时，形成竞争合化
    # 注意：仅"同五行异阴阳"（如甲日主见乙）不直接构成妒合，
    # 必须劫财天干同时有合对象在场（如甲己合+乙庚合争合）才算妒合
    dm_yin_yang = '阴' if day_master in '乙丁己辛癸' else '阳'
    for g in gans:
        if g == day_master:
            continue
        if GAN_WUXING.get(g, '') == GAN_WUXING.get(day_master, ''):
            g_yin_yang = '阴' if g in '乙丁己辛癸' else '阳'
            if g_yin_yang != dm_yin_yang:
                # 劫财天干有自己的合对象在场 → 妒合
                g_he_key = None
                for k in GAN_HE:
                    if g in k:
                        g_he_key = k
                        break
                if g_he_key:
                    g_partner = g_he_key[0] if g_he_key[1] == g else g_he_key[1]
                    if g_partner in gans:
                        breaks.append({'type': '妒合', 'severity': 'high',
                                       'detail': f'天干{g}与{g_partner}合，与日主{day_master}争合化，妒合'})
                        break

    # 克化神检测：天干出现克化神五行之天干
    ke_wx = WUXING_KE.get(hua_wx, '')
    if ke_wx:
        ke_gans = [g for g in gans if GAN_WUXING.get(g, '') == ke_wx]
        if ke_gans:
            breaks.append({'type': '克化神', 'severity': 'medium',
                           'detail': f'天干{",".join(ke_gans)}属{ke_wx}克化神{hua_wx}'})
    return breaks


def _build_break_conditions(dm_root_info):
    """从格破格条件 — 《滴天髓》"日主孤立无气，无地人元，绝无一毫生扶之意"

    根气强度与破格关系：
    - 本气根/中气根：必定破从格（severity=high），日主有强根则不从
    - 余气根：降低confidence但不一定破格（severity=medium），余气根虽弱但仍属"人元"

    Args:
        dm_root_info: _check_dm_root_in_branches() 的返回值

    Returns:
        list[dict]: 破格条件列表
    """
    conditions = []
    if dm_root_info['has_benqi_root'] or dm_root_info['has_zhongqi_root']:
        conditions.append({
            'type': '命逢根气',
            'severity': 'high',
            'detail': '日主有本气/中气根，从格不真',
        })
    elif dm_root_info.get('has_weakqi_root'):
        conditions.append({
            'type': '余气根',
            'severity': 'medium',
            'detail': '日主有余气根，从格不真（降低confidence）',
        })
    return conditions


def _check_jianlu_yangren_break(day_master, dm_wx, bazi_parts, gans, pattern_name):
    """建禄月劫格/羊刃格破格检测

    依据《子平真诠》第四十三章"论建禄月劫"、第四十五章"论阳刃"

    破格条件：
    1. 孤官无辅（medium）：建禄格透正官，天干无财星印星辅佐，官星孤立
       — 《子平真诠》"建禄透官，须财印为辅"
    2. 透刃合煞（high）：羊刃格透七杀，天干有与七杀相合者，杀被合去
       — 《子平真诠》"刃旺用煞，煞不可合"
    3. 会杀为凶（high）：建禄格地支会官杀之方/局
       — 《子平真诠》"禄劫会杀为凶"
    4. 透煞印无财官（medium）：建禄月劫格透煞印而无财官
       — 《子平真诠》"建禄月劫格败：无财官，透煞印"

    Args:
        day_master: 日主天干
        dm_wx: 日主五行
        bazi_parts: 四柱干支列表
        gans: 四天干列表（含日主）
        pattern_name: 格局名称，如 '建禄格，透正官'

    Returns:
        list[dict]: 破格条件列表
    """
    breaks = []

    # 孤官无辅：建禄格透正官，但天干无财星印星辅佐
    if '透正官' in pattern_name:
        has_cai = False
        has_yin = False
        for g in gans:
            if g == day_master:
                continue
            ss = derive_shishen(day_master, g)
            if ss in ('正财', '偏财'):
                has_cai = True
            if ss in ('正印', '偏印'):
                has_yin = True
        if not has_cai and not has_yin:
            breaks.append({
                'type': '孤官无辅',
                'severity': 'medium',
                'detail': '建禄格透正官，天干无财星印星辅佐，官星孤立',
            })

    # 透刃合煞：羊刃格透七杀，天干有与七杀相合者
    if '羊刃格' in pattern_name and '透七杀' in pattern_name:
        sha_gans = []
        for g in gans:
            if g == day_master:
                continue
            ss = derive_shishen(day_master, g)
            if ss == '七杀':
                sha_gans.append(g)
        for sha_g in sha_gans:
            for he_pair in GAN_HE:
                if sha_g in he_pair:
                    other_in_pair = he_pair - {sha_g}
                    if other_in_pair:
                        other_g = list(other_in_pair)[0]
                        if other_g in gans:
                            breaks.append({
                                'type': '透刃合煞',
                                'severity': 'high',
                                'detail': f'羊刃格透七杀{sha_g}，天干{other_g}与七杀相合，杀被合去',
                            })

    # 羊刃无官煞 — 《子平真诠》第九章"阳刃无官煞，刃格败也"
    # 羊刃格天干无官杀制刃，刃旺无制为祸
    if '羊刃格' in pattern_name:
        has_guan_sha = False
        for g in gans:
            if g == day_master:
                continue
            ss = derive_shishen(day_master, g)
            if ss in ('正官', '七杀'):
                has_guan_sha = True
                break
        if not has_guan_sha:
            breaks.append({
                'type': '羊刃无官煞',
                'severity': 'high',
                'detail': '羊刃格天干无官杀制刃，刃旺无制为祸',
            })

    # 会杀为凶：建禄格地支会官杀之方/局
    if '建禄格' in pattern_name:
        sha_wx = KE_MAP.get(dm_wx, '')
        if sha_wx:
            formation = _check_formation(bazi_parts, sha_wx)
            if formation['has_formation']:
                breaks.append({
                    'type': '会杀为凶',
                    'severity': 'high',
                    'detail': f'建禄格地支{formation["type"]}{"".join(formation["branches"])}会{sha_wx}杀，凶',
                })

    # 透煞印无财官：建禄月劫格透煞印而无财官
    # 《子平真诠》"建禄月劫格败：无财官，透煞印"
    # 杀印相生虽为格局之一途，但非禄劫正用（禄劫正用为财官）
    if '建禄格' in pattern_name or '月劫格' in pattern_name:
        has_sha = False
        has_yin = False
        has_cai = False
        has_guan = False
        for g in gans:
            if g == day_master:
                continue
            ss = derive_shishen(day_master, g)
            if ss == '七杀':
                has_sha = True
            if ss in ('正印', '偏印'):
                has_yin = True
            if ss in ('正财', '偏财'):
                has_cai = True
            if ss == '正官':
                has_guan = True
        if has_sha and has_yin and not has_cai and not has_guan:
            breaks.append({
                'type': '透煞印无财官',
                'severity': 'medium',
                'detail': '建禄月劫格透煞印而无财官，杀印相生非禄劫正用',
            })
    return breaks


def _check_zhengge_break(day_master, dm_wx, bazi_parts, gans, pattern_name):
    """正格破格检测 — 依据《子平真诠》第九章"论用神成败救应"

    成格条件（顺用）：
    - 财喜食生+官护财
    - 官喜财生+印护官
    - 印喜官杀生+比劫护
    - 食喜身旺生+财护食

    成格条件（逆用）：
    - 七杀喜食神制伏
    - 伤官喜佩印制+生财化伤
    - 阳刃喜官杀制伏
    - 月劫喜透官制+食化劫

    各格破格条件见下方逐格检查。

    Args:
        day_master: 日主天干
        dm_wx: 日主五行
        bazi_parts: 四柱干支列表
        gans: 四天干列表（含日主）
        pattern_name: 格局名称，如 '正官格'、'财格'

    Returns:
        list[dict]: 破格条件列表，每项含 type/severity/detail
    """
    breaks = []

    # 构建十神→天干映射：{十神名: [天干列表]}
    # 如 {'正官': ['辛'], '伤官': ['丁', '丙']}
    shishen_map = {}
    for g in gans:
        if g == day_master:
            continue
        ss = derive_shishen(day_master, g)
        if ss not in shishen_map:
            shishen_map[ss] = []
        shishen_map[ss].append(g)

    # 提取地支列表（用于刑冲检测）
    zhis = [p[1] for p in bazi_parts if len(p) >= 2]

    # ── 正官格破格 ──
    # 《子平真诠》"官格败：官逢伤克刑冲"
    # 《子平真诠》第九章带忌："透官而又逢合"
    if '正官格' in pattern_name:
        # (1) 伤官见官 — 正官最忌伤官
        # 《子平真诠》"伤官见官为祸百端"
        if '伤官' in shishen_map:
            breaks.append({
                'type': '伤官见官',
                'severity': 'high',
                'detail': f'正官格天干透伤官{"".join(shishen_map["伤官"])}，伤官见官为祸百端',
            })
        # (2) 官星逢合 — 正官被合去则官格不成
        # 《子平真诠》第九章带忌："透官而又逢合"
        # 检查正官天干是否与其他天干构成天干五合
        guan_gans = shishen_map.get('正官', [])
        for gg in guan_gans:
            he_partner = _GAN_HE_PARTNER.get(gg, '')
            if he_partner:
                # 检查合化对象是否在天干中（排除日主自身与正官的合）
                for g in gans:
                    if g == day_master or g == gg:
                        continue
                    if g == he_partner:
                        breaks.append({
                            'type': '官星逢合',
                            'severity': 'high',
                            'detail': f'正官格正官{gg}与{he_partner}相合，官星被合去，官格不成',
                        })
                        break
        # (3) 官星逢刑冲 — 正官根基动摇
        # 检查月支（官星所在）是否被其他地支冲或刑
        month_zhi = zhis[1] if len(zhis) > 1 else ''
        for i, zhi in enumerate(zhis):
            if i == 1:
                continue
            pair = frozenset({month_zhi, zhi})
            if pair in ZHI_CHONG:
                breaks.append({
                    'type': '官星逢冲',
                    'severity': 'high',
                    'detail': f'正官格月支{month_zhi}与{zhi}相冲，官星根基动摇',
                })
                break
            if pair in ZHI_XING:
                breaks.append({
                    'type': '官星逢刑',
                    'severity': 'medium',
                    'detail': f'正官格月支{month_zhi}与{zhi}相刑，官星受损',
                })
                break

    # ── 财格破格 ──
    # 《子平真诠》"财格败：财轻比重，财透七煞"
    if '财格' in pattern_name:
        # (1) 比劫争财 — 天干透比劫且无官杀制比劫或食伤通关
        # 《子平真诠》"财轻比重"：比劫夺财，须官杀制之或食伤化之
        # 《子平真诠》"财逢劫而透食以化之"：食伤可化比劫生财（通关）
        if '比肩' in shishen_map or '劫财' in shishen_map:
            has_guansha = '正官' in shishen_map or '七杀' in shishen_map
            has_shishen_tongguan = '食神' in shishen_map or '伤官' in shishen_map
            if not has_guansha and not has_shishen_tongguan:
                bijie_gans = shishen_map.get('比肩', []) + shishen_map.get('劫财', [])
                breaks.append({
                    'type': '比劫争财',
                    'severity': 'high',
                    'detail': f'财格天干透比劫{"".join(bijie_gans)}，无官杀制比劫，财被争夺',
                })
        # (2) 财透七煞 — 财格透七杀且无食神制杀，财党杀为祸
        # 《子平真诠》"财透七煞"：财生杀，杀得财助反为祸
        if '七杀' in shishen_map:
            has_shishen_zhi_sha = '食神' in shishen_map
            if not has_shishen_zhi_sha:
                sha_gans = shishen_map.get('七杀', [])
                breaks.append({
                    'type': '财透七煞',
                    'severity': 'high',
                    'detail': f'财格天干透七杀{"".join(sha_gans)}，无食神制杀，财党杀为祸',
                })

    # ── 印格破格 ──
    # 《子平真诠》"印格败：印轻逢财，或身强印重而透煞"
    # 印轻条件：印星无本气根（仅有中气/余气根），财星才能破印
    # 若印星强旺（有本气根+透干），财星破不了印
    if '印格' in pattern_name:
        if '正财' in shishen_map or '偏财' in shishen_map:
            # 检查印星是否"轻"：无本气根
            yin_gans = shishen_map.get('正印', []) + shishen_map.get('偏印', [])
            yin_wx_set = set()
            for yg in yin_gans:
                wx = GAN_WUXING.get(yg, '')
                if wx:
                    yin_wx_set.add(wx)
            yin_has_benqi_root = False
            for part in bazi_parts:
                if len(part) < 2:
                    continue
                for cg, ql in get_canggan(part[1]):
                    if GAN_WUXING.get(cg, '') in yin_wx_set and ql == '本气':
                        yin_has_benqi_root = True
                        break
                if yin_has_benqi_root:
                    break
            # 印星无本气根（印轻）+ 财星透干 → 财星破印
            if not yin_has_benqi_root:
                cai_gans = shishen_map.get('正财', []) + shishen_map.get('偏财', [])
                breaks.append({
                    'type': '财星破印',
                    'severity': 'high',
                    'detail': f'印格天干透财星{"".join(cai_gans)}，印星无本气根（印轻），财星破印',
                })

        # 《子平真诠》"身强印重而透煞" — 身旺印旺又透七杀，印星太旺反为偏颇
        # 三条件缺一不可：身强 + 印重 + 透煞
        if '七杀' in shishen_map:
            yin_gans = shishen_map.get('正印', []) + shishen_map.get('偏印', [])
            yin_wx_set = set()
            for yg in yin_gans:
                wx = GAN_WUXING.get(yg, '')
                if wx:
                    yin_wx_set.add(wx)
            # 印星"重"：有本气根
            yin_has_benqi_root = False
            for part in bazi_parts:
                if len(part) < 2:
                    continue
                for cg, ql in get_canggan(part[1]):
                    if GAN_WUXING.get(cg, '') in yin_wx_set and ql == '本气':
                        yin_has_benqi_root = True
                        break
                if yin_has_benqi_root:
                    break
            # 身强判断：天干有比劫或印星（与disease.py一致）
            # 《子平真诠》"身强"：印比力量占主导
            has_bijie = '比肩' in shishen_map or '劫财' in shishen_map
            has_yin = len(yin_gans) >= 1
            is_shenqiang = has_bijie or has_yin
            # 印星重（有本气根+透干）+ 身强 + 透七杀 → 身强印重透煞
            if yin_has_benqi_root and len(yin_gans) >= 1 and is_shenqiang:
                sha_gans = shishen_map.get('七杀', [])
                breaks.append({
                    'type': '身强印重透煞',
                    'severity': 'high',
                    'detail': f'印格印星重（有本气根+透干）又透七杀{"".join(sha_gans)}，身强印重透煞，印星太旺反为偏颇',
                })
        # (3) 透煞生印又透财 — 《子平真诠》第九章带忌
        # "透煞以生印，而又透财，以去印存煞"
        # 印用煞生，但财来去印，煞失去印的调和，反为祸
        if '七杀' in shishen_map and ('正财' in shishen_map or '偏财' in shishen_map):
            sha_gans = shishen_map.get('七杀', [])
            cai_gans = shishen_map.get('正财', []) + shishen_map.get('偏财', [])
            breaks.append({
                'type': '透煞生印又透财',
                'severity': 'medium',
                'detail': f'印格透煞{"".join(sha_gans)}生印又透财{"".join(cai_gans)}，财去印存煞，煞失印调反为祸',
            })

    # ── 食神格破格 ──
    # 《子平真诠》"食格败：食神逢枭，或生财露煞"
    # 《子平真诠》第九章带忌："食神带煞印而又逢财"
    if '食神格' in pattern_name:
        # (1) 枭神夺食 — 偏印克食神
        # 《子平真诠》"食神逢枭"：偏印克食神，食神被夺
        if '偏印' in shishen_map:
            breaks.append({
                'type': '枭神夺食',
                'severity': 'high',
                'detail': f'食神格天干透偏印{"".join(shishen_map["偏印"])}，枭神夺食',
            })
        # (2) 生财露煞 — 食神生财但天干又透七杀
        # 食→财→杀，杀得财助反为祸
        # 《子平真诠》"煞逢食制" — 若有食神制杀，则七杀受制不为病
        # 注意：食神格本身已有食神，食神制杀即格中食神克制七杀
        # 但"生财露煞"特指食神生财→财生杀的传递链，食神已去生财而非制杀
        # 故此处仍标记破格，但若天干另有食伤（非月令食神）制杀则可化解
        if ('正财' in shishen_map or '偏财' in shishen_map) and '七杀' in shishen_map:
            # 检查是否有伤官制杀（食神已去生财，但伤官可制杀）
            has_shangguan_zhi_sha = '伤官' in shishen_map
            if not has_shangguan_zhi_sha:
                sha_gans = shishen_map.get('七杀', [])
                breaks.append({
                    'type': '生财露煞',
                    'severity': 'high',
                    'detail': f'食神格生财又透七杀{"".join(sha_gans)}，食神生财、财生杀，杀得财助为祸',
                })
        # (3) 带忌：食神带煞印而又逢财 — 《子平真诠》第九章带忌
        # "食神带煞印而又逢财"：食神格带煞印（杀印相生），但财星破印，
        # 印星被破则杀失去印的调和，杀直接攻身
        if '七杀' in shishen_map and ('正印' in shishen_map or '偏印' in shishen_map):
            if '正财' in shishen_map or '偏财' in shishen_map:
                cai_gans = shishen_map.get('正财', []) + shishen_map.get('偏财', [])
                breaks.append({
                    'type': '煞印逢财',
                    'severity': 'medium',
                    'detail': f'食神格带煞印又逢财{"".join(cai_gans)}，财破印则杀失印调，杀攻身为祸',
                })

    # ── 七杀格破格 ──
    # 《子平真诠》"煞格败：七煞逢财无制"
    # 《子平真诠》第九章带忌："七煞逢食制而又逢印"
    if '七杀格' in pattern_name:
        if '正财' in shishen_map or '偏财' in shishen_map:
            has_shishen_zhi_sha = '食神' in shishen_map or '正印' in shishen_map or '偏印' in shishen_map
            if not has_shishen_zhi_sha:
                cai_gans = shishen_map.get('正财', []) + shishen_map.get('偏财', [])
                breaks.append({
                    'type': '财党杀无制',
                    'severity': 'high',
                    'detail': f'七杀格天干透财星{"".join(cai_gans)}，无食神/印星制杀，财党杀为祸',
                })
        # 带忌：七煞逢食制而又逢印 — 食神制杀但印星泄食护杀
        # 《子平真诠》第九章"七煞逢食制而又逢印"
        # 食神制杀为成格，但印星克食护杀，制杀之力被削弱
        if '食神' in shishen_map and ('正印' in shishen_map or '偏印' in shishen_map):
            yin_gans = shishen_map.get('正印', []) + shishen_map.get('偏印', [])
            breaks.append({
                'type': '食制逢印',
                'severity': 'medium',
                'detail': f'七杀格食神制杀，但又透印星{"".join(yin_gans)}，印泄食护杀，制杀不力',
            })

    # ── 伤官格破格 ──
    # 《子平真诠》"伤官格败：伤官非金水而见官，或生财生带煞，或佩印而伤轻身旺"
    if '伤官格' in pattern_name:
        is_jin_dm = day_master in ('庚', '辛')
        # (1) 伤官见官（金水伤官除外）
        # 《子平真诠》"伤官见官为祸百端"
        # 金水伤官例外：《子平真诠》"金水伤官喜见官" — 庚辛日主（金日主）
        # 伤官为水，见官（火）反为调候所需，不标记破格
        if '正官' in shishen_map and not is_jin_dm:
            breaks.append({
                'type': '伤官见官',
                'severity': 'high',
                'detail': f'伤官格天干透正官{"".join(shishen_map["正官"])}，伤官见官为祸百端',
            })
        # (2) 生财带煞 — 《子平真诠》"伤官生财生带煞"
        # 伤官生财又透七杀，财转党杀，杀得财助反为祸
        # 《子平真诠》"煞逢食制" — 若有食神制杀，则七杀受制不为病
        if ('正财' in shishen_map or '偏财' in shishen_map) and '七杀' in shishen_map:
            has_shishen_zhi_sha = '食神' in shishen_map
            if not has_shishen_zhi_sha:
                sha_gans = shishen_map.get('七杀', [])
                breaks.append({
                    'type': '生财带煞',
                    'severity': 'high',
                    'detail': f'伤官格生财又透七杀{"".join(sha_gans)}，财转党杀，杀得财助为祸',
                })
        # (3) 佩印无根 — 《子平真诠》"佩印而伤轻身旺"之延伸
        # 伤官格佩印但印星无本气根，印星制伤无力
        if ('正印' in shishen_map or '偏印' in shishen_map) and not is_jin_dm:
            yin_gans = shishen_map.get('正印', []) + shishen_map.get('偏印', [])
            # 检查印星是否有根（地支藏干中有印星五行本气根）
            yin_wx_set = set()
            for yg in yin_gans:
                wx = GAN_WUXING.get(yg, '')
                if wx:
                    yin_wx_set.add(wx)
            yin_has_root = False
            for part in bazi_parts:
                if len(part) < 2:
                    continue
                for cg, ql in get_canggan(part[1]):
                    if GAN_WUXING.get(cg, '') in yin_wx_set and ql == '本气':
                        yin_has_root = True
                        break
                if yin_has_root:
                    break
            if not yin_has_root:
                breaks.append({
                    'type': '佩印无根',
                    'severity': 'medium',
                    'detail': f'伤官格佩印{"".join(yin_gans)}但印星无本气根，佩印无力',
                })
        # (4) 伤轻身旺佩印 — 《子平真诠》第九章带忌"佩印而伤轻身旺"
        # 伤官格佩印，但伤官轻（无本气根）且身旺，印重无制反为破格
        # 身旺：天干有比劫或印星（与disease.py一致）
        if ('正印' in shishen_map or '偏印' in shishen_map) and not is_jin_dm:
            sg_gans = shishen_map.get('伤官', [])
            # 伤官"轻"：无本气根
            sg_wx_set = set()
            for sg_g in sg_gans:
                wx = GAN_WUXING.get(sg_g, '')
                if wx:
                    sg_wx_set.add(wx)
            sg_has_benqi = False
            for part in bazi_parts:
                if len(part) < 2:
                    continue
                for cg, ql in get_canggan(part[1]):
                    if GAN_WUXING.get(cg, '') in sg_wx_set and ql == '本气':
                        sg_has_benqi = True
                        break
                if sg_has_benqi:
                    break
            has_bijie = '比肩' in shishen_map or '劫财' in shishen_map
            has_yin = '正印' in shishen_map or '偏印' in shishen_map
            is_shenqiang = has_bijie or has_yin
            if not sg_has_benqi and is_shenqiang:
                yin_gans = shishen_map.get('正印', []) + shishen_map.get('偏印', [])
                breaks.append({
                    'type': '伤轻身旺佩印',
                    'severity': 'medium',
                    'detail': f'伤官格佩印{"".join(yin_gans)}但伤官轻无本气根且身旺，印重无制反为破格',
                })
        # (5) 伤官生财而财逢合 — 《子平真诠》第九章带忌
        # "伤官生财而财又逢合"：伤官生财但财星被合去，财星无用
        if ('正财' in shishen_map or '偏财' in shishen_map):
            cai_gans = shishen_map.get('正财', []) + shishen_map.get('偏财', [])
            for cg in cai_gans:
                he_partner = _GAN_HE_PARTNER.get(cg, '')
                if he_partner:
                    for g in gans:
                        if g == day_master or g == cg:
                            continue
                        if g == he_partner:
                            breaks.append({
                                'type': '伤官生财财逢合',
                                'severity': 'medium',
                                'detail': f'伤官格生财{cg}，但{cg}与{he_partner}相合，财星被合去',
                            })
                            break

    return breaks


# 格局用神/忌神映射表
# 《子平真诠·论用神》："财官印食顺用，煞伤劫刃逆用"
# 顺用：财喜食生+官护财；官喜财生+印护官；印喜官杀生+比劫护；食喜身旺生+财护食
# 逆用：七杀喜食神制伏；伤官喜佩印制+生财化伤；阳刃喜官杀制伏；月劫喜透官制+食化劫
PATTERN_YONGSHEN = {
    # 正官格：顺用，官喜财生+印护官
    '正官格': {'用神': ['财星', '印星'], '忌神': ['伤官', '七杀']},
    # 七杀格：逆用，杀喜食神制伏或印星化杀
    '七杀格': {'用神': ['食神', '印星'], '忌神': ['财星(无制时)']},
    # 正财格：顺用，财喜食伤生+官星护财
    '正财格': {'用神': ['食伤', '官星'], '忌神': ['比劫']},
    # 偏财格：同正财格
    '偏财格': {'用神': ['食伤', '官星'], '忌神': ['比劫']},
    # 正印格：顺用，印喜官杀生+比劫护印
    '正印格': {'用神': ['官星', '比劫(身弱时)'], '忌神': ['财星']},
    # 偏印格：子平真诠将印格统一处理，印格顺用"印喜官煞相生、劫财护印"
    # 财星是印格忌神（财破印），不应作为偏印格用神
    '偏印格': {'用神': ['官星', '比劫'], '忌神': ['财星']},
    # 食神格：顺用，食喜身旺相生、生财护食
    '食神格': {'用神': ['财星', '比劫'], '忌神': ['偏印']},
    # 伤官格：逆用，伤官喜佩印制+生财化伤
    '伤官格': {'用神': ['印星', '财星'], '忌神': ['官星(见官)']},
    # 建禄格：月令比劫不入正格，须寻财官煞食透干取用
    '建禄格': {'用神': ['官杀', '财星', '食伤'], '忌神': ['比劫']},
    # 月劫格：同建禄格
    '月劫格': {'用神': ['官杀', '财星', '食伤'], '忌神': ['比劫']},
    # 羊刃格：逆用，刃喜官杀制伏
    '羊刃格': {'用神': ['官杀'], '忌神': ['财星(无制时)']},
    # 从强格：顺势，用印比助旺（印星为首选，比劫为次选）
    '从强格': {'用神': ['印星', '比劫'], '忌神': ['官杀', '财星']},
    # 假从强格：同从强格方向
    '假从强格': {'用神': ['印星', '比劫'], '忌神': ['官杀', '财星']},
    # 从财格：顺势，用食伤生财
    '从财格': {'用神': ['食伤', '财星'], '忌神': ['比劫', '印星']},
    # 从官杀格：顺势，用财生官杀
    '从官杀格': {'用神': ['官杀', '财星'], '忌神': ['比劫', '印星']},
    # 从儿格：顺势，用食伤生财（《滴天髓》"只要吾儿又得儿"）
    # 忌神：印星(克食伤)、官杀(逆势)；比劫生食伤不逆势，不为忌
    '从儿格': {'用神': ['食伤', '财星'], '忌神': ['印星', '官杀']},
    # 从势格：顺势，用最强之势
    '从势格': {'用神': ['最强之势'], '忌神': ['逆势五行']},
    # 化气格：用化神五行
    '化气格': {'用神': ['化神五行'], '忌神': ['克化神五行']},
}


def screen_pattern(day_master: str, bazi_parts: list[str],
                   wangshuai: dict, element_forces: dict) -> dict:
    """格局筛查主入口 — 四层筛选 L0→L3

    按《子平真诠》"用神专寻月令"原则，从月令出发逐层筛查格局。
    每层命中即返回，不再向下。若四层均未命中，返回"待定"。

    Args:
        day_master: 日主天干，如 '甲'
        bazi_parts: 四柱干支列表，如 ['甲子', '丙寅', '甲辰', '壬申']
                    每个元素为2字符字符串（天干+地支）
        wangshuai: 旺衰判定结果 dict，含以下关键字段：
            - 'is_extreme_strong': bool  — 是否极旺
            - 'is_strong': bool          — 是否身旺
            - 'is_extreme_weak': bool    — 是否极弱
            - 'is_weak': bool            — 是否身弱
        element_forces: 五行力量分析结果 dict，含以下关键字段：
            - 'percent': dict            — 原始五行百分比，如 {'木': 40, '火': 20, ...}
            - 'percent_adjusted': dict   — 合化修正后百分比
            - 'hehua': dict              — 合化信息，含 'gan_he' 列表

    Returns:
        dict: 格局判定结果，含以下字段：
            - 'pattern': str             — 格局名称，如 '正官格'、'从强格'
            - 'candidates': list         — 候选格局列表
            - 'layer': int               — 命中层级（0-3）
            - 'type': str                — 格局类型描述
            - 'confidence': float        — 置信度（0-1）
            - 'reason': str              — 判定理由
            - 'yongshen_direction': str  — 用神方向
            - 'wangshuai': dict          — 旺衰判定（透传）
            - 'break_conditions': list   — 破格条件（可能不存在）
            - 'formation': dict          — 方局/三合信息（可能不存在）
            - 'trace': dict              — 筛查轨迹，含 layers_checked/layers_missed/layer_details
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx or len(bazi_parts) < 2:
        return {'pattern': '数据不足', 'candidates': [], 'note': '日主或八字数据缺失',
                'trace': {'layers_checked': [], 'layers_missed': ['L0', 'L1', 'L2', 'L3']}}

    month_zhi = bazi_parts[1][1] if len(bazi_parts[1]) >= 2 else ''
    if not month_zhi:
        return {'pattern': '数据不足', 'candidates': [], 'note': '月支缺失',
                'trace': {'layers_checked': [], 'layers_missed': ['L0', 'L1', 'L2', 'L3']}}

    # 格局阈值使用修正前百分比(percent)，非修正后(percent_adjusted)。
    # 原因：合化修正改变了五行分布，但格局框架应在"原局基础力量"上判定；
    # 化气格单独通过 element_forces.hehua 检测，使用 percent_adjusted。
    # 但假从强格需要使用修正后百分比，因为六合（如巳申合水）会显著改变五行分布。
    pct = element_forces.get('percent', {})
    candidates = []
    gans = [p[0] for p in bazi_parts if len(p) >= 1]
    trace = {'layers_checked': [], 'layers_missed': [], 'layer_details': {}}

    # 计算印比合计（日主五行 + 生日主五行）
    # 如甲木日主：印比 = 木(比) + 水(印)
    yin_bi_wx = {dm_wx, SHENG_MAP.get(dm_wx, '')}
    yin_bi_pct = sum(pct.get(wx, 0) for wx in yin_bi_wx)

    # 计算克泄耗合计（除印比外的三行）
    # 克我(官杀) + 我克(财星) + 我生(食伤)
    ke_xie_hao_wx = set()
    for wx in ['木', '火', '土', '金', '水']:
        if wx not in yin_bi_wx:
            ke_xie_hao_wx.add(wx)
    ke_xie_hao_pct = sum(pct.get(wx, 0) for wx in ke_xie_hao_wx)

    # L0：特殊格局（化气/专旺/从格/两行成象）
    layer0_result = _screen_layer0(day_master, dm_wx, month_zhi, bazi_parts,
                                    wangshuai, pct, yin_bi_pct, ke_xie_hao_pct, gans,
                                    element_forces)
    trace['layers_checked'].append('L0')
    if layer0_result:
        candidates.append(layer0_result)
        trace['layer_details']['L0'] = {'hit': True, 'reason': layer0_result['reason']}
        result = _finalize_pattern(candidates, wangshuai)
        result['trace'] = trace
        return result
    trace['layers_missed'].append('L0')
    trace['layer_details']['L0'] = {'hit': False, 'reason': '无专旺/从格/两行成象匹配'}

    # L1：月令本气透干
    layer1_result = _screen_layer1(day_master, month_zhi, gans, bazi_parts)
    trace['layers_checked'].append('L1')
    if layer1_result:
        candidates.append(layer1_result)
        trace['layer_details']['L1'] = {'hit': True, 'reason': layer1_result['reason']}
        result = _finalize_pattern(candidates, wangshuai)
        result['trace'] = trace
        return result
    trace['layers_missed'].append('L1')
    trace['layer_details']['L1'] = {'hit': False, 'reason': '月令本气未透干'}

    # L2：月令中气透干
    layer2_result = _screen_layer2(day_master, month_zhi, gans, bazi_parts)
    trace['layers_checked'].append('L2')
    if layer2_result:
        candidates.append(layer2_result)
        trace['layer_details']['L2'] = {'hit': True, 'reason': layer2_result['reason']}
        result = _finalize_pattern(candidates, wangshuai)
        result['trace'] = trace
        return result
    trace['layers_missed'].append('L2')
    trace['layer_details']['L2'] = {'hit': False, 'reason': '月令中气未透干或本气已透'}

    # L3：暗格/比劫月令
    layer3_result = _screen_layer3(day_master, dm_wx, month_zhi, gans, bazi_parts)
    trace['layers_checked'].append('L3')
    if layer3_result:
        candidates.append(layer3_result)
        trace['layer_details']['L3'] = {'hit': True, 'reason': layer3_result['reason']}
        result = _finalize_pattern(candidates, wangshuai)
        result['trace'] = trace
        return result
    trace['layers_missed'].append('L3')
    trace['layer_details']['L3'] = {'hit': False, 'reason': '月令本气非比劫且已透干'}

    # 四层均未命中，属特殊格局
    result = {'pattern': '待定', 'candidates': candidates,
              'note': '六层筛查未命中，属特殊格局，需人工复核'}
    result['trace'] = trace
    return result


def _screen_layer0(day_master, dm_wx, month_zhi, bazi_parts,
                   wangshuai, pct, yin_bi_pct, ke_xie_hao_pct, gans,
                   element_forces=None):
    """L0：特殊格局筛查 — 化气/专旺/从格/两行成象

    检测顺序：
    1. 化气格：日主参与天干合化，化神五行修正后占比≥60%
    2. 专旺格：日主五行占绝对优势 + 方局/三合成局
    3. 从强格/假从强格：印比合计≥80%且无强根
    4. 两行成象格：克泄耗两行合计≥85%
    5. 从财格/从官杀格/从儿格/从势格：日主极弱，克泄耗成势
    6. 建禄/羊刃月令的从强优先判定

    Args:
        day_master: 日主天干
        dm_wx: 日主五行
        month_zhi: 月支地支
        bazi_parts: 四柱干支列表
        wangshuai: 旺衰判定结果
        pct: 原始五行百分比 dict
        yin_bi_pct: 印比合计百分比
        ke_xie_hao_pct: 克泄耗合计百分比
        gans: 四天干列表
        element_forces: 五行力量完整结果（含 hehua/percent_adjusted）

    Returns:
        dict|None: 命中返回格局结果 dict，未命中返回 None
    """
    dm_pct = pct.get(dm_wx, 0)

    dm_root_in_branch = _check_dm_root_in_branches(day_master, dm_wx, bazi_parts)
    # 《滴天髓》"无地人元"：本气根和中气根都属"人元"，有则从格不真
    has_strong_root = dm_root_in_branch['has_benqi_root'] or dm_root_in_branch['has_zhongqi_root']

    jianlu_zhi = JIANLU_MAP.get(day_master, '')
    yangren_zhi = YANGREN_MAP.get(day_master, '')
    is_jianlu_yangren_month = month_zhi in (jianlu_zhi, yangren_zhi)

    # ── 1. 化气格检测 ──
    # 建禄/羊刃月令不入化气格（禄刃月令优先走建禄/羊刃格路径）
    if element_forces is not None and not is_jianlu_yangren_month:
        hehua = element_forces.get('hehua', {})
        pct_adj = element_forces.get('percent_adjusted', pct)
        for item in hehua.get('gan_he', []):
            if day_master in item['gans'] and item.get('adjacent', False):
                hua_wx = item['hua_wx']
                hua_pct = pct_adj.get(hua_wx, 0)
                # 化神五行修正后占比≥60%：化气格成立的最低门槛
                # 阈值依据：化气需化神力量占主导，60%为经验下限
                if hua_pct >= 60:
                    hua_names = {'土': '化土格', '金': '化金格', '水': '化水格',
                                 '木': '化木格', '火': '化火格'}
                    # 《滴天髓·化象》"化得真者只论化"
                    # 《子平真诠·论杂格》"要化出之物，得时乘令"
                    # 月令当令=真化(confidence=0.85)，不当令=假化(confidence=0.60)
                    hua_season_set = HUA_SEASON_MAP.get(hua_wx, set())
                    is_season = month_zhi in hua_season_set
                    if is_season:
                        confidence = 0.85
                        hua_type = '真化'
                    else:
                        confidence = 0.60
                        hua_type = '假化'
                    # 地支根局提升 confidence +0.05（有方局/三合佐化）
                    formation = _check_formation(bazi_parts, hua_wx)
                    if formation['has_formation']:
                        confidence = min(confidence + 0.05, 0.95)
                    # 破格检测：争合/妒合/克化神
                    break_conditions = _check_hua_break(day_master, hua_wx, gans, bazi_parts)
                    return {
                        'layer': 0, 'type': '化气格',
                        'pattern': hua_names.get(hua_wx, f'化{hua_wx}格'),
                        'confidence': confidence,
                        'reason': f'日主{day_master}参与合化，化神{hua_wx}(修正后)占比{hua_pct}%≥60%，{hua_type}',
                        'yongshen_direction': f'化神{hua_wx}',
                        'break_conditions': break_conditions,
                    }

    # ── 2. 专旺格检测 ──
    # 专旺格传统名称：木=曲直格，火=炎上格，土=稼穑格，金=从革格，水=润下格
    # 《子平真诠》建禄/羊刃月令优先走建禄/羊刃格路径，不入专旺格
    # 例外：非建禄/羊刃月令时，有方局/三合+月令当令 → 专旺格
    zhuanwang_names = {'木': '曲直格', '火': '炎上格', '土': '稼穑格', '金': '从革格', '水': '润下格'}
    zhuanwang_trigger = False
    zhuanwang_reason_base = ''

    # 专旺触发条件（满足任一）：
    # 条件A：日主五行占比≥80%（绝对优势）
    # 条件B：日主五行占比≥50% 且 印比合计≥75%（相对优势+印比合力）
    # 但建禄/羊刃月令不入专旺格（月令定格优先于方局）
    if not is_jianlu_yangren_month:
        if dm_pct >= 80:
            zhuanwang_trigger = True
            zhuanwang_reason_base = f'日主{dm_wx}行占{dm_pct}%≥80%'
        elif dm_pct >= 50 and yin_bi_pct >= 75:
            zhuanwang_trigger = True
            zhuanwang_reason_base = f'日主{dm_wx}行占{dm_pct}%≥50%，印比合计{yin_bi_pct}%≥75%'

    if zhuanwang_trigger:
        formation = _check_formation(bazi_parts, dm_wx)
        if formation['has_formation']:
            # 《子平真诠·论杂格》"有取五行一方秀气者，取甲乙全亥卯未、寅卯辰"
            # 专旺格要求完整方局/三合，半合/半会降级为从强格
            is_full_formation = formation['type'] in ('会方', '三合')
            if is_full_formation:
                # 月令当令检查：不当令降低 confidence 0.15
                season = _check_month_season(month_zhi, dm_wx)
                confidence = 0.90
                if not season['is_season']:
                    confidence -= 0.15
                # 破格条件扣减 confidence：high=-0.2, medium=-0.1
                break_conditions = _check_zhuanwang_break(day_master, dm_wx, bazi_parts, gans)
                for bc in break_conditions:
                    if bc['severity'] == 'high':
                        confidence -= 0.2
                    elif bc['severity'] == 'medium':
                        confidence -= 0.1
                reason = zhuanwang_reason_base + f'，{formation["type"]}{"".join(formation["branches"])}成局'
                if not season['is_season']:
                    reason += '，月令不当令'
                return {
                    'layer': 0, 'type': '专旺格', 'pattern': zhuanwang_names.get(dm_wx, '专旺格'),
                    'confidence': confidence, 'reason': reason,
                    'yongshen_direction': '印星比劫',
                    'formation': formation,
                    'break_conditions': break_conditions,
                }
            # 半合/半会：降级为从强格
            # 《子平真诠》要求完整方局/三合，半合/半会不足以成专旺格
            # 印比≥80%且无强根 → 从强格（顺势）
            if yin_bi_pct >= 80 and not has_strong_root:
                return {
                    'layer': 0, 'type': '从强格', 'pattern': '从强格',
                    'confidence': 0.80,
                    'reason': zhuanwang_reason_base + f'，仅有{formation["type"]}{"".join(formation["branches"])}，非完整方局/三合，降级为从强格',
                    'yongshen_direction': '印星比劫',
                }
        else:
            # 无方局/三合：根据印比力量和根气决定降级方向
            if yin_bi_pct >= 80 and not has_strong_root:
                # 印比极旺且无根 → 从强格
                return {
                    'layer': 0, 'type': '从强格', 'pattern': '从强格',
                    'confidence': 0.85,
                    'reason': zhuanwang_reason_base + '但无方局/三合局，降级为从强格',
                    'yongshen_direction': '印星比劫',
                }
            else:
                # 有根或印比不够 → 身旺（普通旺衰）
                return {
                    'layer': 0, 'type': '身旺', 'pattern': '身旺',
                    'confidence': 0.75,
                    'reason': zhuanwang_reason_base + '但无方局/三合局，降级为身旺',
                    'yongshen_direction': '克泄耗',
                }

    # ── 3. 从强格/假从强格检测（非专旺触发条件） ──
    # 印比合计≥80%且无本气/中气根 → 从强格
    # 阈值80%：印比力量需占绝对主导才能"从强"
    # 但建禄/羊刃月令不从强（走建禄/羊刃格路径）
    # 《渊海子平》：官印双全时不应判从强——官杀力量≥15%则有制身之力
    # 《滴天髓·从象》"日主孤立无气"要求"绝无一毫生扶之意"，
    # 官杀在天干有一定力量（≥15%）说明异党有势，不应从强
    guansha_pct = sum(pct.get(wx, 0) for wx in [KE_MAP.get(dm_wx, '')] if wx)
    if yin_bi_pct >= 80 and not has_strong_root and not is_jianlu_yangren_month and guansha_pct < 15:
        return {
            'layer': 0, 'type': '从强格', 'pattern': '从强格',
            'confidence': 0.85,
            'reason': f'印比合计{yin_bi_pct}%≥80%，地支无本气根（真从强）',
            'yongshen_direction': '印星比劫',
        }

    # 建禄/羊刃月令不从强（走建禄/羊刃格路径）
    if not is_jianlu_yangren_month:
        # 极旺+印比≥80%+无根 → 从强格
        if yin_bi_pct >= 80 and wangshuai.get('is_extreme_strong', False):
            if not has_strong_root:
                return {
                    'layer': 0, 'type': '从强格', 'pattern': '从强格',
                    'confidence': 0.85,
                    'reason': f'印比合计{yin_bi_pct}%≥80%，日主极旺且地支无根（真从强）',
                    'yongshen_direction': '印星比劫',
                }
            else:
                # 有根不能从强，判身旺
                root_info = dm_root_in_branch['root_locations']
                return {
                    'layer': 0, 'type': '身旺',
                    'pattern': '身旺',
                    'confidence': 0.75,
                    'reason': f'印比合计{yin_bi_pct}%≥80%但地支有根（{root_info}），非从强格',
                    'yongshen_direction': '印星比劫',
                }

    # 阴干/阳干从强区分（假从强格）
    # 注："假从强格"为现代命理概念，古籍无此名目。
    # 古籍中"假从"均指日主弱→假从财/假从官杀：
    #   《滴天髓·假从》："日主弱矣，财官强矣，不能不从；中有比劫暗生，从之不真"
    #   《穷通宝鉴·五六月甲木》："或是己土，不见戊土，乃为假从"
    #   《穷通宝鉴·六月壬水》："或一派己土，此假从杀格"
    # 古籍"从"为日主弱→顺从财官，非日主强→顺从印比。
    # 《三命通会》"独弱从强，弃命就财"亦为日主弱→从财之义。
    # 此处"假从强格"指日主有根但印比极旺、异党极弱的边界情况，
    # 属于现代命理对古籍"从"概念的扩展延伸，非古籍原义。
    YIN_STEMS = {'乙', '丁', '己', '辛', '癸'}
    is_yin_gan = day_master in YIN_STEMS
    if not is_jianlu_yangren_month and not has_strong_root:
        if yin_bi_pct >= 80 and wangshuai.get('is_strong', False):
            if not is_yin_gan and not wangshuai.get('is_extreme_strong', False):
                # 阳干+身旺（非极旺）→ 假从强格
                # 阳干天性刚强，虽地支无根但旺衰未至极旺，不能真从
                return {
                    'layer': 0, 'type': '假从强格', 'pattern': '假从强格',
                    'confidence': 0.65,
                    'reason': f'阳干{day_master}天性刚强，虽地支无根但旺衰未至极，假从强格',
                    'yongshen_direction': '印星比劫',
                }
            # 阴干+身旺+无根 → 真从强格
            return {
                'layer': 0, 'type': '从强格', 'pattern': '从强格',
                'confidence': 0.85,
                'reason': f'印比合计{yin_bi_pct}%≥80%，地支无根（阴干{day_master}更易真从）',
                'yongshen_direction': '印星比劫',
            }
        elif yin_bi_pct >= 70 and wangshuai.get('is_strong', False) and is_yin_gan:
            # 阴干+印比≥70%+身旺+无根 → 假从强格
            # 阈值70%：阴干柔顺，印比70%即可假从（低于80%真从门槛）
            return {
                'layer': 0, 'type': '假从强格', 'pattern': '假从强格',
                'confidence': 0.60,
                'reason': f'阴干{day_master}柔顺，印比{yin_bi_pct}%≥70%，地支无根，假从强格',
                'yongshen_direction': '印星比劫',
            }

    # ── 4. 两行成象格检测 ──
    # 克泄耗≥85%且至少2个五行各有势力（pct>5）
    # 若克泄耗仅1行主导，自然掉入下方从格检查
    # 阈值85%：两行成象需克泄耗占绝对主导
    if ke_xie_hao_pct >= 85:
        two_wx = [wx for wx in ['木', '火', '土', '金', '水']
                   if wx not in {dm_wx, SHENG_MAP.get(dm_wx, '')} and pct.get(wx, 0) > 5]
        if len(two_wx) >= 2:
            return {
                'layer': 0, 'type': '两行成象格', 'pattern': f'{two_wx[0]}{two_wx[1]}成象格',
                'confidence': 0.75, 'reason': '克泄耗两行合计≥85%',
                'yongshen_direction': '顺两行气势',
                '_element_forces': element_forces,
            }

    # ── 5. 从格检测（从财/从官杀/从儿/从势） ──
    # 检查地支藏干是否有日主比劫本气根或中气根（破从格）
    # 《滴天髓》"无地人元"：本气根和中气根都属"人元"，有则从格不真
    has_bijie_strong_root = False
    for part in bazi_parts:
        if len(part) < 2:
            continue
        for cg, ql in get_canggan(part[1]):
            if GAN_WUXING.get(cg, '') == dm_wx and ql in ('本气', '中气'):
                has_bijie_strong_root = True
                break
        if has_bijie_strong_root:
            break

    # 从财格/从官杀格：日主极弱 + 克泄耗≥60% + 财星/官杀成势
    # 阈值60%：克泄耗需占主导但不必绝对优势
    if wangshuai.get('is_extreme_weak', False) and ke_xie_hao_pct >= 60:
        shishen_counts = _count_shishen_categories(day_master, gans, bazi_parts, include_canggan=False)
        # 《滴天髓》"绝无一毫生扶之意"：印星和比劫均不可有
        bijie_free = shishen_counts.get('比劫', 0) == 0 and not has_bijie_strong_root
        yin_free = shishen_counts.get('印星', 0) == 0

        # 从财格：财星≥3 + 无比劫无印星
        # 财星≥3：天干中财星数量（不含藏干），确保财星成势
        if shishen_counts.get('财星', 0) >= 3 and bijie_free and yin_free:
            cai_wx = WO_KE_MAP.get(dm_wx, '')
            formation = _check_formation(bazi_parts, cai_wx)
            # 有方局/三合=真从(0.85)，无=假从(0.65)
            if formation['has_formation']:
                result = {
                    'layer': 0, 'type': '从财格', 'pattern': '从财格',
                    'confidence': 0.85,
                    'reason': f'日主极弱，财星成势，{formation["type"]}{"".join(formation["branches"])}（真从）',
                    'yongshen_direction': '食伤生财',
                    'formation': formation, 'is_true': True,
                }
            else:
                result = {
                    'layer': 0, 'type': '从财格', 'pattern': '从财格',
                    'confidence': 0.65,
                    'reason': '日主极弱，财星成势，地支无财星方局/三合局（假从）',
                    'yongshen_direction': '食伤生财',
                    'formation': formation, 'is_true': False,
                }
            break_conds = _build_break_conditions(dm_root_in_branch)
            if break_conds:
                result['break_conditions'] = break_conds
            return result

        # 从官杀格：官杀≥3 + 无比劫无印星
        if shishen_counts.get('官杀', 0) >= 3 and bijie_free and yin_free:
            guan_wx = KE_MAP.get(dm_wx, '')
            formation = _check_formation(bazi_parts, guan_wx)
            if formation['has_formation']:
                result = {
                    'layer': 0, 'type': '从官杀格', 'pattern': '从官杀格',
                    'confidence': 0.85,
                    'reason': f'日主极弱，官杀成势，{formation["type"]}{"".join(formation["branches"])}（真从）',
                    'yongshen_direction': '财生官',
                    'formation': formation, 'is_true': True,
                }
            else:
                result = {
                    'layer': 0, 'type': '从官杀格', 'pattern': '从官杀格',
                    'confidence': 0.65,
                    'reason': '日主极弱，官杀成势，地支无官杀方局/三合局（假从）',
                    'yongshen_direction': '财生官',
                    'formation': formation, 'is_true': False,
                }
            break_conds = _build_break_conditions(dm_root_in_branch)
            if break_conds:
                result['break_conditions'] = break_conds
            return result

    # 从儿格：食伤成势 + 财星承接
    # 《滴天髓》："从儿不管身强弱，只要吾儿又得儿"
    # 不要求极弱，但日主不可身旺有强根
    # "吾儿又得儿"：食伤（儿）须有财星（儿之儿）承接，否则降为食伤泄气
    if ke_xie_hao_pct >= 60:
        shishen_counts = _count_shishen_categories(day_master, gans, bazi_parts, include_canggan=False)
        bijie_free = shishen_counts.get('比劫', 0) == 0 and not has_bijie_strong_root
        yin_free = shishen_counts.get('印星', 0) == 0
        if shishen_counts.get('食伤', 0) >= 3 and bijie_free and yin_free:
            if shishen_counts.get('财星', 0) >= 1:
                # 财星≥1：食伤有承接，从儿格成立
                result = {
                    'layer': 0, 'type': '从儿格', 'pattern': '从儿格',
                    'confidence': 0.80,
                    'reason': '食伤成势，财星承接（吾儿又得儿），日主无强根',
                    'yongshen_direction': '食伤生财',
                }
                break_conds = _build_break_conditions(dm_root_in_branch)
                if break_conds:
                    result['break_conditions'] = break_conds
                return result
            else:
                # 无财星：食伤无承接，降为食伤泄气
                return {
                    'layer': 0, 'type': '食伤泄气', 'pattern': '食伤泄气',
                    'confidence': 0.60,
                    'reason': '食伤成势但无财星承接（吾儿未得儿），降为食伤泄气',
                    'yongshen_direction': '待定',
                }

    # 从势格：日主极弱，克泄耗多类混杂，无单一主导
    # 《滴天髓》："五阴从势无情义"
    # 与从财/从官杀的区别：克泄耗多类并存（财+官+食伤≥2类），无单一≥3
    if wangshuai.get('is_extreme_weak', False) and ke_xie_hao_pct >= 60:
        shishen_counts = _count_shishen_categories(day_master, gans, bazi_parts, include_canggan=False)
        # 《滴天髓》"绝无一毫生扶之意"：印星和比劫均不可有
        bijie_free = shishen_counts.get('比劫', 0) == 0 and not has_bijie_strong_root
        yin_free = shishen_counts.get('印星', 0) == 0
        if bijie_free and yin_free:
            ke_xie_types = [cat for cat in ['财星', '官杀', '食伤']
                           if shishen_counts.get(cat, 0) >= 1]
            # 无单一主导：各类克泄耗均<3
            no_dominance = all(shishen_counts.get(cat, 0) < 3 for cat in ke_xie_types)
            if len(ke_xie_types) >= 2 and no_dominance:
                result = {
                    'layer': 0, 'type': '从势格', 'pattern': '从势格',
                    'confidence': 0.65,
                    'reason': f'日主极弱，克泄耗{",".join(ke_xie_types)}混杂无单一主导，从势格',
                    'yongshen_direction': '顺势而为',
                    '_element_forces': element_forces,
                }
                break_conds = _build_break_conditions(dm_root_in_branch)
                if break_conds:
                    result['break_conditions'] = break_conds
                return result

    # ── 6. 建禄/羊刃月令的格局路径 ──
    # 《子平真诠》"用神专寻月令" — 月令为建禄/羊刃时走建禄/羊刃格路径
    # 但若已有方局/三合成局且月令当令，专旺格已在步骤2中优先判定
    # 此处仅处理无方局/三合的建禄/羊刃月令情况
    if month_zhi == JIANLU_MAP.get(day_master, ''):
        # 返回 None 让 L1/L3 处理建禄格
        return None

    if month_zhi == YANGREN_MAP.get(day_master, ''):
        # 返回 None 让 L3 处理羊刃格
        return None

    return None


def _screen_layer1(day_master, month_zhi, gans, bazi_parts):
    """L1：月令本气透干筛查

    《子平真诠》"用神专寻月令" — 月支本气天干出现在四天干中，
    以该十神定格局名称。本气为比劫则转入建禄月劫格处理。

    Args:
        day_master: 日主天干
        month_zhi: 月支地支
        gans: 四天干列表（含日主）
        bazi_parts: 四柱干支列表

    Returns:
        dict|None: 命中返回格局结果 dict，未命中返回 None
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    canggan = get_canggan(month_zhi)
    if not canggan:
        return None
    benqi_gan = canggan[0][0]  # 本气天干（藏干列表第一个）
    if benqi_gan in gans:
        ss = derive_shishen(day_master, benqi_gan)
        # 本气为比劫：不入正格，转入建禄月劫格
        if ss in ('比肩', '劫财'):
            return _build_jianlu_yuejie(day_master, dm_wx=dm_wx, month_zhi=month_zhi,
                                        gans=gans, bazi_parts=bazi_parts,
                                        benqi_ss=ss, benqi_gan=benqi_gan,
                                        layer=1, layer_type='月令本气比劫透干')
        # 本气非比劫：以十神定格
        pattern_name = f'{ss}格' if ss else '未知格'
        result = {
            'layer': 1, 'type': '月令本气透干', 'pattern': pattern_name,
            'confidence': 0.85, 'reason': f'月支{month_zhi}本气{benqi_gan}透干，十神为{ss}',
            'yongshen_direction': _get_yongshen_direction(ss),
        }
        break_conditions = _check_zhengge_break(day_master, dm_wx, bazi_parts, gans, pattern_name)
        if break_conditions:
            result['break_conditions'] = break_conditions
        return result
    return None


def _screen_layer2(day_master, month_zhi, gans, bazi_parts):
    """L2：月令中气透干筛查

    本气未透但中气透干时，以中气十神定格。
    前提：本气未透干（本气透干已在 L1 处理）。

    Args:
        day_master: 日主天干
        month_zhi: 月支地支
        gans: 四天干列表（含日主）
        bazi_parts: 四柱干支列表

    Returns:
        dict|None: 命中返回格局结果 dict，未命中返回 None
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    canggan = get_canggan(month_zhi)
    if len(canggan) < 2:
        return None  # 月支仅有一个藏干（无中气），无法走 L2
    zhongqi_gan = canggan[1][0]  # 中气天干（藏干列表第二个）
    benqi_gan = canggan[0][0]
    # 本气已透干 → L1 已处理，跳过
    if benqi_gan in gans:
        return None
    if zhongqi_gan in gans:
        ss = derive_shishen(day_master, zhongqi_gan)
        # 中气为比劫：转入建禄月劫格
        if ss in ('比肩', '劫财'):
            return _build_jianlu_yuejie(day_master, dm_wx=dm_wx, month_zhi=month_zhi,
                                        gans=gans, bazi_parts=bazi_parts,
                                        benqi_ss=ss, benqi_gan=zhongqi_gan,
                                        layer=2, layer_type='月令中气比劫透干')
        # 中气非比劫：以十神定格
        pattern_name = f'{ss}格' if ss else '未知格'
        result = {
            'layer': 2, 'type': '月令中气透干', 'pattern': pattern_name,
            'confidence': 0.75, 'reason': f'月支{month_zhi}中气{zhongqi_gan}透干，十神为{ss}',
            'yongshen_direction': _get_yongshen_direction(ss),
        }
        break_conditions = _check_zhengge_break(day_master, dm_wx, bazi_parts, gans, pattern_name)
        if break_conditions:
            result['break_conditions'] = break_conditions
        return result
    return None


def _classify_bijie_pattern(day_master: str, month_zhi: str, benqi_ss: str) -> str:
    """比劫月令的格局分类：建禄格/羊刃格/月劫格

    《子平真诠》第四十三章"论建禄月劫"：
    - 建禄格：月支为日主建禄之地（禄=临官）
    - 羊刃格：月支为日主羊刃之地（刃=帝旺）
    - 月劫格：月支本气为比劫但非建禄/羊刃

    Args:
        day_master: 日主天干
        month_zhi: 月支地支
        benqi_ss: 月支本气十神（比肩/劫财）

    Returns:
        str: 格局基础名称
    """
    if month_zhi == JIANLU_MAP.get(day_master, ''):
        return '建禄格'
    if month_zhi == YANGREN_MAP.get(day_master, ''):
        return '羊刃格'
    return '月劫格'


def _build_jianlu_yuejie(day_master, dm_wx, month_zhi, gans, bazi_parts,
                          benqi_ss, benqi_gan, layer, layer_type):
    """建禄月劫格/羊刃格构建

    《子平真诠》"先透官则取官，次透财则取财" — 按优先级排序透干十神，
    非天干位置顺序。建禄月劫格不入正格，须寻财官煞食透干取用。

    透干优先级（子平真诠"先官后财"原则）：
    正官(0) > 七杀(1) > 正财(2) > 偏财(3) > 食神(4) > 伤官(5)

    Args:
        day_master: 日主天干
        dm_wx: 日主五行
        month_zhi: 月支地支
        gans: 四天干列表（含日主）
        bazi_parts: 四柱干支列表
        benqi_ss: 月支本气/中气十神（比肩/劫财）
        benqi_gan: 月支本气/中气天干
        layer: 命中层级（1/2/3）
        layer_type: 层级类型描述

    Returns:
        dict: 格局结果，含 pattern/confidence/reason/break_conditions 等
    """
    if not dm_wx:
        dm_wx = GAN_WUXING.get(day_master, '')
    pattern_base = _classify_bijie_pattern(day_master, month_zhi, benqi_ss)
    tou_gan_ss = []

    # 透干优先级：《子平真诠》"先透官则取官，次透财则取财"
    # 数字越小优先级越高
    _TOU_PRIORITY = {'正官': 0, '七杀': 1, '正财': 2, '偏财': 3, '食神': 4, '伤官': 5}

    for g in gans:
        if g != day_master:
            ss = derive_shishen(day_master, g)
            if ss in _TOU_PRIORITY:
                tou_gan_ss.append(ss)
    tou_gan_ss.sort(key=lambda s: _TOU_PRIORITY.get(s, 99))

    # 格局名称：如"建禄格，透正官"、"羊刃格，透七杀"
    # 无财官煞食透出时标记为"无财官煞食透出"
    pattern_name = f'{pattern_base}，透{tou_gan_ss[0]}' if tou_gan_ss else f'{pattern_base}，无财官煞食透出'
    break_conditions = _check_jianlu_yangren_break(day_master, dm_wx, bazi_parts, gans, pattern_name)

    if tou_gan_ss:
        main_ss = tou_gan_ss[0]
        result = {
            'layer': layer, 'type': layer_type, 'pattern': pattern_name,
            'confidence': 0.70,
            'reason': f'月令{benqi_gan}为{benqi_ss}，{pattern_base}不入正格，透{main_ss}取用',
            'yongshen_direction': _get_yongshen_direction(main_ss),
        }
    else:
        # 无财官煞食透出：格局未定，confidence较低
        result = {
            'layer': layer, 'type': layer_type, 'pattern': pattern_name,
            'confidence': 0.50,
            'reason': f'月令{benqi_gan}为{benqi_ss}，{pattern_base}不入正格，四天干无财官煞食透出',
            'yongshen_direction': '待定',
        }
    if break_conditions:
        result['break_conditions'] = break_conditions
    return result


def _screen_layer3(day_master, dm_wx, month_zhi, gans, bazi_parts):
    """L3：暗格/比劫月令筛查

    三种情况：
    1. 羊刃月令：月支为日主羊刃之地，转入建禄月劫格处理
    2. 比劫月令：月支本气为比劫，转入建禄月劫格处理
    3. 暗格：月支本气不透干，取为暗格

    《子平真诠》"用神不论透与不透，成败救应一理" — 暗格也需破格检测。

    Args:
        day_master: 日主天干
        dm_wx: 日主五行
        month_zhi: 月支地支
        gans: 四天干列表（含日主）
        bazi_parts: 四柱干支列表

    Returns:
        dict|None: 命中返回格局结果 dict，未命中返回 None
    """
    canggan = get_canggan(month_zhi)
    if not canggan:
        return None
    benqi_gan = canggan[0][0]
    benqi_ss = derive_shishen(day_master, benqi_gan)

    # 羊刃月令：直接转入建禄月劫格处理
    if month_zhi == YANGREN_MAP.get(day_master, ''):
        return _build_jianlu_yuejie(day_master, dm_wx, month_zhi, gans, bazi_parts,
                                    benqi_ss='劫财', benqi_gan=benqi_gan,
                                    layer=3, layer_type='羊刃月令')

    # 比劫月令（非建禄/羊刃）：转入建禄月劫格处理
    if benqi_ss in ('比肩', '劫财'):
        return _build_jianlu_yuejie(day_master, dm_wx, month_zhi, gans, bazi_parts,
                                    benqi_ss=benqi_ss, benqi_gan=benqi_gan,
                                    layer=3, layer_type='比劫月令')

    # 暗格：月支本气不透干，以本气十神取暗格
    # confidence=0.65：暗格力量弱于透干格
    if benqi_ss and benqi_gan not in gans:
        result = {
            'layer': 3, 'type': '暗格', 'pattern': f'{benqi_ss}格',
            'confidence': 0.65,
            'reason': f'月支{month_zhi}本气{benqi_gan}({benqi_ss})不透干，取为暗格',
            'yongshen_direction': _get_yongshen_direction(benqi_ss),
        }
        # 暗格也需破格检测 — 《子平真诠》"用神不论透与不透，成败救应一理"
        break_conditions = _check_zhengge_break(day_master, dm_wx, bazi_parts, gans, f'{benqi_ss}格')
        if break_conditions:
            result['break_conditions'] = break_conditions
        return result

    return None


def _finalize_pattern(candidates, wangshuai):
    """格局结果定稿 — 取首个候选格局，组装最终结果

    Args:
        candidates: 候选格局列表（当前实现中最多1个，因逐层命中即返回）
        wangshuai: 旺衰判定结果（透传到最终结果）

    Returns:
        dict: 最终格局结果，含以下字段：
            - 'pattern': str             — 格局名称
            - 'candidates': list         — 候选格局列表
            - 'layer': int               — 命中层级
            - 'type': str                — 格局类型描述
            - 'confidence': float        — 置信度
            - 'reason': str              — 判定理由
            - 'yongshen_direction': str  — 用神方向
            - 'wangshuai': dict          — 旺衰判定
            - 'formation': dict          — 方局信息（可能不存在）
            - 'break_conditions': list   — 破格条件（可能不存在）
    """
    best = candidates[0]
    result = {
        'pattern': best['pattern'],
        'candidates': candidates,
        'layer': best['layer'],
        'type': best['type'],
        'confidence': best['confidence'],
        'reason': best['reason'],
        'yongshen_direction': best.get('yongshen_direction', '待定'),
        'wangshuai': wangshuai,
    }
    if 'formation' in best:
        result['formation'] = best['formation']
    if 'break_conditions' in best:
        result['break_conditions'] = best['break_conditions']
    return result
