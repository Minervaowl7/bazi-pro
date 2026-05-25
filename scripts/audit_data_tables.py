#!/usr/bin/env python3
"""Agent A: 命理数据表完整性审计

对照《子平真诠》《三命通会》标准，验证 branches.py、constants.py、stems.py 中的数据完整性。

用法:
  python scripts/audit_data_tables.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bazi_pro.core.branches import (
    CANGGAN_WEIGHT,
    DELING_SCORE,
    JIANLU_MAP,
    SHIER_CHANGSHENG,
    YANGREN_MAP,
    ZHI_CANGGAN,
    ZHI_CHONG,
    ZHI_HAI,
    ZHI_HE,
    ZHI_SANHE,
)
from bazi_pro.core.constants import GAN_SHISHEN_MAP, GAN_WUXING, ZHI_WUXING, derive_shishen
from bazi_pro.core.stems import (
    GAN_HE,
    KE_MAP,
    SHENG_MAP,
    WO_KE_MAP,
    WO_SHENG_MAP,
    WUXING_KE,
    WUXING_SHENG,
)

ISSUES = []


def check(name: str, condition: bool, detail: str):
    if not condition:
        ISSUES.append(f"[{name}] {detail}")


# ═══════════════════════════════════════════════════
# 1. GAN_SHISHEN_MAP — 10天干 × 10天干 = 100 条映射
# ═══════════════════════════════════════════════════
def audit_gan_shishen():
    GANS = list(GAN_WUXING.keys())
    for dm in GANS:
        for target in GANS:
            ss = GAN_SHISHEN_MAP.get((dm, target), '')
            check("GAN_SHISHEN_MAP", ss != '', f"缺少 ({dm},{target}) 的十神映射")
            check("GAN_SHISHEN_MAP", ss in _ALL_SHISHEN,
                  f"({dm},{target}) 的十神 '{ss}' 不在已知列表中")

    # derive_shishen 函数覆盖率
    for dm in GANS:
        for target in GANS:
            ss = derive_shishen(dm, target)
            check("derive_shishen", ss != '', f"derive_shishen({dm},{target}) 返回空")


# ═══════════════════════════════════════════════════
# 2. 五行映射完整性
# ═══════════════════════════════════════════════════
def audit_wuxing():
    for gan, wx in GAN_WUXING.items():
        check("GAN_WUXING", wx in _WUXING, f"天干{gan}的五行'{wx}'不在五行列表中")

    for zhi, wx in ZHI_WUXING.items():
        check("ZHI_WUXING", wx in _WUXING, f"地支{zhi}的五行'{wx}'不在五行列表中")

    # 五行生克循环完整性
    for wx in _WUXING:
        check("SHENG_MAP", wx in SHENG_MAP, f"五行'{wx}'不在 SHENG_MAP 中")
        check("KE_MAP", wx in KE_MAP, f"五行'{wx}'不在 KE_MAP 中")
        check("WO_KE_MAP", wx in WO_KE_MAP, f"五行'{wx}'不在 WO_KE_MAP 中")
        check("WO_SHENG_MAP", wx in WO_SHENG_MAP, f"五行'{wx}'不在 WO_SHENG_MAP 中")

    # SHENG_MAP[生我] = 我的五行
    for me, sheng_wo in SHENG_MAP.items():
        check("WUXING_SHENG", (sheng_wo, me) in WUXING_SHENG,
              f"SHENG_MAP 中 {sheng_wo}→{me} 但 WUXING_SHENG 中不存在")

    for me, ke_wo in KE_MAP.items():
        check("WUXING_KE", (ke_wo, me) in WUXING_KE,
              f"KE_MAP 中 {ke_wo}→{me} 但 WUXING_KE 中不存在")


# ═══════════════════════════════════════════════════
# 3. 地支藏干
# ═══════════════════════════════════════════════════
def audit_canggan():
    ZHI_ALL = set(ZHI_WUXING.keys())
    for zhi in ZHI_ALL:
        canggan = ZHI_CANGGAN.get(zhi, [])
        check("ZHI_CANGGAN", zhi in ZHI_CANGGAN, f"地支'{zhi}'不在 ZHI_CANGGAN 中")
        check("ZHI_CANGGAN", len(canggan) >= 1, f"地支'{zhi}'藏干为空")

        weights = [w for _, w in canggan]
        has_benqi = '本气' in weights
        check("ZHI_CANGGAN", has_benqi, f"地支'{zhi}'缺少本气")
        if len(weights) >= 2:
            check("ZHI_CANGGAN", '中气' in weights,
                  f"地支'{zhi}'有{len(canggan)}个藏干但缺少中气")

        for gan, ql in canggan:
            check("ZHI_CANGGAN", ql in CANGGAN_WEIGHT,
                  f"地支'{zhi}'藏干{gan}的气等级'{ql}'不在 CANGGAN_WEIGHT 中")
            check("ZHI_CANGGAN", gan in GAN_WUXING,
                  f"地支'{zhi}'藏干'{gan}'不在 GAN_WUXING 中")


# ═══════════════════════════════════════════════════
# 4. 十二长生
# ═══════════════════════════════════════════════════
def audit_changsheng():
    ZHI_ALL = set(ZHI_WUXING.keys())
    for gan, table in SHIER_CHANGSHENG.items():
        check("SHIER_CHANGSHENG", gan in GAN_WUXING,
              f"'{gan}'不在 GAN_WUXING 中")
        for zhi in ZHI_ALL:
            check("SHIER_CHANGSHENG", zhi in table,
                  f"天干{gan}缺少地支'{zhi}'的十二长生")
            status = table.get(zhi, '')
            check("SHIER_CHANGSHENG", status in DELING_SCORE,
                  f"天干{gan}地支{zhi}的状态'{status}'不在 DELING_SCORE 中")


# ═══════════════════════════════════════════════════
# 5. 刑冲合害
# ═══════════════════════════════════════════════════
def audit_relations():
    ZHI_ALL = set(ZHI_WUXING.keys())

    # 六冲：6对，每对2个，包含所有12个地支
    chong_zhis = set()
    for pair in ZHI_CHONG:
        chong_zhis.update(pair)
    check("ZHI_CHONG", len(ZHI_CHONG) == 6, f"应有6对，实际{len(ZHI_CHONG)}对")
    check("ZHI_CHONG", chong_zhis == ZHI_ALL,
          f"未覆盖的地支: {ZHI_ALL - chong_zhis}")

    # 六合：6对
    he_zhis = set()
    for pair in ZHI_HE:
        he_zhis.update(pair)
    check("ZHI_HE", len(ZHI_HE) == 6, f"应有6对，实际{len(ZHI_HE)}对")
    check("ZHI_HE", he_zhis == ZHI_ALL,
          f"未覆盖的地支: {ZHI_ALL - he_zhis}")

    # 三合：4局
    check("ZHI_SANHE", len(ZHI_SANHE) == 4, f"应有4局，实际{len(ZHI_SANHE)}局")

    # 六害：6对
    check("ZHI_HAI", len(ZHI_HAI) == 6, f"应有6对，实际{len(ZHI_HAI)}对")

    # 天干五合：5对
    check("GAN_HE", len(GAN_HE) == 5, f"应有5对，实际{len(GAN_HE)}对")


# ═══════════════════════════════════════════════════
# 6. 建禄和羊刃
# ═══════════════════════════════════════════════════
def audit_jianlu_yangren():
    # 建禄：10天干都应有
    for gan in GAN_WUXING:
        check("JIANLU_MAP", gan in JIANLU_MAP,
              f"天干'{gan}'不在 JIANLU_MAP 中")
        zhi = JIANLU_MAP.get(gan, '')
        check("JIANLU_MAP", zhi in ZHI_WUXING,
              f"天干{gan}的建禄地支'{zhi}'不在 ZHI_WUXING 中")

    # 羊刃：只有阳干五位
    check("YANGREN_MAP", len(YANGREN_MAP) == 5,
          f"YANGREN_MAP 应有5个阳干，实际{len(YANGREN_MAP)}个")
    for gan in '甲丙戊庚壬':
        check("YANGREN_MAP", gan in YANGREN_MAP,
              f"阳干'{gan}'不在 YANGREN_MAP 中")
    for gan in '乙丁己辛癸':
        check("YANGREN_MAP", gan not in YANGREN_MAP,
              f"阴干'{gan}'不应在 YANGREN_MAP 中（阴干无羊刃）")


# ═══════════════════════════════════════════════════
# 7. 天干合化月令条件
# ═══════════════════════════════════════════════════
def audit_gan_he_yueling():
    from bazi_pro.core.elements import _HE_HUA_YUELING
    for pair, months in _HE_HUA_YUELING.items():
        gans = list(pair)
        check("_HE_HUA_YUELING", len(gans) == 2,
              f"合化对{frozenset(gans)}应有2个天干")
        for g in gans:
            check("_HE_HUA_YUELING", g in GAN_WUXING,
                  f"合化对中的'{g}'不在 GAN_WUXING 中")
        for m in months:
            check("_HE_HUA_YUELING", m in ZHI_WUXING,
                  f"合化月令'{m}'不在 ZHI_WUXING 中")


_SPEC_EXPECTED = {
    '专旺格': '印比', '从强格': '印比', '假从强格': '印比',
    '从财格': '食伤', '从官杀格': '官杀',
    '从儿格': '食伤', '从势格': '顺势', '化气格': '化神',
}


def audit_pattern_yongshen():
    from bazi_pro.core.patterns import PATTERN_YONGSHEN
    # _pattern_yongshen_wx 对某些格局做直接检查而非查表：
    # 从强/假从强/专旺/从财/从官杀/从儿 在进入 PATTERN_YONGSHEN 查表前已返回
    DIRECT_HANDLED = {'从强', '假从强', '专旺', '从财', '从官杀', '从儿'}
    expected_keys = set(PATTERN_YONGSHEN.keys())
    for name in _SPEC_EXPECTED:
        covered = (
            any(sub in name for sub in DIRECT_HANDLED) or
            any(sub in name for sub in expected_keys)
        )
        check("PATTERN_YONGSHEN", covered,
              f"格局'{name}'未被 PATTERN_YONGSHEN 或直接推导覆盖")


_ALL_SHISHEN = {'比肩', '劫财', '食神', '伤官', '偏财', '正财', '七杀', '正官', '偏印', '正印'}
_WUXING = {'木', '火', '土', '金', '水'}


def main():
    audit_gan_shishen()
    audit_wuxing()
    audit_canggan()
    audit_changsheng()
    audit_relations()
    audit_jianlu_yangren()
    audit_gan_he_yueling()
    audit_pattern_yongshen()

    if ISSUES:
        print(f"❌ Agent A (数据表审计): {len(ISSUES)} 个问题")
        for issue in ISSUES:
            print(f"  - {issue}")
        return 1

    print("✅ Agent A (数据表审计): 数据表完整，无问题")
    return 0


if __name__ == "__main__":
    sys.exit(main())
