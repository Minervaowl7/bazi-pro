__version__ = "bazi-pro 确定性命理计算核心 v5.0"

from bazi_pro.core.stems import (
    GAN_HE, WUXING_SHENG, WUXING_KE, SHENG_MAP, KE_MAP, WO_KE_MAP,
)
from bazi_pro.core.branches import (
    ZHI_CANGGAN, CANGGAN_WEIGHT, SHIER_CHANGSHENG, DELING_SCORE,
    ZHI_HE, ZHI_CHONG, ZHI_HAI, ZHI_XING, ZHI_SANHE, ZHI_BANHE,
    JIANLU_MAP, YANGREN_MAP,
)
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.ten_gods import (
    SHISHEN_WUXING_REL, _count_shishen_categories, _get_yongshen_direction,
)
from bazi_pro.core.relations import detect_relations
from bazi_pro.core.elements import calc_element_forces
from bazi_pro.core.strength import (
    calc_deling, calc_dedi, calc_deshi, judge_wangshuai,
)
from bazi_pro.core.patterns import (
    PATTERN_YONGSHEN, screen_pattern,
    _screen_layer0, _screen_layer1, _screen_layer2, _screen_layer3,
    _finalize_pattern,
)
from bazi_pro.core.yongshen import derive_yongshen, _pattern_yongshen_wx

from bazi_pro import GAN_WUXING, ZHI_WUXING, derive_shishen


def full_analysis(mcp_json: dict) -> dict:
    bazi = mcp_json.get('八字', '')
    day_master = mcp_json.get('日主', '')

    if not bazi or not day_master:
        return {'status': 'invalid_input', 'note': '八字或日主缺失'}

    bazi_parts = bazi.split()
    if len(bazi_parts) < 2:
        return {'status': 'invalid_input', 'note': '八字数据不完整，至少需要年月两柱'}

    month_zhi = bazi_parts[1][1] if len(bazi_parts[1]) >= 2 else ''

    deling_status, deling_score = calc_deling(day_master, month_zhi)
    dedi = calc_dedi(day_master, bazi_parts)
    deshi = calc_deshi(day_master, bazi_parts)
    wangshuai = judge_wangshuai(deling_score, dedi['score'], deshi['score'])

    element_forces = calc_element_forces(bazi_parts, month_zhi)
    relations = detect_relations(bazi_parts)
    pattern = screen_pattern(day_master, bazi_parts, wangshuai, element_forces)
    yongshen = derive_yongshen(day_master, bazi_parts, pattern, wangshuai, element_forces)

    pillars = []
    positions = ['年', '月', '日', '时']
    for i, part in enumerate(bazi_parts):
        if len(part) >= 2:
            gan, zhi = part[0], part[1]
            canggan = get_canggan(zhi)
            pillars.append({
                'position': positions[i] if i < 4 else '',
                'gan': gan, 'zhi': zhi,
                'wuxing_gan': GAN_WUXING.get(gan, ''),
                'wuxing_zhi': ZHI_WUXING.get(zhi, ''),
                'shishen': derive_shishen(day_master, gan),
                'canggan': [{'gan': cg, 'qi': ql, 'wuxing': GAN_WUXING.get(cg, ''),
                              'shishen': derive_shishen(day_master, cg)}
                             for cg, ql in canggan],
            })

    return {
        'status': 'completed',
        'day_master': day_master,
        'deling': {'status': deling_status, 'score': deling_score},
        'dedi': dedi,
        'deshi': deshi,
        'wangshuai': wangshuai,
        'element_forces': element_forces,
        'relations': relations,
        'pattern': pattern,
        'yongshen': yongshen,
        'pillars': pillars,
    }


__all__ = [
    '__version__',
    'full_analysis',
    'GAN_HE', 'WUXING_SHENG', 'WUXING_KE', 'SHENG_MAP', 'KE_MAP', 'WO_KE_MAP',
    'ZHI_CANGGAN', 'CANGGAN_WEIGHT', 'SHIER_CHANGSHENG', 'DELING_SCORE',
    'ZHI_HE', 'ZHI_CHONG', 'ZHI_HAI', 'ZHI_XING', 'ZHI_SANHE', 'ZHI_BANHE',
    'JIANLU_MAP', 'YANGREN_MAP',
    'get_canggan',
    'SHISHEN_WUXING_REL', '_count_shishen_categories', '_get_yongshen_direction',
    'detect_relations',
    'calc_element_forces',
    'calc_deling', 'calc_dedi', 'calc_deshi', 'judge_wangshuai',
    'PATTERN_YONGSHEN', 'screen_pattern',
    '_screen_layer0', '_screen_layer1', '_screen_layer2', '_screen_layer3',
    '_finalize_pattern',
    'derive_yongshen', '_pattern_yongshen_wx',
]
