from bazi_pro.core.constants import GAN_WUXING, ZHI_WUXING, derive_shishen

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
SHENGXIAO = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪']

# 节气分界表：(月, 日, 月支索引)。使用固定日期近似，实际节气每年浮动1-2天。
# 边界日期（节气当天前后1天）的月支判断可能有误差，建议用户手动确认。
JIEQI_BOUNDARIES = [
    (1, 6, 1),   # 小寒  → 丑月
    (2, 4, 2),   # 立春  → 寅月
    (3, 6, 3),   # 惊蛰  → 卯月
    (4, 5, 4),   # 清明  → 辰月
    (5, 6, 5),   # 立夏  → 巳月
    (6, 6, 6),   # 芒种  → 午月
    (7, 7, 7),   # 小暑  → 未月
    (8, 8, 8),   # 立秋  → 申月
    (9, 8, 9),   # 白露  → 酉月
    (10, 8, 10), # 寒露  → 戌月
    (11, 7, 11), # 立冬  → 亥月
    (12, 7, 0),  # 大雪  → 子月
]


def _parse_datetime(solar_datetime: str):
    if not solar_datetime:
        return None
    parts = solar_datetime.strip().split()
    date_part = parts[0]
    time_part = parts[1] if len(parts) > 1 else None

    date_fields = date_part.split('-')
    if len(date_fields) != 3:
        return None
    try:
        year = int(date_fields[0])
        month = int(date_fields[1])
        day = int(date_fields[2])
    except ValueError:
        return None

    hour = None
    if time_part:
        time_fields = time_part.split(':')
        try:
            hour = int(time_fields[0])
        except (ValueError, IndexError):
            return None

    return year, month, day, hour


def _get_month_zhi_index(month: int, day: int) -> int:
    for i in range(len(JIEQI_BOUNDARIES) - 1, -1, -1):
        jq_month, jq_day, zhi_idx = JIEQI_BOUNDARIES[i]
        if month > jq_month or (month == jq_month and day >= jq_day):
            return zhi_idx
    return 0


def _get_year_for_pillar(year: int, month: int, day: int) -> int:
    if month < 2 or (month == 2 and day < 4):
        return year - 1
    return year


def _julian_day_number(year: int, month: int, day: int) -> int:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _get_hour_zhi_index(hour: int) -> int:
    if hour == 23:
        return 0
    return (hour + 1) // 2


def _calc_dayun(year_gan_idx, month_gan_idx, month_zhi_idx, gender, day_master, year, month, day):
    is_yang_year = year_gan_idx % 2 == 0
    is_male = gender == '男'
    forward = (is_yang_year and is_male) or (not is_yang_year and not is_male)

    birth_jdn = _julian_day_number(year, month, day)
    candidates = []
    for y in range(year - 1, year + 2):
        for jq_month, jq_day, _ in JIEQI_BOUNDARIES:
            jq_jdn = _julian_day_number(y, jq_month, jq_day)
            if forward and jq_jdn > birth_jdn:
                candidates.append(jq_jdn - birth_jdn)
            elif not forward and jq_jdn < birth_jdn:
                candidates.append(birth_jdn - jq_jdn)

    if candidates:
        qiyun_age = round(min(candidates) / 3)
    else:
        qiyun_age = 5

    if qiyun_age < 1:
        qiyun_age = 1

    num_steps = 8
    dayun_list = []
    for step in range(1, num_steps + 1):
        if forward:
            gan_idx = (month_gan_idx + step) % 10
            zhi_idx = (month_zhi_idx + step) % 12
        else:
            gan_idx = (month_gan_idx - step) % 10
            zhi_idx = (month_zhi_idx - step) % 12

        gan = TIANGAN[gan_idx]
        zhi = DIZHI[zhi_idx]
        start_age = qiyun_age + (step - 1) * 10
        end_age = start_age + 9

        dayun_list.append({
            "step": step,
            "gan": gan,
            "zhi": zhi,
            "gan_zhi": gan + zhi,
            "age_range": f"{start_age}-{end_age}",
            "start_age": start_age,
            "shishen_gan": derive_shishen(day_master, gan),
        })

    return dayun_list, qiyun_age


def paipan_from_datetime(solar_datetime: str, gender: str, lunar: str = "") -> dict:
    parsed = _parse_datetime(solar_datetime)
    if parsed is None:
        return {"status": "error", "message": "日期格式错误"}

    year, month, day, hour = parsed

    pillar_year = _get_year_for_pillar(year, month, day)

    year_gan_idx = (pillar_year - 4) % 10
    year_zhi_idx = (pillar_year - 4) % 12
    year_gan = TIANGAN[year_gan_idx]
    year_zhi = DIZHI[year_zhi_idx]

    month_zhi_idx = _get_month_zhi_index(month, day)
    month_zhi = DIZHI[month_zhi_idx]
    start_gan_for_yin = (year_gan_idx % 5 * 2 + 2) % 10
    month_offset = (month_zhi_idx - 2 + 12) % 12
    month_gan_idx = (start_gan_for_yin + month_offset) % 10
    month_gan = TIANGAN[month_gan_idx]

    jdn = _julian_day_number(year, month, day)
    if hour is not None and hour >= 23:
        jdn += 1

    day_gan_idx = (jdn + 9) % 10
    day_zhi_idx = (jdn + 1) % 12
    day_gan = TIANGAN[day_gan_idx]
    day_zhi = DIZHI[day_zhi_idx]

    if hour is not None:
        hour_zhi_idx = _get_hour_zhi_index(hour)
        hour_zhi = DIZHI[hour_zhi_idx]
        hour_start_gan = (day_gan_idx % 5) * 2
        hour_gan_idx = (hour_start_gan + hour_zhi_idx) % 10
        hour_gan = TIANGAN[hour_gan_idx]
        has_hour = True
    else:
        hour_gan = ""
        hour_zhi = ""
        has_hour = False

    bazi_str = f"{year_gan}{year_zhi} {month_gan}{month_zhi} {day_gan}{day_zhi}"
    if has_hour:
        bazi_str += f" {hour_gan}{hour_zhi}"

    shengxiao_idx = (pillar_year - 4) % 12
    shengxiao = SHENGXIAO[shengxiao_idx]

    pillars = [
        {
            "position": "年柱",
            "gan": year_gan,
            "zhi": year_zhi,
            "wuxing_gan": GAN_WUXING.get(year_gan, ""),
            "wuxing_zhi": ZHI_WUXING.get(year_zhi, ""),
        },
        {
            "position": "月柱",
            "gan": month_gan,
            "zhi": month_zhi,
            "wuxing_gan": GAN_WUXING.get(month_gan, ""),
            "wuxing_zhi": ZHI_WUXING.get(month_zhi, ""),
        },
        {
            "position": "日柱",
            "gan": day_gan,
            "zhi": day_zhi,
            "wuxing_gan": GAN_WUXING.get(day_gan, ""),
            "wuxing_zhi": ZHI_WUXING.get(day_zhi, ""),
        },
    ]

    if has_hour:
        pillars.append({
            "position": "时柱",
            "gan": hour_gan,
            "zhi": hour_zhi,
            "wuxing_gan": GAN_WUXING.get(hour_gan, ""),
            "wuxing_zhi": ZHI_WUXING.get(hour_zhi, ""),
        })
    else:
        pillars.append({
            "position": "时柱",
            "gan": "",
            "zhi": "",
            "wuxing_gan": "",
            "wuxing_zhi": "",
        })

    dayun_list, qiyun_age = _calc_dayun(
        year_gan_idx, month_gan_idx, month_zhi_idx, gender, day_gan, year, month, day
    )

    return {
        "status": "completed",
        "八字": bazi_str,
        "日主": day_gan,
        "性别": gender,
        "阳历": solar_datetime,
        "生肖": shengxiao,
        "pillars": pillars,
        "dayun": dayun_list,
        "qiyun_age": qiyun_age,
    }
