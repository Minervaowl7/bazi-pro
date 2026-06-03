from bazi_pro.core.branches import CANGGAN_WEIGHT, DELING_SCORE, SHIER_CHANGSHENG
from bazi_pro.core.constants import GAN_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.stems import SHENG_MAP


def calc_deling(day_master: str, month_zhi: str) -> tuple[str, int]:
    changsheng_table = SHIER_CHANGSHENG.get(day_master, {})
    status = changsheng_table.get(month_zhi, '')
    score = DELING_SCORE.get(status, 0)
    return status, score


def calc_dedi(day_master: str, bazi_parts: list[str]) -> dict:
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
                weight = CANGGAN_WEIGHT.get(qi_level, 0)
                total += weight
                details.append({
                    'zhi': zhi, 'canggan_gan': gan, 'qi_level': qi_level,
                    'weight': weight, 'wuxing': gan_wx,
                })

    if total >= 3:
        level = '得地'
    elif total >= 1.5:
        level = '偏得地'
    else:
        level = '不得地'

    return {'score': total, 'details': details, 'level': level}


def calc_deshi(day_master: str, bazi_parts: list[str]) -> dict:
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
                day_idx = i

    for i, part in enumerate(bazi_parts):
        if len(part) < 1:
            continue
        gan = part[0]
        if i == day_idx:
            continue
        ss = derive_shishen(day_master, gan)
        if ss in ('比肩', '劫财', '正印', '偏印'):
            # 《子平真诠》"近者力大，远者力微"
            # 月干/时干紧贴日干，帮身力大(2分)；年干远隔，力微(1分)
            if i == 1 or i == 3:  # 月干或时干
                score = 2
            else:  # 年干
                score = 1
            total += score
            details.append({
                'position': positions[i] if i < 4 else '',
                'gan': gan, 'shishen': ss, 'score': score,
            })

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

    if total >= 4:
        level = '得势'
    elif total >= 2:
        level = '偏得势'
    else:
        level = '不得势'

    return {'score': total, 'details': details, 'level': level}


def judge_wangshuai(deling_score: int, dedi_score: float, deshi_score: float, day_master: str = '', element_forces: dict = None) -> dict:
    # 《滴天髓》"衰旺"章："旺则宜泄宜伤，衰则喜帮喜助"
    # 极旺/极弱必须优先判断（AGENTS.md 规则8：极旺/极弱必须在身旺/身弱之前）
    if deling_score >= 3 and dedi_score >= 3 and deshi_score >= 6:
        verdict = '极旺'
    # 《滴天髓》"日主孤立无气" — 极弱条件：
    # 1. 得令极差（绝/死）+ 不得地 + 不得势
    # 2. 得令差（病）+ 不得地 + 极不得势（完全无助）
    elif deling_score <= -2 and dedi_score < 1.5 and deshi_score <= 1:
        verdict = '极弱'
    elif deling_score <= -1 and dedi_score < 1.0 and deshi_score <= 0.5:
        verdict = '极弱'
    # 身旺：得令+得地+得势
    elif deling_score >= 2 and dedi_score >= 3 and deshi_score >= 4:
        verdict = '身旺'
    elif deling_score >= 2 and dedi_score >= 3 and deshi_score < 4:
        verdict = '偏旺'
    elif deling_score >= 2 and dedi_score < 3 and deshi_score >= 4:
        verdict = '偏旺'
    elif deling_score >= 2 and dedi_score < 3 and deshi_score < 4:
        verdict = '中和偏旺'
    # 身弱：不得令+不得地+不得势
    elif deling_score <= 0 and dedi_score < 1.5 and deshi_score < 2:
        verdict = '身弱'
    elif deling_score <= -1 and dedi_score < 1.5:
        # 补充覆盖：得令极差（绝/死/病）且不得地，即使得势略高也偏弱
        verdict = '身弱'
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

    if element_forces and day_master:
        dm_wx = GAN_WUXING.get(day_master, '')
        if dm_wx:
            yin_wx = SHENG_MAP.get(dm_wx, '')
            percent = element_forces.get('percent', {})
            bi_pct = percent.get(dm_wx, 0)
            yin_pct = percent.get(yin_wx, 0) if yin_wx else 0
            yin_bi_ratio = bi_pct + yin_pct
            if yin_bi_ratio >= 75:
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
