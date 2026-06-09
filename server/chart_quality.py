"""命局层次评分系统 (Chart Quality Scoring)

基于确定性计算数据，从 5 个维度评估命局质量：
1. 格局清纯度 (30分) — 格局判定的纯度和完整性
2. 用神状态   (25分) — 用神是否明确、有力（透干有根）、无伤
3. 冲突交战   (15分) — 刑冲的严重程度（区分喜忌）
4. 五行流通   (15分) — 五行力量分布（普通格求中和，特殊格求纯一）
5. 大运配合   (15分) — 大运对命局的配合程度（地支为主，天干为辅）

总分 100 分，分级：
  90-100: 卓越命局 (Exceptional)
  80-89:  优秀命局 (Excellent)
  70-79:  良好命局 (Good)
  60-69:  平稳命局 (Stable)
  <60:    需努力命局 (Challenging)

古籍对齐说明：
  - 格局高低总纲：《子平真诠》第十二章「论用神格局高低」"有情有力"
  - 用神透干有根：《子平真诠》第十六章「论杂气取用」、第三十三章「论财」
  - 破格与救应：《子平真诠》第九章「论用神成败救应」
  - 专旺/从格偏枯：《滴天髓》第十二章「从象」、第十六章「顺局」
  - 冲的喜忌：《子平真诠》第十七章「论墓库刑冲之说」"冲去忌神反为吉"
  - 大运地支权重：《渊海子平》「论大运」"大运看支，岁君看干"
  - 大运成格变格：《子平真诠》第二十六章「论行运成格变格」
"""

from bazi_pro.core.branches import ZHI_CANGGAN
from bazi_pro.core.constants import GAN_WUXING, ZHI_WUXING
from bazi_pro.core.stems import KE_MAP, SHENG_MAP

# 地支四墓库 — 《子平真诠》第十七章：四库喜冲，不为不足
_SI_KU = {'辰', '戌', '丑', '未'}


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


def _is_special_pattern(pat_name: str) -> bool:
    """判断是否为专旺格/从格/化气格（五行偏枯或纯一是成格条件，非缺陷）

    专旺格/从格：《滴天髓》第十二章「从象」、第十六章「顺局」
    化气格：《子平真诠》第四十七章「论杂格」，化气格以所化五行为用，纯一为贵
    """
    special = ('专旺格', '从强格', '从财格', '从官杀格', '从儿格', '从势格',
               '曲直格', '炎上格', '稼穑格', '从革格', '润下格',
               '化气格')
    return any(s in pat_name for s in special)


def _score_pattern_purity(result: dict) -> dict:
    """维度 1：格局清纯度（30分）

    依据《子平真诠》第九章「论用神成败救应」：
    - 成格条件满足 → 基础分
    - 破格条件存在 → 扣分（severity 分级）
    - 救应（相神）存在 → 恢复部分分数

    注意：特殊格局（从格/专旺格）不额外加分，
    《子平真诠》第四十七章将化气格列为杂格，地位不如正格。
    """
    pattern = result.get('pattern', {})
    confidence = pattern.get('confidence', 0)
    break_conds = pattern.get('break_conditions', [])
    max_score = 30

    # 基础分 = confidence × 22（confidence 来自 patterns.py 四层筛查 L0-L3）
    base = int(confidence * 22)

    # 无破格条件 → 满额加分
    if not break_conds:
        base += 8
    else:
        # 破格扣分：high 重，medium 中
        # 仅在此维度扣分，维度 3 不再重复扣
        high = sum(1 for b in break_conds if b.get('severity') == 'high')
        med = sum(1 for b in break_conds if b.get('severity') == 'medium')
        base -= high * 5
        base -= med * 3

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
    """维度 2：用神状态（25分）

    依据《子平真诠》第十二章「论用神格局高低」"有情有力"总纲：
    - 用神明确 → 基础分
    - 用神透干 → 加分（第十六章「论杂气取用」"透干会取其清者用之"）
    - 用神有根（根深）→ 加分（第三十三章「论财」"财喜根深"）
    - 喜神存在 → 加分
    - 旺衰判定有效 → 加分

    不再将 confidence 二次计入（已在维度 1 中计入）。
    忌神存在为中性，不加分（命局必然有忌神）。
    """
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

    score = 13  # 用神明确基础分（最高可达：13+2+2+4+4=25）

    xishen = ys.get('xishen', [])

    # 喜神存在 → 加分
    if xishen:
        score += 2

    # 旺衰判定有效 → 加分
    ws = result.get('strength', {}).get('wangshuai', {})
    if ws.get('verdict') and ws['verdict'] not in ('中和', '数据不足'):
        score += 2

    # ── 用神透干检查 ──
    # 《子平真诠》第十六章："透干会取其清者用之"
    bazi_str = result.get('bazi', '') or result.get('validation', {}).get('bazi', '')
    bazi_parts = bazi_str.split() if bazi_str else []
    gans = [p[0] for p in bazi_parts if len(p) >= 2]
    zhis = [p[1] for p in bazi_parts if len(p) >= 2]

    yongshen_tougan = any(GAN_WUXING.get(g, '') == yongshen_wx for g in gans)
    if yongshen_tougan:
        score += 4  # 透干加分（"有情"维度）

    # ── 用神有根检查 ──
    # 《子平真诠》第三十三章："财喜根深"；第四十三章："官煞露而根深，其贵也大"
    root_score = 0
    rooted_zhi_count = 0
    for zhi in zhis:
        cangs = ZHI_CANGGAN.get(zhi, [])
        has_root_here = False
        for gan_name, level in cangs:
            if GAN_WUXING.get(gan_name, '') == yongshen_wx:
                has_root_here = True
                if level == '本气':
                    root_score = max(root_score, 3)  # 根深
                elif level == '中气':
                    root_score = max(root_score, 2)  # 根中
                elif level == '余气':
                    root_score = max(root_score, 1)  # 根浅
        if has_root_here:
            rooted_zhi_count += 1
    # 多根加成：用神在多地支有根，力量更强
    if rooted_zhi_count >= 2:
        root_score = 4
    score += root_score  # 有力维度

    score = max(0, min(max_score, score))

    detail = f"用神{yongshen_wx}"
    if yongshen_tougan:
        detail += "，透干"
    if root_score >= 4:
        detail += "，多根深固"
    elif root_score >= 3:
        detail += "，根深"
    elif root_score >= 2:
        detail += "，有根"
    elif root_score >= 1:
        detail += "，根浅"
    if xishen:
        detail += f"，喜神{'、'.join(xishen)}"

    return {
        'name': '用神状态',
        'name_en': 'Yongshen Clarity',
        'score': score,
        'max': max_score,
        'detail': detail,
    }


def _score_conflict(result: dict) -> dict:
    """维度 3：冲突交战（15分）

    依据《子平真诠》第十七章「论墓库刑冲之说」：
    - 四库之冲为"冲动之冲"，非"冲克之冲"，不忌
    - 冲忌神反为吉（"冲去忌神反为吉"）
    - 冲用神为凶（破格风险）

    依据《滴天髓》"生方怕动库宜开"：
    - 寅申巳亥（生方）忌冲
    - 辰戌丑未（四库）宜冲

    注意：破格条件扣分已在维度 1 中完成，此处不重复扣分。
    """
    relations = result.get('relations', [])
    max_score = 15

    # 获取忌神五行，用于判断冲的喜忌
    ys = result.get('yongshen', {})
    jishen_wx = set(ys.get('jishen', []))
    yongshen_wx = ys.get('yongshen', '')
    xishen_wx = set(ys.get('xishen', []))
    # 忌神 = 与用神/喜神相克的五行
    if yongshen_wx:
        jishen_wx.add(KE_MAP.get(yongshen_wx, ''))
        for xs in xishen_wx:
            jishen_wx.add(KE_MAP.get(xs, ''))
    jishen_wx.discard('')

    penalty = 0
    bonus = 0
    chong_count = 0
    xing_count = 0

    for r in relations:
        if not isinstance(r, dict):
            continue
        rtype = r.get('type', r.get('description', ''))

        # ── 地支冲 ──
        if '冲' in rtype and '天干' not in rtype:
            elements = r.get('elements', [])
            if len(elements) >= 2:
                z1, z2 = elements[0], elements[1]
                wx1 = ZHI_WUXING.get(z1, '')
                wx2 = ZHI_WUXING.get(z2, '')

                # 四库之冲：冲动之冲，非冲克之冲，不忌
                # 《子平真诠》："四库喜冲，不为不足"
                if z1 in _SI_KU and z2 in _SI_KU:
                    continue

                # 判断冲的是用神还是忌神
                # 《子平真诠》："冲去忌神反为吉"
                is_chong_yongshen = (wx1 == yongshen_wx or wx2 == yongshen_wx)
                is_chong_jishen = (wx1 in jishen_wx or wx2 in jishen_wx)

                if is_chong_yongshen and not is_chong_jishen:
                    chong_count += 1  # 冲用神，扣分
                elif is_chong_jishen and not is_chong_yongshen:
                    bonus += 1  # 冲忌神，加分（解忌）
                elif is_chong_yongshen and is_chong_jishen:
                    pass  # 用神忌神同时被冲，视为中性（冲去忌神之利与冲损用神之害相抵）
                else:
                    chong_count += 1  # 无法判断喜忌，保守扣分

        # ── 地支刑 ──
        elif '刑' in rtype and '六害' not in rtype:
            xing_count += 1

    # 冲的扣分（已区分喜忌）
    if chong_count >= 3:
        penalty += 4
    elif chong_count >= 2:
        penalty += 2
    elif chong_count >= 1:
        penalty += 1

    # 刑的扣分
    if xing_count >= 2:
        penalty += 3
    elif xing_count >= 1:
        penalty += 1

    # bonus 上限为 2：冲忌神有益但冲突本身仍是动荡信号
    score = max(0, min(max_score, max_score - penalty + min(bonus, 2)))

    if penalty == 0 and bonus == 0:
        detail = '无重大冲突，格局清纯'
    else:
        parts = []
        if chong_count:
            parts.append(f'{chong_count}组冲')
        if bonus:
            parts.append(f'{bonus}组冲（解忌神）')
        if xing_count:
            parts.append(f'{xing_count}组刑')
        detail = '、'.join(parts)

    return {
        'name': '冲突交战',
        'name_en': 'Conflict',
        'score': score,
        'max': max_score,
        'detail': detail,
    }


def _score_wuxing_flow(result: dict) -> dict:
    """维度 4：五行流通（15分）

    普通格局：依据《滴天髓》"流通变化，此造化之妙"，五行均衡为吉。
    专旺格/从格：依据《滴天髓》第十二章「从象」和第十六章「顺局」，
    五行偏枯是成格条件，不视为缺陷。改用"顺势流通"标准：
    - 所从/所旺五行占比高 → 好（纯一）
    - 逆势五行（官杀）占比低 → 好

    依据《子平真诠》第四十七章「论杂格」：
    "取五行一方秀气者，本是一派劫财，以五行各得其全体，所以成格"
    """
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
            'score': 7,  # 数据缺失给中性分，非惩罚（与其他维度一致）
            'max': max_score,
            'detail': '五行数据缺失',
        }

    # 判断是否为专旺格/从格
    pattern = result.get('pattern', {})
    pat_name = pattern.get('pattern', '')
    is_special = _is_special_pattern(pat_name)

    if is_special:
        # ── 专旺格/从格：顺势流通标准 ──
        # 所从/所旺五行占比越高越好（纯一）
        dominant_pct = max(values)
        if dominant_pct >= 70:
            score = 15
            detail = f'五行纯一（{dominant_pct:.0f}%），顺势成格'
        elif dominant_pct >= 50:
            score = 13
            detail = f'五行偏重（{dominant_pct:.0f}%），顺势流通'
        elif dominant_pct >= 35:
            score = 10
            detail = f'五行尚可偏重（{dominant_pct:.0f}%），顺势基本成格'
        else:
            score = 7
            detail = f'五行偏重不足（{dominant_pct:.0f}%），顺势力度偏弱'
    else:
        # ── 普通格局：中和标准 ──
        # 《滴天髓》"五气不戾，性情中和"
        avg = raw_total / 5
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

        # 五行齐全加成（+2）
        # 《三命通会》："四柱纯粹，无刑冲破害...更有福神互为之助方为吉命"
        present = [wx for wx, v in zip(('木', '火', '土', '金', '水'), values) if v > 2]
        if len(present) == 5:
            score = min(max_score, score + 2)
            detail += '，五行齐全'

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
    """维度 5：大运配合（15分）

    依据《渊海子平》「论大运」："子平之法，大运看支，岁君看干"
    依据《三命通会》："凡行运，在干兼用地支之神，在支则弃天干之物。
    盖大运重地支"
    依据《子平真诠》第二十七章「论喜忌干支有别」：
    "干主天，动而有为，支主地，静以待用，且干主一而支藏多"

    实现：
    - 大运地支本气五行权重 60%，天干五行权重 40%
    - 吉凶判断基于用神/喜神/忌神体系
    - 无数据时返回中间值 7 分（数据缺失 ≠ 命局质量差）
    """
    max_score = 15

    if not dayun_list:
        return {
            'name': '大运配合',
            'name_en': 'Dayun Fortune',
            'score': 7,
            'max': max_score,
            'detail': '大运数据不可用，按中性处理',
        }

    ys = result.get('yongshen', {})
    yongshen_wx = ys.get('yongshen', '')
    xishen_wx = set(ys.get('xishen', []))
    jishen_wx = set(ys.get('jishen', []))

    if not yongshen_wx or yongshen_wx == '待定':
        return {
            'name': '大运配合',
            'name_en': 'Dayun Fortune',
            'score': 7,
            'max': max_score,
            'detail': '用神待定，无法评估大运配合',
        }

    # 筛选中年大运（10-70 岁）
    mid_dayun = [dy for dy in dayun_list if isinstance(dy, dict)
                 and _age_overlaps_mid_life(dy.get('age_range', ''))]
    if not mid_dayun:
        mid_dayun = dayun_list[:8]

    ji_count = 0
    xiong_count = 0
    total_dy = len(mid_dayun)

    for dy in mid_dayun:
        dy_gan = dy.get('gan', '')
        dy_zhi = dy.get('zhi', '')

        # 天干五行（权重 40%）
        gan_wx = GAN_WUXING.get(dy_gan, '')
        # 地支本气五行（权重 60%）
        # 《渊海子平》："大运看支，岁君看干"
        zhi_wx = ZHI_WUXING.get(dy_zhi, '')

        # 对天干和地支分别判断吉凶
        gan_score = _eval_wx_jixiong(gan_wx, yongshen_wx, xishen_wx, jishen_wx)
        zhi_score = _eval_wx_jixiong(zhi_wx, yongshen_wx, xishen_wx, jishen_wx)

        # 加权：地支 60% + 天干 40%
        combined = zhi_score * 0.6 + gan_score * 0.4

        if combined > 0:
            ji_count += 1
        elif combined < 0:
            xiong_count += 1

    if total_dy > 0:
        if ji_count == 0 and xiong_count == 0:
            # 全部中性运，按中性处理（数据存在但无明显吉凶 ≠ 质量差）
            score = 7
        else:
            ji_ratio = ji_count / total_dy
            score = int(ji_ratio * max_score)
    else:
        score = 7

    score = max(0, min(max_score, score))

    detail_parts = []
    if ji_count:
        detail_parts.append(f'{ji_count}柱吉运')
    if xiong_count:
        detail_parts.append(f'{xiong_count}柱凶运')

    if detail_parts:
        detail = f"大运{'、'.join(detail_parts)}（干支综合判断）"
    else:
        detail = '大运平平，无明显吉凶'

    return {
        'name': '大运配合',
        'name_en': 'Dayun Fortune',
        'score': score,
        'max': max_score,
        'detail': detail,
    }


def _eval_wx_jixiong(wx: str, yongshen_wx: str,
                     xishen_wx: set, jishen_wx: set) -> int:
    """判断某五行对命局的吉凶。返回 +1（吉）、-1（凶）、0（中性）。

    依据《子平真诠》第二十五章「论行运」：
    - 喜运："命中所喜之神，我得而助之者"
    - 忌运："命中所忌，我逆而施之者"
    """
    if not wx:
        return 0
    if wx in jishen_wx:
        return -1
    # 克喜神亦为凶（喜神被克，命局受损）
    for xs in xishen_wx:
        if KE_MAP.get(xs, '') == wx:
            return -1
    if wx in xishen_wx or wx == yongshen_wx:
        return 1
    # 生用神 → 吉；克用神 → 凶
    if yongshen_wx:
        if SHENG_MAP.get(yongshen_wx) == wx:
            return 1
        if KE_MAP.get(yongshen_wx) == wx:
            return -1
    return 0


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
