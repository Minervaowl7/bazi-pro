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
    ZHI_SANXING,
    ZHI_XING,
)
from bazi_pro.core.constants import GAN_WUXING, WUXING_TO_GAN, ZHI_WUXING, derive_shishen
from bazi_pro.core.disease import detect_disease
from bazi_pro.core.elements import calc_element_forces
from bazi_pro.core.family import analyze_family  # noqa: F401
from bazi_pro.core.health import analyze_health  # noqa: F401
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.marriage import analyze_marriage  # noqa: F401
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
from bazi_pro.core.schools import SCHOOL_REGISTRY, SchoolAnalyzer, school_analyze
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
from bazi_pro.core.tiaohou import lookup_tiaohou
from bazi_pro.core.wealth import analyze_wealth  # noqa: F401
from bazi_pro.core.yongshen import _pattern_yongshen_wx, derive_yongshen


def full_analysis(mcp_json: dict) -> dict:
    for key in list(mcp_json.keys()):
        if mcp_json[key] is None:
            mcp_json[key] = ''

    from bazi_pro.validation import validate_bazi_input
    validation = validate_bazi_input(mcp_json, require_gender=False)
    if not validation['valid']:
        return {'status': 'invalid_input', 'errors': validation['errors']}

    bazi = mcp_json.get('八字') or ''
    day_master = mcp_json.get('日主') or ''
    dayun = mcp_json.get('dayun', [])

    bazi_parts = bazi.split()
    month_zhi = bazi_parts[1][1] if len(bazi_parts[1]) >= 2 else ''

    deling_status, deling_score = calc_deling(day_master, month_zhi)
    dedi = calc_dedi(day_master, bazi_parts)
    deshi = calc_deshi(day_master, bazi_parts)
    element_forces = calc_element_forces(bazi_parts, month_zhi)
    wangshuai = judge_wangshuai(deling_score, dedi['score'], deshi['score'], day_master, element_forces)
    relations = detect_relations(bazi_parts)
    shishen_relations = detect_shishen_relations(day_master, bazi_parts)
    # 合并并去重（两类检测来源不同，type 不重叠，但防御性保留去重逻辑）
    seen = set()
    merged = []
    for r in relations + shishen_relations:
        key = (r['type'], frozenset(r.get('elements', [])))
        if key not in seen:
            seen.add(key)
            merged.append(r)
    relations = merged
    pattern = screen_pattern(day_master, bazi_parts, wangshuai, element_forces)
    tiaohou = lookup_tiaohou(day_master, month_zhi)
    yongshen = derive_yongshen(day_master, bazi_parts, pattern, wangshuai, element_forces, tiaohou=tiaohou)
    disease = detect_disease(day_master, bazi_parts, element_forces)

    # Augment jishen with disease sources not already present
    if disease['has_disease']:
        yong_wx = yongshen.get('yongshen', '')
        xi_wx = set(yongshen.get('xishen', []))
        existing_jishen = set(yongshen.get('jishen', []))
        for item in disease['items']:
            d_wx = item.get('disease_element', '')
            if d_wx and d_wx not in existing_jishen and d_wx != yong_wx and d_wx not in xi_wx:
                existing_jishen.add(d_wx)
        yongshen['jishen'] = list(existing_jishen)
        yongshen['jishen_gan'] = [WUXING_TO_GAN.get(w, '') for w in yongshen['jishen']]

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
        'tiaohou': tiaohou,
        'pillars': pillars,
        'dayun': dayun,
        'school_analyses': {},
    }


__all__ = [
    '__version__',
    'full_analysis',
    'GAN_HE', 'WUXING_SHENG', 'WUXING_KE', 'SHENG_MAP', 'KE_MAP', 'WO_KE_MAP', 'WO_SHENG_MAP',
    'ZHI_CANGGAN', 'CANGGAN_WEIGHT', 'SHIER_CHANGSHENG', 'DELING_SCORE',
    'ZHI_HE', 'ZHI_CHONG', 'ZHI_HAI', 'ZHI_XING', 'ZHI_SANHE', 'ZHI_SANXING', 'ZHI_BANHE', 'ZHI_HUIFANG',
    'JIANLU_MAP', 'YANGREN_MAP', 'WUXING_TO_GAN',
    'get_canggan',
    'SHISHEN_WUXING_REL', '_count_shishen_categories', '_get_yongshen_direction',
    'detect_relations', 'detect_shishen_relations', 'detect_disease', 'lookup_tiaohou',
    'calc_element_forces',
    'calc_deling', 'calc_dedi', 'calc_deshi', 'judge_wangshuai',
    'PATTERN_YONGSHEN', 'screen_pattern',
    '_screen_layer0', '_screen_layer1', '_screen_layer2', '_screen_layer3',
    '_finalize_pattern',
    'derive_yongshen', '_pattern_yongshen_wx',
    'SchoolAnalyzer', 'school_analyze', 'SCHOOL_REGISTRY',
    'analyze_marriage', 'analyze_health', 'analyze_wealth', 'analyze_family',
]
