from bazi_pro.core.constants import GAN_WUXING, ZHI_WUXING
from bazi_pro.paipan import DIZHI, TIANGAN


def score_dayun(dayun_list, yongshen_wx, jishen_wx, day_master):
    if not dayun_list:
        return []

    jishen_set = set(jishen_wx) if isinstance(jishen_wx, list) else {jishen_wx}
    results = []
    for step_info in dayun_list:
        score = 50
        gan = step_info.get('gan', '')
        zhi = step_info.get('zhi', '')
        gan_wx = GAN_WUXING.get(gan, '')
        zhi_wx = ZHI_WUXING.get(zhi, '')

        if gan_wx == yongshen_wx:
            score += 20
        if gan_wx in jishen_set:
            score -= 20
        if zhi_wx == yongshen_wx:
            score += 15
        if zhi_wx in jishen_set:
            score -= 15

        score = max(0, min(100, score))
        results.append({
            'step': step_info.get('step', 0),
            'gan_zhi': step_info.get('gan_zhi', gan + zhi),
            'score': score,
            'age_range': step_info.get('age_range', ''),
        })
    return results


def score_liunian(dayun_list, yongshen_wx, jishen_wx, xishen_wx, day_master,
                  birth_year, qiyun_age):
    if not birth_year:
        return []

    jishen_set = set(jishen_wx) if isinstance(jishen_wx, list) else {jishen_wx}
    xishen_set = set(xishen_wx) if isinstance(xishen_wx, list) else {xishen_wx}

    dayun_scored = score_dayun(dayun_list, yongshen_wx, jishen_wx, day_master)
    dayun_score_map = {}
    for ds in dayun_scored:
        dayun_score_map[ds['step']] = ds['score']

    dayun_by_age = {}
    for step_info in (dayun_list or []):
        age_range = step_info.get('age_range', '')
        if '-' in age_range:
            parts = age_range.split('-')
            try:
                start_age = int(parts[0])
                end_age = int(parts[1])
            except (ValueError, IndexError):
                continue
            for a in range(start_age, end_age + 1):
                dayun_by_age[a] = step_info

    results = []
    for age in range(1, 101):
        year = birth_year + age - 1
        gan_idx = (year - 4) % 10
        zhi_idx = (year - 4) % 12
        gan = TIANGAN[gan_idx]
        zhi = DIZHI[zhi_idx]
        gan_zhi = gan + zhi
        gan_wx = GAN_WUXING.get(gan, '')
        zhi_wx = ZHI_WUXING.get(zhi, '')

        liunian_score = 50
        reasons = []

        if gan_wx == yongshen_wx:
            liunian_score += 20
            reasons.append(f'{gan}{gan_wx}用神到位')
        elif gan_wx in xishen_set:
            liunian_score += 10
            reasons.append(f'{gan}{gan_wx}喜神助运')
        elif gan_wx in jishen_set:
            liunian_score -= 20
            reasons.append(f'{gan}{gan_wx}忌神到位')

        if zhi_wx == yongshen_wx:
            liunian_score += 15
            reasons.append(f'{zhi}{zhi_wx}用神到位')
        elif zhi_wx in xishen_set:
            liunian_score += 8
            reasons.append(f'{zhi}{zhi_wx}喜神助运')
        elif zhi_wx in jishen_set:
            liunian_score -= 15
            reasons.append(f'{zhi}{zhi_wx}忌神到位')

        liunian_score = max(0, min(100, liunian_score))

        dayun_step_info = dayun_by_age.get(age)
        dayun_base = 50
        dayun_gan_zhi = ''
        if dayun_step_info:
            step_num = dayun_step_info.get('step', 0)
            dayun_base = dayun_score_map.get(step_num, 50)
            dayun_gan_zhi = dayun_step_info.get('gan_zhi', '')

        combined = round(dayun_base * 0.4 + liunian_score * 0.6)
        combined = max(0, min(100, combined))

        reason = '、'.join(reasons) if reasons else '中性流年'

        results.append({
            'age': age,
            'year': year,
            'gan_zhi': gan_zhi,
            'score': combined,
            'dayun': dayun_gan_zhi,
            'reason': reason,
        })

    return results
