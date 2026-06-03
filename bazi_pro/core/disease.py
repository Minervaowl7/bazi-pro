"""格局之病检测模块 — 检测原局中破坏格局的病源，并给出药方建议

核心概念：
- 病（disease）：命局中破坏格局成立的十神组合，如枭神夺食、伤官见官等
- 药（medicine）：化解病源的十神或五行，如财星制枭、印星化伤官等
- 严重程度（severity）：active=病源透干（已发作），potential=病源仅藏干（潜伏）

检测项目（共9种格局之病）：
1. 枭神夺食 / 食神制杀逢枭 — 偏印克食神
2. 伤官见官 — 伤官克正官（金水伤官除外）
3. 比劫争财 — 比劫旺而财星弱
4. 官杀混杂 — 正官与七杀同时有根且无制化
5. 贪财坏印 — 财星克破轻印
6. 七杀无制 / 财党杀无制 — 七杀无食神制或印星化
7. 用神被冲 — 月支被其他地支冲克
8. 身强印重透煞 — 身旺印旺又透七杀
9. 伤官生财带煞 — 伤官生财又透七杀，财转党杀

古籍依据：
- 《子平真诠》第九章"论用神成败救应"
- 《神峰通考》"病药说"
- 《子平真诠》第四十一章"金水伤官喜见官"
"""

from bazi_pro.core.branches import CANGGAN_WEIGHT, ZHI_CHONG
from bazi_pro.core.constants import GAN_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.stems import KE_MAP, SHENG_MAP, WO_KE_MAP


def _get_transparent_gans(bazi_parts: list[str]) -> set[str]:
    """返回所有透干（天干）的干集合

    透干指四柱天干上出现的干，透干的十神力量远大于仅藏干者。
    """
    return {p[0] for p in bazi_parts if len(p) >= 1}


def _find_shishen_instances(
    day_master: str,
    target_shishen: str,
    bazi_parts: list[str],
) -> list[dict]:
    """找出命盘中所有属于 target_shishen 的干（天干+藏干）

    遍历四柱天干和地支藏干，找出所有十神属性为 target_shishen 的干，
    并记录其位置、是否透干、气之深浅、根气权重等信息。

    参数：
        day_master: 日主天干
        target_shishen: 目标十神名（如"偏印"、"食神"、"七杀"等）
        bazi_parts: 四柱干支列表

    返回：
        实例列表，每项含：
        - gan: 天干字符
        - position: 位置描述（如"月干"、"年支寅(本气)"）
        - is_transparent: 是否透干
        - qi_level: 气之深浅（'透干'/'本气'/'中气'/'余气'）
        - root_weight: 根气权重（透干1.0/本气1.0/中气0.6/余气0.3）
    """
    transparent = _get_transparent_gans(bazi_parts)
    positions = ['年', '月', '日', '时']
    results = []

    for i, part in enumerate(bazi_parts):
        if len(part) < 2:
            continue
        gan, zhi = part[0], part[1]
        pos = positions[i] if i < 4 else ''

        # 天干：透干力量最强，root_weight=1.0
        if derive_shishen(day_master, gan) == target_shishen:
            results.append({
                'gan': gan,
                'position': f'{pos}干',
                'is_transparent': True,
                'qi_level': '透干',
                'root_weight': 1.0,
            })

        # 藏干：根据气之深浅赋予权重
        for cg, ql in get_canggan(zhi):
            if derive_shishen(day_master, cg) == target_shishen:
                results.append({
                    'gan': cg,
                    'position': f'{pos}支{zhi}({ql})',
                    'is_transparent': cg in transparent,
                    'qi_level': ql,
                    'root_weight': CANGGAN_WEIGHT.get(ql, 0),
                })

    # 去重：同一个干只保留最强的一条（避免天干和藏干重复计数）
    seen: dict[str, dict] = {}
    for item in results:
        g = item['gan']
        if g not in seen or item['root_weight'] > seen[g]['root_weight']:
            seen[g] = item
    return list(seen.values())


def _severity(disease_instances: list[dict]) -> str:
    """根据病源干的存在方式判断严重程度

    判定规则：
    - active：病源透干（天干上出现），力量外显，已发作
    - potential：病源只在藏干（不透干），力量潜伏，尚未发作

    参数：
        disease_instances: 病源干实例列表

    返回：
        'active' 或 'potential'
    """
    for inst in disease_instances:
        if inst['is_transparent']:
            return 'active'
    return 'potential'


def _best_instance(instances: list[dict]) -> dict:
    """返回根气最强的一条实例

    在多个同十神实例中，取 root_weight 最大的作为代表，
    用于病源/受害神的定位和描述。

    参数：
        instances: 实例列表

    返回：
        root_weight 最大的实例字典
    """
    return max(instances, key=lambda x: x['root_weight'])


def detect_disease(
    day_master: str,
    bazi_parts: list[str],
    element_forces: dict,
) -> dict:
    """检测原局格局之病的顶层入口函数

    依次调用9种病检测函数，汇总结果并生成药方建议。
    结果按严重程度排序：active 优先于 potential。

    参数：
        day_master: 日主天干
        bazi_parts: 四柱干支列表
        element_forces: 五行力量分布（部分检测函数需要）

    返回：
        dict {
            'has_disease': 是否存在格局之病（bool），
            'items': DiseaseItem 列表，按 severity 排序，
            'medicine_advice': 药方建议汇总文本，
        }

    DiseaseItem 字段：
        - name: 病名（如"枭神夺食"、"伤官见官"）
        - severity: 严重程度（'active'/'potential'）
        - disease_god: 病源十神名
        - disease_element: 病源五行
        - disease_gan: 病源天干
        - disease_position: 病源位置
        - affected_god: 受害十神名
        - affected_element: 受害五行
        - affected_gan: 受害天干
        - affected_position: 受害位置
        - medicine: 药方描述
        - medicine_element: 药方五行
        - reason: 病因说明
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {'has_disease': False, 'items': [], 'medicine_advice': ''}

    items: list[dict] = []

    items.extend(_detect_xiaoshen_duoshi(day_master, dm_wx, bazi_parts, element_forces))
    items.extend(_detect_shangguan_jianguan(day_master, dm_wx, bazi_parts))
    items.extend(_detect_bijie_zhengcai(day_master, dm_wx, bazi_parts, element_forces))
    items.extend(_detect_guansha_hunza(day_master, dm_wx, bazi_parts))
    # 新增：《子平真诠》明确定义的格局之病
    items.extend(_detect_tancai_huaiyin(day_master, dm_wx, bazi_parts))
    items.extend(_detect_qisha_wuzhi(day_master, dm_wx, bazi_parts))
    items.extend(_detect_yongshen_chong(day_master, dm_wx, bazi_parts))
    # 《子平真诠》第九章新增破格检测
    items.extend(_detect_shenqiang_yinzong_tousha(day_master, dm_wx, bazi_parts, element_forces))
    items.extend(_detect_shangguan_shengcai_daisa(day_master, dm_wx, bazi_parts))

    # 汇总药方建议（去重）
    medicine_parts = []
    for item in items:
        med = item.get('medicine', '')
        if med and med not in medicine_parts:
            medicine_parts.append(med)

    advice = '；'.join(medicine_parts) if medicine_parts else ''

    # 按严重程度排序：active 优先于 potential
    items.sort(key=lambda x: (0 if x.get('severity') == 'active' else 1, x.get('name', '')))

    return {
        'has_disease': len(items) > 0,
        'items': items,
        'medicine_advice': advice,
    }


def _detect_xiaoshen_duoshi(
    day_master: str,
    dm_wx: str,
    bazi_parts: list[str],
    element_forces: dict,
) -> list[dict]:
    """枭神夺食 / 食神制杀逢枭

    病源：偏印克食神
    条件：偏印有根（本气/中气/透干）+ 食神有根
    变体：若命局同时有七杀，则为"食神制杀逢枭"（食神制杀格被破）

    药方：财星制枭 — 财星克偏印，解救食神

    古籍依据：《子平真诠》"食神逢枭，食格败也"
    """
    results = []

    pian_yin_instances = _find_shishen_instances(day_master, '偏印', bazi_parts)
    shishen_instances = _find_shishen_instances(day_master, '食神', bazi_parts)

    if not pian_yin_instances or not shishen_instances:
        return results

    # 偏印需要有根（本气/中气/透干），root_weight≥0.6 确保非余气
    pian_yin_rooted = [x for x in pian_yin_instances if x['root_weight'] >= 0.6 or x['is_transparent']]
    if not pian_yin_rooted:
        return results

    # 食神需要有根（任意根气即可）
    shishen_rooted = [x for x in shishen_instances if x['root_weight'] > 0 or x['is_transparent']]
    if not shishen_rooted:
        return results

    best_py = _best_instance(pian_yin_rooted)
    best_ss = _best_instance(shishen_rooted)

    py_wx = GAN_WUXING.get(best_py['gan'], '')
    ss_wx = GAN_WUXING.get(best_ss['gan'], '')
    medicine_wx = WO_KE_MAP.get(dm_wx, '')  # 财星五行 = 日主所克

    sev = _severity(pian_yin_rooted)

    # 判断是否同时有七杀（食神制杀格被破）
    sha_instances = _find_shishen_instances(day_master, '七杀', bazi_parts)
    sha_rooted = [x for x in sha_instances if x['root_weight'] > 0 or x['is_transparent']]
    name = '食神制杀逢枭' if sha_rooted else '枭神夺食'

    results.append({
        'name': name,
        'severity': sev,
        'disease_god': '偏印',
        'disease_element': py_wx,
        'disease_gan': best_py['gan'],
        'disease_position': best_py['position'],
        'affected_god': '食神',
        'affected_element': ss_wx,
        'affected_gan': best_ss['gan'],
        'affected_position': best_ss['position'],
        'medicine': f'财星({medicine_wx})制枭',
        'medicine_element': medicine_wx,
        'reason': (
            f'偏印{best_py["gan"]}{py_wx}在{best_py["position"]}有根，'
            f'食神{best_ss["gan"]}{ss_wx}在{best_ss["position"]}，'
            f'偏印克食神成格'
        ),
    })
    return results


def _detect_shangguan_jianguan(
    day_master: str,
    dm_wx: str,
    bazi_parts: list[str],
) -> list[dict]:
    """伤官见官 — 《子平真诠》"伤官见官，为祸百端，而金水见之，反为秀气"

    病源：伤官克正官
    条件：伤官有根 + 正官有根 + 无财星通关 + 无印星制化
    例外：金水伤官（庚/辛日主）除外 — 《子平真诠》"金水伤官喜见官"

    药方：印星化伤官 — 印星克制伤官，保护正官

    化解条件（任一即可化解此病）：
    1. 财星通关：伤官→财星→正官，财星在中间通关
    2. 印星制化：印星克制伤官，保护正官
    """
    results = []

    # 金水伤官除外：《子平真诠》第四十一章"金水伤官喜见官"
    if day_master in ('庚', '辛'):
        return results

    sg_instances = _find_shishen_instances(day_master, '伤官', bazi_parts)
    zg_instances = _find_shishen_instances(day_master, '正官', bazi_parts)

    if not sg_instances or not zg_instances:
        return results

    sg_rooted = [x for x in sg_instances if x['root_weight'] > 0 or x['is_transparent']]
    zg_rooted = [x for x in zg_instances if x['root_weight'] > 0 or x['is_transparent']]

    if not sg_rooted or not zg_rooted:
        return results

    # 检查是否有财星通关（财星有根）— 伤官→财→正官，通关化解
    cai_instances = _find_shishen_instances(day_master, '正财', bazi_parts)
    cai_instances += _find_shishen_instances(day_master, '偏财', bazi_parts)
    cai_rooted = [x for x in cai_instances if x['root_weight'] > 0 or x['is_transparent']]
    if cai_rooted:
        return results  # 财星通关，病被化解

    # 检查是否有印星制化（印星有根，克制伤官）
    yin_instances = _find_shishen_instances(day_master, '正印', bazi_parts)
    yin_instances += _find_shishen_instances(day_master, '偏印', bazi_parts)
    yin_rooted = [x for x in yin_instances if x['root_weight'] > 0 or x['is_transparent']]
    if yin_rooted:
        return results  # 印星制化，病被化解

    best_sg = _best_instance(sg_rooted)
    best_zg = _best_instance(zg_rooted)
    sg_wx = GAN_WUXING.get(best_sg['gan'], '')
    zg_wx = GAN_WUXING.get(best_zg['gan'], '')
    medicine_wx = SHENG_MAP.get(dm_wx, '')  # 印星化伤官

    sev = _severity(sg_rooted)

    results.append({
        'name': '伤官见官',
        'severity': sev,
        'disease_god': '伤官',
        'disease_element': sg_wx,
        'disease_gan': best_sg['gan'],
        'disease_position': best_sg['position'],
        'affected_god': '正官',
        'affected_element': zg_wx,
        'affected_gan': best_zg['gan'],
        'affected_position': best_zg['position'],
        'medicine': f'印星({medicine_wx})化伤官',
        'medicine_element': medicine_wx,
        'reason': (
            f'伤官{best_sg["gan"]}{sg_wx}在{best_sg["position"]}，'
            f'正官{best_zg["gan"]}{zg_wx}在{best_zg["position"]}，'
            f'伤官克正官，无财星通关或印星制化'
        ),
    })
    return results


def _detect_bijie_zhengcai(
    day_master: str,
    dm_wx: str,
    bazi_parts: list[str],
    element_forces: dict,
) -> list[dict]:
    """比劫争财

    病源：比劫旺而财星弱
    条件：比劫≥2个透干或有本气根 + 财星无强根（root_weight<0.6且不透干）

    药方：官杀制比劫 — 官杀克制比劫，保护财星

    古籍依据：《子平真诠》"财格败：比劫争财"
    """
    results = []

    bj_instances = (
        _find_shishen_instances(day_master, '比肩', bazi_parts)
        + _find_shishen_instances(day_master, '劫财', bazi_parts)
    )
    cai_instances = (
        _find_shishen_instances(day_master, '正财', bazi_parts)
        + _find_shishen_instances(day_master, '偏财', bazi_parts)
    )

    if not bj_instances or not cai_instances:
        return results

    # 比劫旺：≥2个透干 或 有强根（本气）
    bj_transparent = [x for x in bj_instances if x['is_transparent']]
    bj_benqi = [x for x in bj_instances if x['qi_level'] == '本气']
    bj_strong = len(bj_transparent) >= 2 or len(bj_benqi) >= 1

    if not bj_strong:
        return results

    # 财星弱：无根或仅余气（root_weight<0.6 且不透干）
    cai_rooted = [x for x in cai_instances if x['root_weight'] >= 0.6 or x['is_transparent']]
    if cai_rooted:
        return results  # 财星有根，不成病

    best_bj = _best_instance(bj_instances)
    best_cai = _best_instance(cai_instances)
    bj_wx = GAN_WUXING.get(best_bj['gan'], '')
    cai_wx = GAN_WUXING.get(best_cai['gan'], '')
    ke_bj_wx = KE_MAP.get(dm_wx, '')  # 官杀克比劫

    # 严重程度：≥2个透干=active，否则=potential
    sev = 'active' if len(bj_transparent) >= 2 else 'potential'

    results.append({
        'name': '比劫争财',
        'severity': sev,
        'disease_god': '比劫',
        'disease_element': bj_wx,
        'disease_gan': best_bj['gan'],
        'disease_position': best_bj['position'],
        'affected_god': '财星',
        'affected_element': cai_wx,
        'affected_gan': best_cai['gan'],
        'affected_position': best_cai['position'],
        'medicine': f'官杀({ke_bj_wx})制比劫',
        'medicine_element': ke_bj_wx,
        'reason': (
            f'比劫旺（{len(bj_transparent)}个透干），'
            f'财星{best_cai["gan"]}{cai_wx}无强根，比劫争财'
        ),
    })
    return results


def _detect_guansha_hunza(
    day_master: str,
    dm_wx: str,
    bazi_parts: list[str],
) -> list[dict]:
    """官杀混杂

    病源：正官与七杀同时有根
    条件：正官有根 + 七杀有根 + 无食伤制杀 + 无印星化杀

    药方：食伤制杀 — 食伤克制七杀，保留正官清纯

    化解条件（任一即可化解此病）：
    1. 食伤制杀：食神/伤官克制七杀
    2. 印星化杀：印星化泄七杀之力

    古籍依据：《子平真诠》"官杀混杂，须去杀留官"
    """
    results = []

    zg_instances = _find_shishen_instances(day_master, '正官', bazi_parts)
    sha_instances = _find_shishen_instances(day_master, '七杀', bazi_parts)

    if not zg_instances or not sha_instances:
        return results

    zg_rooted = [x for x in zg_instances if x['root_weight'] > 0 or x['is_transparent']]
    sha_rooted = [x for x in sha_instances if x['root_weight'] > 0 or x['is_transparent']]

    if not zg_rooted or not sha_rooted:
        return results

    # 检查是否有食伤制杀或印星化杀
    si_instances = (
        _find_shishen_instances(day_master, '食神', bazi_parts)
        + _find_shishen_instances(day_master, '伤官', bazi_parts)
    )
    yin_instances = (
        _find_shishen_instances(day_master, '正印', bazi_parts)
        + _find_shishen_instances(day_master, '偏印', bazi_parts)
    )
    si_rooted = [x for x in si_instances if x['root_weight'] > 0 or x['is_transparent']]
    yin_rooted = [x for x in yin_instances if x['root_weight'] > 0 or x['is_transparent']]
    if si_rooted or yin_rooted:
        return results  # 有制化，不成病

    best_zg = _best_instance(zg_rooted)
    best_sha = _best_instance(sha_rooted)
    zg_wx = GAN_WUXING.get(best_zg['gan'], '')
    sha_wx = GAN_WUXING.get(best_sha['gan'], '')
    medicine_wx = WO_KE_MAP.get(dm_wx, '')  # 食伤制杀

    sev = _severity(sha_rooted)

    results.append({
        'name': '官杀混杂',
        'severity': sev,
        'disease_god': '七杀',
        'disease_element': sha_wx,
        'disease_gan': best_sha['gan'],
        'disease_position': best_sha['position'],
        'affected_god': '正官',
        'affected_element': zg_wx,
        'affected_gan': best_zg['gan'],
        'affected_position': best_zg['position'],
        'medicine': f'食伤({medicine_wx})制杀',
        'medicine_element': medicine_wx,
        'reason': (
            f'正官{best_zg["gan"]}{zg_wx}与七杀{best_sha["gan"]}{sha_wx}同时有根，'
            f'无食伤制化，官杀混杂'
        ),
    })
    return results


def _detect_tancai_huaiyin(
    day_master: str,
    dm_wx: str,
    bazi_parts: list[str],
) -> list[dict]:
    """贪财坏印（财星破印）— 《子平真诠》"印轻逢财，印格败也"；《神峰通考》"用印以财为病"

    病源：财星克破印星
    条件：印星"轻"（无本气根或仅余气根）+ 财星有根 + 无官杀通关
    关键：印星必须"轻"才能被财破。若印星强旺（有本气根+透干），财星破不了印。

    药方：官杀泄财生印 — 官杀在财印之间通关（财→官→印）

    化解条件：官杀通关 — 财生官→官生印，财不破印
    """
    results = []

    yin_instances = (
        _find_shishen_instances(day_master, '正印', bazi_parts)
        + _find_shishen_instances(day_master, '偏印', bazi_parts)
    )
    cai_instances = (
        _find_shishen_instances(day_master, '正财', bazi_parts)
        + _find_shishen_instances(day_master, '偏财', bazi_parts)
    )

    if not yin_instances or not cai_instances:
        return results

    yin_rooted = [x for x in yin_instances if x['root_weight'] > 0 or x['is_transparent']]
    cai_rooted = [x for x in cai_instances if x['root_weight'] > 0 or x['is_transparent']]

    if not yin_rooted or not cai_rooted:
        return results

    # 《子平真诠》"印轻逢财" — 印星必须"轻"才能被财破
    # 印星"轻"：无本气根（仅有中气/余气根），或虽有本气根但被冲克
    # 印星"重"：有本气根+透干 → 财星破不了印
    yin_benqi = [x for x in yin_rooted if x['qi_level'] == '本气']
    yin_transparent = [x for x in yin_rooted if x['is_transparent']]
    yin_is_heavy = len(yin_benqi) >= 1 and len(yin_transparent) >= 1
    if yin_is_heavy:
        return results  # 印星强旺，财星破不了印

    # 检查是否有官杀通关（财生官→官生印，财不破印）
    guan_sha_instances = (
        _find_shishen_instances(day_master, '正官', bazi_parts)
        + _find_shishen_instances(day_master, '七杀', bazi_parts)
    )
    guan_sha_rooted = [x for x in guan_sha_instances if x['root_weight'] > 0 or x['is_transparent']]
    if guan_sha_rooted:
        return results  # 官杀通关，财→官→印，财不破印

    best_yin = _best_instance(yin_rooted)
    best_cai = _best_instance(cai_rooted)
    yin_wx = GAN_WUXING.get(best_yin['gan'], '')
    cai_wx = GAN_WUXING.get(best_cai['gan'], '')
    medicine_wx = KE_MAP.get(dm_wx, '')  # 官杀五行 = 克日主

    sev = _severity(cai_rooted)

    results.append({
        'name': '贪财坏印',
        'severity': sev,
        'disease_god': '财星',
        'disease_element': cai_wx,
        'disease_gan': best_cai['gan'],
        'disease_position': best_cai['position'],
        'affected_god': '印星',
        'affected_element': yin_wx,
        'affected_gan': best_yin['gan'],
        'affected_position': best_yin['position'],
        'medicine': f'官杀({medicine_wx})泄财生印',
        'medicine_element': medicine_wx,
        'reason': (
            f'印星{best_yin["gan"]}{yin_wx}在{best_yin["position"]}轻（无本气根或仅余气），'
            f'财星{best_cai["gan"]}{cai_wx}在{best_cai["position"]}有根，'
            f'财星克破印星'
        ),
    })
    return results


def _detect_qisha_wuzhi(
    day_master: str,
    dm_wx: str,
    bazi_parts: list[str],
) -> list[dict]:
    """七杀无制 — 《子平真诠》"七煞逢财无制，煞格败也"；《神峰通考》"偏官无制曰七杀，故宜制伏"

    病源：七杀无食神制或印星化
    条件：七杀有根 + 无食神制杀 + 无印星化杀
    变体：若同时有财星生杀，则为"财党杀无制"（更凶）

    药方：食伤制杀 — 食伤克制七杀

    化解条件（任一即可化解此病）：
    1. 食神制杀
    2. 印星化杀
    """
    results = []

    sha_instances = _find_shishen_instances(day_master, '七杀', bazi_parts)
    if not sha_instances:
        return results

    sha_rooted = [x for x in sha_instances if x['root_weight'] > 0 or x['is_transparent']]
    if not sha_rooted:
        return results

    # 检查是否有食神制杀或印星化杀
    shishen_instances = _find_shishen_instances(day_master, '食神', bazi_parts)
    yin_instances = (
        _find_shishen_instances(day_master, '正印', bazi_parts)
        + _find_shishen_instances(day_master, '偏印', bazi_parts)
    )
    shishen_rooted = [x for x in shishen_instances if x['root_weight'] > 0 or x['is_transparent']]
    yin_rooted = [x for x in yin_instances if x['root_weight'] > 0 or x['is_transparent']]

    if shishen_rooted or yin_rooted:
        return results  # 有制化，不成病

    # 检查是否财党杀（财星生杀无制）— 财星生七杀使杀更凶
    cai_instances = (
        _find_shishen_instances(day_master, '正财', bazi_parts)
        + _find_shishen_instances(day_master, '偏财', bazi_parts)
    )
    cai_rooted = [x for x in cai_instances if x['root_weight'] > 0 or x['is_transparent']]
    has_cai_dang_sha = len(cai_rooted) > 0

    best_sha = _best_instance(sha_rooted)
    sha_wx = GAN_WUXING.get(best_sha['gan'], '')
    medicine_wx = WO_KE_MAP.get(dm_wx, '')  # 食伤五行 = 日主所生

    name = '财党杀无制' if has_cai_dang_sha else '七杀无制'
    sev = _severity(sha_rooted)

    results.append({
        'name': name,
        'severity': sev,
        'disease_god': '七杀',
        'disease_element': sha_wx,
        'disease_gan': best_sha['gan'],
        'disease_position': best_sha['position'],
        'affected_god': '日主',
        'affected_element': dm_wx,
        'affected_gan': day_master,
        'affected_position': '日干',
        'medicine': f'食伤({medicine_wx})制杀',
        'medicine_element': medicine_wx,
        'reason': (
            f'七杀{best_sha["gan"]}{sha_wx}在{best_sha["position"]}有根，'
            f'无食神制杀或印星化杀'
            + ('，财星党杀为祸' if has_cai_dang_sha else '')
        ),
    })
    return results


def _detect_yongshen_chong(
    day_master: str,
    dm_wx: str,
    bazi_parts: list[str],
) -> list[dict]:
    """用神被冲 — 《子平真诠》"官逢刑冲破害，官格败也"

    病源：月支被其他地支冲克
    条件：月支与其他地支构成六冲（ZHI_CHONG 表）

    药方：合解冲或制冲 — 通过地支合来化解冲

    注意：月支是用神的根基（"用神专寻月令"），月支被冲则用神根基动摇。
    """
    results = []

    zhis = [p[1] for p in bazi_parts if len(p) >= 2]
    if len(zhis) < 2:
        return results

    month_zhi = zhis[1]  # 月支是用神的根基

    for i, zhi in enumerate(zhis):
        if i == 1:
            continue  # 跳过月支自身
        pair = frozenset({month_zhi, zhi})
        if pair in ZHI_CHONG:
            results.append({
                'name': '用神被冲',
                'severity': 'active',  # 冲是直接作用，始终为 active
                'disease_god': '冲',
                'disease_element': '',
                'disease_gan': '',
                'disease_position': f'{zhi}冲{month_zhi}',
                'affected_god': '月令',
                'affected_element': '',
                'affected_gan': '',
                'affected_position': f'月支{month_zhi}',
                'medicine': '合解冲或制冲',
                'medicine_element': '',
                'reason': f'月支{month_zhi}被{zhi}冲，用神根基动摇',
            })
            break  # 只报告一次（取第一个冲即可）

    return results


def _detect_shenqiang_yinzong_tousha(
    day_master: str,
    dm_wx: str,
    bazi_parts: list[str],
    element_forces: dict = None,
) -> list[dict]:
    """身强印重透煞 — 《子平真诠》"印格败：身强印重而透煞"

    病源：身旺印旺又透七杀
    条件：身强（印比占比≥50%）+ 印星有本气根+透干 + 天干透七杀
    原理：印星太旺反为偏颇，杀得印助更凶

    药方：食伤制杀泄印 — 食伤克制七杀，同时泄印星之力

    身强判断：
    - 有五行力量数据时：印比占比≥50%
    - 无力量数据时：比劫+印星数量≥2（粗判）
    """
    results = []

    # 《子平真诠》"身强印重" — 必须身强才构成此病
    # 身强判断：印比≥50%或日主五行占比≥35%
    if element_forces:
        pct = element_forces.get('percent', {})
        sheng_wo_wx = SHENG_MAP.get(dm_wx, '')
        yin_bi_pct = pct.get(dm_wx, 0) + pct.get(sheng_wo_wx, 0)
        if yin_bi_pct < 50:
            return results  # 身不强，不构成此病
    else:
        # 无力量数据时，用比劫+印星数量粗判
        bj_count = len(_find_shishen_instances(day_master, '比肩', bazi_parts))
        bj_count += len(_find_shishen_instances(day_master, '劫财', bazi_parts))
        yin_count = len(_find_shishen_instances(day_master, '正印', bazi_parts))
        yin_count += len(_find_shishen_instances(day_master, '偏印', bazi_parts))
        if bj_count + yin_count < 2:
            return results  # 身不强，不构成此病

    yin_instances = (
        _find_shishen_instances(day_master, '正印', bazi_parts)
        + _find_shishen_instances(day_master, '偏印', bazi_parts)
    )
    sha_instances = _find_shishen_instances(day_master, '七杀', bazi_parts)

    if not yin_instances or not sha_instances:
        return results

    yin_rooted = [x for x in yin_instances if x['root_weight'] > 0 or x['is_transparent']]
    sha_rooted = [x for x in sha_instances if x['root_weight'] > 0 or x['is_transparent']]

    if not yin_rooted or not sha_rooted:
        return results

    # 印星"重"：有本气根+透干 — 两者兼备才算"重"
    yin_benqi = [x for x in yin_rooted if x['qi_level'] == '本气']
    yin_transparent = [x for x in yin_rooted if x['is_transparent']]
    yin_is_heavy = len(yin_benqi) >= 1 and len(yin_transparent) >= 1

    if not yin_is_heavy:
        return results  # 印星不重，不构成此病

    best_yin = _best_instance(yin_rooted)
    best_sha = _best_instance(sha_rooted)
    yin_wx = GAN_WUXING.get(best_yin['gan'], '')
    sha_wx = GAN_WUXING.get(best_sha['gan'], '')
    medicine_wx = WO_KE_MAP.get(dm_wx, '')  # 食伤制杀

    sev = _severity(sha_rooted)

    results.append({
        'name': '身强印重透煞',
        'severity': sev,
        'disease_god': '七杀',
        'disease_element': sha_wx,
        'disease_gan': best_sha['gan'],
        'disease_position': best_sha['position'],
        'affected_god': '印星',
        'affected_element': yin_wx,
        'affected_gan': best_yin['gan'],
        'affected_position': best_yin['position'],
        'medicine': f'食伤({medicine_wx})制杀泄印',
        'medicine_element': medicine_wx,
        'reason': (
            f'印星{best_yin["gan"]}{yin_wx}在{best_yin["position"]}重（有本气根+透干），'
            f'七杀{best_sha["gan"]}{sha_wx}在{best_sha["position"]}，'
            f'身强印重透煞，印星太旺反为偏颇'
        ),
    })
    return results


def _detect_shangguan_shengcai_daisa(
    day_master: str,
    dm_wx: str,
    bazi_parts: list[str],
) -> list[dict]:
    """伤官生财带煞 — 《子平真诠》"伤官格败：生财生带煞"

    病源：伤官生财又透七杀，财转党杀
    条件：伤官有根 + 财星有根 + 七杀有根 + 无食神制杀
    原理：伤官生财本为吉，但财又生杀，杀得财助反为祸

    药方：食伤制杀 — 食神克制七杀，截断财→杀的传递链

    化解条件：食神制杀 — 《子平真诠》"煞逢食制"，食神制杀可化解财党杀
    """
    results = []

    sg_instances = _find_shishen_instances(day_master, '伤官', bazi_parts)
    cai_instances = (
        _find_shishen_instances(day_master, '正财', bazi_parts)
        + _find_shishen_instances(day_master, '偏财', bazi_parts)
    )
    sha_instances = _find_shishen_instances(day_master, '七杀', bazi_parts)

    if not sg_instances or not cai_instances or not sha_instances:
        return results

    sg_rooted = [x for x in sg_instances if x['root_weight'] > 0 or x['is_transparent']]
    cai_rooted = [x for x in cai_instances if x['root_weight'] > 0 or x['is_transparent']]
    sha_rooted = [x for x in sha_instances if x['root_weight'] > 0 or x['is_transparent']]

    if not sg_rooted or not cai_rooted or not sha_rooted:
        return results

    # 检查是否有食神制杀 — 若有食神制杀，则七杀受制不为病
    # 《子平真诠》"煞逢食制" — 食神制杀可化解财党杀
    shishen_instances = _find_shishen_instances(day_master, '食神', bazi_parts)
    shishen_rooted = [x for x in shishen_instances if x['root_weight'] > 0 or x['is_transparent']]
    if shishen_rooted:
        return results  # 食神制杀，不构成此病

    best_sg = _best_instance(sg_rooted)
    best_cai = _best_instance(cai_rooted)
    best_sha = _best_instance(sha_rooted)
    sg_wx = GAN_WUXING.get(best_sg['gan'], '')
    cai_wx = GAN_WUXING.get(best_cai['gan'], '')
    sha_wx = GAN_WUXING.get(best_sha['gan'], '')
    medicine_wx = WO_KE_MAP.get(dm_wx, '')  # 食伤制杀

    sev = _severity(sha_rooted)

    results.append({
        'name': '伤官生财带煞',
        'severity': sev,
        'disease_god': '七杀',
        'disease_element': sha_wx,
        'disease_gan': best_sha['gan'],
        'disease_position': best_sha['position'],
        'affected_god': '财星',
        'affected_element': cai_wx,
        'affected_gan': best_cai['gan'],
        'affected_position': best_cai['position'],
        'medicine': f'食伤({medicine_wx})制杀',
        'medicine_element': medicine_wx,
        'reason': (
            f'伤官{best_sg["gan"]}{sg_wx}生财{best_cai["gan"]}{cai_wx}，'
            f'又透七杀{best_sha["gan"]}{sha_wx}，财转党杀，杀得财助为祸'
        ),
    })
    return results
