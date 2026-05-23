from bazi_pro import GAN_WUXING
from bazi_pro.core.patterns import PATTERN_YONGSHEN
from bazi_pro.core.ten_gods import SHISHEN_WUXING_REL
from bazi_pro.core.stems import SHENG_MAP, KE_MAP, WO_KE_MAP


def derive_yongshen(day_master: str, bazi_parts: list[str],
                    pattern_result: dict, wangshuai: dict,
                    element_forces: dict) -> dict:
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {'yongshen': '待定', 'xishen': [], 'jishen': [], 'confidence': 0}

    pattern_name = pattern_result.get('pattern', '')
    is_weak = wangshuai.get('is_weak', False)
    is_strong = wangshuai.get('is_strong', False)

    yongshen_wx = _pattern_yongshen_wx(pattern_name, dm_wx)
    if not yongshen_wx:
        if is_weak:
            yongshen_wx = SHENG_MAP.get(dm_wx, '')
        elif is_strong:
            ke_wx = KE_MAP.get(dm_wx, '')
            sheng_wx = WO_KE_MAP.get(dm_wx, '')
            yongshen_wx = ke_wx if ke_wx else sheng_wx
        else:
            yongshen_wx = SHENG_MAP.get(dm_wx, '')

    xishen_wx = []
    if yongshen_wx == SHENG_MAP.get(dm_wx, ''):
        xishen_wx.append(dm_wx)
    elif yongshen_wx == dm_wx:
        xishen_wx.append(SHENG_MAP.get(dm_wx, ''))

    jishen_wx = []
    ke_wo = KE_MAP.get(dm_wx, '')
    wo_ke = WO_KE_MAP.get(dm_wx, '')
    if is_weak:
        jishen_wx = [w for w in [ke_wo, wo_ke] if w and w != yongshen_wx]
    elif is_strong:
        jishen_wx = [dm_wx, SHENG_MAP.get(dm_wx, '')] if yongshen_wx != dm_wx else []

    wx_to_gan = {'木': '甲乙', '火': '丙丁', '土': '戊己', '金': '庚辛', '水': '壬癸'}

    return {
        'yongshen': yongshen_wx,
        'yongshen_gan': wx_to_gan.get(yongshen_wx, ''),
        'xishen': xishen_wx,
        'xishen_gan': [wx_to_gan.get(w, '') for w in xishen_wx],
        'jishen': jishen_wx,
        'jishen_gan': [wx_to_gan.get(w, '') for w in jishen_wx],
        'confidence': pattern_result.get('confidence', 0.5),
        'pattern_basis': pattern_name,
        'note': '确定性推导，基于格局+旺衰规则。调候用神需查穷通宝鉴，由LLM补充。',
    }


def _pattern_yongshen_wx(pattern_name: str, dm_wx: str) -> str:
    if '从强' in pattern_name or '专旺' in pattern_name:
        return SHENG_MAP.get(dm_wx, '')
    if '从财' in pattern_name:
        return WO_KE_MAP.get(dm_wx, '')
    if '从官杀' in pattern_name:
        return WO_KE_MAP.get(dm_wx, '')
    if '从儿' in pattern_name:
        return dm_wx

    for ss_name, info in PATTERN_YONGSHEN.items():
        if ss_name in pattern_name:
            yong_list = info.get('用神', [])
            if yong_list:
                first = yong_list[0]
                rel = SHISHEN_WUXING_REL.get(first, '')
                if rel == '同我':
                    return dm_wx
                elif rel == '生我':
                    return SHENG_MAP.get(dm_wx, '')
                elif rel == '我生':
                    return WO_KE_MAP.get(dm_wx, '')
                elif rel == '我克':
                    return WO_KE_MAP.get(dm_wx, '')
                elif rel == '克我':
                    return KE_MAP.get(dm_wx, '')
    return ''
