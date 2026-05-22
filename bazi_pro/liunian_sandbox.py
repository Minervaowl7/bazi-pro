#!/usr/bin/env python3
"""
bazi-pro 流年推演沙盒 v4.8
年份滑块 2020-2040，拖拽实时更新流年干支、合冲关系、五行变化
"""

from dataclasses import dataclass, field

# 60甲子表
GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']


@dataclass
class YearData:
    """单年流年数据"""
    year: int
    gan: str
    zhi: str
    gan_zhi: str
    relations: list[dict] = field(default_factory=list)  # 与原局合冲关系
    wuxing_shift: dict = field(default_factory=dict)     # 五行力量变化
    shen_trigger: list[str] = field(default_factory=list)  # 引动十神
    bookmark: str = ''  # ⭐/⚠️ 标记


class LiunianSandbox:
    """流年推演沙盒

    接收 MCP JSON 中的原局数据，计算每年流年干支及其与原局的互动
    """

    def __init__(self, mcp_json: dict):
        self.bazi = mcp_json.get('八字', '')
        self.day_master = mcp_json.get('日主', '')
        self._year_range = (2020, 2040)
        self._year_data: dict[int, YearData] = {}

    def set_year_range(self, start: int, end: int) -> None:
        """设置推演年份范围"""
        self._year_range = (start, end)
        self._year_data.clear()

    def get_year_data(self, year: int) -> YearData:
        """获取某年流年数据"""
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

        # 简化的关系分析
        bazi_parts = self.bazi.split()
        for pillar in bazi_parts:
            if len(pillar) >= 2:
                p_gan, p_zhi = pillar[0], pillar[1]
                # 天干合
                if (gan, p_gan) in [('甲', '己'), ('己', '甲'), ('乙', '庚'), ('庚', '乙'),
                                     ('丙', '辛'), ('辛', '丙'), ('丁', '壬'), ('壬', '丁'),
                                     ('戊', '癸'), ('癸', '戊')]:
                    yd.relations.append({'type': '天干合', 'with': pillar, 'desc': f'{gan}合{p_gan}'})
                # 地支冲
                if (zhi, p_zhi) in [('子', '午'), ('午', '子'), ('丑', '未'), ('未', '丑'),
                                     ('寅', '申'), ('申', '寅'), ('卯', '酉'), ('酉', '卯'),
                                     ('辰', '戌'), ('戌', '辰'), ('巳', '亥'), ('亥', '巳')]:
                    yd.relations.append({'type': '地支冲', 'with': pillar, 'desc': f'{zhi}冲{p_zhi}'})

        self._year_data[year] = yd
        return yd

    def mark_key_years(self) -> list[YearData]:
        """自动标记关键年份（用神到位 ⭐ / 忌神引动 ⚠️）"""
        # 简化：基于天干与日主的关系标记
        marked = []
        for year in range(self._year_range[0], self._year_range[1] + 1):
            yd = self.get_year_data(year)
            # 简化判断逻辑
            favorable_gan = _get_favorable_gan(self.day_master)
            if yd.gan in favorable_gan:
                yd.bookmark = '⭐ 用神到位'
            elif len(yd.relations) >= 2:
                yd.bookmark = '⚠️ 引动频繁'
            marked.append(yd)
        return marked

    def export_year_pdf(self, year: int) -> str:
        """导出逐年摘要（PDF 需额外依赖）"""
        yd = self.get_year_data(year)
        return (
            f"{year}年 {yd.gan_zhi}\n"
            f"天干: {yd.gan} | 地支: {yd.zhi}\n"
            f"关系: {', '.join(r['desc'] for r in yd.relations) or '无特殊关系'}\n"
            f"标记: {yd.bookmark or '无'}"
        )

    @property
    def year_range(self) -> tuple:
        return self._year_range


def _get_favorable_gan(day_master: str) -> list[str]:
    """基于日主返回有利天干（简化）"""
    favorable_map = {
        '甲': ['丙', '丁', '癸'], '乙': ['丙', '丁', '癸'],
        '丙': ['甲', '乙', '壬'], '丁': ['甲', '乙', '壬'],
        '戊': ['丙', '丁', '甲'], '己': ['丙', '丁', '甲'],
        '庚': ['戊', '己', '丁'], '辛': ['戊', '己', '丁'],
        '壬': ['庚', '辛', '戊'], '癸': ['庚', '辛', '戊'],
    }
    return favorable_map.get(day_master, [])
