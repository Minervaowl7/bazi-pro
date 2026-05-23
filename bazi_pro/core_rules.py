"""bazi-pro 确定性命理计算核心 v5.0 — 向后兼容代理

所有计算逻辑已迁移至 bazi_pro.core 子包。
本模块仅做 re-export，保持 from bazi_pro.core_rules import xxx 的向后兼容。

.. deprecated::
    请直接使用 ``from bazi_pro.core import xxx`` 或 ``from bazi_pro.core.constants import xxx``。
    本模块将在未来版本中移除。
"""

import warnings

from bazi_pro.core import *  # noqa: F401,F403
from bazi_pro.core import (  # noqa: F401
    CANGGAN_WEIGHT,
    DELING_SCORE,
    GAN_HE,
    JIANLU_MAP,
    KE_MAP,
    PATTERN_YONGSHEN,
    SHENG_MAP,
    SHIER_CHANGSHENG,
    SHISHEN_WUXING_REL,
    WO_KE_MAP,
    WUXING_KE,
    WUXING_SHENG,
    YANGREN_MAP,
    ZHI_BANHE,
    ZHI_CANGGAN,
    ZHI_CHONG,
    ZHI_HAI,
    ZHI_HE,
    ZHI_SANHE,
    ZHI_XING,
    __version__,
    calc_dedi,
    calc_deling,
    calc_deshi,
    calc_element_forces,
    derive_yongshen,
    detect_relations,
    full_analysis,
    get_canggan,
    judge_wangshuai,
    screen_pattern,
)

warnings.warn(
    "bazi_pro.core_rules is deprecated; use bazi_pro.core instead.",
    DeprecationWarning,
    stacklevel=2,
)
