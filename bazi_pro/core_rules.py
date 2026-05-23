"""bazi-pro 确定性命理计算核心 v5.0 — 向后兼容代理

所有计算逻辑已迁移至 bazi_pro.core 子包。
本模块仅做 re-export，保持 from bazi_pro.core_rules import xxx 的向后兼容。
"""

from bazi_pro.core import *  # noqa: F401,F403
from bazi_pro.core import (  # noqa: F401
    __version__,
    full_analysis,
    GAN_HE, WUXING_SHENG, WUXING_KE, SHENG_MAP, KE_MAP, WO_KE_MAP,
    ZHI_CANGGAN, CANGGAN_WEIGHT, SHIER_CHANGSHENG, DELING_SCORE,
    ZHI_HE, ZHI_CHONG, ZHI_HAI, ZHI_XING, ZHI_SANHE, ZHI_BANHE,
    JIANLU_MAP, YANGREN_MAP,
    get_canggan,
    SHISHEN_WUXING_REL,
    detect_relations,
    calc_element_forces,
    calc_deling, calc_dedi, calc_deshi, judge_wangshuai,
    PATTERN_YONGSHEN, screen_pattern,
    derive_yongshen,
)
