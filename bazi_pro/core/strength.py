"""旺衰判断核心模块 — 基于得令/得地/得势三要素判定日主旺衰

核心概念：
- 得令（deling）：日主在月令（月支）的十二长生状态，衡量月令对日主的生扶
- 得地（dedi）：日主五行在地支藏干中的根气，衡量地支对日主的支撑
- 得势（deshi）：四柱中比劫/印星的数量和位置，衡量天干藏干对日主的帮扶

判定层级（AGENTS.md 规则8：极旺/极弱必须在身旺/身弱之前判断）：
1. 极旺：得令+得地+得势均极强
2. 极弱：不得令+不得地+不得势
3. 身旺：得令+得地+得势
4. 身弱：不得令+不得地+不得势
5. 中和偏旺/中和偏弱：介于旺弱之间的过渡状态

古籍依据：
- 《滴天髓》"旺衰论"："旺则宜泄宜伤，衰则喜帮喜助"
- 《子平真诠》"论五行生克"：得令/得地/得势三要素
- 《子平真诠》"近者力大，远者力微"：天干位置远近影响帮身力度
"""

from bazi_pro.core.branches import CANGGAN_WEIGHT, DELING_SCORE, SHIER_CHANGSHENG
from bazi_pro.core.constants import GAN_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.stems import KE_MAP, SHENG_MAP


def calc_deling(day_master: str, month_zhi: str) -> tuple[str, int]:
    """计算得令（日主在月令的十二长生状态及评分）

    得令是旺衰判断的首要因素，《子平真诠》以月令为"提纲"，
    日主在月令的长生状态直接决定得令与否。

    参数：
        day_master: 日主天干（如"甲"）
        month_zhi: 月支地支（如"寅"）

    返回：
        (status, score) 元组：
        - status: 十二长生状态名（如"长生"、"帝旺"、"绝"等）
        - score: 得令评分，正值=得令，负值=失令
          （帝旺+3, 临官+3, 长生+2, 冠带+1, 养+1,
            沐浴0, 衰0, 胎0, 病-1, 墓-1, 死-2, 绝-3）
    """
    changsheng_table = SHIER_CHANGSHENG.get(day_master, {})
    status = changsheng_table.get(month_zhi, '')
    score = DELING_SCORE.get(status, 0)

    # 阴干长生力量修正 —《滴天髓·论阴阳生死》
    # "阳长生有力，而阴长生不甚有力，然亦不弱"
    # "若是逢库，则阳为有根，而阴为无用"
    # 阴干：仅墓加深（阴逢库为无用），长生保持不变（"然亦不弱"）
    if day_master in '乙丁己辛癸':
        if status == '墓':
            score = -2  # 阴逢库为无用，比阳干更不利

    return status, score


def calc_dedi(day_master: str, bazi_parts: list[str]) -> dict:
    """计算得地（日主五行在地支藏干中的根气）

    得地衡量地支藏干中与日主同五行的干的数量和权重。
    本气根权重最高(1.0)，中气次之(0.6)，余气最低(0.3)。

    参数：
        day_master: 日主天干
        bazi_parts: 四柱干支列表，格式 ["甲子","丙寅","戊辰","庚午"]

    返回：
        dict {
            'score': 得地总分（浮点数），
            'details': 各藏干明细列表，
            'level': 得地等级（'得地'≥3 / '偏得地'≥1.5 / '不得地'<1.5），
        }
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {'score': 0.0, 'details': [], 'level': '不得地'}

    total = 0.0
    details = []
    for part in bazi_parts:
        if len(part) < 2:
            continue
        zhi = part[1]
        for gan, qi_level in get_canggan(zhi):
            gan_wx = GAN_WUXING.get(gan, '')
            if gan_wx == dm_wx:
                # 藏干权重：本气1.0、中气0.6、余气0.3（来自 CANGGAN_WEIGHT 常量表）
                weight = CANGGAN_WEIGHT.get(qi_level, 0)
                total += weight
                details.append({
                    'zhi': zhi, 'canggan_gan': gan, 'qi_level': qi_level,
                    'weight': weight, 'wuxing': gan_wx,
                })

    # 得地等级阈值：≥3为得地，≥1.5为偏得地，<1.5为不得地
    if total >= 3:
        level = '得地'
    elif total >= 1.5:
        level = '偏得地'
    else:
        level = '不得地'

    return {'score': total, 'details': details, 'level': level}


def calc_deshi(day_master: str, bazi_parts: list[str]) -> dict:
    """计算得势（四柱中比劫/印星对日主的帮扶力度）

    得势衡量天干和藏干中比肩/劫财/正印/偏印的数量和位置。
    天干按位置远近评分：月干/时干紧贴日干(2分)，年干远隔(1分)。
    藏干按气之深浅评分：本气(1分)、中气(0.5分)、余气(0.3分)。

    参数：
        day_master: 日主天干
        bazi_parts: 四柱干支列表

    返回：
        dict {
            'score': 得势总分（浮点数），
            'details': 各帮身干明细列表，
            'level': 得势等级（'得势'≥4 / '偏得势'≥2 / '不得势'<2），
        }
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {'score': 0.0, 'details': [], 'level': '不得势'}

    total = 0.0
    details = []
    positions = ['年', '月', '日', '时']
    day_idx = -1
    for i, part in enumerate(bazi_parts):
        if len(part) >= 2 and i < 4:
            if i == 2:
                day_idx = i  # 日柱索引为2（第三柱）

    # ── 天干得势 ──
    for i, part in enumerate(bazi_parts):
        if len(part) < 1:
            continue
        gan = part[0]
        if i == day_idx:
            continue  # 跳过日干自身
        ss = derive_shishen(day_master, gan)
        if ss in ('比肩', '劫财', '正印', '偏印'):
            # 《子平真诠》"近者力大，远者力微"
            # 月干/时干紧贴日干，帮身力大(2分)；年干远隔，力微(1分)
            if i == 1 or i == 3:  # 月干或时干
                score = 2
                distance = 1  # 紧贴日干
            else:  # 年干
                score = 1
                distance = 2  # 远隔日干
            total += score
            details.append({
                'position': positions[i] if i < 4 else '',
                'gan': gan, 'shishen': ss, 'distance': distance, 'score': score,
            })

    # ── 藏干得势 ──
    for part in bazi_parts:
        if len(part) < 2:
            continue
        zhi = part[1]
        for gan, qi_level in get_canggan(zhi):
            # 不跳过比肩藏干：比肩和劫财都是帮身之力，不应区别对待
            # 旧代码 `if gan == day_master: continue` 导致比肩藏干被跳过而劫财保留
            ss = derive_shishen(day_master, gan)
            if ss in ('比肩', '劫财', '正印', '偏印'):
                # 本气/中气/余气都算得势，权重递减
                # 《子平真诠》"得势者，比劫多也" — 中气/余气也是帮身之力
                if qi_level == '本气':
                    score = 1
                elif qi_level == '中气':
                    score = 0.5
                else:  # 余气
                    score = 0.3
                total += score
                details.append({
                    'zhi': zhi, 'canggan_gan': gan, 'shishen': ss,
                    'qi_level': qi_level, 'score': score,
                })

    # 得势等级阈值：≥4为得势，≥2为偏得势，<2为不得势
    if total >= 4:
        level = '得势'
    elif total >= 2:
        level = '偏得势'
    else:
        level = '不得势'

    return {'score': total, 'details': details, 'level': level}


def judge_wangshuai(deling_score: int, dedi_score: float, deshi_score: float,
                    day_master: str = '', element_forces: dict = None) -> dict:
    """综合判定日主旺衰

    基于《滴天髓》"旺衰论"和《子平真诠》三要素（得令/得地/得势），
    通过多条件分支判定日主的旺衰等级。

    判定顺序（AGENTS.md 规则8：极旺/极弱必须在身旺/身弱之前判断）：
    1. 极旺：得令≥3 + 得地≥3 + 得势≥6
    2. 极弱：得令≤-2 + 不得地(<1.5) + 不得势(≤1)，或得令≤-1 + 极不得地(<1.0) + 极不得势(≤0.5)
    3. 身旺：得令≥2 + 得地≥3 + 得势≥4
    4. 偏旺：得令≥2 + 得地≥3但得势不足，或得令≥2 + 得势≥4但得地不足
    5. 中和偏旺：得令≥2但地/势均不足，或得令中等+地根+得势
    6. 身弱：不得令(≤0) + 不得地(<1.5) + 不得势(<2)
    7. 中和偏弱：得令中等但地/势偏弱
    8. 中和：以上均不满足

    参数：
        deling_score: 得令评分（整数，-2~+3）
        dedi_score: 得地评分（浮点数，0~∞）
        deshi_score: 得势评分（浮点数，0~∞）
        day_master: 日主天干（用于五行力量补充判断）
        element_forces: 五行力量分布（可选，用于印比占比极旺修正）

    返回：
        dict {
            'verdict': 旺衰判定结果（极旺/身旺/偏旺/中和偏旺/中和/中和偏弱/身弱/极弱），
            'deling_score': 得令评分，
            'dedi_score': 得地评分，
            'deshi_score': 得势评分，
            'is_weak': 是否偏弱（verdict含"弱"），
            'is_strong': 是否偏旺（verdict含"旺"或"强"），
            'is_extreme_weak': 是否极弱，
            'is_extreme_strong': 是否极旺，
        }
    """
    # 《滴天髓》"衰旺"章："旺则宜泄宜伤，衰则喜帮喜助"
    # 极旺/极弱必须优先判断（AGENTS.md 规则8：极旺/极弱必须在身旺/身弱之前）

    # ── 极旺：三要素均极强 ──
    if deling_score >= 3 and dedi_score >= 3 and deshi_score >= 6:
        verdict = '极旺'
    # ── 极弱：日主孤立无气 ──
    # 《滴天髓》"日主孤立无气" — 极弱的核心是"孤立无气"
    # 条件1：得令极差（绝/死）+ 不得地 + 不得势（帮身极弱）
    # 条件2：得令差（病）+ 极不得地 + 极不得势（完全无助）
    elif deling_score <= -2 and dedi_score < 1.5 and deshi_score < 2:
        verdict = '极弱'
    elif deling_score <= -1 and dedi_score < 1.0 and deshi_score <= 0.5:
        verdict = '极弱'
    # ── 身旺：得令+得地+得势 ──
    elif deling_score >= 2 and dedi_score >= 3 and deshi_score >= 4:
        verdict = '身旺'
    # ── 偏旺：得令+得地但得势不足，或得令+得势但得地不足 ──
    elif deling_score >= 2 and dedi_score >= 3 and deshi_score < 4:
        verdict = '偏旺'
    elif deling_score >= 2 and dedi_score < 3 and deshi_score >= 4:
        verdict = '偏旺'
    # ── 中和偏旺：得令但地/势均不足 ──
    elif deling_score >= 2 and dedi_score < 3 and deshi_score < 4:
        verdict = '中和偏旺'
    # ── 身弱：不得令+不得地+不得势 ──
    elif deling_score <= 0 and dedi_score < 1.5 and deshi_score < 2:
        verdict = '身弱'
    elif deling_score <= -1 and dedi_score < 1.5 and deshi_score < 4:
        # 补充覆盖：得令极差（绝/死/病）且不得地，即使得势略高也偏弱
        verdict = '身弱'
    # ── 中和偏旺/偏弱过渡区 ──
    elif 0 <= deling_score <= 1 and dedi_score >= 3 and deshi_score >= 4:
        verdict = '中和偏旺'
    elif 0 <= deling_score <= 1 and dedi_score < 1.5 and deshi_score < 2:
        verdict = '身弱'
    elif -1 <= deling_score <= 1 and 1.5 <= dedi_score < 3 and deshi_score >= 10:
        verdict = '中和偏旺'
    elif -1 <= deling_score <= 1 and 1.5 <= dedi_score < 3 and deshi_score < 1:
        verdict = '中和偏弱'
    # 补充覆盖：得令中等但地支有根且得势 → 偏旺
    elif deling_score >= 1 and dedi_score >= 1.5 and deshi_score >= 2:
        verdict = '中和偏旺'
    # 补充覆盖：得令中等但地支无根且不得势 → 偏弱
    elif deling_score <= 0 and dedi_score < 3 and deshi_score < 4:
        verdict = '中和偏弱'
    else:
        verdict = '中和'

    # ── 五行力量补充修正 ──
    # 当印星+比劫占比≥75%时，若官杀力量也强（≥15%），则不强制极旺
    # 《滴天髓》"旺极者，宜泄不宜克" — 但官杀有力则身不能极旺
    # 《渊海子平》官印双全格，印比虽高但官杀制身，应为中和或偏旺
    if element_forces and day_master:
        dm_wx = GAN_WUXING.get(day_master, '')
        if dm_wx:
            yin_wx = SHENG_MAP.get(dm_wx, '')  # 印星五行
            ke_wx = KE_MAP.get(dm_wx, '')       # 官杀五行（克我者）
            percent = element_forces.get('percent', {})
            bi_pct = percent.get(dm_wx, 0)      # 比劫占比
            yin_pct = percent.get(yin_wx, 0) if yin_wx else 0  # 印星占比
            yin_bi_ratio = bi_pct + yin_pct      # 印比总占比
            guansha_pct = percent.get(ke_wx, 0) if ke_wx else 0  # 官杀占比
            if yin_bi_ratio >= 75 and guansha_pct < 15:
                verdict = '极旺'

    return {
        'verdict': verdict,
        'deling_score': deling_score,
        'dedi_score': dedi_score,
        'deshi_score': deshi_score,
        'is_weak': '弱' in verdict,
        'is_strong': '旺' in verdict or '强' in verdict,
        'is_extreme_weak': verdict == '极弱',
        'is_extreme_strong': verdict == '极旺',
    }
