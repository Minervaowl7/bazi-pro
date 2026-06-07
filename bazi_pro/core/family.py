"""六亲分析模块 — 从八字命盘中提取六亲关系维度的确定性分析

核心概念：
- 宫位（palace）：四柱对应不同亲属——年柱=祖上/父母宫，月柱=父母/兄弟宫，日柱=配偶宫，时柱=子女宫
- 六亲星（star）：以日主为中心推导的十神，对应不同亲属——偏财=父，正印=母，比劫=兄弟，官杀=子女等
- 缘分深浅（affinity）：综合星之旺衰、冲合、墓绝、神煞等因素判定亲属缘分

分析项目（共5类六亲维度）：
1. 父亲 — 偏财为父星（不分性别），年柱/月柱为父宫
2. 母亲 — 正印为母星（不分性别），年柱/月柱为母宫
3. 兄弟姐妹 — 比肩/劫财为兄弟星，月柱为兄弟宫
4. 子女 — 正官七杀(男)/食神伤官(女)为子女星，时柱为子女宫
5. 六亲风险 — 年柱天克地冲、孤辰寡宿近宫等

古籍依据：
- 《子平真诠》"论六亲"："以日主为主，配合年月时，分论六亲"
- 《渊海子平》"论六亲取用"："偏财为父，正印为母"
- 《三命通会》"论六亲"："男以官杀为子，女以食伤为子"
- 《滴天髓》"何知其人父先丧，年月财官被克伤"
"""

from __future__ import annotations

from bazi_pro.core.branches import CANGGAN_WEIGHT, SHIER_CHANGSHENG, ZHI_CHONG
from bazi_pro.core.constants import GAN_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan


_PILLAR_NAMES = ['年柱', '月柱', '日柱', '时柱']


def _get_transparent_gans(bazi_parts: list[str]) -> set[str]:
    return {p[0] for p in bazi_parts if len(p) >= 1}


def _find_star_instances(
    day_master: str,
    target_shishen: str,
    bazi_parts: list[str],
) -> list[dict]:
    transparent = _get_transparent_gans(bazi_parts)
    results = []

    for i, part in enumerate(bazi_parts):
        if len(part) < 2:
            continue
        gan, zhi = part[0], part[1]
        pillar = _PILLAR_NAMES[i] if i < 4 else ''

        if derive_shishen(day_master, gan) == target_shishen:
            results.append({
                'gan': gan,
                'position': f'{pillar}干',
                'pillar_idx': i,
                'is_transparent': True,
                'qi_level': '透干',
                'root_weight': 1.0,
            })

        for cg, ql in get_canggan(zhi):
            if derive_shishen(day_master, cg) == target_shishen:
                results.append({
                    'gan': cg,
                    'position': f'{pillar}支{zhi}({ql})',
                    'pillar_idx': i,
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


def _get_six_relatives(gender: str) -> dict:
    if gender == '男':
        return {
            'father': {'stars': ['偏财'], 'palace': [0, 1]},
            'mother': {'stars': ['正印'], 'palace': [0, 1]},
            'siblings': {'stars': ['比肩', '劫财'], 'palace': [1]},
            'children': {'stars': ['正官', '七杀'], 'palace': [3]},
        }
    return {
        'father': {'stars': ['偏财'], 'palace': [0, 1]},
        'mother': {'stars': ['正印'], 'palace': [0, 1]},
        'siblings': {'stars': ['比肩', '劫财'], 'palace': [1]},
        'children': {'stars': ['食神', '伤官'], 'palace': [3]},
    }


def _calc_star_strength(instances: list[dict]) -> int:
    if not instances:
        return 0
    max_weight = max(x['root_weight'] for x in instances)
    transparent_count = sum(1 for x in instances if x['is_transparent'])
    score = max_weight * 40 + transparent_count * 20
    if any(x['qi_level'] == '本气' for x in instances):
        score += 20
    elif any(x['qi_level'] == '中气' for x in instances):
        score += 10
    return min(100, score)


def _calc_affinity(
    day_master: str,
    instances: list[dict],
    strength: int,
    bazi_parts: list[str] = None,
    relations: list = None,
    shensha: dict = None,
    palace_indices: list = None,
) -> tuple[str, list[dict]]:
    if not instances:
        return '浅', [{'type': '星不现', 'detail': '六亲星未现于原局'}]

    score = 50
    indicators = []

    score += (strength - 50) * 0.4

    if relations:
        star_zhis = set()
        for inst in instances:
            pos = inst.get('position', '')
            if '支' in pos:
                zhi = pos.split('支')[1][0] if len(pos.split('支')[1]) > 0 else ''
                if zhi:
                    star_zhis.add(zhi)
        for rel in relations:
            if rel.get('type') == '地支冲':
                elems = rel.get('elements', [])
                if any(e in star_zhis for e in elems):
                    score -= 15
                    indicators.append({'type': '冲', 'detail': f'六亲星地支{rel.get("result", "")}'})

    dm_changsheng = SHIER_CHANGSHENG.get(day_master, {})
    for inst in instances:
        pos = inst.get('position', '')
        for zhi in '子丑寅卯辰巳午未申酉戌亥':
            if zhi in pos:
                stage = dm_changsheng.get(zhi, '')
                if stage in ('墓', '绝'):
                    score -= 10
                    indicators.append({'type': stage, 'detail': f'六亲星在{zhi}（{stage}），缘分偏浅'})
                break

    if shensha and palace_indices is not None and bazi_parts:
        palace_zhis = set()
        for idx in palace_indices:
            if idx < len(bazi_parts) and len(bazi_parts[idx]) >= 2:
                palace_zhis.add(bazi_parts[idx][1])

        for shensha_name in ('孤辰', '寡宿'):
            shensha_info = shensha.get(shensha_name)
            if shensha_info:
                positions = shensha_info if isinstance(shensha_info, list) else [shensha_info]
                for pos_info in positions:
                    if isinstance(pos_info, dict):
                        pos_str = pos_info.get('position', '')
                    else:
                        pos_str = str(pos_info)
                    for zhi in palace_zhis:
                        if zhi in pos_str:
                            score -= 10
                            indicators.append({'type': shensha_name, 'detail': f'{shensha_name}临宫位'})

    if score >= 70:
        return '深', indicators
    if score >= 40:
        return '中', indicators
    return '浅', indicators


def _check_risk_indicator(
    bazi_parts: list[str],
    relations: list = None,
    shensha: dict = None,
) -> list[dict]:
    risks = []

    if relations:
        year_zhi = bazi_parts[0][1] if len(bazi_parts) >= 1 and len(bazi_parts[0]) >= 2 else ''
        month_zhi = bazi_parts[1][1] if len(bazi_parts) >= 2 and len(bazi_parts[1]) >= 2 else ''
        year_gan = bazi_parts[0][0] if len(bazi_parts) >= 1 and len(bazi_parts[0]) >= 1 else ''
        month_gan = bazi_parts[1][0] if len(bazi_parts) >= 2 and len(bazi_parts[1]) >= 1 else ''

        for rel in relations:
            if rel.get('type') == '地支冲':
                elems = rel.get('elements', [])
                if year_zhi in elems and month_zhi in elems:
                    risks.append({
                        'type': '年月柱地支相冲',
                        'affects': '父母',
                        'detail': f'{rel.get("result", "")}，父母宫逢冲，主父母关系或自身幼年多波折',
                    })

    return risks


def _get_star_in_palace(
    instances: list[dict],
    palace_indices: list[int],
) -> list[dict]:
    return [x for x in instances if x.get('pillar_idx') in palace_indices]


def analyze_family(
    day_master: str,
    gender: str,
    bazi_parts: list[str],
    shensha: dict = None,
    relations: list = None,
) -> dict:
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {
            'father': {'star': '', 'star_name': '', 'palace': '', 'strength': 0, 'affinity': '浅', 'indicators': []},
            'mother': {'star': '', 'star_name': '', 'palace': '', 'strength': 0, 'affinity': '浅', 'indicators': []},
            'siblings': {'star': '', 'count': 0, 'affinity': '浅', 'indicators': []},
            'children': {'star': '', 'count_estimate': '', 'affinity': '浅', 'indicators': []},
            'family_risks': [],
            'summary': '日主五行不明，无法分析六亲',
        }

    relatives = _get_six_relatives(gender)
    father_stars = relatives['father']['stars']
    mother_stars = relatives['mother']['stars']
    sibling_stars = relatives['siblings']['stars']
    child_stars = relatives['children']['stars']

    father_instances = []
    for s in father_stars:
        father_instances.extend(_find_star_instances(day_master, s, bazi_parts))
    mother_instances = []
    for s in mother_stars:
        mother_instances.extend(_find_star_instances(day_master, s, bazi_parts))
    sibling_instances = []
    for s in sibling_stars:
        sibling_instances.extend(_find_star_instances(day_master, s, bazi_parts))
    child_instances = []
    for s in child_stars:
        child_instances.extend(_find_star_instances(day_master, s, bazi_parts))

    father_strength = _calc_star_strength(father_instances)
    mother_strength = _calc_star_strength(mother_instances)
    sibling_strength = _calc_star_strength(sibling_instances)
    child_strength = _calc_star_strength(child_instances)

    father_affinity, father_indicators = _calc_affinity(
        day_master, father_instances, father_strength, bazi_parts, relations, shensha, [0, 1],
    )
    mother_affinity, mother_indicators = _calc_affinity(
        day_master, mother_instances, mother_strength, bazi_parts, relations, shensha, [0, 1],
    )
    sibling_affinity, sibling_indicators = _calc_affinity(
        day_master, sibling_instances, sibling_strength, bazi_parts, relations, shensha, [1],
    )
    child_affinity, child_indicators = _calc_affinity(
        day_master, child_instances, child_strength, bazi_parts, relations, shensha, [3],
    )

    father_in_palace = _get_star_in_palace(father_instances, [0, 1])
    if not father_in_palace and father_instances:
        father_indicators.append({'type': '星不在宫', 'detail': '父星不在年月柱，与父缘分较远'})

    mother_in_palace = _get_star_in_palace(mother_instances, [0, 1])
    if not mother_in_palace and mother_instances:
        mother_indicators.append({'type': '星不在宫', 'detail': '母星不在年月柱，与母缘分较远'})

    child_in_palace = _get_star_in_palace(child_instances, [3])
    if not child_in_palace and child_instances:
        child_indicators.append({'type': '星不在宫', 'detail': '子女星不在时柱，与子女缘分较远'})

    sibling_ganji = len(sibling_instances)
    if sibling_ganji >= 3:
        sibling_count = '多（3个以上）'
    elif sibling_ganji >= 2:
        sibling_count = '中等（2-3个）'
    elif sibling_ganji >= 1:
        sibling_count = '少（1-2个）'
    else:
        sibling_count = '无明显兄弟姐妹星'

    child_ganji = len(child_instances)
    if child_ganji >= 3:
        child_estimate = '子女星旺，子女缘较深'
    elif child_ganji >= 2:
        child_estimate = '子女星有根，子女缘中等'
    elif child_ganji >= 1:
        child_estimate = '子女星偏弱，子女缘较浅'
    else:
        child_estimate = '子女星不显，子女缘需大运引动'

    family_risks = _check_risk_indicator(bazi_parts, relations, shensha)

    summary_parts = []
    summary_parts.append(f'父缘{father_affinity}')
    summary_parts.append(f'母缘{mother_affinity}')
    summary_parts.append(f'兄弟姐妹{sibling_count}')
    summary_parts.append(f'子女缘{"较深" if child_affinity == "深" else "中等" if child_affinity == "中" else "较浅"}')
    if family_risks:
        summary_parts.append('存在六亲风险')

    return {
        'father': {
            'star': '、'.join(father_stars),
            'star_name': father_stars[0] if father_stars else '',
            'palace': '年柱/月柱',
            'strength': father_strength,
            'affinity': father_affinity,
            'indicators': father_indicators,
        },
        'mother': {
            'star': '、'.join(mother_stars),
            'star_name': mother_stars[0] if mother_stars else '',
            'palace': '年柱/月柱',
            'strength': mother_strength,
            'affinity': mother_affinity,
            'indicators': mother_indicators,
        },
        'siblings': {
            'star': '、'.join(sibling_stars),
            'count': sibling_ganji,
            'count_desc': sibling_count,
            'affinity': sibling_affinity,
            'indicators': sibling_indicators,
        },
        'children': {
            'star': '、'.join(child_stars),
            'count_estimate': child_estimate,
            'affinity': child_affinity,
            'indicators': child_indicators,
        },
        'family_risks': family_risks,
        'summary': '，'.join(summary_parts),
    }
