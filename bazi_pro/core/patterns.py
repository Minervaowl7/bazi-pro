from bazi_pro import GAN_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.branches import JIANLU_MAP, YANGREN_MAP
from bazi_pro.core.ten_gods import _count_shishen_categories, _get_yongshen_direction
from bazi_pro.core.stems import SHENG_MAP

PATTERN_YONGSHEN = {
    '正官格': {'用神': ['财星', '印星'], '忌神': ['伤官', '七杀']},
    '七杀格': {'用神': ['食神', '印星'], '忌神': ['财星(无制时)']},
    '正财格': {'用神': ['食伤', '官星'], '忌神': ['比劫']},
    '偏财格': {'用神': ['食伤', '官星'], '忌神': ['比劫']},
    '正印格': {'用神': ['官星', '比劫(身弱时)'], '忌神': ['财星']},
    '偏印格': {'用神': ['财星', '官星(身弱时)'], '忌神': ['食神(枭夺食)']},
    '食神格': {'用神': ['比劫', '财星'], '忌神': ['偏印']},
    '伤官格': {'用神': ['印星', '财星'], '忌神': ['官星(见官)']},
    '建禄格': {'用神': ['官杀', '食伤'], '忌神': ['比劫']},
    '羊刃格': {'用神': ['官杀'], '忌神': ['财星(无制时)']},
    '从强格': {'用神': ['印比'], '忌神': ['官杀', '财星']},
    '从财格': {'用神': ['食伤', '财星'], '忌神': ['比劫', '印星']},
    '从官杀格': {'用神': ['财星', '官杀'], '忌神': ['比劫', '印星']},
    '从儿格': {'用神': ['比劫(生食伤)'], '忌神': ['印星', '官杀']},
    '从势格': {'用神': ['最强之势'], '忌神': ['逆势五行']},
    '化气格': {'用神': ['化神五行'], '忌神': ['克化神五行']},
}


def screen_pattern(day_master: str, bazi_parts: list[str],
                   wangshuai: dict, element_forces: dict) -> dict:
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx or len(bazi_parts) < 2:
        return {'pattern': '数据不足', 'candidates': [], 'note': '日主或八字数据缺失'}

    month_zhi = bazi_parts[1][1] if len(bazi_parts[1]) >= 2 else ''
    if not month_zhi:
        return {'pattern': '数据不足', 'candidates': [], 'note': '月支缺失'}

    pct = element_forces.get('percent', {})
    candidates = []
    gans = [p[0] for p in bazi_parts if len(p) >= 1]

    yin_bi_wx = {dm_wx, SHENG_MAP.get(dm_wx, '')}
    yin_bi_pct = sum(pct.get(wx, 0) for wx in yin_bi_wx)

    ke_xie_hao_wx = set()
    for wx in ['木', '火', '土', '金', '水']:
        if wx not in yin_bi_wx:
            ke_xie_hao_wx.add(wx)
    ke_xie_hao_pct = sum(pct.get(wx, 0) for wx in ke_xie_hao_wx)

    layer0_result = _screen_layer0(day_master, dm_wx, month_zhi, bazi_parts,
                                    wangshuai, pct, yin_bi_pct, ke_xie_hao_pct, gans)
    if layer0_result:
        candidates.append(layer0_result)
        return _finalize_pattern(candidates, wangshuai)

    layer1_result = _screen_layer1(day_master, month_zhi, gans)
    if layer1_result:
        candidates.append(layer1_result)
        return _finalize_pattern(candidates, wangshuai)

    layer2_result = _screen_layer2(day_master, month_zhi, gans)
    if layer2_result:
        candidates.append(layer2_result)
        return _finalize_pattern(candidates, wangshuai)

    layer3_result = _screen_layer3(day_master, dm_wx, month_zhi, gans)
    if layer3_result:
        candidates.append(layer3_result)
        return _finalize_pattern(candidates, wangshuai)

    return {'pattern': '待定', 'candidates': candidates,
            'note': '六层筛查未命中，需LLM综合判断'}


def _screen_layer0(day_master, dm_wx, month_zhi, bazi_parts,
                   wangshuai, pct, yin_bi_pct, ke_xie_hao_pct, gans):
    dm_pct = pct.get(dm_wx, 0)

    if dm_pct >= 80:
        zhuanwang_names = {'木': '曲直格', '火': '炎上格', '土': '稼穑格', '金': '从革格', '水': '润下格'}
        return {
            'layer': 0, 'type': '专旺格', 'pattern': zhuanwang_names.get(dm_wx, '专旺格'),
            'confidence': 0.90, 'reason': f'日主{dm_wx}行占{dm_pct}%≥80%',
            'yongshen_direction': '印比',
        }

    if yin_bi_pct >= 80 and wangshuai.get('is_extreme_strong', False):
        return {
            'layer': 0, 'type': '从强格', 'pattern': '从强格',
            'confidence': 0.85, 'reason': f'印比合计{yin_bi_pct}%≥80%，日主极旺',
            'yongshen_direction': '印比',
        }

    if ke_xie_hao_pct >= 85:
        two_wx = [wx for wx in ['木', '火', '土', '金', '水']
                   if wx not in {dm_wx, SHENG_MAP.get(dm_wx, '')} and pct.get(wx, 0) > 5]
        if len(two_wx) >= 2:
            return {
                'layer': 0, 'type': '两行成象格', 'pattern': f'{two_wx[0]}{two_wx[1]}成象格',
                'confidence': 0.75, 'reason': '克泄耗两行合计≥85%',
                'yongshen_direction': '顺两行气势',
            }

    if wangshuai.get('is_extreme_weak', False) and ke_xie_hao_pct >= 60:
        shishen_counts = _count_shishen_categories(day_master, gans, bazi_parts)
        if shishen_counts.get('财星', 0) >= 3 and shishen_counts.get('比劫', 0) == 0:
            return {
                'layer': 0, 'type': '从财格', 'pattern': '从财格',
                'confidence': 0.80, 'reason': '日主极弱，财星成势，无比劫印星',
                'yongshen_direction': '食伤生财',
            }
        if shishen_counts.get('官杀', 0) >= 3 and shishen_counts.get('比劫', 0) == 0:
            return {
                'layer': 0, 'type': '从官杀格', 'pattern': '从官杀格',
                'confidence': 0.80, 'reason': '日主极弱，官杀成势，无比劫印星',
                'yongshen_direction': '财生官',
            }
        if shishen_counts.get('食伤', 0) >= 3 and shishen_counts.get('比劫', 0) == 0:
            return {
                'layer': 0, 'type': '从儿格', 'pattern': '从儿格',
                'confidence': 0.80, 'reason': '日主极弱，食伤成势，无比劫印星',
                'yongshen_direction': '比劫生食伤',
            }

    if month_zhi == JIANLU_MAP.get(day_master, ''):
        return None

    if month_zhi == YANGREN_MAP.get(day_master, ''):
        if yin_bi_pct >= 80:
            return {
                'layer': 0, 'type': '从强格', 'pattern': '从强格',
                'confidence': 0.85, 'reason': f'月支羊刃但印比{yin_bi_pct}%≥80%，从强格优先',
                'yongshen_direction': '印比',
            }

    return None


def _screen_layer1(day_master, month_zhi, gans):
    canggan = get_canggan(month_zhi)
    if not canggan:
        return None
    benqi_gan = canggan[0][0]
    if benqi_gan in gans:
        ss = derive_shishen(day_master, benqi_gan)
        pattern_name = f'{ss}格' if ss else '未知格'
        return {
            'layer': 1, 'type': '月令本气透干', 'pattern': pattern_name,
            'confidence': 0.85, 'reason': f'月支{month_zhi}本气{benqi_gan}透干，十神为{ss}',
            'yongshen_direction': _get_yongshen_direction(ss),
        }
    return None


def _screen_layer2(day_master, month_zhi, gans):
    canggan = get_canggan(month_zhi)
    if len(canggan) < 2:
        return None
    zhongqi_gan = canggan[1][0]
    benqi_gan = canggan[0][0]
    if benqi_gan in gans:
        return None
    if zhongqi_gan in gans:
        ss = derive_shishen(day_master, zhongqi_gan)
        pattern_name = f'{ss}格' if ss else '未知格'
        return {
            'layer': 2, 'type': '月令中气透干', 'pattern': pattern_name,
            'confidence': 0.75, 'reason': f'月支{month_zhi}中气{zhongqi_gan}透干，十神为{ss}',
            'yongshen_direction': _get_yongshen_direction(ss),
        }
    return None


def _screen_layer3(day_master, dm_wx, month_zhi, gans):
    canggan = get_canggan(month_zhi)
    if not canggan:
        return None
    benqi_gan = canggan[0][0]
    benqi_ss = derive_shishen(day_master, benqi_gan)

    if benqi_ss in ('比肩', '劫财'):
        tou_gan_ss = []
        for g in gans:
            if g != day_master:
                ss = derive_shishen(day_master, g)
                if ss in ('正官', '七杀', '正财', '偏财', '食神', '伤官'):
                    tou_gan_ss.append(ss)
        if tou_gan_ss:
            main_ss = tou_gan_ss[0]
            return {
                'layer': 3, 'type': '建禄月劫', 'pattern': f'建禄月劫，透{main_ss}',
                'confidence': 0.70,
                'reason': f'月令本气{benqi_gan}为{benqi_ss}，透{main_ss}取用',
                'yongshen_direction': _get_yongshen_direction(main_ss),
            }
        else:
            return {
                'layer': 3, 'type': '建禄月劫', 'pattern': '建禄月劫，无财官煞食透出',
                'confidence': 0.50,
                'reason': f'月令本气{benqi_gan}为{benqi_ss}，四天干无财官煞食透出',
                'yongshen_direction': '待定',
            }

    if benqi_ss and benqi_gan not in gans:
        return {
            'layer': 3, 'type': '暗格', 'pattern': f'暗{benqi_ss}格',
            'confidence': 0.65,
            'reason': f'月支{month_zhi}本气{benqi_gan}({benqi_ss})不透干，以暗{benqi_ss}格论',
            'yongshen_direction': _get_yongshen_direction(benqi_ss),
        }

    return None


def _finalize_pattern(candidates, wangshuai):
    best = candidates[0]
    return {
        'pattern': best['pattern'],
        'candidates': candidates,
        'layer': best['layer'],
        'type': best['type'],
        'confidence': best['confidence'],
        'reason': best['reason'],
        'yongshen_direction': best.get('yongshen_direction', '待定'),
        'wangshuai': wangshuai,
    }
