#!/usr/bin/env python3
"""
bazi-pro 确定性命理计算核心 v5.0
将 SKILL.md 中的旺衰量化、藏干映射、格局筛查、喜用神推导下沉为可测试的 Python 代码。
所有计算均为确定性映射，不依赖 LLM。
"""

from bazi_pro import GAN_WUXING, ZHI_WUXING, derive_shishen

ZHI_CANGGAN = {
    '子': [('癸', '本气')],
    '丑': [('己', '本气'), ('癸', '中气'), ('辛', '余气')],
    '寅': [('甲', '本气'), ('丙', '中气'), ('戊', '余气')],
    '卯': [('乙', '本气')],
    '辰': [('戊', '本气'), ('乙', '中气'), ('癸', '余气')],
    '巳': [('丙', '本气'), ('戊', '中气'), ('庚', '余气')],
    '午': [('丁', '本气'), ('己', '中气')],
    '未': [('己', '本气'), ('丁', '中气'), ('乙', '余气')],
    '申': [('庚', '本气'), ('壬', '中气'), ('戊', '余气')],
    '酉': [('辛', '本气')],
    '戌': [('戊', '本气'), ('辛', '中气'), ('丁', '余气')],
    '亥': [('壬', '本气'), ('甲', '中气')],
}

CANGGAN_WEIGHT = {'本气': 1.0, '中气': 0.6, '余气': 0.3}

SHIER_CHANGSHENG = {
    '甲': {'亥': '长生', '子': '沐浴', '丑': '冠带', '寅': '临官', '卯': '帝旺',
           '辰': '衰', '巳': '病', '午': '死', '未': '墓', '申': '绝', '酉': '胎', '戌': '养'},
    '乙': {'午': '长生', '巳': '沐浴', '辰': '冠带', '卯': '临官', '寅': '帝旺',
           '丑': '衰', '子': '病', '亥': '死', '戌': '墓', '酉': '绝', '申': '胎', '未': '养'},
    '丙': {'寅': '长生', '卯': '沐浴', '辰': '冠带', '巳': '临官', '午': '帝旺',
           '未': '衰', '申': '病', '酉': '死', '戌': '墓', '亥': '绝', '子': '胎', '丑': '养'},
    '丁': {'酉': '长生', '申': '沐浴', '未': '冠带', '午': '临官', '巳': '帝旺',
           '辰': '衰', '卯': '病', '寅': '死', '丑': '墓', '子': '绝', '亥': '胎', '戌': '养'},
    '戊': {'寅': '长生', '卯': '沐浴', '辰': '冠带', '巳': '临官', '午': '帝旺',
           '未': '衰', '申': '病', '酉': '死', '戌': '墓', '亥': '绝', '子': '胎', '丑': '养'},
    '己': {'酉': '长生', '申': '沐浴', '未': '冠带', '午': '临官', '巳': '帝旺',
           '辰': '衰', '卯': '病', '寅': '死', '丑': '墓', '子': '绝', '亥': '胎', '戌': '养'},
    '庚': {'巳': '长生', '午': '沐浴', '未': '冠带', '申': '临官', '酉': '帝旺',
           '戌': '衰', '亥': '病', '子': '死', '丑': '墓', '寅': '绝', '卯': '胎', '辰': '养'},
    '辛': {'子': '长生', '亥': '沐浴', '戌': '冠带', '酉': '临官', '申': '帝旺',
           '未': '衰', '午': '病', '巳': '死', '辰': '墓', '卯': '绝', '寅': '胎', '丑': '养'},
    '壬': {'申': '长生', '酉': '沐浴', '戌': '冠带', '亥': '临官', '子': '帝旺',
           '丑': '衰', '寅': '病', '卯': '死', '辰': '墓', '巳': '绝', '午': '胎', '未': '养'},
    '癸': {'卯': '长生', '寅': '沐浴', '丑': '冠带', '子': '临官', '亥': '帝旺',
           '戌': '衰', '酉': '病', '申': '死', '未': '墓', '午': '绝', '巳': '胎', '辰': '养'},
}

DELING_SCORE = {
    '帝旺': 3, '临官': 3, '长生': 2, '冠带': 1, '沐浴': 1,
    '衰': 0, '病': -1, '死': -2, '墓': -2, '绝': -3, '养': 0, '胎': 0,
}

GAN_HE = {
    frozenset({'甲', '己'}): '土', frozenset({'乙', '庚'}): '金',
    frozenset({'丙', '辛'}): '水', frozenset({'丁', '壬'}): '木',
    frozenset({'戊', '癸'}): '火',
}

ZHI_HE = {
    frozenset({'子', '丑'}): '土', frozenset({'寅', '亥'}): '木',
    frozenset({'卯', '戌'}): '火', frozenset({'辰', '酉'}): '金',
    frozenset({'巳', '申'}): '水', frozenset({'午', '未'}): '土',
}

ZHI_CHONG = {
    frozenset({'子', '午'}), frozenset({'丑', '未'}),
    frozenset({'寅', '申'}), frozenset({'卯', '酉'}),
    frozenset({'辰', '戌'}), frozenset({'巳', '亥'}),
}

ZHI_HAI = {
    frozenset({'子', '未'}), frozenset({'丑', '午'}),
    frozenset({'寅', '巳'}), frozenset({'卯', '辰'}),
    frozenset({'申', '亥'}), frozenset({'酉', '戌'}),
}

ZHI_XING = {
    frozenset({'子', '卯'}), frozenset({'寅', '巳'}),
    frozenset({'丑', '戌'}), frozenset({'未', '戌'}),
    frozenset({'辰', '辰'}), frozenset({'午', '午'}),
    frozenset({'酉', '酉'}), frozenset({'亥', '亥'}),
}

ZHI_SANHE = [
    ({'申', '子', '辰'}, '水'),
    ({'亥', '卯', '未'}, '木'),
    ({'寅', '午', '戌'}, '火'),
    ({'巳', '酉', '丑'}, '金'),
]

ZHI_BANHE = [
    ({'申', '子'}, '水'), ({'子', '辰'}, '水'),
    ({'亥', '卯'}, '木'), ({'卯', '未'}, '木'),
    ({'寅', '午'}, '火'), ({'午', '戌'}, '火'),
    ({'巳', '酉'}, '金'), ({'酉', '丑'}, '金'),
]

WUXING_SHENG = {
    ('木', '火'): True, ('火', '土'): True, ('土', '金'): True,
    ('金', '水'): True, ('水', '木'): True,
}

WUXING_KE = {
    ('木', '土'): True, ('土', '水'): True, ('水', '火'): True,
    ('火', '金'): True, ('金', '木'): True,
}

SHENG_MAP = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
KE_MAP = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}
WO_KE_MAP = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}

JIANLU_MAP = {
    '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午',
    '戊': '巳', '己': '午', '庚': '申', '辛': '酉',
    '壬': '亥', '癸': '子',
}

YANGREN_MAP = {
    '甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子',
}

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

SHISHEN_WUXING_REL = {
    '比肩': '同我', '劫财': '同我',
    '食神': '我生', '伤官': '我生',
    '偏财': '我克', '正财': '我克',
    '七杀': '克我', '正官': '克我',
    '偏印': '生我', '正印': '生我',
}


def get_canggan(zhi: str) -> list[tuple[str, str]]:
    return ZHI_CANGGAN.get(zhi, [])


def calc_deling(day_master: str, month_zhi: str) -> tuple[str, int]:
    changsheng_table = SHIER_CHANGSHENG.get(day_master, {})
    status = changsheng_table.get(month_zhi, '')
    score = DELING_SCORE.get(status, 0)
    return status, score


def calc_dedi(day_master: str, bazi_parts: list[str]) -> dict:
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {'score': 0.0, 'details': [], 'level': '不得地'}

    total = 0.0
    details = []
    for part in bazi_parts:
        if len(part) < 2:
            continue
        zhi = part[1]
        for gan, qi_level in get_canggan(zhi):
            gan_wx = GAN_WUXING.get(gan, '')
            if gan_wx == dm_wx:
                weight = CANGGAN_WEIGHT.get(qi_level, 0)
                total += weight
                details.append({
                    'zhi': zhi, 'canggan_gan': gan, 'qi_level': qi_level,
                    'weight': weight, 'wuxing': gan_wx,
                })

    if total >= 3:
        level = '得地'
    elif total >= 1.5:
        level = '偏得地'
    else:
        level = '不得地'

    return {'score': total, 'details': details, 'level': level}


def calc_deshi(day_master: str, bazi_parts: list[str]) -> dict:
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return {'score': 0.0, 'details': [], 'level': '不得势'}

    total = 0.0
    details = []
    positions = ['年', '月', '日', '时']
    day_idx = -1
    for i, part in enumerate(bazi_parts):
        if len(part) >= 2 and i < 4:
            positions[i]
            if i == 2:
                day_idx = i

    for i, part in enumerate(bazi_parts):
        if len(part) < 1:
            continue
        gan = part[0]
        if gan == day_master:
            continue
        ss = derive_shishen(day_master, gan)
        if ss in ('比肩', '劫财', '正印', '偏印'):
            dist = abs(i - day_idx) if day_idx >= 0 else 2
            score = 2 if dist <= 1 else 1
            total += score
            details.append({
                'position': positions[i] if i < 4 else '',
                'gan': gan, 'shishen': ss, 'distance': dist, 'score': score,
            })

    for part in bazi_parts:
        if len(part) < 2:
            continue
        zhi = part[1]
        for gan, qi_level in get_canggan(zhi):
            if gan == day_master:
                continue
            ss = derive_shishen(day_master, gan)
            if ss in ('比肩', '劫财', '正印', '偏印') and qi_level == '本气':
                total += 1
                details.append({
                    'zhi': zhi, 'canggan_gan': gan, 'shishen': ss,
                    'qi_level': qi_level, 'score': 1,
                })

    if total >= 4:
        level = '得势'
    elif total >= 2:
        level = '偏得势'
    else:
        level = '不得势'

    return {'score': total, 'details': details, 'level': level}


def judge_wangshuai(deling_score: int, dedi_score: float, deshi_score: float) -> dict:
    if deling_score >= 2 and dedi_score >= 3 and deshi_score >= 4:
        verdict = '身旺'
    elif deling_score >= 2 and dedi_score >= 3 and deshi_score < 4:
        verdict = '偏旺'
    elif deling_score >= 2 and dedi_score < 3 and deshi_score >= 4:
        verdict = '偏旺'
    elif deling_score >= 2 and dedi_score < 3 and deshi_score < 4:
        verdict = '中和偏旺'
    elif deling_score <= 0 and dedi_score < 1.5 and deshi_score < 2:
        verdict = '身弱'
    elif 0 <= deling_score <= 1 and dedi_score >= 3 and deshi_score >= 4:
        verdict = '中和偏弱'
    elif 0 <= deling_score <= 1 and dedi_score < 1.5 and deshi_score < 2:
        verdict = '身弱'
    elif deling_score <= -2 and dedi_score < 1.5 and deshi_score == 0:
        verdict = '极弱'
    elif deling_score >= 3 and dedi_score >= 3 and deshi_score >= 6:
        verdict = '极旺'
    else:
        verdict = '中和'

    return {
        'verdict': verdict,
        'deling_score': deling_score,
        'dedi_score': dedi_score,
        'deshi_score': deshi_score,
        'is_weak': '弱' in verdict,
        'is_strong': '旺' in verdict or '强' in verdict,
        'is_extreme_weak': verdict == '极弱',
        'is_extreme_strong': verdict == '极旺',
    }


def calc_element_forces(bazi_parts: list[str], month_zhi: str) -> dict:
    forces = {'木': 0.0, '火': 0.0, '土': 0.0, '金': 0.0, '水': 0.0}

    for i, part in enumerate(bazi_parts):
        if len(part) < 2:
            continue
        gan, zhi = part[0], part[1]

        gan_wx = GAN_WUXING.get(gan, '')
        if gan_wx:
            has_root = False
            for p2 in bazi_parts:
                if len(p2) < 2:
                    continue
                for cg, ql in get_canggan(p2[1]):
                    if GAN_WUXING.get(cg, '') == gan_wx and ql in ('本气', '中气'):
                        has_root = True
                        break
                if has_root:
                    break
            forces[gan_wx] += 1.2 if has_root else 0.5

        for cg, ql in get_canggan(zhi):
            cg_wx = GAN_WUXING.get(cg, '')
            if not cg_wx:
                continue
            weight = CANGGAN_WEIGHT.get(ql, 0)
            if i == 1 and ql == '本气':
                weight *= 1.5
            forces[cg_wx] += weight

    total = max(0.01, sum(forces.values()))
    pct = {k: round(v / total * 100, 1) for k, v in forces.items()}
    return {'raw': forces, 'percent': pct, 'total': round(total, 2)}


def detect_relations(bazi_parts: list[str]) -> list[dict]:
    relations = []
    gans = [p[0] for p in bazi_parts if len(p) >= 1]
    zhis = [p[1] for p in bazi_parts if len(p) >= 2]

    for i in range(len(gans)):
        for j in range(i + 1, len(gans)):
            pair = frozenset({gans[i], gans[j]})
            if pair in GAN_HE:
                he_wx = GAN_HE[pair]
                relations.append({
                    'type': '天干合', 'elements': [gans[i], gans[j]],
                    'result': f'{gans[i]}合{gans[j]}→化{he_wx}',
                    'hua_wuxing': he_wx,
                })

    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            pair = frozenset({zhis[i], zhis[j]})
            if pair in ZHI_CHONG:
                relations.append({
                    'type': '地支冲', 'elements': [zhis[i], zhis[j]],
                    'result': f'{zhis[i]}冲{zhis[j]}',
                })
            if pair in ZHI_HE:
                he_wx = ZHI_HE[pair]
                relations.append({
                    'type': '地支合', 'elements': [zhis[i], zhis[j]],
                    'result': f'{zhis[i]}合{zhis[j]}→化{he_wx}',
                    'hua_wuxing': he_wx,
                })
            if pair in ZHI_HAI:
                relations.append({
                    'type': '地支害', 'elements': [zhis[i], zhis[j]],
                    'result': f'{zhis[i]}害{zhis[j]}',
                })
            if pair in ZHI_XING:
                relations.append({
                    'type': '地支刑', 'elements': [zhis[i], zhis[j]],
                    'result': f'{zhis[i]}刑{zhis[j]}',
                })

    zhi_set = set(zhis)
    for group, he_wx in ZHI_SANHE:
        if group.issubset(zhi_set):
            relations.append({
                'type': '三合局', 'elements': sorted(group),
                'result': f'{" ".join(sorted(group))} 三合成{he_wx}局',
                'hua_wuxing': he_wx,
            })

    return relations


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


def _count_shishen_categories(day_master, gans, bazi_parts):
    counts = {'官杀': 0, '财星': 0, '食伤': 0, '印星': 0, '比劫': 0}
    for g in gans:
        ss = derive_shishen(day_master, g)
        if ss in ('正官', '七杀'):
            counts['官杀'] += 1
        elif ss in ('正财', '偏财'):
            counts['财星'] += 1
        elif ss in ('食神', '伤官'):
            counts['食伤'] += 1
        elif ss in ('正印', '偏印'):
            counts['印星'] += 1
        elif ss in ('比肩', '劫财'):
            counts['比劫'] += 1
    return counts


def _get_yongshen_direction(shishen: str) -> str:
    direction_map = {
        '正官': '财印', '七杀': '食印', '正财': '食官', '偏财': '食官',
        '正印': '官比', '偏印': '财官', '食神': '比财', '伤官': '印财',
        '比肩': '官食', '劫财': '官杀',
    }
    return direction_map.get(shishen, '待定')


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
