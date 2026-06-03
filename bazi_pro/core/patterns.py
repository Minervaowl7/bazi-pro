from bazi_pro.core.branches import JIANLU_MAP, SHIER_CHANGSHENG, YANGREN_MAP, ZHI_BANHE, ZHI_HUIFANG, ZHI_SANHE
from bazi_pro.core.constants import GAN_WUXING, ZHI_WUXING, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.stems import GAN_HE, KE_MAP, SHENG_MAP, WO_KE_MAP
from bazi_pro.core.ten_gods import _count_shishen_categories, _get_yongshen_direction


def _check_dm_root_in_branches(day_master: str, dm_wx: str, bazi_parts: list) -> dict:
    """检查日主在地支是否有根气（《渊海子平》："命逢根气，命殞无猜"）

    从格判断的核心：地支无根是从格成立的首要条件

    Returns:
        dict: {
            'has_benqi_root': bool,  # 是否有本气根
            'has_zhongqi_root': bool,  # 是否有中气根
            'has_weakqi_root': bool,  # 是否有余气根
            'root_locations': list,  # 根气所在位置，如 ['辰（本气）', '寅（中气）']
        }
    """
    result = {
        'has_benqi_root': False,
        'has_zhongqi_root': False,
        'has_weakqi_root': False,
        'root_locations': []
    }

    for part in bazi_parts:
        if len(part) < 2:
            continue
        zhi = part[1]
        for cg, ql in get_canggan(zhi):
            if GAN_WUXING.get(cg, '') == dm_wx:
                if ql == '本气':
                    result['has_benqi_root'] = True
                    result['root_locations'].append(f'{zhi}（本气）')
                elif ql == '中气':
                    result['has_zhongqi_root'] = True
                    result['root_locations'].append(f'{zhi}（中气）')
                elif ql == '余气':
                    result['has_weakqi_root'] = True
                    result['root_locations'].append(f'{zhi}（余气）')

    return result


HUA_SEASON_MAP = {
    '土': {'辰', '戌', '丑', '未'},
    '金': {'申', '酉'},
    '水': {'亥', '子'},
    '木': {'寅', '卯'},
    '火': {'巳', '午'},
}

GAN_HE_DUO = {
    frozenset({'甲', '己'}): {'争合': '己', '妒合': '乙'},
    frozenset({'乙', '庚'}): {'争合': '庚', '妒合': '甲'},
    frozenset({'丙', '辛'}): {'争合': '辛', '妒合': '丁'},
    frozenset({'丁', '壬'}): {'争合': '壬', '妒合': '丙'},
    frozenset({'戊', '癸'}): {'争合': '癸', '妒合': '己'},
}

WUXING_KE = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}


def _check_formation(bazi_parts, target_wx):
    branches = []
    for part in bazi_parts:
        if len(part) >= 2:
            branches.append(part[1])
    branch_set = set(branches)
    for fang_set, fang_wx in ZHI_HUIFANG:
        if fang_set.issubset(branch_set) and fang_wx == target_wx:
            return {
                'has_formation': True,
                'type': '会方',
                'branches': sorted(list(fang_set)),
                'element': target_wx,
            }
    for he_set, he_wx in ZHI_SANHE:
        if he_set.issubset(branch_set) and he_wx == target_wx:
            return {
                'has_formation': True,
                'type': '三合',
                'branches': sorted(list(he_set)),
                'element': target_wx,
            }
    for fang_set, fang_wx in ZHI_HUIFANG:
        if fang_wx == target_wx:
            overlap = fang_set & branch_set
            if len(overlap) >= 2:
                return {
                    'has_formation': True,
                    'type': '半会',
                    'branches': sorted(list(overlap)),
                    'element': target_wx,
                }
    for banhe_set, banhe_wx in ZHI_BANHE:
        if banhe_set.issubset(branch_set) and banhe_wx == target_wx:
            return {
                'has_formation': True,
                'type': '半合局',
                'branches': sorted(list(banhe_set)),
                'element': target_wx,
            }
    if target_wx == '土':
        siku = {'辰', '戌', '丑', '未'}
        siku_present = siku & branch_set
        if len(siku_present) >= 3:
            return {
                'has_formation': True,
                'type': '会方',
                'branches': sorted(list(siku_present)),
                'element': target_wx,
            }
    wx_count = sum(1 for b in branches if ZHI_WUXING.get(b, '') == target_wx)
    if wx_count >= 3:
        wx_branches = sorted([b for b in branches if ZHI_WUXING.get(b, '') == target_wx])
        return {
            'has_formation': True,
            'type': '会方',
            'branches': wx_branches,
            'element': target_wx,
        }
    return {
        'has_formation': False,
        'type': None,
        'branches': [],
        'element': target_wx,
    }


def _check_month_season(month_zhi, target_wx):
    SEASON_MAP = {
        '木': ['寅', '卯', '辰'],
        '火': ['巳', '午', '未'],
        '金': ['申', '酉', '戌'],
        '水': ['亥', '子', '丑'],
        '土': ['辰', '戌', '丑', '未'],
    }
    season_months = SEASON_MAP.get(target_wx, [])
    return {
        'is_season': month_zhi in season_months,
        'season_months': season_months,
    }


def _check_zhuanwang_break(day_master, dm_wx, bazi_parts, gans):
    breaks = []
    KE_WUXING = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}
    ke_wx = KE_WUXING.get(dm_wx, '')
    if ke_wx:
        for g in gans:
            if GAN_WUXING.get(g, '') == ke_wx:
                ss = derive_shishen(day_master, g)
                breaks.append({
                    'type': '官杀逆势',
                    'severity': 'high',
                    'detail': f'天干{g}({ss})克日主{dm_wx}行，逆专旺之势',
                })
    hour_zhi = bazi_parts[3][1] if len(bazi_parts) >= 4 and len(bazi_parts[3]) >= 2 else ''
    if hour_zhi:
        cs_map = SHIER_CHANGSHENG.get(day_master, {})
        cs_status = cs_map.get(hour_zhi, '')
        if cs_status in ('死', '绝', '墓'):
            breaks.append({
                'type': '引至死绝',
                'severity': 'medium',
                'detail': f'时支{hour_zhi}为日主{day_master}{cs_status}地，专旺气泄',
            })
    return breaks


def _check_hua_break(day_master, hua_wx, gans, bazi_parts):
    breaks = []
    he_key = None
    for k in GAN_HE:
        if day_master in k:
            he_key = k
            break
    if he_key is None:
        return breaks
    duo_info = GAN_HE_DUO.get(he_key, {})
    zhenghe_gan = duo_info.get('争合', '')
    duhe_gan = duo_info.get('妒合', '')
    zhenghe_count = sum(1 for g in gans if g == zhenghe_gan)
    if zhenghe_count >= 2:
        breaks.append({'type': '争合', 'severity': 'high',
                       'detail': f'天干出现{zhenghe_count}个{zhenghe_gan}争合{day_master}'})
    if duhe_gan and duhe_gan in gans:
        breaks.append({'type': '妒合', 'severity': 'high',
                       'detail': f'天干{duhe_gan}妒合，与合神同类但阴阳不同'})
    ke_wx = WUXING_KE.get(hua_wx, '')
    if ke_wx:
        ke_gans = [g for g in gans if GAN_WUXING.get(g, '') == ke_wx]
        if ke_gans:
            breaks.append({'type': '克化神', 'severity': 'medium',
                           'detail': f'天干{",".join(ke_gans)}属{ke_wx}克化神{hua_wx}'})
    return breaks


def _build_break_conditions(dm_root_info):
    conditions = []
    if dm_root_info['has_benqi_root'] or dm_root_info['has_zhongqi_root']:
        conditions.append({
            'type': '命逢根气',
            'severity': 'high',
            'detail': '日主有根气，从格不真',
        })
    return conditions


def _check_jianlu_yangren_break(day_master, dm_wx, bazi_parts, gans, pattern_name):
    breaks = []
    if '透正官' in pattern_name:
        has_cai = False
        has_yin = False
        for g in gans:
            if g == day_master:
                continue
            ss = derive_shishen(day_master, g)
            if ss in ('正财', '偏财'):
                has_cai = True
            if ss in ('正印', '偏印'):
                has_yin = True
        if not has_cai and not has_yin:
            breaks.append({
                'type': '孤官无辅',
                'severity': 'medium',
                'detail': '建禄格透正官，天干无财星印星辅佐，官星孤立',
            })
    if '羊刃格' in pattern_name and '透七杀' in pattern_name:
        sha_gans = []
        for g in gans:
            if g == day_master:
                continue
            ss = derive_shishen(day_master, g)
            if ss == '七杀':
                sha_gans.append(g)
        for sha_g in sha_gans:
            for he_pair in GAN_HE:
                if sha_g in he_pair:
                    other_in_pair = he_pair - {sha_g}
                    if other_in_pair:
                        other_g = list(other_in_pair)[0]
                        if other_g in gans:
                            breaks.append({
                                'type': '透刃合煞',
                                'severity': 'high',
                                'detail': f'羊刃格透七杀{sha_g}，天干{other_g}与七杀相合，杀被合去',
                            })
    if '建禄格' in pattern_name:
        sha_wx = KE_MAP.get(dm_wx, '')
        if sha_wx:
            formation = _check_formation(bazi_parts, sha_wx)
            if formation['has_formation']:
                breaks.append({
                    'type': '会杀为凶',
                    'severity': 'high',
                    'detail': f'建禄格地支{formation["type"]}{"".join(formation["branches"])}会{sha_wx}杀，凶',
                })
    return breaks


def _check_zhengge_break(day_master, dm_wx, bazi_parts, gans, pattern_name):
    breaks = []
    shishen_map = {}
    for g in gans:
        if g == day_master:
            continue
        ss = derive_shishen(day_master, g)
        if ss not in shishen_map:
            shishen_map[ss] = []
        shishen_map[ss].append(g)
    if '正官格' in pattern_name:
        if '伤官' in shishen_map:
            breaks.append({
                'type': '伤官见官',
                'severity': 'high',
                'detail': f'正官格天干透伤官{"".join(shishen_map["伤官"])}，伤官见官为祸百端',
            })
    if '财格' in pattern_name:
        if '比肩' in shishen_map or '劫财' in shishen_map:
            has_guansha = '正官' in shishen_map or '七杀' in shishen_map
            if not has_guansha:
                bijie_gans = shishen_map.get('比肩', []) + shishen_map.get('劫财', [])
                breaks.append({
                    'type': '比劫争财',
                    'severity': 'high',
                    'detail': f'财格天干透比劫{"".join(bijie_gans)}，无官杀制比劫，财被争夺',
                })
    if '印格' in pattern_name:
        if '正财' in shishen_map or '偏财' in shishen_map:
            has_guansha = '正官' in shishen_map or '七杀' in shishen_map
            if not has_guansha:
                cai_gans = shishen_map.get('正财', []) + shishen_map.get('偏财', [])
                breaks.append({
                    'type': '财星破印',
                    'severity': 'high',
                    'detail': f'印格天干透财星{"".join(cai_gans)}，无官杀通关，财星破印',
                })
    if '食神格' in pattern_name:
        if '偏印' in shishen_map:
            breaks.append({
                'type': '枭神夺食',
                'severity': 'high',
                'detail': f'食神格天干透偏印{"".join(shishen_map["偏印"])}，枭神夺食',
            })
    if '伤官格' in pattern_name:
        is_jin_dm = day_master in ('庚', '辛')
        if '正官' in shishen_map and not is_jin_dm:
            breaks.append({
                'type': '伤官见官',
                'severity': 'high',
                'detail': f'伤官格天干透正官{"".join(shishen_map["正官"])}，伤官见官为祸百端',
            })
    return breaks


PATTERN_YONGSHEN = {
    '正官格': {'用神': ['财星', '印星'], '忌神': ['伤官', '七杀']},
    '七杀格': {'用神': ['食神', '印星'], '忌神': ['财星(无制时)']},
    '正财格': {'用神': ['食伤', '官星'], '忌神': ['比劫']},
    '偏财格': {'用神': ['食伤', '官星'], '忌神': ['比劫']},
    '正印格': {'用神': ['官星', '比劫(身弱时)'], '忌神': ['财星']},
    '偏印格': {'用神': ['财星', '官星(身弱时)'], '忌神': ['食神(枭夺食)']},
    '食神格': {'用神': ['比劫', '财星'], '忌神': ['偏印']},
    '伤官格': {'用神': ['印星', '财星'], '忌神': ['官星(见官)']},
    '建禄格': {'用神': ['官杀', '财星', '食伤'], '忌神': ['比劫']},
    '月劫格': {'用神': ['官杀', '财星', '食伤'], '忌神': ['比劫']},
    '羊刃格': {'用神': ['官杀'], '忌神': ['财星(无制时)']},
    '从强格': {'用神': ['印比'], '忌神': ['官杀', '财星']},
    '假从强格': {'用神': ['印比'], '忌神': ['官杀', '财星']},
    '从财格': {'用神': ['食伤', '财星'], '忌神': ['比劫', '印星']},
    '从官杀格': {'用神': ['官杀', '财星'], '忌神': ['比劫', '印星']},
    '从儿格': {'用神': ['食伤', '财星'], '忌神': ['印星', '官杀']},
    '从势格': {'用神': ['最强之势'], '忌神': ['逆势五行']},
    '化气格': {'用神': ['化神五行'], '忌神': ['克化神五行']},
}


def screen_pattern(day_master: str, bazi_parts: list[str],
                   wangshuai: dict, element_forces: dict) -> dict:
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx or len(bazi_parts) < 2:
        return {'pattern': '数据不足', 'candidates': [], 'note': '日主或八字数据缺失',
                'trace': {'layers_checked': [], 'layers_missed': ['L0', 'L1', 'L2', 'L3']}}

    month_zhi = bazi_parts[1][1] if len(bazi_parts[1]) >= 2 else ''
    if not month_zhi:
        return {'pattern': '数据不足', 'candidates': [], 'note': '月支缺失',
                'trace': {'layers_checked': [], 'layers_missed': ['L0', 'L1', 'L2', 'L3']}}

    # 格局阈值使用修正前百分比(percent)，非修正后(percent_adjusted)。
    # 合化修正改变了五行分布，但格局框架应在"原局基础力量"上判定；
    # 化气格单独通过 element_forces.hehua 检测，不受此影响。
    pct = element_forces.get('percent', {})
    candidates = []
    gans = [p[0] for p in bazi_parts if len(p) >= 1]
    trace = {'layers_checked': [], 'layers_missed': [], 'layer_details': {}}

    yin_bi_wx = {dm_wx, SHENG_MAP.get(dm_wx, '')}
    yin_bi_pct = sum(pct.get(wx, 0) for wx in yin_bi_wx)

    ke_xie_hao_wx = set()
    for wx in ['木', '火', '土', '金', '水']:
        if wx not in yin_bi_wx:
            ke_xie_hao_wx.add(wx)
    ke_xie_hao_pct = sum(pct.get(wx, 0) for wx in ke_xie_hao_wx)

    layer0_result = _screen_layer0(day_master, dm_wx, month_zhi, bazi_parts,
                                    wangshuai, pct, yin_bi_pct, ke_xie_hao_pct, gans,
                                    element_forces)
    trace['layers_checked'].append('L0')
    if layer0_result:
        candidates.append(layer0_result)
        trace['layer_details']['L0'] = {'hit': True, 'reason': layer0_result['reason']}
        result = _finalize_pattern(candidates, wangshuai)
        result['trace'] = trace
        return result
    trace['layers_missed'].append('L0')
    trace['layer_details']['L0'] = {'hit': False, 'reason': '无专旺/从格/两行成象匹配'}

    layer1_result = _screen_layer1(day_master, month_zhi, gans, bazi_parts)
    trace['layers_checked'].append('L1')
    if layer1_result:
        candidates.append(layer1_result)
        trace['layer_details']['L1'] = {'hit': True, 'reason': layer1_result['reason']}
        result = _finalize_pattern(candidates, wangshuai)
        result['trace'] = trace
        return result
    trace['layers_missed'].append('L1')
    trace['layer_details']['L1'] = {'hit': False, 'reason': '月令本气未透干'}

    layer2_result = _screen_layer2(day_master, month_zhi, gans, bazi_parts)
    trace['layers_checked'].append('L2')
    if layer2_result:
        candidates.append(layer2_result)
        trace['layer_details']['L2'] = {'hit': True, 'reason': layer2_result['reason']}
        result = _finalize_pattern(candidates, wangshuai)
        result['trace'] = trace
        return result
    trace['layers_missed'].append('L2')
    trace['layer_details']['L2'] = {'hit': False, 'reason': '月令中气未透干或本气已透'}

    layer3_result = _screen_layer3(day_master, dm_wx, month_zhi, gans, bazi_parts)
    trace['layers_checked'].append('L3')
    if layer3_result:
        candidates.append(layer3_result)
        trace['layer_details']['L3'] = {'hit': True, 'reason': layer3_result['reason']}
        result = _finalize_pattern(candidates, wangshuai)
        result['trace'] = trace
        return result
    trace['layers_missed'].append('L3')
    trace['layer_details']['L3'] = {'hit': False, 'reason': '月令本气非比劫且已透干'}

    result = {'pattern': '待定', 'candidates': candidates,
              'note': '六层筛查未命中，属特殊格局，需人工复核'}
    result['trace'] = trace
    return result


def _screen_layer0(day_master, dm_wx, month_zhi, bazi_parts,
                   wangshuai, pct, yin_bi_pct, ke_xie_hao_pct, gans,
                   element_forces=None):
    dm_pct = pct.get(dm_wx, 0)

    dm_root_in_branch = _check_dm_root_in_branches(day_master, dm_wx, bazi_parts)

    jianlu_zhi = JIANLU_MAP.get(day_master, '')
    yangren_zhi = YANGREN_MAP.get(day_master, '')
    is_jianlu_yangren_month = month_zhi in (jianlu_zhi, yangren_zhi)
    if element_forces is not None and not is_jianlu_yangren_month:
        hehua = element_forces.get('hehua', {})
        pct_adj = element_forces.get('percent_adjusted', pct)
        for item in hehua.get('gan_he', []):
            if day_master in item['gans'] and item.get('adjacent', False):
                hua_wx = item['hua_wx']
                hua_pct = pct_adj.get(hua_wx, 0)
                if hua_pct >= 60:
                    hua_names = {'土': '化土格', '金': '化金格', '水': '化水格',
                                 '木': '化木格', '火': '化火格'}
                    return {
                        'layer': 0, 'type': '化气格',
                        'pattern': hua_names.get(hua_wx, f'化{hua_wx}格'),
                        'confidence': 0.80,
                        'reason': f'日主{day_master}参与合化，化神{hua_wx}(修正后)占比{hua_pct}%≥60%',
                        'yongshen_direction': f'化神{hua_wx}',
                    }

    zhuanwang_names = {'木': '曲直格', '火': '炎上格', '土': '稼穑格', '金': '从革格', '水': '润下格'}
    zhuanwang_trigger = False
    zhuanwang_reason_base = ''
    if dm_pct >= 80:
        zhuanwang_trigger = True
        zhuanwang_reason_base = f'日主{dm_wx}行占{dm_pct}%≥80%'
    elif dm_pct >= 50 and yin_bi_pct >= 75:
        zhuanwang_trigger = True
        zhuanwang_reason_base = f'日主{dm_wx}行占{dm_pct}%≥50%，印比合计{yin_bi_pct}%≥75%'

    if zhuanwang_trigger:
        formation = _check_formation(bazi_parts, dm_wx)
        if formation['has_formation']:
            season = _check_month_season(month_zhi, dm_wx)
            confidence = 0.90
            if not season['is_season']:
                confidence -= 0.15
            break_conditions = _check_zhuanwang_break(day_master, dm_wx, bazi_parts, gans)
            for bc in break_conditions:
                if bc['severity'] == 'high':
                    confidence -= 0.2
                elif bc['severity'] == 'medium':
                    confidence -= 0.1
            reason = zhuanwang_reason_base + f'，{formation["type"]}{"".join(formation["branches"])}成局'
            if not season['is_season']:
                reason += '，月令不当令'
            return {
                'layer': 0, 'type': '专旺格', 'pattern': zhuanwang_names.get(dm_wx, '专旺格'),
                'confidence': confidence, 'reason': reason,
                'yongshen_direction': '印比',
                'formation': formation,
                'break_conditions': break_conditions,
            }
        else:
            if yin_bi_pct >= 80 and not dm_root_in_branch['has_benqi_root']:
                return {
                    'layer': 0, 'type': '从强格', 'pattern': '从强格',
                    'confidence': 0.85,
                    'reason': zhuanwang_reason_base + '但无方局/三合局，降级为从强格',
                    'yongshen_direction': '印比',
                }
            else:
                return {
                    'layer': 0, 'type': '身旺', 'pattern': '身旺',
                    'confidence': 0.75,
                    'reason': zhuanwang_reason_base + '但无方局/三合局，降级为身旺',
                    'yongshen_direction': '克泄耗',
                }

    if yin_bi_pct >= 80 and not dm_root_in_branch['has_benqi_root']:
        return {
            'layer': 0, 'type': '从强格', 'pattern': '从强格',
            'confidence': 0.85,
            'reason': f'印比合计{yin_bi_pct}%≥80%，地支无本气根（真从强）',
            'yongshen_direction': '印比',
        }

    if not is_jianlu_yangren_month:
        if yin_bi_pct >= 80 and wangshuai.get('is_extreme_strong', False):
            if not dm_root_in_branch['has_benqi_root']:
                return {
                    'layer': 0, 'type': '从强格', 'pattern': '从强格',
                    'confidence': 0.85,
                    'reason': f'印比合计{yin_bi_pct}%≥80%，日主极旺且地支无根（真从强）',
                    'yongshen_direction': '印比',
                }
            else:
                root_info = dm_root_in_branch['root_locations']
                return {
                    'layer': 0, 'type': '身旺',
                    'pattern': '身旺',
                    'confidence': 0.75,
                    'reason': f'印比合计{yin_bi_pct}%≥80%但地支有根（{root_info}），非从强格',
                    'yongshen_direction': '印比',
                }

    YIN_STEMS = {'乙', '丁', '己', '辛', '癸'}
    is_yin_gan = day_master in YIN_STEMS
    if not is_jianlu_yangren_month and not dm_root_in_branch['has_benqi_root']:
        if yin_bi_pct >= 80 and wangshuai.get('is_strong', False):
            if not is_yin_gan and not wangshuai.get('is_extreme_strong', False):
                return {
                    'layer': 0, 'type': '假从强格', 'pattern': '假从强格',
                    'confidence': 0.65,
                    'reason': f'阳干{day_master}天性刚强，虽地支无根但旺衰未至极，假从强格',
                    'yongshen_direction': '印比',
                }
            return {
                'layer': 0, 'type': '从强格', 'pattern': '从强格',
                'confidence': 0.85,
                'reason': f'印比合计{yin_bi_pct}%≥80%，地支无根（阴干{day_master}更易真从）',
                'yongshen_direction': '印比',
            }
        elif yin_bi_pct >= 70 and wangshuai.get('is_strong', False) and is_yin_gan:
            return {
                'layer': 0, 'type': '假从强格', 'pattern': '假从强格',
                'confidence': 0.60,
                'reason': f'阴干{day_master}柔顺，印比{yin_bi_pct}%≥70%，地支无根，假从强格',
                'yongshen_direction': '印比',
            }

    # 两行成象格：克泄耗≥85%且至少2个五行各有势力
    # 若克泄耗仅1行主导(pct>5的不足2个)，自然掉入下方从格检查
    if ke_xie_hao_pct >= 85:
        two_wx = [wx for wx in ['木', '火', '土', '金', '水']
                   if wx not in {dm_wx, SHENG_MAP.get(dm_wx, '')} and pct.get(wx, 0) > 5]
        if len(two_wx) >= 2:
            return {
                'layer': 0, 'type': '两行成象格', 'pattern': f'{two_wx[0]}{two_wx[1]}成象格',
                'confidence': 0.75, 'reason': '克泄耗两行合计≥85%',
                'yongshen_direction': '顺两行气势',
            }

    # 检查地支藏干是否有日主比劫本气根（破从格）
    # 《渊海子平》："命逢根气，命殞无猜"
    has_bijie_benqi_root = False
    for part in bazi_parts:
        if len(part) < 2:
            continue
        for cg, ql in get_canggan(part[1]):
            if GAN_WUXING.get(cg, '') == dm_wx and ql == '本气':
                has_bijie_benqi_root = True
                break
        if has_bijie_benqi_root:
            break

    if wangshuai.get('is_extreme_weak', False) and ke_xie_hao_pct >= 60:
        shishen_counts = _count_shishen_categories(day_master, gans, bazi_parts, include_canggan=False)
        bijie_free = shishen_counts.get('比劫', 0) == 0 and not has_bijie_benqi_root
        if shishen_counts.get('财星', 0) >= 3 and bijie_free:
            cai_wx = WO_KE_MAP.get(dm_wx, '')
            formation = _check_formation(bazi_parts, cai_wx)
            if formation['has_formation']:
                result = {
                    'layer': 0, 'type': '从财格', 'pattern': '从财格',
                    'confidence': 0.85,
                    'reason': f'日主极弱，财星成势，{formation["type"]}{"".join(formation["branches"])}（真从）',
                    'yongshen_direction': '食伤生财',
                    'formation': formation, 'is_true': True,
                }
            else:
                result = {
                    'layer': 0, 'type': '从财格', 'pattern': '从财格',
                    'confidence': 0.65,
                    'reason': '日主极弱，财星成势，地支无财星方局/三合局（假从）',
                    'yongshen_direction': '食伤生财',
                    'formation': formation, 'is_true': False,
                }
            break_conds = _build_break_conditions(dm_root_in_branch)
            if break_conds:
                result['break_conditions'] = break_conds
            return result
        if shishen_counts.get('官杀', 0) >= 3 and bijie_free:
            guan_wx = KE_MAP.get(dm_wx, '')
            formation = _check_formation(bazi_parts, guan_wx)
            if formation['has_formation']:
                result = {
                    'layer': 0, 'type': '从官杀格', 'pattern': '从官杀格',
                    'confidence': 0.85,
                    'reason': f'日主极弱，官杀成势，{formation["type"]}{"".join(formation["branches"])}（真从）',
                    'yongshen_direction': '财生官',
                    'formation': formation, 'is_true': True,
                }
            else:
                result = {
                    'layer': 0, 'type': '从官杀格', 'pattern': '从官杀格',
                    'confidence': 0.65,
                    'reason': '日主极弱，官杀成势，地支无官杀方局/三合局（假从）',
                    'yongshen_direction': '财生官',
                    'formation': formation, 'is_true': False,
                }
            break_conds = _build_break_conditions(dm_root_in_branch)
            if break_conds:
                result['break_conditions'] = break_conds
            return result

    # 从儿格：食伤成势 + 财星承接
    # 《滴天髓》："从儿不管身强弱，只要吾儿又得儿"
    # 不要求极弱，但日主不可身旺有强根
    if ke_xie_hao_pct >= 60:
        shishen_counts = _count_shishen_categories(day_master, gans, bazi_parts, include_canggan=False)
        bijie_free = shishen_counts.get('比劫', 0) == 0 and not has_bijie_benqi_root
        yin_free = shishen_counts.get('印星', 0) == 0
        if shishen_counts.get('食伤', 0) >= 3 and bijie_free and yin_free:
            if shishen_counts.get('财星', 0) >= 1:
                result = {
                    'layer': 0, 'type': '从儿格', 'pattern': '从儿格',
                    'confidence': 0.80,
                    'reason': '食伤成势，财星承接（吾儿又得儿），日主无强根',
                    'yongshen_direction': '食伤生财',
                }
                break_conds = _build_break_conditions(dm_root_in_branch)
                if break_conds:
                    result['break_conditions'] = break_conds
                return result
            else:
                return {
                    'layer': 0, 'type': '食伤泄气', 'pattern': '食伤泄气',
                    'confidence': 0.60,
                    'reason': '食伤成势但无财星承接（吾儿未得儿），降为食伤泄气',
                    'yongshen_direction': '待定',
                }

    # 从势格：日主极弱，克泄耗多类混杂，无单一主导
    # 《滴天髓》："五阴从势无情义"
    if wangshuai.get('is_extreme_weak', False) and ke_xie_hao_pct >= 60:
        shishen_counts = _count_shishen_categories(day_master, gans, bazi_parts, include_canggan=False)
        bijie_free = shishen_counts.get('比劫', 0) == 0 and not has_bijie_benqi_root
        if bijie_free:
            ke_xie_types = [cat for cat in ['财星', '官杀', '食伤']
                           if shishen_counts.get(cat, 0) >= 1]
            no_dominance = all(shishen_counts.get(cat, 0) < 3 for cat in ke_xie_types)
            if len(ke_xie_types) >= 2 and no_dominance:
                result = {
                    'layer': 0, 'type': '从势格', 'pattern': '从势格',
                    'confidence': 0.65,
                    'reason': f'日主极弱，克泄耗{",".join(ke_xie_types)}混杂无单一主导，从势格',
                    'yongshen_direction': '顺势而为',
                }
                break_conds = _build_break_conditions(dm_root_in_branch)
                if break_conds:
                    result['break_conditions'] = break_conds
                return result

    if month_zhi == JIANLU_MAP.get(day_master, ''):
        return None

    if month_zhi == YANGREN_MAP.get(day_master, ''):
        if yin_bi_pct >= 75:
            return {
                'layer': 0, 'type': '从强格', 'pattern': '从强格',
                'confidence': 0.85, 'reason': f'月支羊刃但印比{yin_bi_pct}%≥75%，从强格优先',
                'yongshen_direction': '印比',
            }
        return None

    return None


def _screen_layer1(day_master, month_zhi, gans, bazi_parts):
    dm_wx = GAN_WUXING.get(day_master, '')
    canggan = get_canggan(month_zhi)
    if not canggan:
        return None
    benqi_gan = canggan[0][0]
    if benqi_gan in gans:
        ss = derive_shishen(day_master, benqi_gan)
        if ss in ('比肩', '劫财'):
            return _build_jianlu_yuejie(day_master, dm_wx=dm_wx, month_zhi=month_zhi,
                                        gans=gans, bazi_parts=bazi_parts,
                                        benqi_ss=ss, benqi_gan=benqi_gan,
                                        layer=1, layer_type='月令本气比劫透干')
        pattern_name = f'{ss}格' if ss else '未知格'
        result = {
            'layer': 1, 'type': '月令本气透干', 'pattern': pattern_name,
            'confidence': 0.85, 'reason': f'月支{month_zhi}本气{benqi_gan}透干，十神为{ss}',
            'yongshen_direction': _get_yongshen_direction(ss),
        }
        break_conditions = _check_zhengge_break(day_master, dm_wx, bazi_parts, gans, pattern_name)
        if break_conditions:
            result['break_conditions'] = break_conditions
        return result
    return None


def _screen_layer2(day_master, month_zhi, gans, bazi_parts):
    dm_wx = GAN_WUXING.get(day_master, '')
    canggan = get_canggan(month_zhi)
    if len(canggan) < 2:
        return None
    zhongqi_gan = canggan[1][0]
    benqi_gan = canggan[0][0]
    if benqi_gan in gans:
        return None
    if zhongqi_gan in gans:
        ss = derive_shishen(day_master, zhongqi_gan)
        if ss in ('比肩', '劫财'):
            return _build_jianlu_yuejie(day_master, dm_wx=dm_wx, month_zhi=month_zhi,
                                        gans=gans, bazi_parts=bazi_parts,
                                        benqi_ss=ss, benqi_gan=zhongqi_gan,
                                        layer=2, layer_type='月令中气比劫透干')
        pattern_name = f'{ss}格' if ss else '未知格'
        result = {
            'layer': 2, 'type': '月令中气透干', 'pattern': pattern_name,
            'confidence': 0.75, 'reason': f'月支{month_zhi}中气{zhongqi_gan}透干，十神为{ss}',
            'yongshen_direction': _get_yongshen_direction(ss),
        }
        break_conditions = _check_zhengge_break(day_master, dm_wx, bazi_parts, gans, pattern_name)
        if break_conditions:
            result['break_conditions'] = break_conditions
        return result
    return None


def _classify_bijie_pattern(day_master: str, month_zhi: str, benqi_ss: str) -> str:
    if month_zhi == JIANLU_MAP.get(day_master, ''):
        return '建禄格'
    if month_zhi == YANGREN_MAP.get(day_master, ''):
        return '羊刃格'
    return '月劫格'


def _build_jianlu_yuejie(day_master, dm_wx, month_zhi, gans, bazi_parts,
                          benqi_ss, benqi_gan, layer, layer_type):
    if not dm_wx:
        dm_wx = GAN_WUXING.get(day_master, '')
    pattern_base = _classify_bijie_pattern(day_master, month_zhi, benqi_ss)
    tou_gan_ss = []
    for g in gans:
        if g != day_master:
            ss = derive_shishen(day_master, g)
            if ss in ('正官', '七杀', '正财', '偏财', '食神', '伤官'):
                tou_gan_ss.append(ss)
    pattern_name = f'{pattern_base}，透{tou_gan_ss[0]}' if tou_gan_ss else f'{pattern_base}，无财官煞食透出'
    break_conditions = _check_jianlu_yangren_break(day_master, dm_wx, bazi_parts, gans, pattern_name)
    if tou_gan_ss:
        main_ss = tou_gan_ss[0]
        result = {
            'layer': layer, 'type': layer_type, 'pattern': pattern_name,
            'confidence': 0.70,
            'reason': f'月令{benqi_gan}为{benqi_ss}，{pattern_base}不入正格，透{main_ss}取用',
            'yongshen_direction': _get_yongshen_direction(main_ss),
        }
    else:
        result = {
            'layer': layer, 'type': layer_type, 'pattern': pattern_name,
            'confidence': 0.50,
            'reason': f'月令{benqi_gan}为{benqi_ss}，{pattern_base}不入正格，四天干无财官煞食透出',
            'yongshen_direction': '待定',
        }
    if break_conditions:
        result['break_conditions'] = break_conditions
    return result


def _screen_layer3(day_master, dm_wx, month_zhi, gans, bazi_parts):
    canggan = get_canggan(month_zhi)
    if not canggan:
        return None
    benqi_gan = canggan[0][0]
    benqi_ss = derive_shishen(day_master, benqi_gan)

    if month_zhi == YANGREN_MAP.get(day_master, ''):
        return _build_jianlu_yuejie(day_master, dm_wx, month_zhi, gans, bazi_parts,
                                    benqi_ss='劫财', benqi_gan=benqi_gan,
                                    layer=3, layer_type='羊刃月令')

    if benqi_ss in ('比肩', '劫财'):
        return _build_jianlu_yuejie(day_master, dm_wx, month_zhi, gans, bazi_parts,
                                    benqi_ss=benqi_ss, benqi_gan=benqi_gan,
                                    layer=3, layer_type='比劫月令')

    if benqi_ss and benqi_gan not in gans:
        return {
            'layer': 3, 'type': '暗格', 'pattern': f'{benqi_ss}格',
            'confidence': 0.65,
            'reason': f'月支{month_zhi}本气{benqi_gan}({benqi_ss})不透干，取为暗格',
            'yongshen_direction': _get_yongshen_direction(benqi_ss),
        }

    return None


def _finalize_pattern(candidates, wangshuai):
    best = candidates[0]
    result = {
        'pattern': best['pattern'],
        'candidates': candidates,
        'layer': best['layer'],
        'type': best['type'],
        'confidence': best['confidence'],
        'reason': best['reason'],
        'yongshen_direction': best.get('yongshen_direction', '待定'),
        'wangshuai': wangshuai,
    }
    if 'formation' in best:
        result['formation'] = best['formation']
    if 'break_conditions' in best:
        result['break_conditions'] = best['break_conditions']
    return result
