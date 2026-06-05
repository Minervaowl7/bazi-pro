"""命局层次评分系统 (Chart Quality Scoring)

基于确定性计算数据，从 5 个维度评估命局质量：
1. 格局清纯度 (30分) — 格局判定的纯度和完整性
2. 用神状态   (25分) — 用神是否明确、有力、无伤
3. 冲突交战   (15分) — 破格条件和刑冲合害的严重程度
4. 五行流通   (15分) — 五行力量分布的均衡性和流通性
5. 大运配合   (15分) — 大运对命局的配合程度

总分 100 分，分级：
  90-100: 卓越命局 (Exceptional)
  80-89:  优秀命局 (Excellent)
  70-79:  良好命局 (Good)
  60-69:  平稳命局 (Stable)
  <60:    需努力命局 (Challenging)
"""

from bazi_pro.core.constants import GAN_WUXING
from bazi_pro.core.stems import KE_MAP, SHENG_MAP


def calculate_chart_quality(result: dict, dayun_list: list | None = None) -> dict:
    dims = []
    dims.append(_score_pattern_purity(result))
    dims.append(_score_yongshen_status(result))
    dims.append(_score_conflict(result))
    dims.append(_score_wuxing_flow(result))
    dims.append(_score_dayun(result, dayun_list))

    total = sum(d['score'] for d in dims)
    total_max = sum(d['max'] for d in dims)

    level, level_en, tier = _grade(total)

    return {
        'total': total,
        'total_max': total_max,
        'level': level,
        'level_en': level_en,
        'tier': tier,
        'dimensions': dims,
    }


def _score_pattern_purity(result: dict) -> dict:
    pattern = result.get('pattern', {})
    confidence = pattern.get('confidence', 0)
    break_conds = pattern.get('break_conditions', [])
    pat_name = pattern.get('pattern', '')
    max_score = 30

    base = int(confidence * 22)

    if not break_conds:
        base += 8
    else:
        high = sum(1 for b in break_conds if b.get('severity') == 'high')
        med = sum(1 for b in break_conds if b.get('severity') == 'medium')
        base -= high * 4
        base -= med * 2

    special = ('从强格', '从财格', '从官杀格', '从儿格', '从势格', '化气格')
    if any(s in pat_name for s in special):
        base += 2

    score = max(0, min(max_score, base))
    detail = _describe_pattern(pattern, break_conds)

    return {
        'name': '格局清纯度',
        'name_en': 'Pattern Purity',
        'score': score,
        'max': max_score,
        'detail': detail,
    }


def _score_yongshen_status(result: dict) -> dict:
    ys = result.get('yongshen', {})
    yongshen_wx = ys.get('yongshen', '')
    max_score = 25

    if not yongshen_wx or yongshen_wx == '待定':
        return {
            'name': '用神状态',
            'name_en': 'Yongshen Clarity',
            'score': 5,
            'max': max_score,
            'detail': '用神待定，命局格局未明',
        }

    score = 12

    xishen = ys.get('xishen', [])
    jishen = ys.get('jishen', [])
    if xishen:
        score += 3
    if jishen:
        score += 1

    ws = result.get('strength', {}).get('wangshuai', {})
    if ws.get('verdict') and ws['verdict'] not in ('中和', '数据不足'):
        score += 2

    pattern = result.get('pattern', {})
    conf = pattern.get('confidence', 0)
    score += int(conf * 7)

    score = max(0, min(max_score, score))

    detail = f"用神{yongshen_wx}"
    if xishen:
        detail += f"，喜神{('、'.join(xishen))}"
    if jishen:
        detail += f"，忌神{('、'.join(jishen))}"

    return {
        'name': '用神状态',
        'name_en': 'Yongshen Clarity',
        'score': score,
        'max': max_score,
        'detail': detail,
    }


def _score_conflict(result: dict) -> dict:
    pattern = result.get('pattern', {})
    break_conds = pattern.get('break_conditions', [])
    relations = result.get('relations', [])
    max_score = 15

    penalty = 0
    for b in break_conds:
        if b.get('severity') == 'high':
            penalty += 5
        elif b.get('severity') == 'medium':
            penalty += 2
        else:
            penalty += 1

    chongs = sum(1 for r in relations
                 if isinstance(r, dict)
                 and '冲' in r.get('type', r.get('description', '')))
    xings = sum(1 for r in relations
                if isinstance(r, dict)
                and ('刑' in r.get('type', r.get('description', '')))
                and '六害' not in r.get('type', r.get('description', '')))

    if chongs >= 3:
        penalty += 4
    elif chongs >= 2:
        penalty += 2
    elif chongs >= 1:
        penalty += 1

    if xings >= 2:
        penalty += 3
    elif xings >= 1:
        penalty += 1

    score = max(0, min(max_score, max_score - penalty))

    if penalty == 0:
        detail = '无重大冲突，格局清纯'
    else:
        parts = []
        if break_conds:
            parts.append(f'{len(break_conds)}个破格条件')
        if chongs:
            parts.append(f'{chongs}组冲')
        if xings:
            parts.append(f'{xings}组刑')
        detail = '、'.join(parts) + '，略有损伤' if penalty <= 4 else '、'.join(parts) + '，冲突较多'

    return {
        'name': '冲突交战',
        'name_en': 'Conflict',
        'score': score,
        'max': max_score,
        'detail': detail,
    }


def _score_wuxing_flow(result: dict) -> dict:
    ef = result.get('elements', {})
    pct = ef.get('percent', {})
    max_score = 15

    if not pct:
        return {
            'name': '五行流通',
            'name_en': 'Element Flow',
            'score': 7,
            'max': max_score,
            'detail': '五行数据不可用',
        }

    values = [pct.get(wx, 0) for wx in ('木', '火', '土', '金', '水')]
    raw_total = sum(values)
    if raw_total < 0.1:
        return {
            'name': '五行流通',
            'name_en': 'Element Flow',
            'score': 0,
            'max': max_score,
            'detail': '五行数据缺失',
        }
    total = raw_total

    avg = total / 5
    variance = sum((v - avg) ** 2 for v in values) / 5
    cv = (variance ** 0.5) / max(avg, 0.01)

    if cv < 0.15:
        score = 15
        detail = '五行均衡，流通极佳'
    elif cv < 0.3:
        score = 13
        detail = '五行流通顺畅'
    elif cv < 0.5:
        score = 10
        detail = '五行略有偏颇，但尚能流通'
    elif cv < 0.8:
        score = 7
        detail = '五行偏枯明显，流通受阻'
    else:
        score = 4
        detail = '五行严重失衡，流通不畅'

    present = [wx for wx, v in zip(('木', '火', '土', '金', '水'), values) if v > 2]
    if len(present) == 5:
        score = min(max_score, score + 1)

    score = max(0, min(max_score, score))

    vals_str = '、'.join(f'{wx}{v:.0f}%' for wx, v in zip(('木', '火', '土', '金', '水'), values))
    detail += f'（{vals_str}）'

    return {
        'name': '五行流通',
        'name_en': 'Element Flow',
        'score': score,
        'max': max_score,
        'detail': detail,
    }


def _score_dayun(result: dict, dayun_list: list | None = None) -> dict:
    max_score = 15
    if not dayun_list:
        return {
            'name': '大运配合',
            'name_en': 'Dayun Fortune',
            'score': 0,
            'max': max_score,
            'detail': '大运数据不可用',
        }

    ys = result.get('yongshen', {})
    yongshen_wx = ys.get('yongshen', '')
    xishen_wx = set(ys.get('xishen', []))
    jishen_wx = set(ys.get('jishen', []))

    if not yongshen_wx or yongshen_wx == '待定':
        return {
            'name': '大运配合',
            'name_en': 'Dayun Fortune',
            'score': 0,
            'max': max_score,
            'detail': '用神待定，无法评估大运配合',
        }

    mid_dayun = [dy for dy in dayun_list if isinstance(dy, dict)
                 and _age_overlaps_mid_life(dy.get('age_range', ''))]

    if not mid_dayun:
        mid_dayun = dayun_list[:8]

    ji_count = 0
    xiong_count = 0
    total_dy = len(mid_dayun)

    for dy in mid_dayun:
        dy_gan = dy.get('gan', '')
        dy_wx = GAN_WUXING.get(dy_gan, '')
        if dy_wx in jishen_wx:
            xiong_count += 1
        elif dy_wx in xishen_wx or dy_wx == yongshen_wx:
            ji_count += 1
        elif dy_wx and yongshen_wx:
            if SHENG_MAP.get(yongshen_wx) == dy_wx:
                ji_count += 1
            elif KE_MAP.get(yongshen_wx) == dy_wx:
                xiong_count += 1

    if total_dy > 0:
        ji_ratio = ji_count / total_dy
        score = int(ji_ratio * max_score)
    else:
        score = 0

    score = max(0, min(max_score, score))

    detail_parts = []
    if ji_count:
        detail_parts.append(f'{ji_count}柱吉运')
    if xiong_count:
        detail_parts.append(f'{xiong_count}柱凶运')

    if detail_parts:
        detail = f"中年大运{'、'.join(detail_parts)}"
    else:
        detail = '大运平平，无明显吉凶'

    return {
        'name': '大运配合',
        'name_en': 'Dayun Fortune',
        'score': score,
        'max': max_score,
        'detail': detail,
    }


def _age_overlaps_mid_life(age_range: str) -> bool:
    try:
        parts = age_range.replace('岁', '').split('-')
        start = int(parts[0])
        end = int(parts[1]) if len(parts) > 1 else start + 10
        return start < 70 and end > 10
    except (ValueError, IndexError):
        return False


def _describe_pattern(pattern: dict, break_conds: list) -> str:
    pat = pattern.get('pattern', '')
    reason = pattern.get('reason', '')

    if break_conds:
        high_breaks = [b for b in break_conds if b.get('severity') == 'high']
        if high_breaks:
            return f'{pat}，但{high_breaks[0].get("type", "有破格")}'
        return f'{pat}，略有瑕疵'

    if '透' in pat and '无' not in pat:
        return f'{pat}，格神透干通根，有护格之神'

    if '无' in pat:
        return f'{pat}，格局未定，需大运引出'

    return f'{pat}，格局完整'


def _grade(total: int) -> tuple[str, str, str]:
    if total >= 90:
        return '高', '卓越命局', 'Exceptional Chart'
    elif total >= 80:
        return '较高', '优秀命局', 'Excellent Chart'
    elif total >= 70:
        return '中', '良好命局', 'Good Chart'
    elif total >= 60:
        return '平稳', '平稳命局', 'Stable Chart'
    else:
        return '需努力', '挑战命局', 'Challenging Chart'
