from bazi_pro.core.constants import GAN_WUXING
from bazi_pro.core.patterns import PATTERN_YONGSHEN
from bazi_pro.core.stems import KE_MAP, SHENG_MAP, WO_KE_MAP, WO_SHENG_MAP
from bazi_pro.core.ten_gods import SHISHEN_WUXING_REL


def derive_yongshen(day_master: str, bazi_parts: list[str],
                    pattern_result: dict, wangshuai: dict,
                    element_forces: dict) -> dict:
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {'yongshen': '待定', 'xishen': [], 'jishen': [], 'confidence': 0,
                'trace': {'method': 'none', 'reason': '日主五行缺失'}}

    pattern_name = pattern_result.get('pattern', '')
    is_weak = wangshuai.get('is_weak', False)
    is_strong = wangshuai.get('is_strong', False)
    trace = {'pattern_basis': pattern_name, 'wangshuai_basis': wangshuai.get('verdict', ''),
             'method': '', 'reason': '', 'candidates_considered': []}

    yongshen_wx = _pattern_yongshen_wx(pattern_name, dm_wx, is_weak, is_strong)
    if yongshen_wx:
        trace['method'] = 'pattern_based'
        trace['reason'] = f'格局"{pattern_name}"推导用神为{yongshen_wx}'
    else:
        trace['method'] = 'wangshuai_fallback'
        if is_weak:
            yongshen_wx = SHENG_MAP.get(dm_wx, '')
            trace['reason'] = f'身弱，取印星({yongshen_wx})为用'
        elif is_strong:
            ke_wx = KE_MAP.get(dm_wx, '')
            sheng_wx = WO_SHENG_MAP.get(dm_wx, '')
            yongshen_wx = ke_wx if ke_wx else sheng_wx
            trace['reason'] = f'身强，取克泄({yongshen_wx})为用'
        else:
            yongshen_wx = SHENG_MAP.get(dm_wx, '')
            trace['reason'] = f'中和偏弱，取印星({yongshen_wx})为用'

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
        'trace': trace,
    }


def _pattern_yongshen_wx(pattern_name: str, dm_wx: str,
                         is_weak: bool = False, is_strong: bool = False) -> str:
    if '从强' in pattern_name or '假从强' in pattern_name or '专旺' in pattern_name:
        return SHENG_MAP.get(dm_wx, '')
    if '从财' in pattern_name:
        return WO_KE_MAP.get(dm_wx, '')
    if '从官杀' in pattern_name:
        return KE_MAP.get(dm_wx, '')
    if '从儿' in pattern_name:
        return dm_wx

    _REL_TO_WX = {
        '同我': lambda w: w,
        '生我': lambda w: SHENG_MAP.get(w, ''),
        '我生': lambda w: WO_SHENG_MAP.get(w, ''),
        '我克': lambda w: WO_KE_MAP.get(w, ''),
        '克我': lambda w: KE_MAP.get(w, ''),
    }

    _WEAK_PREFERRED = {'生我', '同我'}
    _STRONG_PREFERRED = {'克我', '我生', '我克'}

    for ss_name, info in PATTERN_YONGSHEN.items():
        if ss_name in pattern_name:
            yong_list = info.get('用神', [])
            if not yong_list:
                continue

            if is_weak and len(yong_list) >= 2:
                for candidate in yong_list:
                    rel = SHISHEN_WUXING_REL.get(candidate, '')
                    if rel in _WEAK_PREFERRED:
                        return _REL_TO_WX.get(rel, lambda w: '')(dm_wx)

            if is_strong and len(yong_list) >= 2:
                for candidate in yong_list:
                    rel = SHISHEN_WUXING_REL.get(candidate, '')
                    if rel in _STRONG_PREFERRED:
                        return _REL_TO_WX.get(rel, lambda w: '')(dm_wx)

            first = yong_list[0]
            rel = SHISHEN_WUXING_REL.get(first, '')
            return _REL_TO_WX.get(rel, lambda w: '')(dm_wx)

    return ''
