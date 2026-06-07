"""感情婚姻分析模块 — 从八字原局分析婚姻感情维度

核心概念：
- 配偶星（spouse star）：男命以正财为妻星、偏财为次缘；女命以正官为夫星、七杀为次缘
- 配偶宫（spouse palace）：日支为配偶宫，是婚姻的"家"
- 配偶星强度：透干力量最强，有根次之，仅藏干最弱
- 婚姻风险：日支逢冲（婚姻不稳）、比劫争财（男命争妻）、伤官见官（女命克夫）

检测项目（共5类）：
1. 配偶星定位 — 找出正财/偏财（男）或正官/七杀（女）
2. 配偶宫分析 — 日支五行、十神、冲合害关系
3. 配偶星强度评估 — 透干/有根/被冲合等综合评分
4. 婚姻风险指标 — 多配偶星、日支逢冲、比劫争财、伤官见官、孤辰寡宿
5. 感情倾向判定 — 早婚/晚婚、复杂感情、稳定性

古籍依据：
- 《三命通会》"论妻妾"与"论女命"：配偶星与配偶宫的基本规则
- 《子平真诠》"论用神成败救应"：格局对婚姻的影响
- 《渊海子平》"论日主"：日支配偶宫的冲合害规则
- 《神峰通考》"病药说"：婚姻风险的古籍定义
"""

from __future__ import annotations

from bazi_pro.core.branches import CANGGAN_WEIGHT, ZHI_CHONG, ZHI_HAI, ZHI_HE
from bazi_pro.core.constants import GAN_WUXING, ZHI_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan


def _get_spouse_star_name(gender: str) -> dict[str, str]:
    """返回配偶星十神名称映射

    男命：正财=妻星，偏财=次缘（情人/异性缘）
    女命：正官=夫星，七杀=次缘（情人/异性缘）
    """
    if gender == '男':
        return {'primary': '正财', 'secondary': '偏财', 'primary_label': '妻星', 'secondary_label': '次缘'}
    return {'primary': '正官', 'secondary': '七杀', 'primary_label': '夫星', 'secondary_label': '次缘'}


def _find_spouse_star_instances(
    day_master: str,
    gender: str,
    bazi_parts: list[str],
) -> list[dict]:
    """找出配偶星实例（天干+藏干）

    遍历四柱天干和地支藏干，找出所有配偶星（正财/偏财或正官/七杀），
    并记录其位置、是否透干、气之深浅、根气权重等信息。
    """
    spouse_info = _get_spouse_star_name(gender)
    positions = ['年', '月', '日', '时']
    results = []

    for i, part in enumerate(bazi_parts):
        if len(part) < 2:
            continue
        gan, zhi = part[0], part[1]
        pos = positions[i] if i < 4 else ''

        ss = derive_shishen(day_master, gan)
        if ss in (spouse_info['primary'], spouse_info['secondary']):
            is_primary = ss == spouse_info['primary']
            results.append({
                'gan': gan,
                'position': f'{pos}干',
                'is_transparent': True,
                'qi_level': '透干',
                'root_weight': 1.0,
                'star_type': 'primary' if is_primary else 'secondary',
                'star_name': ss,
                'star_label': spouse_info['primary_label'] if is_primary else spouse_info['secondary_label'],
            })

        for cg, ql in get_canggan(zhi):
            ss_cg = derive_shishen(day_master, cg)
            if ss_cg in (spouse_info['primary'], spouse_info['secondary']):
                is_primary = ss_cg == spouse_info['primary']
                results.append({
                    'gan': cg,
                    'position': f'{pos}支{zhi}({ql})',
                    'is_transparent': False,
                    'qi_level': ql,
                    'root_weight': CANGGAN_WEIGHT.get(ql, 0),
                    'star_type': 'primary' if is_primary else 'secondary',
                    'star_name': ss_cg,
                    'star_label': spouse_info['primary_label'] if is_primary else spouse_info['secondary_label'],
                })

    seen: dict[str, dict] = {}
    for item in results:
        key = f"{item['gan']}_{item['star_type']}"
        if key not in seen or item['root_weight'] > seen[key]['root_weight']:
            seen[key] = item
    return list(seen.values())


def _analyze_spouse_palace(
    day_master: str,
    bazi_parts: list[str],
    relations: list[dict] | None,
) -> dict:
    """分析配偶宫（日支）

    日支为配偶宫，分析其五行、十神、以及受冲合害的影响。
    """
    if len(bazi_parts) < 3 or len(bazi_parts[2]) < 2:
        return {'branch': '', 'wuxing': '', 'shishen': '', 'impacts': []}

    day_zhi = bazi_parts[2][1]
    wx = ZHI_WUXING.get(day_zhi, '')
    canggan = get_canggan(day_zhi)
    cg0 = canggan[0][0] if canggan else ''
    ss = derive_shishen(day_master, cg0) if cg0 else ''

    impacts = []
    if relations:
        for rel in relations:
            rel_type = rel.get('type', '')
            elements = rel.get('elements', [])
            if day_zhi in elements:
                other = [e for e in elements if e != day_zhi]
                if rel_type == '地支冲':
                    impacts.append({'type': '冲', 'other': other[0] if other else '', 'detail': f'{day_zhi}逢{other[0] if other else ""}冲'})
                elif rel_type == '地支合':
                    impacts.append({'type': '合', 'other': other[0] if other else '', 'detail': f'{day_zhi}合{other[0] if other else ""}'})
                elif rel_type == '地支害':
                    impacts.append({'type': '害', 'other': other[0] if other else '', 'detail': f'{day_zhi}害{other[0] if other else ""}'})

    return {
        'branch': day_zhi,
        'wuxing': wx,
        'shishen': ss,
        'impacts': impacts,
    }


def _assess_spouse_star_strength(instances: list[dict]) -> dict:
    """评估配偶星综合强度

    评分规则：
    - 透干：+30分（力量外显）
    - 本气根：+30分（根基深厚）
    - 中气根：+15分（根基中等）
    - 余气根：+5分（根基浅薄）
    - 多个实例叠加：每个额外实例+5分

    返回：score(0-100), level(旺/中/弱), details
    """
    if not instances:
        return {'score': 0, 'level': '弱', 'detail': '无配偶星'}

    score = 0
    details = []

    for inst in instances:
        if inst['is_transparent']:
            score += 30
            details.append(f'{inst["gan"]}透干')
        elif inst['qi_level'] == '本气':
            score += 30
            details.append(f'{inst["gan"]}有本气根')
        elif inst['qi_level'] == '中气':
            score += 15
            details.append(f'{inst["gan"]}有中气根')
        elif inst['qi_level'] == '余气':
            score += 5
            details.append(f'{inst["gan"]}有余气根')

    if len(instances) > 1:
        bonus = (len(instances) - 1) * 5
        score += bonus
        details.append(f'多现+{bonus}')

    score = min(score, 100)

    if score >= 70:
        level = '旺'
    elif score >= 40:
        level = '中'
    else:
        level = '弱'

    return {'score': score, 'level': level, 'detail': '；'.join(details)}


def _detect_marriage_risks(
    day_master: str,
    gender: str,
    bazi_parts: list[str],
    spouse_instances: list[dict],
    palace: dict,
    shensha: dict | None,
    relations: list[dict] | None,
) -> list[dict]:
    """检测婚姻风险指标

    检测项目：
    1. 多配偶星：正财+偏财同透（男）或正官+七杀同透（女）= 感情复杂
    2. 日支逢冲：配偶宫被冲 = 婚姻不稳
    3. 比劫争财（男命）：比劫旺而财星弱 = 竞争夺妻
    4. 伤官见官（女命）：伤官克正官 = 攻击夫星
    5. 孤辰/寡宿在配偶宫：日支见孤辰/寡宿
    """
    risks = []

    primary_transparent = [x for x in spouse_instances if x['star_type'] == 'primary' and x['is_transparent']]
    secondary_transparent = [x for x in spouse_instances if x['star_type'] == 'secondary' and x['is_transparent']]

    if primary_transparent and secondary_transparent:
        zc_t = [x for x in primary_transparent + secondary_transparent if x.get('star_name') == '正财']
        pc_t = [x for x in primary_transparent + secondary_transparent if x.get('star_name') == '偏财']
        zg_t = [x for x in primary_transparent + secondary_transparent if x.get('star_name') == '正官']
        qg_t = [x for x in primary_transparent + secondary_transparent if x.get('star_name') == '七杀']
        if zc_t and pc_t:
            detail = '正偏财星同透，感情关系复杂'
        elif zg_t and qg_t:
            detail = '正偏官星同透，感情关系复杂'
        else:
            detail = '多配偶星同透，感情关系复杂'
        risks.append({
            'type': '多配偶星同透',
            'severity': 'medium',
            'detail': detail,
        })

    has_clash = False
    if relations:
        for rel in relations:
            if rel.get('type') == '地支冲':
                elements = rel.get('elements', [])
                if palace.get('branch') in elements:
                    has_clash = True
                    risks.append({
                        'type': '日支逢冲',
                        'severity': 'high',
                        'detail': f'配偶宫{palace["branch"]}逢冲，婚姻不稳定',
                    })
                    break

    if gender == '男':
        bijie_instances = (
            _find_star_instances(day_master, '比肩', bazi_parts)
            + _find_star_instances(day_master, '劫财', bazi_parts)
        )
        cai_instances = [x for x in spouse_instances if x['star_name'] in ('正财', '偏财')]
        bijie_transparent = [x for x in bijie_instances if x['is_transparent']]
        cai_weak = [x for x in cai_instances if x['root_weight'] < 0.6 and not x['is_transparent']]
        if len(bijie_transparent) >= 2 and cai_weak:
            risks.append({
                'type': '比劫争财',
                'severity': 'high',
                'detail': '比劫旺而财星弱，有争夺妻星之象',
            })

    if gender == '女':
        shangguan_instances = _find_star_instances(day_master, '伤官', bazi_parts)
        zg_instances = [x for x in spouse_instances if x['star_name'] == '正官']
        sg_rooted = [x for x in shangguan_instances if x['root_weight'] > 0 or x['is_transparent']]
        zg_rooted = [x for x in zg_instances if x['root_weight'] > 0 or x['is_transparent']]
        if sg_rooted and zg_rooted:
            cai_found = _find_star_instances(day_master, '正财', bazi_parts) + _find_star_instances(day_master, '偏财', bazi_parts)
            has_cai = bool(cai_found)
            if not has_cai:
                risks.append({
                    'type': '伤官见官',
                    'severity': 'high',
                    'detail': '伤官克正官，有攻击夫星之象',
                })

    if shensha and palace.get('branch'):
        for ss_name in ['孤辰', '寡宿']:
            ss_data = shensha.get(ss_name, {})
            if isinstance(ss_data, dict) and palace['branch'] in ss_data.get('positions', []):
                risks.append({
                    'type': ss_name,
                    'severity': 'medium',
                    'detail': f'配偶宫{palace["branch"]}见{ss_name}，婚姻缘分较薄',
                })

    return risks


def _find_star_instances(
    day_master: str,
    target_shishen: str,
    bazi_parts: list[str],
) -> list[dict]:
    """找出命盘中所有属于 target_shishen 的干（天干+藏干）"""
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
                    'is_transparent': False,
                    'qi_level': ql,
                    'root_weight': CANGGAN_WEIGHT.get(ql, 0),
                })

    seen: dict[str, dict] = {}
    for item in results:
        key = f"{item['gan']}_{item['position']}"
        if key not in seen or item['root_weight'] > seen[key]['root_weight']:
            seen[key] = item
    return list(seen.values())


def _assess_romance_tendency(
    spouse_instances: list[dict],
    palace: dict,
    risks: list[dict],
) -> dict:
    """评估感情倾向

    - early_romance: 早婚倾向（配偶星旺且配偶宫无冲）
    - complex_romance: 复杂感情（多配偶星同透或日支逢冲）
    - stable: 感情稳定（配偶星适中、配偶宫无冲无害）
    """
    has_clash = any(r['type'] == '日支逢冲' for r in risks)
    has_multiple = any(r['type'] == '多配偶星同透' for r in risks)
    has_bijie = any(r['type'] == '比劫争财' for r in risks)
    has_shangguan = any(r['type'] == '伤官见官' for r in risks)

    palace_has_harm = any(imp['type'] == '害' for imp in palace.get('impacts', []))

    early_romance = False
    if spouse_instances:
        strong_stars = [x for x in spouse_instances if x['is_transparent'] or x['root_weight'] >= 0.6]
        early_romance = len(strong_stars) > 0 and not has_clash

    complex_romance = has_multiple or has_clash or has_bijie or has_shangguan

    stable = (
        not has_clash
        and not has_multiple
        and not has_bijie
        and not has_shangguan
        and not palace_has_harm
    )

    return {
        'early_romance': early_romance,
        'complex_romance': complex_romance,
        'stable': stable,
    }


def _generate_marriage_summary(
    gender: str,
    spouse_instances: list[dict],
    strength: dict,
    risks: list[dict],
    tendency: dict,
) -> str:
    """生成婚姻分析摘要文本"""
    parts = []

    spouse_info = _get_spouse_star_name(gender)
    if spouse_instances:
        primary = [x for x in spouse_instances if x['star_type'] == 'primary']
        if primary:
            best = max(primary, key=lambda x: x['root_weight'])
            parts.append(f'{spouse_info["primary_label"]}{best["gan"]}{GAN_WUXING.get(best["gan"], "")}在{best["position"]}')
    else:
        parts.append(f'未见{spouse_info["primary_label"]}')

    parts.append(f'配偶星强度{strength["level"]}（{strength["score"]}分）')

    if risks:
        high_risks = [r for r in risks if r['severity'] == 'high']
        if high_risks:
            parts.append(f'婚姻风险：{high_risks[0]["type"]}')

    if tendency['stable']:
        parts.append('感情较稳定')
    elif tendency['complex_romance']:
        parts.append('感情关系复杂')

    return '；'.join(parts)


def analyze_marriage(
    day_master: str,
    gender: str,
    bazi_parts: list[str],
    shensha: dict | None = None,
    relations: list[dict] | None = None,
) -> dict:
    """感情婚姻分析顶层入口函数

    从八字原局分析婚姻感情维度，包括配偶星、配偶宫、配偶星强度、
    婚姻风险、感情倾向等。

    参数：
        day_master: 日主天干（如'甲'）
        gender: 性别（'男'/'女'）
        bazi_parts: 四柱干支列表（如['甲子', '丙寅', '己卯', '癸酉']）
        shensha: 神煞字典（可选，用于检测孤辰/寡宿等）
        relations: 地支关系列表（可选，用于检测冲合害）

    返回：
        dict {
            'spouse_star': 配偶星信息（name, gender_context, instances），
            'spouse_palace': 配偶宫信息（branch, wuxing, shishen, impacts），
            'spouse_star_strength': 配偶星强度（score, level, details），
            'marriage_risks': 婚姻风险列表，
            'romance_tendency': 感情倾向（early_romance, complex_romance, stable），
            'summary': 分析摘要文本，
        }
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {
            'spouse_star': {'name': '', 'gender_context': '', 'instances': []},
            'spouse_palace': {'branch': '', 'wuxing': '', 'shishen': '', 'impacts': []},
            'spouse_star_strength': {'score': 0, 'level': '弱', 'detail': '无效日主'},
            'marriage_risks': [],
            'romance_tendency': {'early_romance': False, 'complex_romance': False, 'stable': True},
            'summary': '无效日主，无法分析',
        }

    spouse_info = _get_spouse_star_name(gender)
    spouse_instances = _find_spouse_star_instances(day_master, gender, bazi_parts)
    palace = _analyze_spouse_palace(day_master, bazi_parts, relations)
    strength = _assess_spouse_star_strength(spouse_instances)
    risks = _detect_marriage_risks(day_master, gender, bazi_parts, spouse_instances, palace, shensha, relations)
    tendency = _assess_romance_tendency(spouse_instances, palace, risks)
    summary = _generate_marriage_summary(gender, spouse_instances, strength, risks, tendency)

    primary_instances = [x for x in spouse_instances if x['star_type'] == 'primary']
    star_name = spouse_info['primary']
    star_label = spouse_info['primary_label']

    return {
        'spouse_star': {
            'name': star_name,
            'gender_context': star_label,
            'instances': spouse_instances,
        },
        'spouse_palace': palace,
        'spouse_star_strength': strength,
        'marriage_risks': risks,
        'romance_tendency': tendency,
        'summary': summary,
    }
