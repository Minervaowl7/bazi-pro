"""用神推导核心模块 — 基于格局与旺衰确定用神、喜神、忌神

核心概念：
- 用神：命局中最关键的平衡五行，取法依格局与旺衰而定
- 喜神：辅助用神的五行，生扶用神或与用神同向
- 忌神：破坏命局平衡的五行，逆用神之势

推导路径（优先级从高到低）：
1. 格局用神表（PATTERN_YONGSHEN）：正格/从格/化气格等按格局名查表
2. 旺衰回退：身弱取印星扶，身强取官杀/食伤克泄
3. 中和偏弱：取印星扶助

五行关系映射（以日主为"我"）：
- WO_SHENG_MAP（我生）：日主所生之五行 → 食伤
- SHENG_MAP（生我）：生日主之五行 → 印星
- KE_MAP（克我）：克日主之五行 → 官杀
- WO_KE_MAP（我克）：日主所克之五行 → 财星

古籍依据：
- 《子平真诠》第八章"论用神"："用神专寻月令，以四柱配合"
- 《子平真诠》"论建禄月劫取运"："禄劫而用伤食，财运最宜"
- 《子平真诠》"阳刃喜官杀制伏，刃旺杀强，功名显达"
- 《滴天髓》"五阴从势无情义"（从势格取最强之势为用）
"""

from bazi_pro.core.constants import GAN_WUXING, WUXING_TO_GAN
from bazi_pro.core.patterns import PATTERN_YONGSHEN
from bazi_pro.core.stems import KE_MAP, SHENG_MAP, WO_KE_MAP, WO_SHENG_MAP, WUXING_KE
from bazi_pro.core.ten_gods import SHISHEN_WUXING_REL


def derive_yongshen(day_master: str, bazi_parts: list[str],
                    pattern_result: dict, wangshuai: dict,
                    element_forces: dict, tiaohou: dict = None) -> dict:
    """推导用神、喜神、忌神的顶层入口函数

    推导流程：
    1. 获取日主五行，缺失则返回"待定"
    2. 优先按格局名查 PATTERN_YONGSHEN 表推导用神五行
    3. 格局无匹配时按旺衰回退：身弱→印星，身强→官杀/食伤，中和偏弱→印星
    4. 根据用神五行推导忌神和喜神

    参数：
        day_master: 日主天干（如"甲"、"乙"）
        bazi_parts: 四柱干支列表，格式 ["甲子","丙寅","戊辰","庚午"]
        pattern_result: 格局筛查结果，含 pattern/type/confidence 等字段
        wangshuai: 旺衰判定结果，含 verdict/is_weak/is_strong 等字段
        element_forces: 五行力量分布，含 percent/percent_adjusted 等字段

    返回：
        dict {
            'yongshen': 用神五行（如"木"），
            'yongshen_gan': 用神对应天干，
            'xishen': 喜神五行列表，
            'xishen_gan': 喜神对应天干列表，
            'jishen': 忌神五行列表，
            'jishen_gan': 忌神对应天干列表，
            'confidence': 置信度（继承自格局筛查），
            'pattern_basis': 格局名称，
            'note': 备注（调候用神需查穷通宝鉴），
            'trace': 推导轨迹（method/reason/candidates_considered），
        }
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {'yongshen': '待定', 'xishen': [], 'jishen': [], 'confidence': 0,
                'trace': {'method': 'none', 'reason': '日主五行缺失'}}

    pattern_name = pattern_result.get('pattern', '')
    pattern_type = pattern_result.get('type', '')
    is_weak = wangshuai.get('is_weak', False)
    is_strong = wangshuai.get('is_strong', False)
    trace = {'pattern_basis': pattern_name, 'wangshuai_basis': wangshuai.get('verdict', ''),
             'method': '', 'reason': '', 'candidates_considered': []}

    # 优先按格局推导用神五行
    yongshen_wx = _pattern_yongshen_wx(pattern_name, dm_wx, is_weak, is_strong,
                                        pattern_type=pattern_type,
                                        pattern_result=pattern_result)
    if yongshen_wx:
        trace['method'] = 'pattern_based'
        trace['reason'] = f'格局"{pattern_name}"推导用神为{yongshen_wx}'
    else:
        # 旺衰回退：格局无匹配时按身弱/身强/中和取用
        trace['method'] = 'wangshuai_fallback'
        if is_weak:
            # 身弱取印星（生我）扶助 — 《子平真诠》"弱则喜帮喜助"
            yongshen_wx = SHENG_MAP.get(dm_wx, '')
            trace['reason'] = f'身弱，取印星({yongshen_wx})为用'
        elif is_strong:
            # 身强优先取官杀（克我），无官杀则取食伤（我生）泄秀
            ke_wx = KE_MAP.get(dm_wx, '')
            sheng_wx = WO_SHENG_MAP.get(dm_wx, '')
            yongshen_wx = ke_wx if ke_wx else sheng_wx
            trace['reason'] = f'身强，取克泄({yongshen_wx})为用'
        else:
            # 中和偏弱取印星扶助
            yongshen_wx = SHENG_MAP.get(dm_wx, '')
            trace['reason'] = f'中和偏弱，取印星({yongshen_wx})为用'

    # 推导忌神和喜神
    jishen_wx = _derive_jishen(pattern_name, dm_wx, yongshen_wx, is_weak, is_strong,
                               pattern_type=pattern_type)
    xishen_wx = _derive_xishen(pattern_name, dm_wx, yongshen_wx, jishen_wx)

    # ── 调候用神整合 ──
    # 《子平真诠》第十四章"论用神配气候得失"：调候为辅助用神，不凌驾格局用神之上
    # 当调候五行与格局用神不同时，调候作为喜神补充；当冲突时，调候不改变用神
    tiaohou_wx_list = []
    if tiaohou and tiaohou.get('has_tiaohou'):
        tiaohou_wx_list = tiaohou.get('tiaohou_wx', [])
        for th_wx in tiaohou_wx_list:
            if th_wx and th_wx != yongshen_wx and th_wx not in xishen_wx and th_wx not in jishen_wx:
                xishen_wx.append(th_wx)
                trace.setdefault('tiaohou_integration', []).append(
                    f'调候{th_wx}≠用神{yongshen_wx}，加入喜神')

    return {
        'yongshen': yongshen_wx,
        'yongshen_gan': WUXING_TO_GAN.get(yongshen_wx, ''),
        'xishen': xishen_wx,
        'xishen_gan': [WUXING_TO_GAN.get(w, '') for w in xishen_wx],
        'jishen': jishen_wx,
        'jishen_gan': [WUXING_TO_GAN.get(w, '') for w in jishen_wx],
        'confidence': pattern_result.get('confidence', 0.5),
        'pattern_basis': pattern_name,
        'note': '基于格局+旺衰+调候三位一体推导。' + (f'调候用神({",".join(tiaohou_wx_list)})已纳入喜神。' if tiaohou_wx_list else ''),
        'trace': trace,
    }


def _derive_xishen(pattern_name: str, dm_wx: str, yongshen_wx: str,
                   jishen_wx: list[str]) -> list[str]:
    """推导喜神五行

    推导逻辑（优先级从高到低）：
    1. 从 PATTERN_YONGSHEN 表取第二候选作为喜神
    2. 通用逻辑：生用神的五行即为喜神，但排除忌神

    参数：
        pattern_name: 格局名称（如"正官格"）
        dm_wx: 日主五行
        yongshen_wx: 用神五行
        jishen_wx: 忌神五行列表

    返回：
        喜神五行列表（通常0-1个元素）
    """
    # 十神关系→五行映射：将"同我/生我/我生/我克/克我"转为具体五行
    _REL_TO_WX = {
        '同我': dm_wx,
        '生我': SHENG_MAP.get(dm_wx, ''),
        '我生': WO_SHENG_MAP.get(dm_wx, ''),
        '我克': WO_KE_MAP.get(dm_wx, ''),
        '克我': KE_MAP.get(dm_wx, ''),
    }

    # 从格局用神表取第二候选作为喜神
    # 按键名长度降序匹配，避免"从强格"误匹配"假从强格"
    sorted_keys = sorted(PATTERN_YONGSHEN.keys(), key=len, reverse=True)
    for ss_name in sorted_keys:
        if ss_name not in pattern_name:
            continue
        info = PATTERN_YONGSHEN[ss_name]
        yong_list = info.get('用神', [])
        if len(yong_list) >= 2:
            # 从第二候选开始遍历，找第一个非用神非忌神的五行
            for candidate in yong_list[1:]:
                base = candidate.split('(')[0].strip()  # 去除括号注释如"财星(无制时)"
                rel = SHISHEN_WUXING_REL.get(base, '')
                wx = _REL_TO_WX.get(rel, '')
                if wx and wx != yongshen_wx and wx not in jishen_wx:
                    return [wx]
        break

    # 通用逻辑：生用神的五行即为喜神（排除忌神）
    # 用神为印星(生我) → 喜神为比劫(同我)，印生比劫帮身
    if yongshen_wx == SHENG_MAP.get(dm_wx, ''):
        xi = dm_wx
    # 用神为比劫(同我) → 喜神为印星(生我)，印生比劫帮身
    elif yongshen_wx == dm_wx:
        xi = SHENG_MAP.get(dm_wx, '')
    # 其他情况：生用神的五行即为喜神
    else:
        xi = SHENG_MAP.get(yongshen_wx, '')

    if xi and xi != yongshen_wx and xi not in jishen_wx:
        return [xi]
    return []


def _derive_jishen(pattern_name: str, dm_wx: str, yongshen_wx: str,
                   is_weak: bool, is_strong: bool, pattern_type: str = '') -> list[str]:
    """推导忌神五行

    规则（按优先级）：
    1. 从格（从强/专旺/从财/从官杀/从儿）：忌神=逆势五行
    2. 扶抑格身弱：忌神=克我(官杀)+我克(财星)，排除用神
    3. 扶抑格身强：忌神=同我(比劫)+生我(印星)，排除用神
    4. 中和：从 PATTERN_YONGSHEN 忌神表推导
    5. 兜底：用神的对立面

    参数：
        pattern_name: 格局名称
        dm_wx: 日主五行
        yongshen_wx: 用神五行
        is_weak: 是否身弱
        is_strong: 是否身强
        pattern_type: 格局类型（如"专旺格"）

    返回：
        忌神五行列表
    """
    ke_wo = KE_MAP.get(dm_wx, '')      # 克我 → 官杀五行
    wo_ke = WO_KE_MAP.get(dm_wx, '')   # 我克 → 财星五行
    sheng_wo = SHENG_MAP.get(dm_wx, '')   # 生我 → 印星五行
    wo_sheng = WO_SHENG_MAP.get(dm_wx, '')  # 我生 → 食伤五行

    # ── 从格：忌神=逆势五行 ──
    is_cong_qiang = ('从强' in pattern_name or '假从强' in pattern_name
                     or '专旺' in pattern_name or pattern_type == '专旺格'
                     or '从强' in pattern_type or '假从强' in pattern_type)
    if is_cong_qiang:
        # 从强顺印比之势，忌官杀(克我)+财星(我克)+食伤(我生) — 皆为逆势
        return [w for w in [ke_wo, wo_ke, wo_sheng] if w and w != yongshen_wx]
    if '从财' in pattern_name:
        # 从财顺财势，忌比劫(同我)+印星(生我) — 皆为逆财势
        return [w for w in [dm_wx, sheng_wo] if w and w != yongshen_wx]
    if '从官杀' in pattern_name:
        # 从官杀顺杀势，忌比劫(同我)+印星(生我) — 皆为逆杀势
        return [w for w in [dm_wx, sheng_wo] if w and w != yongshen_wx]
    if '从儿' in pattern_name:
        # 从儿顺食伤势，忌印星(克食伤)+官杀(逆势)
        # 《滴天髓》"从儿不管身强弱，只要吾儿又得儿" — 比劫生食伤不逆势，不应为忌
        return [w for w in [sheng_wo, ke_wo] if w and w != yongshen_wx]
    if '从势' in pattern_name:
        # 从势格：日主孤立无气，顺最强之势
        # 《滴天髓》"从得真者只论从" — 忌逆势五行
        # 比劫在从势格中力量极弱（日主无根），不是主要威胁
        # 忌神：克我(官杀)+我克(财星)+生我(印星)，皆为逆最强之势
        # 但用神五行本身不应为忌，需排除
        return [w for w in [ke_wo, wo_ke, sheng_wo] if w and w != yongshen_wx]
    if '成象格' in pattern_name:
        # 两行成象格：《滴天髓》"两气合而成象" — 忌逆两行之势
        # 忌神：克用神之五行 + 用神所克之五行
        if yongshen_wx:
            ke_yong = WUXING_KE.get(yongshen_wx, '')
            yong_ke = [k for k, v in WUXING_KE.items() if v == yongshen_wx]
            result = [ke_yong] + yong_ke if ke_yong else yong_ke
            return [w for w in result if w and w != yongshen_wx and w != dm_wx]
        return [dm_wx]

    # ── 扶抑格 ──
    if is_weak:
        # 身弱忌克我(官杀)+我克(财星)，皆消耗日主
        return [w for w in [ke_wo, wo_ke] if w and w != yongshen_wx]
    if is_strong:
        # 身强忌同我(比劫)+生我(印星)，皆助长日主过旺
        return [w for w in [dm_wx, sheng_wo] if w and w != yongshen_wx]

    # ── 中和：从格局忌神表推导 ──
    jishen = _jishen_from_pattern_table(pattern_name, dm_wx, yongshen_wx)
    if jishen:
        return jishen

    # 兜底：用神的对立面
    # 用神为印星 → 忌官杀+财星；用神为官杀 → 忌比劫+印星
    if yongshen_wx == sheng_wo:
        return [w for w in [ke_wo, wo_ke] if w]
    elif yongshen_wx == ke_wo:
        return [w for w in [dm_wx, sheng_wo] if w]
    return []


def _jishen_from_pattern_table(pattern_name: str, dm_wx: str, yongshen_wx: str) -> list[str]:
    """从 PATTERN_YONGSHEN 忌神表推导忌神五行

    在 PATTERN_YONGSHEN 字典中按键名长度降序匹配格局名，
    将忌神十神关系（如"比劫"、"财星"）转换为具体五行。

    参数：
        pattern_name: 格局名称
        dm_wx: 日主五行
        yongshen_wx: 用神五行（用于排除）

    返回：
        忌神五行列表，无匹配则返回空列表
    """
    _REL_TO_WX = {
        '同我': dm_wx,
        '生我': SHENG_MAP.get(dm_wx, ''),
        '我生': WO_SHENG_MAP.get(dm_wx, ''),
        '我克': WO_KE_MAP.get(dm_wx, ''),
        '克我': KE_MAP.get(dm_wx, ''),
    }

    # 按键名长度降序匹配，避免"从强格"误匹配"假从强格"
    sorted_keys = sorted(PATTERN_YONGSHEN.keys(), key=len, reverse=True)
    for ss_name in sorted_keys:
        if ss_name not in pattern_name:
            continue
        info = PATTERN_YONGSHEN[ss_name]
        ji_list = info.get('忌神', [])
        result = []
        for candidate in ji_list:
            rel = SHISHEN_WUXING_REL.get(candidate, '')
            if not rel:
                # 带括号注释的忌神如 '财星(无制时)' → 提取前缀
                base = candidate.split('(')[0].strip()
                rel = SHISHEN_WUXING_REL.get(base, '')
            wx = _REL_TO_WX.get(rel, '')
            if wx and wx != yongshen_wx and wx not in result:
                result.append(wx)
        return result
    return []


def _pattern_yongshen_wx(pattern_name: str, dm_wx: str,
                         is_weak: bool = False, is_strong: bool = False,
                         pattern_type: str = '',
                         pattern_result: dict = None) -> str:
    """按格局名推导用神五行

    推导优先级：
    1. 从强/专旺格 → 印星（顺印比之势）
    2. 从财格 → 财星（顺财势）
    3. 从官杀格 → 官杀（顺杀势）
    4. 从儿格 → 食伤（顺食伤势）
    5. 化气格 → 化神五行
    6. 从势格 → 最强之势的五行
    7. 建禄/月劫格 → 透干决定，无透干则身强取食伤（泄秀法），身弱取印星
    8. 羊刃格 → 透干决定，无透干则取官杀（制伏法）
    9. 其他正格 → PATTERN_YONGSHEN 表查表

    参数：
        pattern_name: 格局名称（如"正官格"、"建禄格，透正官"）
        dm_wx: 日主五行
        is_weak: 是否身弱
        is_strong: 是否身强
        pattern_type: 格局类型（如"专旺格"）
        pattern_result: 格局筛查结果（化气格需从中获取化神方向）

    返回：
        用神五行字符串（如"木"），无匹配则返回空字符串
    """
    # ── 从格/专旺格：检查 pattern_name 和 pattern_type 两个维度 ──
    is_cong_qiang = ('从强' in pattern_name or '假从强' in pattern_name
                     or '专旺' in pattern_name or pattern_type == '专旺格'
                     or '从强' in pattern_type or '假从强' in pattern_type)
    if is_cong_qiang:
        # 从强/专旺顺印比之势，用神取印星（生我）
        return SHENG_MAP.get(dm_wx, '')
    if '从财' in pattern_name:
        # 从财顺财势，用神取财星（我克）
        return WO_KE_MAP.get(dm_wx, '')
    if '从官杀' in pattern_name:
        # 从官杀顺杀势，用神取官杀（克我）
        return KE_MAP.get(dm_wx, '')
    if '从儿' in pattern_name:
        # 从儿顺食伤势，用神取食伤（我生）
        return WO_SHENG_MAP.get(dm_wx, '')

    # ── 化气格：《子平真诠》"运喜所化之物，与所化之印绶" ──
    # 用神=化神五行，从 pattern_result 中获取
    if '化' in pattern_name and pattern_result:
        hua_wx = pattern_result.get('yongshen_direction', '')
        # yongshen_direction 格式为 "化神X"，提取五行
        if hua_wx.startswith('化神'):
            return hua_wx[2:]  # "化神土" → "土"
        # 从 pattern_name 推导：化土格→土、化金格→金 等
        hua_names = {'化土格': '土', '化金格': '金', '化水格': '水',
                     '化木格': '木', '化火格': '火'}
        for name, wx in hua_names.items():
            if name in pattern_name:
                return wx

    # ── 从势格：《滴天髓》"五阴从势无情义" — 用神取最强之势 ──
    if '从势' in pattern_name:
        # 优先从 element_forces 参数获取（通过 derive_yongshen 传入）
        # 备选从 pattern_result._element_forces 获取
        pct = {}
        if pattern_result and pattern_result.get('_element_forces'):
            pct = pattern_result['_element_forces'].get('percent', {})
        if not pct:
            return WO_SHENG_MAP.get(dm_wx, '')  # fallback: 食伤
        strongest = max(pct, key=pct.get)
        return strongest

    # ── 两行成象格：《滴天髓》"两气合而成象" — 用神取两行中较强之势 ──
    # 格局名格式为"火土成象格"、"金水成象格"等
    if '成象格' in pattern_name:
        pct = {}
        if pattern_result and pattern_result.get('_element_forces'):
            pct = pattern_result['_element_forces'].get('percent', {})
        if pct:
            # 取两行中力量最强者（非日主五行、非印星五行）
            candidates = {wx: p for wx, p in pct.items()
                          if wx != dm_wx and wx != SHENG_MAP.get(dm_wx, '')}
            if candidates:
                strongest = max(candidates, key=candidates.get)
                return strongest
        # fallback: 取我克（财星方向）
        return WO_KE_MAP.get(dm_wx, '')

    # 十神关系→五行转换函数（用于查表后的五行映射）
    _REL_TO_WX = {
        '同我': lambda w: w,
        '生我': lambda w: SHENG_MAP.get(w, ''),
        '我生': lambda w: WO_SHENG_MAP.get(w, ''),
        '我克': lambda w: WO_KE_MAP.get(w, ''),
        '克我': lambda w: KE_MAP.get(w, ''),
    }

    # ── 建禄月劫格特殊处理：用神由"透X"决定 ──
    # 《子平真诠》："建禄月劫，无官煞则用食伤，食伤亦无则用财"
    if '建禄格' in pattern_name or '月劫格' in pattern_name:
        # 精确匹配"透X"：pattern_name 格式为"建禄格，透正官"或"建禄格，无财官煞食透出"
        # "无...透出"不应匹配，只有"透X"才应匹配
        if '，透' in pattern_name:
            tou_ss = pattern_name.split('，透')[-1]
            rel = SHISHEN_WUXING_REL.get(tou_ss, '')
            if rel:
                return _REL_TO_WX.get(rel, lambda w: '')(dm_wx)
        # 无透干：《子平真诠》"建禄月劫，无官煞则用食伤，食伤亦无则用财"
        # 身强时优先取食伤（泄秀法）
        # 《子平真诠》"论建禄月劫取运"："禄劫而用伤食，财运最宜"
        if is_strong:
            return WO_SHENG_MAP.get(dm_wx, '')  # 食伤（泄秀法）
        return SHENG_MAP.get(dm_wx, '')  # 印星（扶弱法）

    # ── 羊刃格特殊处理：《子平真诠》"阳刃喜官杀制伏" ──
    # 羊刃格与建禄格不同，羊刃性刚暴，必须用官杀制伏，非泄秀
    if '羊刃格' in pattern_name:
        if '，透' in pattern_name:
            tou_ss = pattern_name.split('，透')[-1]
            rel = SHISHEN_WUXING_REL.get(tou_ss, '')
            if rel:
                return _REL_TO_WX.get(rel, lambda w: '')(dm_wx)
        # 无透干：羊刃格取官杀制伏
        # 《子平真诠》"阳刃喜官杀制伏，刃旺杀强，功名显达"
        return KE_MAP.get(dm_wx, '')  # 官杀（制伏法）

    # 身弱时优先取扶助类（生我/同我），身强时优先取克泄类（克我/我生/我克）
    _WEAK_PREFERRED = {'生我', '同我'}
    _STRONG_PREFERRED = {'克我', '我生', '我克'}

    # ── 其他正格：从 PATTERN_YONGSHEN 表查表 ──
    # 按键名长度降序匹配，避免短名误匹配长名
    for ss_name in sorted(PATTERN_YONGSHEN.keys(), key=len, reverse=True):
        if ss_name not in pattern_name:
            continue
        info = PATTERN_YONGSHEN[ss_name]
        yong_list = info.get('用神', [])
        if not yong_list:
            continue

        # 身弱时从候选中优先选扶助类（生我/同我）
        if is_weak and len(yong_list) >= 2:
            for candidate in yong_list:
                base = candidate.split('(')[0].strip()
                rel = SHISHEN_WUXING_REL.get(base, '')
                if rel in _WEAK_PREFERRED:
                    return _REL_TO_WX.get(rel, lambda w: '')(dm_wx)

        # 身强时从候选中优先选克泄类（克我/我生/我克）
        if is_strong and len(yong_list) >= 2:
            for candidate in yong_list:
                base = candidate.split('(')[0].strip()
                rel = SHISHEN_WUXING_REL.get(base, '')
                if rel in _STRONG_PREFERRED:
                    return _REL_TO_WX.get(rel, lambda w: '')(dm_wx)

        # 无旺衰偏好或只有一个候选，取第一个
        first = yong_list[0]
        base = first.split('(')[0].strip()
        rel = SHISHEN_WUXING_REL.get(base, '')
        return _REL_TO_WX.get(rel, lambda w: '')(dm_wx)

    return ''
