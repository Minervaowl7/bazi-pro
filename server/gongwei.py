"""宫位计算 — 胎元、命宫、身宫"""

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

_YEAR_GAN_MINGGONG_BASE = {
    "甲": 0, "己": 0,
    "乙": 2, "庚": 2,
    "丙": 4, "辛": 4,
    "丁": 6, "壬": 6,
    "戊": 8, "癸": 8,
}


def _zhi_to_gan(year_gan: str, zhi: str) -> str:
    """根据年干和地支推算天干（五虎遁/五鼠遁规则）"""
    base = _YEAR_GAN_MINGGONG_BASE.get(year_gan, 0)
    zhi_idx = DIZHI.index(zhi) if zhi in DIZHI else -1
    if zhi_idx < 0:
        return ""
    gan_idx = (base + zhi_idx) % 10
    return TIANGAN[gan_idx]


def calc_taiyuan(month_gan: str, month_zhi: str) -> str:
    """胎元：月干进一位 + 月支进三位"""
    gan_idx = TIANGAN.index(month_gan) if month_gan in TIANGAN else -1
    zhi_idx = DIZHI.index(month_zhi) if month_zhi in DIZHI else -1
    if gan_idx < 0 or zhi_idx < 0:
        return ""
    new_gan = TIANGAN[(gan_idx + 1) % 10]
    new_zhi = DIZHI[(zhi_idx + 3) % 12]
    return new_gan + new_zhi


def calc_minggong(month_zhi: str, hour_zhi: str) -> str:
    """命宫：从卯起正月逆数到生月，再从该支起子时顺数到生时"""
    month_idx = DIZHI.index(month_zhi) if month_zhi in DIZHI else -1
    hour_idx = DIZHI.index(hour_zhi) if hour_zhi in DIZHI else -1
    if month_idx < 0 or hour_idx < 0:
        return ""
    # 寅月=1, 卯月=2, ... 从卯(idx=3)起正月逆数
    # 月份序号: 寅=1,卯=2,辰=3,...丑=12
    month_num = (month_idx - 2) % 12 + 1  # 寅=1
    # 从卯逆数month_num步
    base_zhi_idx = (3 - (month_num - 1)) % 12  # 卯=3
    # 从base_zhi顺数到生时
    result_zhi_idx = (base_zhi_idx + hour_idx) % 12
    return DIZHI[result_zhi_idx]


def calc_shengong(month_zhi: str, hour_zhi: str) -> str:
    """身宫：从卯起正月顺数到生月，再从该支起子时顺数到生时"""
    month_idx = DIZHI.index(month_zhi) if month_zhi in DIZHI else -1
    hour_idx = DIZHI.index(hour_zhi) if hour_zhi in DIZHI else -1
    if month_idx < 0 or hour_idx < 0:
        return ""
    month_num = (month_idx - 2) % 12 + 1
    # 从卯顺数month_num步
    base_zhi_idx = (3 + (month_num - 1)) % 12
    # 从base_zhi顺数到生时
    result_zhi_idx = (base_zhi_idx + hour_idx) % 12
    return DIZHI[result_zhi_idx]


def calc_gongwei(bazi_parts: list[str]) -> dict:
    """计算全部宫位信息"""
    if len(bazi_parts) < 4:
        return {}

    year_gan = bazi_parts[0][0] if len(bazi_parts[0]) >= 2 else ""
    month_gan = bazi_parts[1][0] if len(bazi_parts[1]) >= 2 else ""
    month_zhi = bazi_parts[1][1] if len(bazi_parts[1]) >= 2 else ""
    hour_zhi = bazi_parts[3][1] if len(bazi_parts[3]) >= 2 else ""

    result = {}
    taiyuan = calc_taiyuan(month_gan, month_zhi)
    if taiyuan:
        result["胎元"] = taiyuan

    minggong_zhi = calc_minggong(month_zhi, hour_zhi)
    if minggong_zhi:
        minggong_gan = _zhi_to_gan(year_gan, minggong_zhi) if year_gan else ""
        result["命宫"] = (minggong_gan + minggong_zhi) if minggong_gan else minggong_zhi

    shengong_zhi = calc_shengong(month_zhi, hour_zhi)
    if shengong_zhi:
        shengong_gan = _zhi_to_gan(year_gan, shengong_zhi) if year_gan else ""
        result["身宫"] = (shengong_gan + shengong_zhi) if shengong_gan else shengong_zhi

    return result
