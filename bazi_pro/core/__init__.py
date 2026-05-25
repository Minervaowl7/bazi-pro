__version__ = "bazi-pro 确定性命理计算核心 v5.0"

from bazi_pro.core.branches import (
    CANGGAN_WEIGHT,
    DELING_SCORE,
    JIANLU_MAP,
    SHIER_CHANGSHENG,
    YANGREN_MAP,
    ZHI_BANHE,
    ZHI_CANGGAN,
    ZHI_CHONG,
    ZHI_HAI,
    ZHI_HE,
    ZHI_HUIFANG,
    ZHI_SANHE,
    ZHI_XING,
)
from bazi_pro.core.constants import GAN_WUXING, ZHI_WUXING, derive_shishen
from bazi_pro.core.disease import detect_disease
from bazi_pro.core.elements import calc_element_forces
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.patterns import (
    PATTERN_YONGSHEN,
    _finalize_pattern,
    _screen_layer0,
    _screen_layer1,
    _screen_layer2,
    _screen_layer3,
    screen_pattern,
)
from bazi_pro.core.relations import detect_relations, detect_shishen_relations
from bazi_pro.core.stems import (
    GAN_HE,
    KE_MAP,
    SHENG_MAP,
    WO_KE_MAP,
    WO_SHENG_MAP,
    WUXING_KE,
    WUXING_SHENG,
)
from bazi_pro.core.strength import (
    calc_dedi,
    calc_deling,
    calc_deshi,
    judge_wangshuai,
)
from bazi_pro.core.ten_gods import (
    SHISHEN_WUXING_REL,
    _count_shishen_categories,
    _get_yongshen_direction,
)
from bazi_pro.core.yongshen import _pattern_yongshen_wx, derive_yongshen


def full_analysis(mcp_json: dict) -> dict:
    from bazi_pro.validation import validate_bazi_input
    validation = validate_bazi_input(mcp_json, require_gender=False)
    if not validation['valid']:
        return {'status': 'invalid_input', 'errors': validation['errors']}

    bazi = mcp_json.get('八字', '')
    day_master = mcp_json.get('日主', '')

    bazi_parts = bazi.split()
    month_zhi = bazi_parts[1][1] if len(bazi_parts[1]) >= 2 else ''

    deling_status, deling_score = calc_deling(day_master, month_zhi)
    dedi = calc_dedi(day_master, bazi_parts)
    deshi = calc_deshi(day_master, bazi_parts)
    wangshuai = judge_wangshuai(deling_score, dedi['score'], deshi['score'])

    element_forces = calc_element_forces(bazi_parts, month_zhi)
    relations = detect_relations(bazi_parts)
    shishen_relations = detect_shishen_relations(day_master, bazi_parts)
    relations = relations + shishen_relations
    pattern = screen_pattern(day_master, bazi_parts, wangshuai, element_forces)
    yongshen = derive_yongshen(day_master, bazi_parts, pattern, wangshuai, element_forces)
    disease = detect_disease(day_master, bazi_parts, element_forces)

    # Augment jishen with disease sources not already present
    if disease['has_disease']:
        existing_jishen = set(yongshen.get('jishen', []))
        for item in disease['items']:
            d_wx = item.get('disease_element', '')
            if d_wx and d_wx not in existing_jishen:
                existing_jishen.add(d_wx)
        wx_to_gan = {'木': '甲乙', '火': '丙丁', '土': '戊己', '金': '庚辛', '水': '壬癸'}
        yongshen['jishen'] = list(existing_jishen)
        yongshen['jishen_gan'] = [wx_to_gan.get(w, '') for w in yongshen['jishen']]

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
        'disease': disease,
        'pillars': pillars,
    }


__all__ = [
    '__version__',
    'full_analysis',
    'GAN_HE', 'WUXING_SHENG', 'WUXING_KE', 'SHENG_MAP', 'KE_MAP', 'WO_KE_MAP', 'WO_SHENG_MAP',
    'ZHI_CANGGAN', 'CANGGAN_WEIGHT', 'SHIER_CHANGSHENG', 'DELING_SCORE',
    'ZHI_HE', 'ZHI_CHONG', 'ZHI_HAI', 'ZHI_XING', 'ZHI_SANHE', 'ZHI_BANHE', 'ZHI_HUIFANG',
    'JIANLU_MAP', 'YANGREN_MAP',
    'get_canggan',
    'SHISHEN_WUXING_REL', '_count_shishen_categories', '_get_yongshen_direction',
    'detect_relations', 'detect_shishen_relations', 'detect_disease',
    'calc_element_forces',
    'calc_deling', 'calc_dedi', 'calc_deshi', 'judge_wangshuai',
    'PATTERN_YONGSHEN', 'screen_pattern',
    '_screen_layer0', '_screen_layer1', '_screen_layer2', '_screen_layer3',
    '_finalize_pattern',
    'derive_yongshen', '_pattern_yongshen_wx',
]
