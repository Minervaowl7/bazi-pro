from bazi_pro import GAN_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.branches import CANGGAN_WEIGHT, SHIER_CHANGSHENG, DELING_SCORE


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
            positions[i]
            if i == 2:
                day_idx = i

    for i, part in enumerate(bazi_parts):
        if len(part) < 1:
            continue
        gan = part[0]
        if gan == day_master:
            continue
        ss = derive_shishen(day_master, gan)
        if ss in ('比肩', '劫财', '正印', '偏印'):
            dist = abs(i - day_idx) if day_idx >= 0 else 2
            score = 2 if dist <= 1 else 1
            total += score
            details.append({
                'position': positions[i] if i < 4 else '',
                'gan': gan, 'shishen': ss, 'distance': dist, 'score': score,
            })

    for part in bazi_parts:
        if len(part) < 2:
            continue
        zhi = part[1]
        for gan, qi_level in get_canggan(zhi):
            if gan == day_master:
                continue
            ss = derive_shishen(day_master, gan)
            if ss in ('比肩', '劫财', '正印', '偏印') and qi_level == '本气':
                total += 1
                details.append({
                    'zhi': zhi, 'canggan_gan': gan, 'shishen': ss,
                    'qi_level': qi_level, 'score': 1,
                })

    if total >= 4:
        level = '得势'
    elif total >= 2:
        level = '偏得势'
    else:
        level = '不得势'

    return {'score': total, 'details': details, 'level': level}


def judge_wangshuai(deling_score: int, dedi_score: float, deshi_score: float) -> dict:
    if deling_score >= 2 and dedi_score >= 3 and deshi_score >= 4:
        verdict = '身旺'
    elif deling_score >= 2 and dedi_score >= 3 and deshi_score < 4:
        verdict = '偏旺'
    elif deling_score >= 2 and dedi_score < 3 and deshi_score >= 4:
        verdict = '偏旺'
    elif deling_score >= 2 and dedi_score < 3 and deshi_score < 4:
        verdict = '中和偏旺'
    elif deling_score <= 0 and dedi_score < 1.5 and deshi_score < 2:
        verdict = '身弱'
    elif 0 <= deling_score <= 1 and dedi_score >= 3 and deshi_score >= 4:
        verdict = '中和偏弱'
    elif 0 <= deling_score <= 1 and dedi_score < 1.5 and deshi_score < 2:
        verdict = '身弱'
    elif deling_score <= -2 and dedi_score < 1.5 and deshi_score == 0:
        verdict = '极弱'
    elif deling_score >= 3 and dedi_score >= 3 and deshi_score >= 6:
        verdict = '极旺'
    else:
        verdict = '中和'

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
