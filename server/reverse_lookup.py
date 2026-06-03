"""四柱反查 — 输入四柱干支，反推 1900-2100 年间所有可能的出生日期"""

import time
from datetime import date, timedelta

from bazi_pro.paipan import DIZHI, TIANGAN, paipan_from_datetime

_MAX_REVERSE_LOOKUP_SECONDS = 10
_MAX_REVERSE_LOOKUP_RESULTS = 20


def reverse_lookup_pillars(bazi_str: str, start_year: int = 1940,
                           end_year: int = 2030) -> list[dict]:
    if not bazi_str:
        return []
    parts = bazi_str.strip().split()
    if len(parts) != 4:
        return []

    target_year = parts[0]

    results = []

    year_gan_idx = TIANGAN.index(target_year[0]) if target_year[0] in TIANGAN else -1
    year_zhi_idx = DIZHI.index(target_year[1]) if target_year[1] in DIZHI else -1
    if year_gan_idx < 0 or year_zhi_idx < 0:
        return []

    candidate_years = []
    for y in range(start_year, end_year + 1):
        g = (y - 4) % 10
        z = (y - 4) % 12
        if g == year_gan_idx and z == year_zhi_idx:
            candidate_years.append(y)

    start_time = time.time()
    max_year_month_checks = 5000
    checks = 0

    for year in candidate_years:
        for month in range(1, 13):
            for day in range(1, 32):
                if checks >= max_year_month_checks:
                    return results
                if time.time() - start_time > _MAX_REVERSE_LOOKUP_SECONDS:
                    return results

                try:
                    d = date(year, month, day)
                except ValueError:
                    continue
                checks += 1

                for gender in ["男", "女"]:
                    try:
                        solar_str = f"{year}-{month:02d}-{day:02d} 00:00"
                        result = paipan_from_datetime(solar_str, gender)
                        if result and result.get("八字", "") == bazi_str:
                            results.append({
                                "date": d.isoformat(),
                                "gender": gender,
                                "bazi": bazi_str,
                            })
                    except Exception:
                        continue

                if len(results) >= _MAX_REVERSE_LOOKUP_RESULTS:
                    return results

    return results


def reverse_lookup_day_pillar(day_pillar: str, start_year: int = 2020,
                              end_year: int = 2030) -> list[str]:
    """根据日柱反查日期（更快速的方法）。

    日柱60天一循环，直接计算。
    """
    if len(day_pillar) != 2:
        return []

    gan = day_pillar[0]
    zhi = day_pillar[1]
    if gan not in TIANGAN or zhi not in DIZHI:
        return []

    gan_idx = TIANGAN.index(gan)
    zhi_idx = DIZHI.index(zhi)

    if (gan_idx % 2) != (zhi_idx % 2):
        return []

    from bazi_pro.paipan import _julian_day_number

    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)

    # 使用 JDN 计算日柱，与 paipan.py 保持一致
    # 日柱天干索引 = (JDN + 9) % 10
    # 日柱地支索引 = (JDN + 1) % 12
    start_jdn = _julian_day_number(start.year, start.month, start.day)
    start_gan_idx = (start_jdn + 9) % 10
    start_zhi_idx = (start_jdn + 1) % 12

    # 找到从 start 开始第一个满足目标天干地支的偏移天数
    # 需要: (start_gan_idx + days) % 10 == gan_idx
    #       (start_zhi_idx + days) % 12 == zhi_idx
    # 即: days % 10 == (gan_idx - start_gan_idx) % 10
    #     days % 12 == (zhi_idx - start_zhi_idx) % 12
    gan_diff = (gan_idx - start_gan_idx) % 10
    zhi_diff = (zhi_idx - start_zhi_idx) % 12

    # 用中国剩余定理求解最小正天数
    # days ≡ gan_diff (mod 10)
    # days ≡ zhi_diff (mod 12)
    # 因为 10 和 12 的 GCD=2，需要 gan_diff ≡ zhi_diff (mod 2)
    # 前面已经检查了 (gan_idx % 2) == (zhi_idx % 2)
    # 所以 (start_gan_idx + gan_diff) % 2 == gan_idx % 2
    #      (start_zhi_idx + zhi_diff) % 2 == zhi_idx % 2
    # gan_idx % 2 == zhi_idx % 2 (已验证)
    # start_gan_idx % 2 == start_zhi_idx % 2 (因为日柱天干地支阴阳一致)
    # 所以 gan_diff % 2 == zhi_diff % 2，有解

    first_days = None
    for days in range(60):
        if days % 10 == gan_diff and days % 12 == zhi_diff:
            first_days = days
            break

    if first_days is None:
        return []

    results = []
    current = start + timedelta(days=first_days)
    while current <= end:
        results.append(current.isoformat())
        current += timedelta(days=60)
        if len(results) >= 100:
            break

    return results
