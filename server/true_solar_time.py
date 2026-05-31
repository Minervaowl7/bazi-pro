"""真太阳时校正 — 基于 Jean Meeus 天文算法

通过经度差 + 时差方程(Equation of Time)计算真太阳时与北京时间的偏差分钟数。
"""

import math
from datetime import datetime, timedelta

BEIJING_LONGITUDE = 116.4


def equation_of_time(day_of_year: int) -> float:
    """计算时差方程(EoT)，返回分钟数。
    基于 Jean Meeus《Astronomical Algorithms》简化公式。
    """
    B = 2 * math.pi * (day_of_year - 81) / 365.0
    eot = (9.87 * math.sin(2 * B)
           - 7.53 * math.cos(B)
           - 1.5 * math.sin(B))
    return eot


def true_solar_time_offset(longitude: float, dt: datetime) -> float:
    """计算真太阳时相对于北京时间(东八区)的偏差分钟数。

    正值表示真太阳时比北京时间快，负值表示慢。
    """
    day_of_year = dt.timetuple().tm_yday
    eot = equation_of_time(day_of_year)
    longitude_correction = (longitude - BEIJING_LONGITUDE) * 4.0
    return longitude_correction + eot


def correct_to_true_solar_time(dt: datetime, longitude: float) -> datetime:
    """将北京时间转换为真太阳时。"""
    offset_minutes = true_solar_time_offset(longitude, dt)
    return dt + timedelta(minutes=offset_minutes)


CHINA_CITIES: dict[str, tuple[float, float]] = {
    "北京": (116.40, 39.90),
    "上海": (121.47, 31.23),
    "广州": (113.26, 23.13),
    "深圳": (114.06, 22.55),
    "成都": (104.07, 30.67),
    "重庆": (106.55, 29.56),
    "武汉": (114.30, 30.60),
    "杭州": (120.15, 30.28),
    "南京": (118.78, 32.06),
    "天津": (117.20, 39.13),
    "西安": (108.94, 34.26),
    "长沙": (112.97, 28.23),
    "沈阳": (123.43, 41.80),
    "哈尔滨": (126.63, 45.75),
    "大连": (121.62, 38.91),
    "济南": (117.00, 36.65),
    "青岛": (120.38, 36.07),
    "郑州": (113.65, 34.76),
    "昆明": (102.73, 25.04),
    "兰州": (103.83, 36.06),
    "太原": (112.55, 37.87),
    "合肥": (117.28, 31.86),
    "福州": (119.30, 26.08),
    "厦门": (118.10, 24.49),
    "南昌": (115.89, 28.68),
    "长春": (125.32, 43.88),
    "石家庄": (114.51, 38.04),
    "贵阳": (106.71, 26.65),
    "南宁": (108.37, 22.82),
    "海口": (110.35, 20.02),
    "呼和浩特": (111.75, 40.84),
    "乌鲁木齐": (87.62, 43.83),
    "拉萨": (91.11, 29.65),
    "银川": (106.27, 38.47),
    "西宁": (101.77, 36.62),
    "台北": (121.56, 25.04),
    "香港": (114.17, 22.32),
    "澳门": (113.55, 22.20),
}


def get_city_longitude(city: str) -> float | None:
    """根据城市名获取经度，返回 None 表示未找到。"""
    coords = CHINA_CITIES.get(city)
    return coords[0] if coords else None
