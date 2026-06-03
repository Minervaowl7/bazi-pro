from bazi_pro.core import (
    CANGGAN_WEIGHT,
    DELING_SCORE,
    GAN_WUXING,
    KE_MAP,
    SHENG_MAP,
    SHIER_CHANGSHENG,
    WO_KE_MAP,
    WO_SHENG_MAP,
    ZHI_CHONG,
    ZHI_HAI,
    ZHI_HE,
    ZHI_WUXING,
    ZHI_XING,
    derive_shishen,
    full_analysis,
)
from bazi_pro.core.schools import register_school
from bazi_pro.core.schools.base import SchoolAnalyzer

# 盲派体用分类 — 依据段建业《盲派初级命理学》
# "我们把日主、印星、禄神、比劫当体，财星、官杀星当用"
# "食神与伤官既可以是体，也可以是用……食神更近于体，伤官则接近于用"
TI_STEMS = {'比肩', '劫财', '正印', '偏印', '食神'}
YONG_STEMS = {'正财', '偏财', '正官', '七杀', '伤官'}

KE_PAIRS = {('木', '土'), ('土', '水'), ('水', '火'), ('火', '金'), ('金', '木')}
SHENG_PAIRS = {('木', '火'), ('火', '土'), ('土', '金'), ('金', '水'), ('水', '木')}

# 墓库收神表 — 依据段建业《盲派初级命理学》
# 辰墓收水：亥（水长生）、丑（水余气/金库）、未（火余气）均可入辰墓
# 戌墓收火：巳（火长生）、未（火余气/木库）可入戌墓
# 丑墓收金：申（金长生）、酉（金旺地）可入丑墓
# 未墓收木：寅（木长生）、卯（木旺地）可入未墓
MU_KU = {
    '辰': {'wx': '水', 'collects': {'亥', '丑', '未'}},
    '戌': {'wx': '火', 'collects': {'巳', '未'}},
    '丑': {'wx': '金', 'collects': {'申', '酉'}},
    '未': {'wx': '木', 'collects': {'寅', '卯'}},
}

SHI_PARTIES = [
    {'name': '木火势', 'wx': ['木', '火']},
    {'name': '金水势', 'wx': ['金', '水']},
    {'name': '水木势', 'wx': ['水', '木']},
    {'name': '火燥土势', 'wx': ['火', '土'], 'sub_cond': {'土': ['戌', '未']}},
    {'name': '金湿土势', 'wx': ['金', '土'], 'sub_cond': {'土': ['丑', '辰']}},
    {'name': '水湿土势', 'wx': ['水', '土'], 'sub_cond': {'土': ['丑', '辰']}},
]


def _shishen_to_wuxing(day_master: str, shishen: str) -> str:
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return ''
    if shishen in ('比肩', '劫财'):
        return dm_wx
    if shishen in ('食神', '伤官'):
        return WO_SHENG_MAP.get(dm_wx, '')
    if shishen in ('正财', '偏财'):
        return WO_KE_MAP.get(dm_wx, '')
    if shishen in ('正官', '七杀'):
        return KE_MAP.get(dm_wx, '')
    if shishen in ('正印', '偏印'):
        return SHENG_MAP.get(dm_wx, '')
    return ''


class MangpaiAnalyzer(SchoolAnalyzer):
    @property
    def name(self) -> str:
        return "mangpai"

    @property
    def description(self) -> str:
        return "盲派 - 做功/宾主/象法，源自民间盲派命理传统，以体用、宾主、做功为核心分析方法"

    def analyze(self, mcp_json: dict) -> dict:
        result = full_analysis(mcp_json)
        if result.get('status') != 'completed':
            return {'status': 'error', 'school': 'mangpai', 'message': '核心分析失败'}

        day_master = result.get('day_master', '')

        binzhu = self._analyze_binzhu(day_master, result)
        tiyong = self._analyze_tiyong(day_master, result)
        zuogong = self._analyze_zuogong(day_master, result)
        gongli = self._evaluate_gongli(zuogong, tiyong, day_master, result)
        yingqi = self._predict_yingqi(zuogong, result, tiyong)
        zeishen = self._analyze_zeishen(tiyong, day_master, result)
        shi = self._analyze_shi(result)
        summary = self._generate_summary(binzhu, tiyong, zuogong, gongli, zeishen, shi)

        return {
            'status': 'completed',
            'school': 'mangpai',
            'school_name': '盲派',
            'binzhu': binzhu,
            'tiyong': tiyong,
            'zuogong': zuogong,
            'gongli': gongli,
            'yingqi': yingqi,
            'zeishen': zeishen,
            'shi': shi,
            'summary': summary,
        }

    def _analyze_binzhu(self, day_master: str, result: dict) -> dict:
        pillars = result.get('pillars', [])

        bin_positions = []
        zhu_positions = []

        for p in pillars:
            pos = p.get('position', '')
            if pos in ('年', '月'):
                bin_positions.append(p)
            elif pos in ('日', '时'):
                zhu_positions.append(p)

        bin_shishen = []
        for p in bin_positions:
            shishen = p.get('shishen', '')
            gan = p.get('gan', '')
            if shishen:
                bin_shishen.append({
                    'position': p.get('position', ''),
                    'gan': gan,
                    'shishen': shishen,
                    'wuxing': _shishen_to_wuxing(day_master, shishen),
                })
            for cg in p.get('canggan', []):
                cg_shishen = cg.get('shishen', '')
                if cg_shishen:
                    bin_shishen.append({
                        'position': p.get('position', '') + '藏',
                        'gan': cg.get('gan', ''),
                        'shishen': cg_shishen,
                        'wuxing': _shishen_to_wuxing(day_master, cg_shishen),
                    })

        zhu_shishen = []
        for p in zhu_positions:
            shishen = p.get('shishen', '')
            gan = p.get('gan', '')
            if shishen:
                zhu_shishen.append({
                    'position': p.get('position', ''),
                    'gan': gan,
                    'shishen': shishen,
                    'wuxing': _shishen_to_wuxing(day_master, shishen),
                })
            for cg in p.get('canggan', []):
                cg_shishen = cg.get('shishen', '')
                if cg_shishen:
                    zhu_shishen.append({
                        'position': p.get('position', '') + '藏',
                        'gan': cg.get('gan', ''),
                        'shishen': cg_shishen,
                        'wuxing': _shishen_to_wuxing(day_master, cg_shishen),
                    })

        interpretations = []
        for bs in bin_shishen:
            bs_wx = bs.get('wuxing', '')
            bs_ss = bs.get('shishen', '')
            for zs in zhu_shishen:
                zs_wx = zs.get('wuxing', '')
                zs_ss = zs.get('shishen', '')
                if not bs_wx or not zs_wx:
                    continue
                if (bs_wx, zs_wx) in KE_PAIRS:
                    if bs_ss in ('正官', '七杀'):
                        meaning = '宾位官星克主，可能为贵亦可能为官灾，需看做功效率'
                    elif bs_ss in ('正财', '偏财'):
                        meaning = '宾位财星克主，可能为富亦可能为财累，需看做功效率'
                    else:
                        meaning = '宾克主，意义取决于具体十神与做功效率'
                    interpretations.append({
                        'type': '宾主交战',
                        'bin': bs,
                        'zhu': zs,
                        'relation': '宾克主',
                        'meaning': meaning,
                    })
                elif (zs_wx, bs_wx) in KE_PAIRS:
                    if zs_ss in ('比肩', '劫财'):
                        meaning = '主位比劫克宾，可能为富亦可能为破财，需看做功效率'
                    elif zs_ss in ('食神', '伤官'):
                        meaning = '主位食伤克宾，可能为才华施展亦可能为耗泄，需看做功效率'
                    else:
                        meaning = '主克宾，意义取决于具体十神与做功效率'
                    interpretations.append({
                        'type': '宾主交战',
                        'bin': bs,
                        'zhu': zs,
                        'relation': '主克宾',
                        'meaning': meaning,
                    })

        return {
            'bin': bin_shishen,
            'zhu': zhu_shishen,
            'interpretations': interpretations,
        }

    def _analyze_tiyong(self, day_master: str, result: dict) -> dict:
        pillars = result.get('pillars', [])

        ti_items = []
        yong_items = []

        for p in pillars:
            gan = p.get('gan', '')
            gan_shishen = p.get('shishen', '')
            if gan_shishen in TI_STEMS:
                ti_items.append({
                    'position': p.get('position', ''),
                    'gan': gan,
                    'shishen': gan_shishen,
                    'wuxing': _shishen_to_wuxing(day_master, gan_shishen),
                    'source': '天干',
                })
            elif gan_shishen in YONG_STEMS:
                yong_items.append({
                    'position': p.get('position', ''),
                    'gan': gan,
                    'shishen': gan_shishen,
                    'wuxing': _shishen_to_wuxing(day_master, gan_shishen),
                    'source': '天干',
                })

            for cg in p.get('canggan', []):
                cg_shishen = cg.get('shishen', '')
                cg_gan = cg.get('gan', '')
                if cg_shishen in TI_STEMS:
                    ti_items.append({
                        'position': p.get('position', '') + '藏',
                        'gan': cg_gan,
                        'shishen': cg_shishen,
                        'wuxing': _shishen_to_wuxing(day_master, cg_shishen),
                        'source': '藏干',
                    })
                elif cg_shishen in YONG_STEMS:
                    yong_items.append({
                        'position': p.get('position', '') + '藏',
                        'gan': cg_gan,
                        'shishen': cg_shishen,
                        'wuxing': _shishen_to_wuxing(day_master, cg_shishen),
                        'source': '藏干',
                    })

        seen_ti = set()
        deduped_ti = []
        for x in ti_items:
            key = (x['position'], x['gan'])
            if key not in seen_ti:
                seen_ti.add(key)
                deduped_ti.append(x)

        seen_yong = set()
        deduped_yong = []
        for x in yong_items:
            key = (x['position'], x['gan'])
            if key not in seen_yong:
                seen_yong.add(key)
                deduped_yong.append(x)

        ti_strength = self._calc_strength(deduped_ti, result)
        yong_strength = self._calc_strength(deduped_yong, result)

        return {
            'ti': deduped_ti,
            'yong': deduped_yong,
            'ti_strength': ti_strength,
            'yong_strength': yong_strength,
        }

    def _analyze_zuogong(self, day_master: str, result: dict) -> dict:
        pillars = result.get('pillars', [])
        relations = result.get('relations', [])

        gong_types = {
            'zhiyong': [],
            'huayong': [],
            'shengyong': [],
            'heyong': [],
            'muyong': [],
            'fuhe': [],
        }

        for p in pillars:
            gan = p.get('gan', '')
            gan_wx = GAN_WUXING.get(gan, '')
            gan_shishen = p.get('shishen', '')

            canggan_list = p.get('canggan', [])

            for cg_item in canggan_list:
                cg = cg_item.get('gan', '')
                cg_wx = GAN_WUXING.get(cg, '')
                cg_shishen = derive_shishen(day_master, cg)

                if gan_shishen in TI_STEMS and cg_shishen in YONG_STEMS:
                    if (gan_wx, cg_wx) in KE_PAIRS:
                        gong_types['zhiyong'].append({
                            'type': '制用',
                            'tool': {'position': p.get('position', ''), 'gan': gan,
                                     'shishen': gan_shishen, 'wuxing': gan_wx},
                            'target': {'position': p.get('position', '') + '藏',
                                       'gan': cg, 'shishen': cg_shishen, 'wuxing': cg_wx},
                            'description': '{}{}({})制{}({})'.format(gan_shishen, gan, gan, cg_shishen, cg),
                        })

                if gan_shishen in TI_STEMS and cg_shishen in YONG_STEMS:
                    if (gan_wx, cg_wx) in SHENG_PAIRS:
                        gong_types['shengyong'].append({
                            'type': '生用',
                            'tool': {'position': p.get('position', ''), 'gan': gan,
                                     'shishen': gan_shishen, 'wuxing': gan_wx},
                            'target': {'position': p.get('position', '') + '藏',
                                       'gan': cg, 'shishen': cg_shishen, 'wuxing': cg_wx},
                            'description': '{}{}({})生{}({})'.format(gan_shishen, gan, gan, cg_shishen, cg),
                        })

                if gan_shishen in YONG_STEMS and cg_shishen in TI_STEMS:
                    if (gan_wx, cg_wx) in SHENG_PAIRS:
                        gong_types['huayong'].append({
                            'type': '化用',
                            'tool': {'position': p.get('position', '') + '藏',
                                     'gan': cg, 'shishen': cg_shishen, 'wuxing': cg_wx},
                            'target': {'position': p.get('position', ''), 'gan': gan,
                                       'shishen': gan_shishen, 'wuxing': gan_wx},
                            'description': '{}({})化泄{}{}({})'.format(cg_shishen, cg, gan_shishen, gan, gan),
                        })

            if gan_shishen in {'食神', '伤官'}:
                for cg_item in canggan_list:
                    cg = cg_item.get('gan', '')
                    cg_wx = GAN_WUXING.get(cg, '')
                    cg_shishen = derive_shishen(day_master, cg)
                    if cg_shishen in {'七杀', '正官'}:
                        if (gan_wx, cg_wx) in KE_PAIRS:
                            gong_types['zhiyong'].append({
                                'type': '制用',
                                'tool': {'position': p.get('position', ''), 'gan': gan,
                                         'shishen': gan_shishen, 'wuxing': gan_wx},
                                'target': {'position': p.get('position', '') + '藏',
                                           'gan': cg, 'shishen': cg_shishen, 'wuxing': cg_wx},
                                'description': '{}{}({})制{}({})'.format(gan_shishen, gan, gan, cg_shishen, cg),
                            })

        for rel in relations:
            rel_type = rel.get('type', '')
            if rel_type == '天干合':
                gans = rel.get('elements', [])
                if len(gans) == 2:
                    g1, g2 = gans[0], gans[1]
                    ss1 = derive_shishen(day_master, g1)
                    ss2 = derive_shishen(day_master, g2)
                    wx1 = GAN_WUXING.get(g1, '')
                    wx2 = GAN_WUXING.get(g2, '')
                    if ss1 in TI_STEMS and ss2 in YONG_STEMS:
                        gong_types['heyong'].append({
                            'type': '合用',
                            'tool': {'gan': g1, 'shishen': ss1, 'wuxing': wx1},
                            'target': {'gan': g2, 'shishen': ss2, 'wuxing': wx2},
                            'description': '{}{}({})合{}({})为我用'.format(ss1, g1, g1, ss2, g2),
                        })
                    elif ss2 in TI_STEMS and ss1 in YONG_STEMS:
                        gong_types['heyong'].append({
                            'type': '合用',
                            'tool': {'gan': g2, 'shishen': ss2, 'wuxing': wx2},
                            'target': {'gan': g1, 'shishen': ss1, 'wuxing': wx1},
                            'description': '{}{}({})合{}({})为我用'.format(ss2, g2, g2, ss1, g1),
                        })

        self._detect_dizhi_zuogong(pillars, day_master, gong_types)
        self._detect_muyong(pillars, gong_types)
        self._detect_fuhe(gong_types)

        return gong_types

    def _detect_dizhi_zuogong(self, pillars: list, day_master: str, gong_types: dict) -> None:
        """地支间做功：冲、穿(害)、合、刑——盲派做功以地支为主"""
        zhu_zhis = []
        bin_zhis = []
        for p in pillars:
            pos = p.get('position', '')
            zhi = p.get('zhi', '')
            if not zhi:
                continue
            if pos in ('日', '时'):
                zhu_zhis.append((pos, zhi))
            elif pos in ('年', '月'):
                bin_zhis.append((pos, zhi))

        for zhu_pos, zhu_zhi in zhu_zhis:
            zhu_wx = ZHI_WUXING.get(zhu_zhi, '')
            for bin_pos, bin_zhi in bin_zhis:
                bin_wx = ZHI_WUXING.get(bin_zhi, '')
                pair = frozenset({zhu_zhi, bin_zhi})

                if pair in ZHI_CHONG:
                    gong_types['zhiyong'].append({
                        'type': '制用',
                        'tool': {'position': zhu_pos, 'zhi': zhu_zhi, 'wuxing': zhu_wx},
                        'target': {'position': bin_pos, 'zhi': bin_zhi, 'wuxing': bin_wx},
                        'description': '主位{}冲宾位{}（地支冲做功）'.format(zhu_zhi, bin_zhi),
                        'mechanism': '地支冲',
                    })

                if pair in ZHI_HAI:
                    gong_types['zhiyong'].append({
                        'type': '制用',
                        'tool': {'position': zhu_pos, 'zhi': zhu_zhi, 'wuxing': zhu_wx},
                        'target': {'position': bin_pos, 'zhi': bin_zhi, 'wuxing': bin_wx},
                        'description': '主位{}穿宾位{}（地支穿做功）'.format(zhu_zhi, bin_zhi),
                        'mechanism': '地支穿',
                    })

                if pair in ZHI_HE:
                    he_wx = ZHI_HE[pair]
                    gong_types['heyong'].append({
                        'type': '合用',
                        'tool': {'position': zhu_pos, 'zhi': zhu_zhi, 'wuxing': zhu_wx},
                        'target': {'position': bin_pos, 'zhi': bin_zhi, 'wuxing': bin_wx},
                        'description': '主位{}合宾位{}化{}（地支合做功）'.format(
                            zhu_zhi, bin_zhi, he_wx),
                        'mechanism': '地支合',
                    })

                if pair in ZHI_XING:
                    gong_types['zhiyong'].append({
                        'type': '制用',
                        'tool': {'position': zhu_pos, 'zhi': zhu_zhi, 'wuxing': zhu_wx},
                        'target': {'position': bin_pos, 'zhi': bin_zhi, 'wuxing': bin_wx},
                        'description': '主位{}刑宾位{}（地支刑做功）'.format(zhu_zhi, bin_zhi),
                        'mechanism': '地支刑',
                    })

    def _detect_muyong(self, pillars: list, gong_types: dict) -> None:
        zhu_zhis = []
        bin_zhis = []
        for p in pillars:
            pos = p.get('position', '')
            zhi = p.get('zhi', '')
            if pos in ('日', '时'):
                zhu_zhis.append((pos, zhi))
            elif pos in ('年', '月'):
                bin_zhis.append((pos, zhi))

        for zhu_pos, zhu_zhi in zhu_zhis:
            if zhu_zhi not in MU_KU:
                continue
            ku_info = MU_KU[zhu_zhi]
            collects = ku_info['collects']
            for bin_pos, bin_zhi in bin_zhis:
                if bin_zhi in collects:
                    gong_types['muyong'].append({
                        'type': '墓用',
                        'tool': {'position': zhu_pos, 'zhi': zhu_zhi,
                                 'wuxing': ZHI_WUXING.get(zhu_zhi, '')},
                        'target': {'position': bin_pos, 'zhi': bin_zhi,
                                   'wuxing': ZHI_WUXING.get(bin_zhi, '')},
                        'description': '主位{}收宾位{}入墓（{}库收{}）'.format(
                            zhu_zhi, bin_zhi, zhu_zhi, ku_info['wx']),
                    })

    def _detect_fuhe(self, gong_types: dict) -> None:
        active_types = []
        for gtype in ('zhiyong', 'huayong', 'shengyong', 'heyong', 'muyong'):
            if gong_types.get(gtype):
                active_types.append(gtype)

        if len(active_types) >= 2:
            desc_parts = []
            for gtype in active_types:
                count = len(gong_types[gtype])
                type_name = gong_types[gtype][0].get('type', gtype)
                desc_parts.append('{}{}次'.format(type_name, count))
            gong_types['fuhe'].append({
                'type': '复合结构',
                'combined_types': active_types,
                'description': '命局存在复合做功：' + '、'.join(desc_parts),
            })

    def _evaluate_gongli(self, zuogong: dict, tiyong: dict, day_master: str, result: dict) -> dict:
        all_gong = []
        for gong_list in zuogong.values():
            all_gong.extend(gong_list)

        if not all_gong:
            return {
                'level': '无功',
                'score': 0,
                'analysis': '命局中缺乏有效做功组合',
                'gongshen': [],
                'feishen': [],
            }

        ti_strength = tiyong.get('ti_strength', 0)
        yong_strength = tiyong.get('yong_strength', 0)

        tool_count = len(all_gong)

        if tool_count >= 3 and ti_strength > yong_strength:
            level = '高功'
            score = 85
        elif tool_count >= 2 and ti_strength >= yong_strength:
            level = '中功'
            score = 70
        elif tool_count >= 1:
            level = '低功'
            score = 50
        else:
            level = '无功'
            score = 0

        analysis_parts = ['做功项目数：{}'.format(tool_count)]
        if ti_strength > yong_strength:
            analysis_parts.append('体强于用，做功效率高')
        elif ti_strength < yong_strength:
            analysis_parts.append('用强于体，做功效率低')
        else:
            analysis_parts.append('体用相当，做功效率中等')

        gongshen_set = set()
        for g in all_gong:
            tool = g.get('tool', {})
            target = g.get('target', {})
            for item in (tool, target):
                gan = item.get('gan', '')
                zhi = item.get('zhi', '')
                pos = item.get('position', '')
                if gan:
                    gongshen_set.add((gan, pos))
                if zhi:
                    gongshen_set.add((zhi, pos))

        gongshen = []
        for gan, pos in gongshen_set:
            shishen = derive_shishen(day_master, gan) if gan else ''
            gongshen.append({'gan': gan, 'position': pos, 'shishen': shishen})

        feishen = []
        for p in result.get('pillars', []):
            gan = p.get('gan', '')
            pos = p.get('position', '')
            if gan and (gan, pos) not in gongshen_set:
                shishen = p.get('shishen', '')
                feishen.append({'gan': gan, 'position': pos, 'shishen': shishen})
            for cg in p.get('canggan', []):
                cg_gan = cg.get('gan', '')
                cg_pos = pos + '藏'
                if cg_gan and (cg_gan, cg_pos) not in gongshen_set:
                    cg_shishen = cg.get('shishen', '')
                    feishen.append({'gan': cg_gan, 'position': cg_pos, 'shishen': cg_shishen})

        return {
            'level': level,
            'score': score,
            'analysis': '，'.join(analysis_parts),
            'gongshen': gongshen,
            'feishen': feishen,
        }

    def _predict_yingqi(self, zuogong: dict, result: dict, tiyong: dict) -> dict:
        all_gong = []
        for gong_list in zuogong.values():
            all_gong.extend(gong_list)

        if not all_gong:
            return {'triggers': [], 'note': '无功可应'}

        triggers = []
        relations = result.get('relations', [])

        gong_zhis = set()
        for g in all_gong:
            tool_pos = g.get('tool', {}).get('position', '')
            if '藏' in tool_pos:
                tool_pos = tool_pos.replace('藏', '')
            if tool_pos in ('年', '月', '日', '时'):
                for p in result.get('pillars', []):
                    if p.get('position', '') == tool_pos:
                        gong_zhis.add(p.get('zhi', ''))

        for rel in relations:
            rel_type = rel.get('type', '')
            rel_elements = rel.get('elements', [])
            if rel_type in ('地支冲', '地支合', '地支刑', '地支害'):
                for zhi in rel_elements:
                    if zhi in gong_zhis:
                        triggers.append({
                            'type': rel_type,
                            'zhi': zhi,
                            'description': '大运/流年{}时引动做功'.format(rel.get('result', '')),
                        })

        zeishen_items = tiyong.get('yong', [])
        for ys in zeishen_items:
            gan = ys.get('gan', '')
            pos = ys.get('position', '')
            if gan:
                triggers.append({
                    'type': '出现为应',
                    'zhi': gan,
                    'description': '贼神{}在大运流年出现时为应期'.format(gan),
                })

        pillars = result.get('pillars', [])
        for p in pillars:
            zhi = p.get('zhi', '')
            pos = p.get('position', '')
            for p2 in pillars:
                gan2 = p2.get('gan', '')
                gan2_wx = GAN_WUXING.get(gan2, '')
                zhi_wx = ZHI_WUXING.get(zhi, '')
                if gan2_wx and zhi_wx and gan2_wx == zhi_wx:
                    triggers.append({
                        'type': '反客为主',
                        'zhi': zhi,
                        'description': '太岁天干与{}支{}见比时确定应期'.format(pos, zhi),
                    })

        return {
            'triggers': triggers[:10],
            'note': '大运地支与原局做功地支发生冲合刑害时为应期；贼神出现为应；太岁见比反客为主' if triggers else '待大运流年引动',
        }

    def _analyze_zeishen(self, tiyong: dict, day_master: str, result: dict) -> dict:
        yong_items = tiyong.get('yong', [])
        ti_items = tiyong.get('ti', [])

        if not yong_items or not ti_items:
            return {'is_zeishen_pattern': False, 'bushen': [], 'zeishen': [], 'yingqi_note': ''}

        # 《盲派初级命理学》："如果这个主或者体比较旺，宾或者用相对弱，
        # 那么这时候，我们就把它们叫做贼神和捕神"
        # 条件：体旺 + 用弱 → 贼神捕神格局
        ti_strength = self._calc_strength(ti_items, result)
        yong_strength = self._calc_strength(yong_items, result)
        is_zeishen_pattern = ti_strength > yong_strength and len(yong_items) > 0

        bushen = []
        zeishen = []

        if is_zeishen_pattern:
            for item in ti_items:
                bushen.append({
                    'gan': item.get('gan', ''),
                    'shishen': item.get('shishen', ''),
                    'wuxing': item.get('wuxing', ''),
                    'position': item.get('position', ''),
                })
            for item in yong_items:
                zeishen.append({
                    'gan': item.get('gan', ''),
                    'shishen': item.get('shishen', ''),
                    'wuxing': item.get('wuxing', ''),
                    'position': item.get('position', ''),
                })

        yingqi_note = ''
        if is_zeishen_pattern and zeishen:
            zeishen_names = '、'.join([z.get('shishen', '') for z in zeishen])
            yingqi_note = '贼神（{}）在大运流年出现时为应期，如小偷出现时警察才能抓'.format(zeishen_names)

        return {
            'is_zeishen_pattern': is_zeishen_pattern,
            'bushen': bushen,
            'zeishen': zeishen,
            'yingqi_note': yingqi_note,
        }

    def _analyze_shi(self, result: dict) -> dict:
        pillars = result.get('pillars', [])
        zhi_list = []
        for p in pillars:
            zhi = p.get('zhi', '')
            if zhi:
                zhi_list.append({'zhi': zhi, 'position': p.get('position', '')})
            for cg in p.get('canggan', []):
                cg_gan = cg.get('gan', '')
                if cg_gan:
                    zhi_list.append({'zhi': cg_gan, 'position': p.get('position', '') + '藏'})

        wx_count = {'木': 0, '火': 0, '金': 0, '水': 0, '土': 0}
        wx_elements = {'木': [], '火': [], '金': [], '水': [], '土': []}

        for item in zhi_list:
            zhi = item.get('zhi', '')
            wx = ZHI_WUXING.get(zhi, '') or GAN_WUXING.get(zhi, '')
            if wx and wx in wx_count:
                wx_count[wx] += 1
                wx_elements[wx].append({'zhi': zhi, 'position': item.get('position', ''), 'wuxing': wx})

        dominant_shi = ''
        shi_type = ''
        shi_elements = []

        for party in SHI_PARTIES:
            party_name = party['name']
            party_wx_list = party['wx']
            sub_cond = party.get('sub_cond', {})

            total = 0
            party_elems = []
            meets_sub_cond = True

            for wx in party_wx_list:
                count = wx_count.get(wx, 0)
                if sub_cond and wx in sub_cond:
                    allowed_zhis = sub_cond[wx]
                    filtered = [e for e in wx_elements.get(wx, []) if e['zhi'] in allowed_zhis]
                    count = len(filtered)
                    party_elems.extend(filtered)
                else:
                    party_elems.extend(wx_elements.get(wx, []))
                total += count

            if total >= 3 and meets_sub_cond:
                dominant_shi = party_name
                shi_type = party_name
                shi_elements = party_elems
                break

        if not dominant_shi:
            single_wx = max(wx_count, key=wx_count.get)
            if wx_count[single_wx] >= 3:
                dominant_shi = single_wx + '势'
                shi_type = single_wx + '势'
                shi_elements = wx_elements.get(single_wx, [])

        return {
            'dominant_shi': dominant_shi,
            'shi_type': shi_type,
            'shi_elements': shi_elements,
        }

    def _generate_summary(self, binzhu: dict, tiyong: dict, zuogong: dict,
                          gongli: dict, zeishen: dict, shi: dict) -> str:
        parts = []

        ti_count = len(tiyong.get('ti', []))
        yong_count = len(tiyong.get('yong', []))

        parts.append('体用：体{}个，用{}个'.format(ti_count, yong_count))

        all_gong = []
        for gong_list in zuogong.values():
            all_gong.extend(gong_list)

        if all_gong:
            gong_types = {}
            for g in all_gong:
                gt = g.get('type', '')
                gong_types[gt] = gong_types.get(gt, 0) + 1
            type_str = '、'.join([k + str(v) + '次' for k, v in gong_types.items()])
            parts.append('做功：' + type_str)
        else:
            parts.append('做功：暂无有效做功')

        parts.append('功力：{}（{}分）'.format(gongli.get('level', ''), gongli.get('score', 0)))

        gongshen_count = len(gongli.get('gongshen', []))
        feishen_count = len(gongli.get('feishen', []))
        parts.append('功神{}个，废神{}个'.format(gongshen_count, feishen_count))

        if zeishen.get('is_zeishen_pattern'):
            zeishen_names = '、'.join([z.get('shishen', '') for z in zeishen.get('zeishen', [])])
            parts.append('贼神捕神：贼神为{}'.format(zeishen_names))

        if shi.get('dominant_shi'):
            parts.append('势：{}'.format(shi.get('dominant_shi')))

        return '；'.join(parts)

    def _calc_strength(self, items: list, result: dict) -> float:
        if not items:
            return 0.0

        strength = 0.0

        for item in items:
            gan = item.get('gan', '')
            pos = item.get('position', '')

            for p in result.get('pillars', []):
                if p.get('position', '') in pos or pos in p.get('position', ''):
                    zhi = p.get('zhi', '')
                    changsheng = SHIER_CHANGSHENG.get(gan, {}).get(zhi, '')
                    # 十二长生状态用 DELING_SCORE 查权重，非 CANGGAN_WEIGHT（藏干气位）
                    if changsheng in DELING_SCORE:
                        strength += max(0, DELING_SCORE.get(changsheng, 0)) * 0.5

                    canggan = p.get('canggan', [])
                    for cg_item in canggan:
                        if cg_item.get('gan') == gan:
                            qi = cg_item.get('qi', '')
                            strength += CANGGAN_WEIGHT.get(qi, 0) * 0.5

        return round(strength, 2)


register_school('mangpai', MangpaiAnalyzer)
