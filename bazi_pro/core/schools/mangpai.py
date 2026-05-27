from bazi_pro.core import (
    CANGGAN_WEIGHT,
    GAN_WUXING,
    KE_MAP,
    SHENG_MAP,
    SHIER_CHANGSHENG,
    WO_KE_MAP,
    WO_SHENG_MAP,
    derive_shishen,
    full_analysis,
)
from bazi_pro.core.schools import register_school
from bazi_pro.core.schools.base import SchoolAnalyzer

TI_STEMS = {'比肩', '劫财', '正印', '偏印'}
YONG_STEMS = {'正财', '偏财', '正官', '七杀', '食神', '伤官'}

KE_PAIRS = {('木', '土'), ('土', '水'), ('水', '火'), ('火', '金'), ('金', '木')}
SHENG_PAIRS = {('木', '火'), ('火', '土'), ('土', '金'), ('金', '水'), ('水', '木')}


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
        gongli = self._evaluate_gongli(zuogong, tiyong)
        yingqi = self._predict_yingqi(zuogong, result)
        summary = self._generate_summary(binzhu, tiyong, zuogong, gongli)

        return {
            'status': 'completed',
            'school': 'mangpai',
            'school_name': '盲派',
            'binzhu': binzhu,
            'tiyong': tiyong,
            'zuogong': zuogong,
            'gongli': gongli,
            'yingqi': yingqi,
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
            for zs in zhu_shishen:
                zs_wx = zs.get('wuxing', '')
                if not bs_wx or not zs_wx:
                    continue
                if (bs_wx, zs_wx) in KE_PAIRS:
                    interpretations.append({
                        'type': '宾主交战',
                        'bin': bs,
                        'zhu': zs,
                        'relation': '宾克主',
                        'meaning': '贵',
                    })
                elif (zs_wx, bs_wx) in KE_PAIRS:
                    interpretations.append({
                        'type': '宾主交战',
                        'bin': bs,
                        'zhu': zs,
                        'relation': '主克宾',
                        'meaning': '富',
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
                    if (cg_wx, gan_wx) in SHENG_PAIRS:
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
                    for cg in gans:
                        cg_wx = GAN_WUXING.get(cg, '')
                        cg_shishen = derive_shishen(day_master, cg)
                        if cg_shishen in YONG_STEMS:
                            gong_types['heyong'].append({
                                'type': '合用',
                                'tool': {'gan': cg, 'shishen': cg_shishen, 'wuxing': cg_wx},
                                'description': '合{}({})为我用'.format(cg_shishen, cg),
                            })

        return gong_types

    def _evaluate_gongli(self, zuogong: dict, tiyong: dict) -> dict:
        all_gong = []
        for gong_list in zuogong.values():
            all_gong.extend(gong_list)

        if not all_gong:
            return {
                'level': '无功',
                'score': 0,
                'analysis': '命局中缺乏有效做功组合',
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

        return {
            'level': level,
            'score': score,
            'analysis': '，'.join(analysis_parts),
        }

    def _predict_yingqi(self, zuogong: dict, result: dict) -> dict:
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

        return {
            'triggers': triggers[:5],
            'note': '大运地支与原局做功地支发生冲合刑害时为应期' if triggers else '待大运流年引动',
        }

    def _generate_summary(self, binzhu: dict, tiyong: dict, zuogong: dict, gongli: dict) -> str:
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
                    if changsheng in CANGGAN_WEIGHT:
                        strength += CANGGAN_WEIGHT.get(changsheng, 0)

                    canggan = p.get('canggan', [])
                    for cg_item in canggan:
                        if cg_item.get('gan') == gan:
                            qi = cg_item.get('qi', '')
                            strength += CANGGAN_WEIGHT.get(qi, 0) * 0.5

        return round(strength, 2)


register_school('mangpai', MangpaiAnalyzer)
