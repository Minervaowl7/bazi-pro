"""格局之病检测 — 枭神夺食、伤官见官、官杀混杂、比劫争财、食神制杀逢枭"""

from bazi_pro.core.branches import CANGGAN_WEIGHT
from bazi_pro.core.constants import GAN_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.stems import KE_MAP, SHENG_MAP, WO_KE_MAP


def _get_transparent_gans(bazi_parts: list[str]) -> set[str]:
    """返回所有透干（天干）的干集合。"""
    return {p[0] for p in bazi_parts if len(p) >= 1}


def _find_shishen_instances(
    day_master: str,
    target_shishen: str,
    bazi_parts: list[str],
) -> list[dict]:
    """
    找出命盘中所有属于 target_shishen 的干（天干+藏干）。
    返回列表，每项含 gan, position, is_transparent, qi_level, root_weight。
    """
    transparent = _get_transparent_gans(bazi_parts)
    positions = ['年', '月', '日', '时']
    results = []

    for i, part in enumerate(bazi_parts):
        if len(part) < 2:
            continue
        gan, zhi = part[0], part[1]
        pos = positions[i] if i < 4 else ''

        # 天干
        if derive_shishen(day_master, gan) == target_shishen:
            results.append({
                'gan': gan,
                'position': f'{pos}干',
                'is_transparent': True,
                'qi_level': '透干',
                'root_weight': 1.2,
            })

        # 藏干
        for cg, ql in get_canggan(zhi):
            if derive_shishen(day_master, cg) == target_shishen:
                results.append({
                    'gan': cg,
                    'position': f'{pos}支{zhi}({ql})',
                    'is_transparent': cg in transparent,
                    'qi_level': ql,
                    'root_weight': CANGGAN_WEIGHT.get(ql, 0),
                })

    # 去重：同一个干只保留最强的一条
    seen: dict[str, dict] = {}
    for item in results:
        g = item['gan']
        if g not in seen or item['root_weight'] > seen[g]['root_weight']:
            seen[g] = item
    return list(seen.values())


def _severity(disease_instances: list[dict]) -> str:
    """
    根据病源干的存在方式判断严重程度。
    active: 病源透干
    potential: 病源只在藏干（不透干）
    """
    for inst in disease_instances:
        if inst['is_transparent']:
            return 'active'
    return 'potential'


def _best_instance(instances: list[dict]) -> dict:
    """返回根气最强的一条实例。"""
    return max(instances, key=lambda x: x['root_weight'])


def detect_disease(
    day_master: str,
    bazi_parts: list[str],
    element_forces: dict,
) -> dict:
    """
    检测原局格局之病。

    返回:
        {
            'has_disease': bool,
            'items': [DiseaseItem, ...],
            'medicine_advice': str,
        }

    DiseaseItem 字段见下方各检测函数。
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {'has_disease': False, 'items': [], 'medicine_advice': ''}

    items: list[dict] = []

    items.extend(_detect_xiaoshen_duoshi(day_master, dm_wx, bazi_parts, element_forces))
    items.extend(_detect_shangguan_jianguan(day_master, dm_wx, bazi_parts))
    items.extend(_detect_bijie_zhengcai(day_master, dm_wx, bazi_parts, element_forces))
    items.extend(_detect_guansha_hunza(day_master, dm_wx, bazi_parts))

    medicine_parts = []
    for item in items:
        med = item.get('medicine', '')
        if med and med not in medicine_parts:
            medicine_parts.append(med)

    advice = '；'.join(medicine_parts) if medicine_parts else ''

    # Sort by severity: 'active' first, then 'potential'
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
    """枭神夺食 / 食神制杀逢枭"""
    results = []

    pian_yin_instances = _find_shishen_instances(day_master, '偏印', bazi_parts)
    shishen_instances = _find_shishen_instances(day_master, '食神', bazi_parts)

    if not pian_yin_instances or not shishen_instances:
        return results

    # 偏印需要有根（本气/中气/透干）
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
    """伤官见官"""
    results = []

    sg_instances = _find_shishen_instances(day_master, '伤官', bazi_parts)
    zg_instances = _find_shishen_instances(day_master, '正官', bazi_parts)

    if not sg_instances or not zg_instances:
        return results

    sg_rooted = [x for x in sg_instances if x['root_weight'] > 0 or x['is_transparent']]
    zg_rooted = [x for x in zg_instances if x['root_weight'] > 0 or x['is_transparent']]

    if not sg_rooted or not zg_rooted:
        return results

    # 检查是否有财星通关（财星有根）
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
    """比劫争财"""
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

    # 财星弱：无根或仅余气
    cai_rooted = [x for x in cai_instances if x['root_weight'] >= 0.6 or x['is_transparent']]
    if cai_rooted:
        return results  # 财星有根，不成病

    best_bj = _best_instance(bj_instances)
    best_cai = _best_instance(cai_instances)
    bj_wx = GAN_WUXING.get(best_bj['gan'], '')
    cai_wx = GAN_WUXING.get(best_cai['gan'], '')
    ke_bj_wx = KE_MAP.get(dm_wx, '')  # 官杀克比劫

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
    """官杀混杂"""
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
