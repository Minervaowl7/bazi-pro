"""财运分析模块 — 从八字命盘中提取财运维度的确定性分析

核心概念：
- 正财（zhengcai）：稳定收入、薪资、正当得财
- 偏财（piancai）：横财、投资、副业、意外之财
- 身旺担财：日主强旺方能驾驭财星，否则财多身弱反为祸
- 食伤生财：食伤泄日主之秀气而生财星，为才能生财之象

分析项目（共5类财运格局）：
1. 食伤生财 — 食伤有根+财星有根，才能生财（吉）
2. 财官双美 — 财星有根+正官有根，事业得财（吉）
3. 比劫争财 — 比劫旺+财星弱，财务竞争/损耗（凶）
4. 财多身弱 — 财星力量过重+日主偏弱，留不住钱（凶）
5. 枭神夺食 — 偏印克食神，断财源链条（凶）

古籍依据：
- 《子平真诠》"论财"："财星宜藏不宜透，透则易被劫夺"
- 《滴天髓》"何知其人富，财气通门户"
- 《子平真诠》"财格败：比劫争财"
- 《渊海子平》"食神生财，富贵自然来"
- 《神峰通考》"枭神夺食，食格败也"
"""

from __future__ import annotations

from bazi_pro.core.branches import CANGGAN_WEIGHT
from bazi_pro.core.constants import GAN_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.stems import SHENG_MAP, WO_KE_MAP


def _get_transparent_gans(bazi_parts: list[str]) -> set[str]:
    return {p[0] for p in bazi_parts if len(p) >= 1}


def _find_shishen_instances(
    day_master: str,
    target_shishen: str,
    bazi_parts: list[str],
) -> list[dict]:
    transparent = _get_transparent_gans(bazi_parts)
    positions = ['年', '月', '日', '时']
    results = []

    for i, part in enumerate(bazi_parts):
        if len(part) < 2:
            continue
        gan, zhi = part[0], part[1]
        pos = positions[i] if i < 4 else ''

        if derive_shishen(day_master, gan) == target_shishen:
            results.append({
                'gan': gan,
                'position': f'{pos}干',
                'is_transparent': True,
                'qi_level': '透干',
                'root_weight': 1.0,
            })

        for cg, ql in get_canggan(zhi):
            if derive_shishen(day_master, cg) == target_shishen:
                results.append({
                    'gan': cg,
                    'position': f'{pos}支{zhi}({ql})',
                    'is_transparent': cg in transparent,
                    'qi_level': ql,
                    'root_weight': CANGGAN_WEIGHT.get(ql, 0),
                })

    seen: dict[str, dict] = {}
    for item in results:
        g = item['gan']
        if g not in seen or item['root_weight'] > seen[g]['root_weight']:
            seen[g] = item
    return list(seen.values())


def _best_instance(instances: list[dict]) -> dict:
    return max(instances, key=lambda x: x['root_weight'])


def _has_root(instances: list[dict]) -> bool:
    return any(x['root_weight'] >= 0.6 or x['is_transparent'] for x in instances)


def _is_strong_enough(
    day_master: str,
    bazi_parts: list[str],
    element_forces: dict = None,
) -> dict:
    if element_forces:
        dm_wx = GAN_WUXING.get(day_master, '')
        yin_wx = SHENG_MAP.get(dm_wx, '') if dm_wx else ''
        percent = element_forces.get('percent', {})
        bi_pct = percent.get(dm_wx, 0)
        yin_pct = percent.get(yin_wx, 0) if yin_wx else 0
        yin_bi_pct = bi_pct + yin_pct
        if yin_bi_pct >= 50:
            return {'can_carry': True, 'detail': f'印比占比{yin_bi_pct:.1f}%，身旺可担财'}
        if yin_bi_pct >= 35:
            return {'can_carry': True, 'detail': f'印比占比{yin_bi_pct:.1f}%，身中和偏旺，尚可担财'}
        return {'can_carry': False, 'detail': f'印比占比{yin_bi_pct:.1f}%，身弱难担财'}

    bj_count = len(_find_shishen_instances(day_master, '比肩', bazi_parts))
    bj_count += len(_find_shishen_instances(day_master, '劫财', bazi_parts))
    yin_count = len(_find_shishen_instances(day_master, '正印', bazi_parts))
    yin_count += len(_find_shishen_instances(day_master, '偏印', bazi_parts))
    total = bj_count + yin_count
    if total >= 3:
        return {'can_carry': True, 'detail': f'比劫+印星共{total}个，身旺可担财'}
    if total >= 2:
        return {'can_carry': True, 'detail': f'比劫+印星共{total}个，身中和，尚可担财'}
    return {'can_carry': False, 'detail': f'比劫+印星仅{total}个，身弱难担财'}


def _detect_shishan_shengcai(
    day_master: str,
    bazi_parts: list[str],
) -> dict | None:
    dm_wx = GAN_WUXING.get(day_master, '')
    caishen_wx = WO_KE_MAP.get(dm_wx, '') if dm_wx else ''
    if not caishen_wx:
        return None

    shishen_instances = (
        _find_shishen_instances(day_master, '食神', bazi_parts)
        + _find_shishen_instances(day_master, '伤官', bazi_parts)
    )
    cai_instances = (
        _find_shishen_instances(day_master, '正财', bazi_parts)
        + _find_shishen_instances(day_master, '偏财', bazi_parts)
    )
    if not shishen_instances or not cai_instances:
        return None
    if not _has_root(shishen_instances) or not _has_root(cai_instances):
        return None

    return {
        'pattern': '食伤生财',
        'description': '食伤有根生财星，才能生财之象，主凭技艺专长得财',
        'quality': 'good',
    }


def _detect_caiguan_shuangmei(
    day_master: str,
    bazi_parts: list[str],
) -> dict | None:
    cai_instances = (
        _find_shishen_instances(day_master, '正财', bazi_parts)
        + _find_shishen_instances(day_master, '偏财', bazi_parts)
    )
    zg_instances = _find_shishen_instances(day_master, '正官', bazi_parts)
    if not cai_instances or not zg_instances:
        return None
    if not _has_root(cai_instances) or not _has_root(zg_instances):
        return None

    return {
        'pattern': '财官双美',
        'description': '财星与正官皆有根，事业顺遂得财，主因社会地位或职权而获财',
        'quality': 'good',
    }


def _detect_bijie_zhengcai(
    day_master: str,
    bazi_parts: list[str],
) -> dict | None:
    bj_instances = (
        _find_shishen_instances(day_master, '比肩', bazi_parts)
        + _find_shishen_instances(day_master, '劫财', bazi_parts)
    )
    cai_instances = (
        _find_shishen_instances(day_master, '正财', bazi_parts)
        + _find_shishen_instances(day_master, '偏财', bazi_parts)
    )
    if not bj_instances or not cai_instances:
        return None

    bj_transparent = [x for x in bj_instances if x['is_transparent']]
    bj_benqi = [x for x in bj_instances if x['qi_level'] == '本气']
    bj_strong = len(bj_transparent) >= 2 or len(bj_benqi) >= 1
    if not bj_strong:
        return None

    cai_strong = [x for x in cai_instances if x['root_weight'] >= 0.6 or x['is_transparent']]
    if cai_strong:
        return None

    return {
        'pattern': '比劫争财',
        'description': '比劫旺而财星弱，主财务竞争、合伙纠纷或投资损耗',
        'quality': 'bad',
    }


def _detect_caiduo_shenruo(
    day_master: str,
    bazi_parts: list[str],
    element_forces: dict = None,
    carry_info: dict = None,
) -> dict | None:
    if carry_info and carry_info.get('can_carry', True):
        return None

    cai_instances = (
        _find_shishen_instances(day_master, '正财', bazi_parts)
        + _find_shishen_instances(day_master, '偏财', bazi_parts)
    )
    if not cai_instances:
        return None

    cai_has_root = _has_root(cai_instances)

    if element_forces:
        dm_wx = GAN_WUXING.get(day_master, '')
        percent = element_forces.get('percent', {})
        cai_wx = WO_KE_MAP.get(dm_wx, '') if dm_wx else ''
        cai_pct = percent.get(cai_wx, 0) if cai_wx else 0
        if cai_pct >= 25 and cai_has_root:
            return {
                'pattern': '财多身弱',
                'description': f'财星力量{cai_pct:.1f}%且有根，日主偏弱留不住钱，主财来财去',
                'quality': 'bad',
            }
    elif cai_has_root:
        return {
            'pattern': '财多身弱',
            'description': '财星有根而日主偏弱，留不住钱，主财来财去',
            'quality': 'bad',
        }

    return None


def _detect_xiaoshen_duoshi(
    day_master: str,
    bazi_parts: list[str],
) -> dict | None:
    pian_yin_instances = _find_shishen_instances(day_master, '偏印', bazi_parts)
    shishen_instances = _find_shishen_instances(day_master, '食神', bazi_parts)
    if not pian_yin_instances or not shishen_instances:
        return None

    pian_yin_strong = [x for x in pian_yin_instances if x['root_weight'] >= 0.6 or x['is_transparent']]
    if not pian_yin_strong:
        return None

    shishen_rooted = [x for x in shishen_instances if x['root_weight'] > 0 or x['is_transparent']]
    if not shishen_rooted:
        return None

    return {
        'pattern': '枭神夺食',
        'description': '偏印克食神，断食伤生财之链条，主财源受阻或收入不稳定',
        'quality': 'bad',
    }


def _calc_wealth_risks(
    day_master: str,
    bazi_parts: list[str],
    carry_info: dict,
    relations: list = None,
) -> list[dict]:
    risks = []

    bj_instances = (
        _find_shishen_instances(day_master, '比肩', bazi_parts)
        + _find_shishen_instances(day_master, '劫财', bazi_parts)
    )
    cai_instances = (
        _find_shishen_instances(day_master, '正财', bazi_parts)
        + _find_shishen_instances(day_master, '偏财', bazi_parts)
    )
    if bj_instances and cai_instances:
        bj_transparent = [x for x in bj_instances if x['is_transparent']]
        if len(bj_transparent) >= 2:
            risks.append({
                'type': '比劫争财',
                'severity': 'high',
                'detail': f'{len(bj_transparent)}个比劫透干，主合伙纠纷或投资竞争',
            })

    if not carry_info.get('can_carry', True):
        risks.append({
            'type': '财多身弱',
            'severity': 'high',
            'detail': carry_info.get('detail', '日主偏弱难担财'),
        })

    if relations:
        cai_zhis = set()
        for x in cai_instances:
            pos = x.get('position', '')
            for z in '子丑寅卯辰巳午未申酉戌亥':
                if z in pos:
                    cai_zhis.add(z)
                    break
        for rel in relations:
            if rel.get('type') == '地支冲':
                zhis = rel.get('elements', [])
                if any(z in cai_zhis for z in zhis):
                    risks.append({
                        'type': '财星逢冲',
                        'severity': 'medium',
                        'detail': f'财星地支{"".join(zhis)}逢冲，主财运波动',
                    })

    return risks


def _calc_income_tendency(
    day_master: str,
    bazi_parts: list[str],
    patterns: list[dict],
    element_forces: dict = None,
) -> dict:
    pattern_names = {p['pattern'] for p in patterns}

    stable = '财官双美' in pattern_names
    windfall = '食伤生财' in pattern_names

    zhengcai_instances = _find_shishen_instances(day_master, '正财', bazi_parts)
    piancai_instances = _find_shishen_instances(day_master, '偏财', bazi_parts)
    zhengcai_transparent = [x for x in zhengcai_instances if x['is_transparent']]
    piancai_transparent = [x for x in piancai_instances if x['is_transparent']]

    if zhengcai_transparent and not piancai_transparent:
        stable = True
    elif piancai_transparent and not zhengcai_transparent:
        windfall = True
    elif zhengcai_transparent and piancai_transparent:
        stable = True
        windfall = True

    if element_forces:
        dm_wx = GAN_WUXING.get(day_master, '')
        cai_wx = WO_KE_MAP.get(dm_wx, '') if dm_wx else ''
        percent = element_forces.get('percent', {})
        cai_pct = percent.get(cai_wx, 0) if cai_wx else 0
        if cai_pct < 10:
            stable = False
            windfall = False

    parts = []
    if stable and windfall:
        parts.append('正偏财兼有，稳定收入与投资理财皆可获利')
    elif stable:
        parts.append('正财为主，适合稳定薪资收入')
    elif windfall:
        parts.append('偏财为主，适合投资理财或副业收入')
    else:
        parts.append('财星不显或力量不足，财运需努力开拓')

    if '食伤生财' in pattern_names:
        parts.append('食伤生财，凭技艺专长生财')

    detail = '；'.join(parts)
    return {'stable': stable, 'windfall': windfall, 'detail': detail}


def _calc_wealth_score(
    patterns: list[dict],
    carry_info: dict,
    risks: list[dict],
    zhengcai_transparent: bool,
    piancai_transparent: bool,
) -> int:
    score = 50

    for p in patterns:
        if p['quality'] == 'good':
            score += 15
        elif p['quality'] == 'bad':
            score -= 10

    if carry_info.get('can_carry', True):
        score += 10
    else:
        score -= 15

    for r in risks:
        if r['severity'] == 'high':
            score -= 10
        elif r['severity'] == 'medium':
            score -= 5

    if zhengcai_transparent:
        score += 5
    if piancai_transparent:
        score += 5

    return max(0, min(100, score))


def analyze_wealth(
    day_master: str,
    gender: str,
    bazi_parts: list[str],
    element_forces: dict = None,
    shensha: dict = None,
    relations: list = None,
) -> dict:
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {
            'wealth_stars': {
                'zhengcai': {'instances': [], 'transparent': False, 'rooted': False},
                'piancai': {'instances': [], 'transparent': False, 'rooted': False},
            },
            'wealth_patterns': [],
            'day_master_carry_wealth': {'can_carry': False, 'detail': '日主五行不明'},
            'wealth_risks': [],
            'wealth_score': 0,
            'income_tendency': {'stable': False, 'windfall': False, 'detail': '无法分析'},
            'summary': '日主五行不明，无法分析财运',
        }

    zhengcai_instances = _find_shishen_instances(day_master, '正财', bazi_parts)
    piancai_instances = _find_shishen_instances(day_master, '偏财', bazi_parts)

    zhengcai_transparent = any(x['is_transparent'] for x in zhengcai_instances)
    piancai_transparent = any(x['is_transparent'] for x in piancai_instances)
    zhengcai_rooted = _has_root(zhengcai_instances)
    piancai_rooted = _has_root(piancai_instances)

    carry_info = _is_strong_enough(day_master, bazi_parts, element_forces)

    patterns = []
    p1 = _detect_shishan_shengcai(day_master, bazi_parts)
    if p1:
        patterns.append(p1)
    p2 = _detect_caiguan_shuangmei(day_master, bazi_parts)
    if p2:
        patterns.append(p2)
    p3 = _detect_bijie_zhengcai(day_master, bazi_parts)
    if p3:
        patterns.append(p3)
    p4 = _detect_caiduo_shenruo(day_master, bazi_parts, element_forces, carry_info)
    if p4:
        patterns.append(p4)
    p5 = _detect_xiaoshen_duoshi(day_master, bazi_parts)
    if p5:
        patterns.append(p5)

    risks = _calc_wealth_risks(day_master, bazi_parts, carry_info, relations)
    income_tendency = _calc_income_tendency(day_master, bazi_parts, patterns, element_forces)
    wealth_score = _calc_wealth_score(
        patterns, carry_info, risks, zhengcai_transparent, piancai_transparent,
    )

    summary_parts = []
    if not zhengcai_instances and not piancai_instances:
        summary_parts.append('原局财星不显，财运需大运流年引动')
    elif zhengcai_transparent and piancai_transparent:
        summary_parts.append('正偏财皆透，财路多元')
    elif zhengcai_transparent:
        summary_parts.append('正财透干，主稳定收入')
    elif piancai_transparent:
        summary_parts.append('偏财透干，主投资理财之财')

    if carry_info.get('can_carry', True):
        summary_parts.append('日主有力担财')
    else:
        summary_parts.append('日主偏弱，财来财去不易留住')

    good_patterns = [p['pattern'] for p in patterns if p['quality'] == 'good']
    bad_patterns = [p['pattern'] for p in patterns if p['quality'] == 'bad']
    if good_patterns:
        summary_parts.append(f'吉格：{"、".join(good_patterns)}')
    if bad_patterns:
        summary_parts.append(f'凶格：{"、".join(bad_patterns)}')

    summary = '，'.join(summary_parts) if summary_parts else '财运平稳'

    return {
        'wealth_stars': {
            'zhengcai': {
                'instances': zhengcai_instances,
                'transparent': zhengcai_transparent,
                'rooted': zhengcai_rooted,
            },
            'piancai': {
                'instances': piancai_instances,
                'transparent': piancai_transparent,
                'rooted': piancai_rooted,
            },
        },
        'wealth_patterns': patterns,
        'day_master_carry_wealth': carry_info,
        'wealth_risks': risks,
        'wealth_score': wealth_score,
        'income_tendency': income_tendency,
        'summary': summary,
    }
