from bazi_pro.core.constants import GAN_WUXING, WUXING_TO_GAN
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
    pattern_type = pattern_result.get('type', '')
    is_weak = wangshuai.get('is_weak', False)
    is_strong = wangshuai.get('is_strong', False)
    trace = {'pattern_basis': pattern_name, 'wangshuai_basis': wangshuai.get('verdict', ''),
             'method': '', 'reason': '', 'candidates_considered': []}

    yongshen_wx = _pattern_yongshen_wx(pattern_name, dm_wx, is_weak, is_strong,
                                        pattern_type=pattern_type)
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

    jishen_wx = _derive_jishen(pattern_name, dm_wx, yongshen_wx, is_weak, is_strong,
                               pattern_type=pattern_type)
    xishen_wx = _derive_xishen(pattern_name, dm_wx, yongshen_wx, jishen_wx)

    return {
        'yongshen': yongshen_wx,
        'yongshen_gan': WUXING_TO_GAN.get(yongshen_wx, ''),
        'xishen': xishen_wx,
        'xishen_gan': [WUXING_TO_GAN.get(w, '') for w in xishen_wx],
        'jishen': jishen_wx,
        'jishen_gan': [WUXING_TO_GAN.get(w, '') for w in jishen_wx],
        'confidence': pattern_result.get('confidence', 0.5),
        'pattern_basis': pattern_name,
        'note': '确定性推导，基于格局+旺衰规则。调候用神需查穷通宝鉴，由LLM补充。',
        'trace': trace,
    }


def _derive_xishen(pattern_name: str, dm_wx: str, yongshen_wx: str,
                   jishen_wx: list[str]) -> list[str]:
    """
    推导喜神五行。

    优先从格局用神表的第二候选推导；
    若无第二候选，用通用逻辑（生用神的五行），但排除忌神。
    """
    _REL_TO_WX = {
        '同我': dm_wx,
        '生我': SHENG_MAP.get(dm_wx, ''),
        '我生': WO_SHENG_MAP.get(dm_wx, ''),
        '我克': WO_KE_MAP.get(dm_wx, ''),
        '克我': KE_MAP.get(dm_wx, ''),
    }

    # 从格局用神表取第二候选作为喜神
    for ss_name, info in PATTERN_YONGSHEN.items():
        if ss_name in pattern_name:
            yong_list = info.get('用神', [])
            if len(yong_list) >= 2:
                for candidate in yong_list[1:]:
                    base = candidate.split('(')[0].strip()
                    rel = SHISHEN_WUXING_REL.get(base, '')
                    wx = _REL_TO_WX.get(rel, '')
                    if wx and wx != yongshen_wx and wx not in jishen_wx:
                        return [wx]
            break

    # 通用逻辑：生用神的五行（排除忌神）
    if yongshen_wx == SHENG_MAP.get(dm_wx, ''):
        xi = dm_wx
    elif yongshen_wx == dm_wx:
        xi = SHENG_MAP.get(dm_wx, '')
    else:
        xi = SHENG_MAP.get(yongshen_wx, '')

    if xi and xi != yongshen_wx and xi not in jishen_wx:
        return [xi]
    return []


def _derive_jishen(pattern_name: str, dm_wx: str, yongshen_wx: str,
                   is_weak: bool, is_strong: bool, pattern_type: str = '') -> list[str]:
    """
    推导忌神五行。

    规则：
    1. 从格（从强/专旺/从财/从官杀/从儿）：忌神=逆势五行
    2. 扶抑格身弱：忌神=克我+我克（排除用神）
    3. 扶抑格身强：忌神=同我+生我（排除用神）
    4. 中和：从格局忌神表推导（PATTERN_YONGSHEN[格局]['忌神']）
    """
    ke_wo = KE_MAP.get(dm_wx, '')
    wo_ke = WO_KE_MAP.get(dm_wx, '')
    sheng_wo = SHENG_MAP.get(dm_wx, '')
    wo_sheng = WO_SHENG_MAP.get(dm_wx, '')

    # ── 从格：忌神=逆势五行 ──
    is_cong_qiang = ('从强' in pattern_name or '假从强' in pattern_name
                     or '专旺' in pattern_name or pattern_type == '专旺格'
                     or '从强' in pattern_type or '假从强' in pattern_type)
    if is_cong_qiang:
        # 从强顺印比之势，忌官杀+财星+食伤
        return [w for w in [ke_wo, wo_ke, wo_sheng] if w and w != yongshen_wx]
    if '从财' in pattern_name:
        # 从财顺财势，忌比劫+印星
        return [w for w in [dm_wx, sheng_wo] if w and w != yongshen_wx]
    if '从官杀' in pattern_name:
        # 从官杀顺杀势，忌比劫+印星
        return [w for w in [dm_wx, sheng_wo] if w and w != yongshen_wx]
    if '从儿' in pattern_name:
        # 从儿顺食伤势，忌印星+官杀
        return [w for w in [sheng_wo, ke_wo] if w and w != yongshen_wx]

    # ── 扶抑格 ──
    if is_weak:
        return [w for w in [ke_wo, wo_ke] if w and w != yongshen_wx]
    if is_strong:
        return [w for w in [dm_wx, sheng_wo] if w and w != yongshen_wx]

    # ── 中和：从格局忌神表推导 ──
    jishen = _jishen_from_pattern_table(pattern_name, dm_wx, yongshen_wx)
    if jishen:
        return jishen

    # 兜底：用神的对立面
    if yongshen_wx == sheng_wo:
        return [w for w in [ke_wo, wo_ke] if w]
    elif yongshen_wx == ke_wo:
        return [w for w in [dm_wx, sheng_wo] if w]
    return []


def _jishen_from_pattern_table(pattern_name: str, dm_wx: str, yongshen_wx: str) -> list[str]:
    """从 PATTERN_YONGSHEN 忌神表推导忌神五行。"""
    _REL_TO_WX = {
        '同我': dm_wx,
        '生我': SHENG_MAP.get(dm_wx, ''),
        '我生': WO_SHENG_MAP.get(dm_wx, ''),
        '我克': WO_KE_MAP.get(dm_wx, ''),
        '克我': KE_MAP.get(dm_wx, ''),
    }

    for ss_name, info in PATTERN_YONGSHEN.items():
        if ss_name in pattern_name:
            ji_list = info.get('忌神', [])
            result = []
            for candidate in ji_list:
                rel = SHISHEN_WUXING_REL.get(candidate, '')
                if not rel:
                    # 带括号注释的忌神如 '财星(无制时)' → 提取前缀
                    base = candidate.split('(')[0].strip()
                    rel = SHISHEN_WUXING_REL.get(base, '')
                wx = _REL_TO_WX.get(rel, '')
                if wx and wx != yongshen_wx and wx not in result:
                    result.append(wx)
            return result
    return []


def _pattern_yongshen_wx(pattern_name: str, dm_wx: str,
                         is_weak: bool = False, is_strong: bool = False,
                         pattern_type: str = '') -> str:
    # 从格/专旺格：检查 pattern_name 和 pattern_type 两个维度
    is_cong_qiang = ('从强' in pattern_name or '假从强' in pattern_name
                     or '专旺' in pattern_name or pattern_type == '专旺格'
                     or '从强' in pattern_type or '假从强' in pattern_type)
    if is_cong_qiang:
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
