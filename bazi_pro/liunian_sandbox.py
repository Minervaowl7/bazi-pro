#!/usr/bin/env python3
"""bazi-pro 流年沙盒 v5.0 (EXPERIMENTAL)"""

from dataclasses import dataclass, field

from bazi_pro import GAN_WUXING, ZHI_WUXING, count_wuxing_from_bazi, derive_shishen, wuxing_pct
from bazi_pro.core import full_analysis
from bazi_pro.core.stems import SHENG_MAP

EXPERIMENTAL = True

GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

GAN_HE = {
    frozenset({'甲', '己'}): '土', frozenset({'乙', '庚'}): '金',
    frozenset({'丙', '辛'}): '水', frozenset({'丁', '壬'}): '木',
    frozenset({'戊', '癸'}): '火',
}

ZHI_HE = {
    frozenset({'子', '丑'}): '土', frozenset({'寅', '亥'}): '木',
    frozenset({'卯', '戌'}): '火', frozenset({'辰', '酉'}): '金',
    frozenset({'巳', '申'}): '水', frozenset({'午', '未'}): '土',
}

ZHI_CHONG = {
    frozenset({'子', '午'}): True, frozenset({'丑', '未'}): True,
    frozenset({'寅', '申'}): True, frozenset({'卯', '酉'}): True,
    frozenset({'辰', '戌'}): True, frozenset({'巳', '亥'}): True,
}

ZHI_HAI = {
    frozenset({'子', '未'}): True, frozenset({'丑', '午'}): True,
    frozenset({'寅', '巳'}): True, frozenset({'卯', '辰'}): True,
    frozenset({'申', '亥'}): True, frozenset({'酉', '戌'}): True,
}

ZHI_XING = {
    frozenset({'子', '卯'}): True, frozenset({'寅', '巳'}): True,
    frozenset({'巳', '申'}): True, frozenset({'寅', '申'}): True,
    frozenset({'丑', '戌'}): True, frozenset({'未', '戌'}): True,
    frozenset({'丑', '未'}): True,
    frozenset({'辰', '辰'}): True, frozenset({'午', '午'}): True,
    frozenset({'酉', '酉'}): True, frozenset({'亥', '亥'}): True,
}

ZHI_SANHE = [
    {'申', '子', '辰'},
    {'亥', '卯', '未'},
    {'寅', '午', '戌'},
    {'巳', '酉', '丑'},
]


@dataclass
class YearData:
    year: int
    gan: str
    zhi: str
    gan_zhi: str
    relations: list[dict] = field(default_factory=list)
    wuxing_shift: dict = field(default_factory=dict)
    shen_trigger: list[str] = field(default_factory=list)
    bookmark: str = ''


class LiunianSandbox:

    def __init__(self, mcp_json: dict):
        self.bazi = mcp_json.get('八字', '')
        self.day_master = mcp_json.get('日主', '')
        self._year_range = (2020, 2040)
        self._year_data: dict[int, YearData] = {}
        self._core_result = full_analysis(mcp_json)

    def get_core_result(self):
        return self._core_result

    def set_year_range(self, start: int, end: int) -> None:
        self._year_range = (start, end)
        self._year_data.clear()

    def get_year_data(self, year: int) -> YearData:
        if year in self._year_data:
            return self._year_data[year]

        gan_idx = (year - 4) % 10
        zhi_idx = (year - 4) % 12
        gan = GAN[gan_idx]
        zhi = ZHI[zhi_idx]
        gan_zhi = f'{gan}{zhi}'

        yd = YearData(
            year=year,
            gan=gan,
            zhi=zhi,
            gan_zhi=gan_zhi,
        )

        bazi_parts = self.bazi.split()
        for pillar in bazi_parts:
            if len(pillar) >= 2:
                p_gan, p_zhi = pillar[0], pillar[1]

                if frozenset({gan, p_gan}) in GAN_HE:
                    he_wx = GAN_HE[frozenset({gan, p_gan})]
                    yd.relations.append({'type': '天干合', 'with': pillar, 'desc': f'{gan}合{p_gan}→化{he_wx}'})

                pair = frozenset({zhi, p_zhi})
                if pair in ZHI_CHONG:
                    yd.relations.append({'type': '地支冲', 'with': pillar, 'desc': f'{zhi}冲{p_zhi}'})
                if pair in ZHI_HE:
                    he_wx = ZHI_HE[pair]
                    yd.relations.append({'type': '地支合', 'with': pillar, 'desc': f'{zhi}合{p_zhi}→化{he_wx}'})
                if pair in ZHI_HAI:
                    yd.relations.append({'type': '地支害', 'with': pillar, 'desc': f'{zhi}害{p_zhi}'})
                if pair in ZHI_XING:
                    yd.relations.append({'type': '地支刑', 'with': pillar, 'desc': f'{zhi}刑{p_zhi}'})

        if self.day_master:
            yd.shen_trigger.append(f'流年天干→{derive_shishen(self.day_master, gan)}')
            zhi_wx = ZHI_WUXING.get(zhi, '')
            dm_wx = GAN_WUXING.get(self.day_master, '')
            if zhi_wx and dm_wx:
                if zhi_wx == dm_wx:
                    yd.shen_trigger.append(f'地支{zhi}({zhi_wx})→比肩力量')
                elif SHENG_MAP.get(zhi_wx) == dm_wx:
                    yd.shen_trigger.append(f'地支{zhi}({zhi_wx})→印星力量')
                elif SHENG_MAP.get(dm_wx) == zhi_wx:
                    yd.shen_trigger.append(f'地支{zhi}({zhi_wx})→食伤力量')

        yd.wuxing_shift = self._calc_wuxing_shift(gan, zhi)

        self._year_data[year] = yd
        return yd

    def mark_key_years(self) -> list[YearData]:
        marked = []
        yongshen = self._core_result.get('yongshen', {})
        yong_gan = set(yongshen.get('yongshen_gan', ''))
        xi_gans: set[str] = set()
        for g in yongshen.get('xishen_gan', []):
            xi_gans.update(g)
        favorable = yong_gan | xi_gans

        ji_gans: set[str] = set()
        for g in yongshen.get('jishen_gan', []):
            ji_gans.update(g)

        for year in range(self._year_range[0], self._year_range[1] + 1):
            yd = self.get_year_data(year)
            if yd.gan in favorable:
                yd.bookmark = '⭐ 用神到位'
            elif yd.gan in ji_gans:
                yd.bookmark = '⚠️ 忌神引动'
            elif len(yd.relations) >= 2:
                has_negative = any(r['type'] in ('地支冲', '地支刑', '地支害') for r in yd.relations)
                if has_negative:
                    yd.bookmark = '⚠️ 冲刑害频繁'
                else:
                    yd.bookmark = '⭐ 合多吉象'
            marked.append(yd)
        return marked

    def export_year_pdf(self, year: int) -> str:
        yd = self.get_year_data(year)
        return (
            f"{year}年 {yd.gan_zhi}\n"
            f"天干: {yd.gan} | 地支: {yd.zhi}\n"
            f"关系: {', '.join(r['desc'] for r in yd.relations) or '无特殊关系'}\n"
            f"十神引动: {', '.join(yd.shen_trigger) or '无'}\n"
            f"标记: {yd.bookmark or '无'}"
        )

    def detect_sanhe(self, year: int) -> list[dict]:
        yd = self.get_year_data(year)
        bazi_zhis = {p[1] for p in self.bazi.split() if len(p) >= 2}
        bazi_zhis.add(yd.zhi)
        results = []
        for group in ZHI_SANHE:
            if group.issubset(bazi_zhis):
                results.append({
                    'type': '三合局',
                    'branches': sorted(group),
                    'desc': f'{" ".join(sorted(group))} 三合成局',
                })
        return results

    @property
    def year_range(self) -> tuple:
        return self._year_range

    def _calc_wuxing_shift(self, liunian_gan: str, liunian_zhi: str) -> dict:
        base = count_wuxing_from_bazi(self.bazi)
        gan_wx = GAN_WUXING.get(liunian_gan, '')
        zhi_wx = ZHI_WUXING.get(liunian_zhi, '')
        if gan_wx:
            base[gan_wx] = base.get(gan_wx, 0) + 1
        if zhi_wx:
            base[zhi_wx] = base.get(zhi_wx, 0) + 1
        return wuxing_pct(base)

