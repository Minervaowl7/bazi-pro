"""健康分析模块 — 从八字原局分析健康体质与风险维度

核心概念：
- 五行-脏腑对应：木=肝胆、火=心小肠、土=脾胃、金=肺大肠、水=肾膀胱
- 天干-身体部位：甲=头/胆、乙=颈/肝、丙=肩/小肠、丁=心/胸、戊=胃/鼻、
  己=脾/腹、庚=筋/大肠、辛=胸/肺、壬=胫/膀胱、癸=肾/足
- 体质寒热：水多=寒、火多=热、金多=燥、木多=湿、土多=中性
- 健康危机：天克地冲、羊刃倒戈、天医/流霞/血刃/飞刃等神煞

检测项目（共5类）：
1. 脏腑风险 — 五行过弱（<10%）或过旺（>30%）对应脏腑风险
2. 身体部位风险 — 天干受克/坐墓绝对应身体部位
3. 体质判定 — 寒热燥湿综合判定
4. 健康危机指标 — 天克地冲、羊刃倒戈、健康相关神煞
5. 健康评分 — 综合评分0-100

古籍依据：
- 《三命通会》"论疾病"：五行与脏腑对应关系
- 《渊海子平》"论天干地支身体"：天干与身体部位对应
- 《子平真诠》"论用神成败救应"：格局对健康的影响
- 《神峰通考》"病药说"：健康风险的古籍定义
"""

from __future__ import annotations

from bazi_pro.core.branches import CANGGAN_WEIGHT, SHIER_CHANGSHENG
from bazi_pro.core.constants import GAN_WUXING, ZHI_WUXING
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.stems import KE_MAP, SHENG_MAP

WUXING_ORGAN = {
    '木': ('肝', '胆'),
    '火': ('心', '小肠'),
    '土': ('脾', '胃'),
    '金': ('肺', '大肠'),
    '水': ('肾', '膀胱'),
}

GAN_BODY_PART = {
    '甲': ('头', '胆'),
    '乙': ('颈', '肝'),
    '丙': ('肩', '小肠'),
    '丁': ('心', '胸'),
    '戊': ('胃', '鼻'),
    '己': ('脾', '腹'),
    '庚': ('筋', '大肠'),
    '辛': ('胸', '肺'),
    '壬': ('胫', '膀胱'),
    '癸': ('肾', '足'),
}

_TOMB绝_STATES = {'墓', '绝'}


def _assess_organ_risks(
    element_forces: dict | None,
    day_master: str,
) -> list[dict]:
    """评估脏腑风险

    规则：
    - 五行占比<10%：对应脏腑虚弱风险（high）
    - 五行占比>30%：对应脏腑亢盛风险（medium）
    - 日主五行特殊关注：日主过弱易体虚
    """
    risks = []
    pct = element_forces.get('percent', {}) if element_forces else {}

    if not pct:
        return risks

    dm_wx = GAN_WUXING.get(day_master, '')

    for wx, organs in WUXING_ORGAN.items():
        ratio = pct.get(wx, 0)
        organ_name = f'{organs[0]}{organs[1]}'

        if ratio < 10:
            risks.append({
                'organ': organ_name,
                'element': wx,
                'status': 'weak',
                'risk_level': 'high',
                'detail': f'{wx}力仅{ratio:.1f}%，{organs[0]}{organs[1]}虚弱风险',
            })
        elif ratio > 30:
            risks.append({
                'organ': organ_name,
                'element': wx,
                'status': 'excess',
                'risk_level': 'medium',
                'detail': f'{wx}力{ratio:.1f}%，{organs[0]}{organs[1]}亢盛风险',
            })

    dm_ratio = pct.get(dm_wx, 0)
    if dm_ratio < 10 and dm_wx:
        dm_organs = WUXING_ORGAN.get(dm_wx, ('', ''))
        risks.append({
            'organ': f'日主{dm_organs[0]}{dm_organs[1]}',
            'element': dm_wx,
            'status': 'weak',
            'risk_level': 'high',
            'detail': f'日主{dm_wx}力仅{dm_ratio:.1f}%，体质偏弱',
        })

    return risks


def _assess_body_part_risks(
    day_master: str,
    bazi_parts: list[str],
    relations: list[dict] | None,
) -> list[dict]:
    """评估身体部位风险

    规则：
    - 天干受克：该天干对应的身体部位有风险
    - 日主坐墓/绝：日柱地支为日主的墓或绝
    """
    risks = []

    positions = ['年', '月', '日', '时']
    for i, part in enumerate(bazi_parts):
        if len(part) < 1:
            continue
        gan = part[0]
        pos = positions[i] if i < 4 else ''
        body = GAN_BODY_PART.get(gan, ('', ''))

        if relations:
            for rel in relations:
                rel_type = rel.get('type', '')
                if rel_type == '天干合':
                    elements = rel.get('elements', [])
                    if gan in elements:
                        hua_wx = rel.get('hua_wuxing', '')
                        target_wx = GAN_WUXING.get(gan, '')
                        if hua_wx and target_wx and hua_wx != target_wx:
                            risks.append({
                                'part': f'{body[0]}{body[1]}',
                                'related_gan': gan,
                                'position': f'{pos}干',
                                'risk': f'{gan}被合化{hua_wx}，{body[0]}{body[1]}受克',
                            })

    gans = [p[0] for p in bazi_parts if len(p) >= 1]
    for i, gan in enumerate(gans):
        for j, other_gan in enumerate(gans):
            if i != j and KE_MAP.get(other_gan, '') == gan:
                body = GAN_BODY_PART.get(gan, ('', ''))
                if body[0]:
                    risks.append({
                        'part': f'{body[0]}{body[1]}',
                        'related_gan': gan,
                        'risk': f'{other_gan}克{gan}，{body[0]}{body[1]}有风险',
                    })

    if len(bazi_parts) >= 3 and len(bazi_parts[2]) >= 2:
        day_zhi = bazi_parts[2][1]
        changsheng = SHIER_CHANGSHENG.get(day_master, {})
        state = changsheng.get(day_zhi, '')
        if state in _TOMB绝_STATES:
            dm_body = GAN_BODY_PART.get(day_master, ('', ''))
            risks.append({
                'part': f'{dm_body[0]}{dm_body[1]}',
                'related_gan': day_master,
                'position': '日干',
                'risk': f'日主{day_master}坐{state}（{day_zhi}），根基薄弱',
            })

    return risks


def _assess_constitution(
    element_forces: dict | None,
    bazi_parts: list[str],
) -> dict:
    """评估体质类型（寒热燥湿）

    规则：
    - 水多=寒，火多=热，金多=燥，木多=湿，土多=中性
    - 月支季节加成：冬月（亥子丑）加寒、夏月（巳午未）加热

    返回：type(偏寒/偏热/偏燥/偏湿/中性), detail
    """
    pct = element_forces.get('percent', {}) if element_forces else {}

    if not pct:
        return {'type': '中性', 'detail': '无五行力量数据'}

    water = pct.get('水', 0)
    fire = pct.get('火', 0)
    metal = pct.get('金', 0)
    wood = pct.get('木', 0)

    season_bonus = {'寒': 0, '热': 0, '燥': 0, '湿': 0}
    if len(bazi_parts) >= 2 and len(bazi_parts[1]) >= 2:
        month_zhi = bazi_parts[1][1]
        if month_zhi in ('亥', '子', '丑'):
            season_bonus['寒'] += 10
        elif month_zhi in ('巳', '午', '未'):
            season_bonus['热'] += 10
        elif month_zhi in ('申', '酉', '戌'):
            season_bonus['燥'] += 5
        elif month_zhi in ('寅', '卯', '辰'):
            season_bonus['湿'] += 5

    scores = {
        '寒': water * 1.0 + season_bonus['寒'],
        '热': fire * 1.0 + season_bonus['热'],
        '燥': metal * 0.8 + season_bonus['燥'],
        '湿': wood * 0.8 + season_bonus['湿'],
    }

    max_type = max(scores, key=scores.get)
    max_score = scores[max_type]

    if max_score < 20:
        return {'type': '中性', 'detail': f'五行分布均衡，寒热燥湿得分均<20'}

    details = []
    for t, s in sorted(scores.items(), key=lambda x: -x[1]):
        if s >= 15:
            details.append(f'{t}={s:.0f}')

    return {'type': f'偏{max_type}', 'detail': '；'.join(details)}


def _detect_crisis_indicators(
    day_master: str,
    bazi_parts: list[str],
    shensha: dict | None,
    relations: list[dict] | None,
) -> list[dict]:
    """检测健康危机指标

    检测项目：
    1. 天克地冲：天干相克+地支相冲同时出现
    2. 羊刃倒戈：阳刃逢冲（甲卯、丙午、戊午、庚酉、壬子逢冲）
    3. 天医：神煞中的天医星
    4. 流霞/血刃/飞刃：健康相关凶煞
    """
    indicators = []

    if relations:
        gans = [p[0] for p in bazi_parts if len(p) >= 1]
        zhis = [p[1] for p in bazi_parts if len(p) >= 2]

        for rel in relations:
            if rel.get('type') == '地支冲':
                elements = rel.get('elements', [])
                if len(elements) == 2:
                    z1, z2 = elements
                    idx1 = zhis.index(z1) if z1 in zhis else -1
                    idx2 = zhis.index(z2) if z2 in zhis else -1
                    if idx1 >= 0 and idx2 >= 0 and idx1 < len(gans) and idx2 < len(gans):
                        g1, g2 = gans[idx1], gans[idx2]
                        wx1 = GAN_WUXING.get(g1, '')
                        wx2 = GAN_WUXING.get(g2, '')
                        if KE_MAP.get(wx1) == wx2 or KE_MAP.get(wx2) == wx1:
                            indicators.append({
                                'type': '天克地冲',
                                'detail': f'{g1}{z1}克冲{g2}{z2}，天干地支同时受克冲',
                            })

    yangren_map = {
        '甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子',
    }
    yangren_zhi = yangren_map.get(day_master, '')
    if yangren_zhi and relations:
        for rel in relations:
            if rel.get('type') == '地支冲':
                elements = rel.get('elements', [])
                if yangren_zhi in elements:
                    indicators.append({
                        'type': '羊刃倒戈',
                        'detail': f'日主{day_master}阳刃{yangren_zhi}逢冲，健康有险',
                    })

    if shensha:
        for ss_name in ['天医', '流霞', '血刃', '飞刃']:
            ss_data = shensha.get(ss_name)
            if ss_data:
                if isinstance(ss_data, dict):
                    positions = ss_data.get('positions', [])
                    if positions:
                        indicators.append({
                            'type': ss_name,
                            'detail': f'命中带{ss_name}（{"、".join(positions)}），需注意健康',
                        })
                elif isinstance(ss_data, list) and ss_data:
                    indicators.append({
                        'type': ss_name,
                        'detail': f'命中带{ss_name}，需注意健康',
                    })

    return indicators


def _calculate_health_score(
    organ_risks: list[dict],
    body_risks: list[dict],
    constitution: dict,
    crisis: list[dict],
) -> int:
    """计算健康综合评分

    基础分80分，根据风险扣分：
    - 脏腑虚弱风险（high）：-8分/个
    - 脏腑亢盛风险（medium）：-4分/个
    - 身体部位风险：-3分/个
    - 健康危机指标：-10分/个
    - 体质偏颇：-5分

    最低0分，最高100分。
    """
    score = 80

    for risk in organ_risks:
        if risk['risk_level'] == 'high':
            score -= 8
        elif risk['risk_level'] == 'medium':
            score -= 4

    score -= len(body_risks) * 3

    score -= len(crisis) * 10

    if constitution.get('type') != '中性':
        score -= 5

    return max(0, min(100, score))


def _generate_health_summary(
    organ_risks: list[dict],
    body_risks: list[dict],
    constitution: dict,
    crisis: list[dict],
    health_score: int,
) -> str:
    """生成健康分析摘要文本"""
    parts = []

    weak_organs = [r for r in organ_risks if r['status'] == 'weak']
    excess_organs = [r for r in organ_risks if r['status'] == 'excess']

    if weak_organs:
        parts.append(f'虚弱脏腑：{"、".join(r["organ"] for r in weak_organs[:2])}')
    if excess_organs:
        parts.append(f'亢盛脏腑：{"、".join(r["organ"] for r in excess_organs[:2])}')

    parts.append(f'体质{constitution["type"]}')

    if crisis:
        parts.append(f'危机指标：{crisis[0]["type"]}')

    parts.append(f'健康评分{health_score}分')

    return '；'.join(parts)


def analyze_health(
    day_master: str,
    gender: str,
    bazi_parts: list[str],
    element_forces: dict | None = None,
    shensha: dict | None = None,
    relations: list[dict] | None = None,
) -> dict:
    """健康分析顶层入口函数

    从八字原局分析健康体质与风险维度，包括脏腑风险、身体部位风险、
    体质类型、健康危机指标、健康评分等。

    参数：
        day_master: 日主天干（如'甲'）
        gender: 性别（'男'/'女'）
        bazi_parts: 四柱干支列表（如['甲子', '丙寅', '己卯', '癸酉']）
        element_forces: 五行力量分布（可选，用于脏腑风险评估）
        shensha: 神煞字典（可选，用于检测天医/流霞等健康神煞）
        relations: 地支关系列表（可选，用于检测天克地冲等）

    返回：
        dict {
            'organ_risks': 脏腑风险列表（organ, element, status, risk_level, detail），
            'body_part_risks': 身体部位风险列表（part, related_gan, position, risk），
            'constitution': 体质类型（type, detail），
            'crisis_indicators': 健康危机指标列表（type, detail），
            'health_score': 健康综合评分（0-100），
            'summary': 分析摘要文本，
        }
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {
            'organ_risks': [],
            'body_part_risks': [],
            'constitution': {'type': '中性', 'detail': '无效日主'},
            'crisis_indicators': [],
            'health_score': 0,
            'summary': '无效日主，无法分析',
        }

    organ_risks = _assess_organ_risks(element_forces, day_master)
    body_risks = _assess_body_part_risks(day_master, bazi_parts, relations)
    constitution = _assess_constitution(element_forces, bazi_parts)
    crisis = _detect_crisis_indicators(day_master, bazi_parts, shensha, relations)
    health_score = _calculate_health_score(organ_risks, body_risks, constitution, crisis)
    summary = _generate_health_summary(organ_risks, body_risks, constitution, crisis, health_score)

    return {
        'organ_risks': organ_risks,
        'body_part_risks': body_risks,
        'constitution': constitution,
        'crisis_indicators': crisis,
        'health_score': health_score,
        'summary': summary,
    }
