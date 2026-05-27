from bazi_pro.core import (
    GAN_WUXING,
    KE_MAP,
    SHENG_MAP,
    WO_KE_MAP,
    WO_SHENG_MAP,
    ZHI_WUXING,
    derive_shishen,
    full_analysis,
)
from bazi_pro.core.constants import WUXING_TO_GAN
from bazi_pro.core.schools import register_school
from bazi_pro.core.schools.base import SchoolAnalyzer

LIUJIA_XUN = {
    '甲子': ['戌', '亥'], '乙丑': ['亥', '子'], '丙寅': ['子', '丑'], '丁卯': ['丑', '寅'],
    '戊辰': ['寅', '卯'], '己巳': ['卯', '辰'], '庚午': ['辰', '巳'], '辛未': ['巳', '午'],
    '壬申': ['午', '未'], '癸酉': ['未', '申'],
    '甲戌': ['申', '酉'], '乙亥': ['酉', '戌'], '丙子': ['戌', '亥'], '丁丑': ['亥', '子'],
    '戊寅': ['子', '丑'], '己卯': ['丑', '寅'], '庚辰': ['寅', '卯'], '辛巳': ['卯', '辰'],
    '壬午': ['辰', '巳'], '癸未': ['巳', '午'],
    '甲申': ['午', '未'], '乙酉': ['未', '申'], '丙戌': ['申', '酉'], '丁亥': ['酉', '戌'],
    '戊子': ['戌', '亥'], '己丑': ['亥', '子'], '庚寅': ['子', '丑'], '辛卯': ['丑', '寅'],
    '壬辰': ['寅', '卯'], '癸巳': ['卯', '辰'],
    '甲午': ['辰', '巳'], '乙未': ['巳', '午'], '丙申': ['午', '未'], '丁酉': ['未', '申'],
    '戊戌': ['申', '酉'], '己亥': ['酉', '戌'], '庚子': ['戌', '亥'], '辛丑': ['亥', '子'],
    '壬寅': ['子', '丑'], '癸卯': ['丑', '寅'],
    '甲辰': ['寅', '卯'], '乙巳': ['卯', '辰'], '丙午': ['辰', '巳'], '丁未': ['巳', '午'],
    '戊申': ['午', '未'], '己酉': ['未', '申'], '庚戌': ['申', '酉'], '辛亥': ['酉', '戌'],
    '壬子': ['戌', '亥'], '癸丑': ['亥', '子'],
    '甲寅': ['子', '丑'], '乙卯': ['丑', '寅'], '丙辰': ['寅', '卯'], '丁巳': ['卯', '辰'],
    '戊午': ['辰', '巳'], '己未': ['巳', '午'], '庚申': ['午', '未'], '辛酉': ['未', '申'],
    '壬戌': ['申', '酉'], '癸亥': ['酉', '戌'],
}

KE_PAIRS_SET = {('木', '土'), ('土', '水'), ('水', '火'), ('火', '金'), ('金', '木')}

BAISHEN_RULES = {
    '正官': {'position': '月干', 'condition': 'not_on_gan'},
    '七杀': {'position': '时干', 'condition': 'not_on_gan'},
    '正财': {'position': '月干', 'condition': 'not_on_gan'},
    '偏财': {'position': '时干', 'condition': 'not_on_gan'},
    '正印': {'position': '月干', 'condition': 'not_on_gan'},
    '偏印': {'position': '时干', 'condition': 'not_on_gan'},
    '食神': {'position': '时干', 'condition': 'not_on_gan'},
    '伤官': {'position': '月干', 'condition': 'not_on_gan'},
}


class XinpaiAnalyzer(SchoolAnalyzer):
    @property
    def name(self) -> str:
        return "xinpai"

    @property
    def description(self) -> str:
        return "新派 - 百神论/空亡论/反断论，源自李涵辰新法，以用忌神为核心，强调空亡和反断"

    def analyze(self, mcp_json: dict) -> dict:
        result = full_analysis(mcp_json)
        if result.get('status') != 'completed':
            return {'status': 'error', 'school': 'xinpai', 'message': '核心分析失败'}

        yong_ji = self._determine_yong_ji(result)
        baishen = self._apply_baishen(result)
        kongwang = self._apply_kongwang(result)
        fanduan = self._apply_fanduan(result, yong_ji)
        dayun_verdict = self._judge_dayun_xinpai(result, yong_ji, kongwang)
        summary = self._generate_summary(yong_ji, kongwang, fanduan)

        return {
            'status': 'completed',
            'school': 'xinpai',
            'school_name': '新派',
            'yong_ji': yong_ji,
            'baishen': baishen,
            'kongwang': kongwang,
            'fanduan': fanduan,
            'dayun_verdict': dayun_verdict,
            'summary': summary,
            'pillars': result.get('pillars', []),
            'element_forces': result.get('element_forces', {}),
        }

    def _determine_yong_ji(self, result: dict) -> dict:
        day_master = result.get('day_master', '')
        dm_wx = GAN_WUXING.get(day_master, '')
        pillars = result.get('pillars', [])

        if not pillars:
            return {'sheng_fu': '身旺', 'yongshen': [], 'jishen': [], 'reason': '无法确定'}

        month_zhi = pillars[1].get('zhi', '') if len(pillars) > 1 else ''
        month_zhi_wx = ZHI_WUXING.get(month_zhi, '')

        sheng_fu = self._judge_sheng_fu(dm_wx, month_zhi_wx)

        yongshen_names = []
        jishen_names = []

        if sheng_fu == '身旺':
            yongshen_names = ['官星', '财星', '食伤']
            jishen_names = ['印星', '比劫']
        else:
            yongshen_names = ['印星', '比劫']
            jishen_names = ['官星', '财星', '食伤']

        if month_zhi_wx == dm_wx and dm_wx:
            sheng_fu = '身旺极'
            yongshen_names = ['食伤']
            jishen_names = ['印星', '比劫', '官星', '财星']
        elif (month_zhi_wx, dm_wx) in KE_PAIRS_SET:
            sheng_fu = '身弱极'
            yongshen_names = ['印星', '比劫']
            jishen_names = ['官星', '财星', '食伤']

        yong_wx_list = self._names_to_wuxing(dm_wx, yongshen_names)
        ji_wx_list = self._names_to_wuxing(dm_wx, jishen_names)

        yongshen_gan = []
        for wx in yong_wx_list:
            if wx:
                yongshen_gan.extend(list(WUXING_TO_GAN.get(wx, '')))

        jishen_gan = []
        for wx in ji_wx_list:
            if wx:
                jishen_gan.extend(list(WUXING_TO_GAN.get(wx, '')))

        return {
            'sheng_fu': sheng_fu,
            'yongshen': yong_wx_list,
            'yongshen_name': yongshen_names,
            'yongshen_gan': yongshen_gan,
            'jishen': ji_wx_list,
            'jishen_name': jishen_names,
            'jishen_gan': jishen_gan,
            'reason': '月令{}({})与日主{}关系判定'.format(month_zhi, month_zhi_wx, dm_wx),
        }

    def _names_to_wuxing(self, dm_wx: str, names: list) -> list:
        result = []
        for name in names:
            if name == '印星':
                wx = SHENG_MAP.get(dm_wx, '')
            elif name == '比劫':
                wx = dm_wx
            elif name == '官星':
                wx = KE_MAP.get(dm_wx, '')
            elif name == '财星':
                wx = WO_KE_MAP.get(dm_wx, '')
            elif name == '食伤':
                wx = WO_SHENG_MAP.get(dm_wx, '')
            else:
                wx = ''
            if wx and wx not in result:
                result.append(wx)
        return result

    def _judge_sheng_fu(self, dm_wx: str, month_wx: str) -> str:
        if not dm_wx or not month_wx:
            return '身旺'

        if month_wx == dm_wx:
            return '身旺'
        if month_wx == SHENG_MAP.get(dm_wx, ''):
            return '身旺'
        if (month_wx, dm_wx) in KE_PAIRS_SET:
            return '身弱'
        if month_wx == WO_SHENG_MAP.get(dm_wx, ''):
            return '身弱'
        if month_wx == WO_KE_MAP.get(dm_wx, ''):
            return '身弱'

        return '身旺'

    def _apply_baishen(self, result: dict) -> dict:
        pillars = result.get('pillars', [])
        day_master = result.get('day_master', '')
        if not pillars:
            return {'replacements': {}, 'original': {}}

        replacements = {}
        original = {}

        tiangan_list = [p.get('gan', '') for p in pillars]
        shishen_list = [derive_shishen(day_master, g) for g in tiangan_list]

        for i, shishen in enumerate(shishen_list):
            if shishen in BAISHEN_RULES:
                rule = BAISHEN_RULES[shishen]
                original[shishen] = {'position': rule['position'], 'replaced_by': None}

        for shishen, rule in BAISHEN_RULES.items():
            if shishen not in shishen_list:
                month_gan = tiangan_list[1] if len(tiangan_list) > 1 else ''
                hour_gan = tiangan_list[3] if len(tiangan_list) > 3 else ''

                if rule['position'] == '月干' and month_gan:
                    original[shishen] = {'position': '月干', 'replaced_by': month_gan}
                    replacements[shishen] = {
                        'position': '月干',
                        'gan': month_gan,
                        'wuxing': GAN_WUXING.get(month_gan, ''),
                    }
                elif rule['position'] == '时干' and hour_gan:
                    original[shishen] = {'position': '时干', 'replaced_by': hour_gan}
                    replacements[shishen] = {
                        'position': '时干',
                        'gan': hour_gan,
                        'wuxing': GAN_WUXING.get(hour_gan, ''),
                    }

        return {
            'replacements': replacements,
            'original': original,
            'shishen_on_gan': dict(zip(tiangan_list, shishen_list)),
        }

    def _apply_kongwang(self, result: dict) -> dict:
        pillars = result.get('pillars', [])
        if not pillars:
            return {'kongwang_zhi': [], 'affected': [], 'power_reduction': 0.5}

        day_gan = pillars[2].get('gan', '') if len(pillars) > 2 else ''
        day_zhi = pillars[2].get('zhi', '') if len(pillars) > 2 else ''
        day_ganzhi = day_gan + day_zhi

        kongwang_zhi = LIUJIA_XUN.get(day_ganzhi, [])

        if not kongwang_zhi:
            year_ganzhi = (pillars[0].get('gan', '') + pillars[0].get('zhi', '')) if pillars else ''
            kongwang_zhi = LIUJIA_XUN.get(year_ganzhi, [])

        affected = []
        for pillar in pillars:
            zhi = pillar.get('zhi', '')
            if zhi in kongwang_zhi:
                affected.append({
                    'position': pillar.get('position', ''),
                    'zhi': zhi,
                    'original_power': '1.0',
                    'reduced_power': '0.5',
                })

        return {
            'kongwang_zhi': kongwang_zhi,
            'affected': affected,
            'power_reduction': 0.5,
            'canggan_excluded': len(affected) > 0,
        }

    def _apply_fanduan(self, result: dict, yong_ji: dict) -> dict:
        day_master = result.get('day_master', '')
        dm_wx = GAN_WUXING.get(day_master, '')
        pillars = result.get('pillars', [])

        kongwang = self._apply_kongwang(result)
        kongwang_zhi = kongwang.get('kongwang_zhi', [])

        month_zhi = pillars[1].get('zhi', '') if len(pillars) > 1 else ''
        month_zhi_wx = ZHI_WUXING.get(month_zhi, '')

        conditions = []
        fanduan_yong = []
        fanduan_ji = []

        if month_zhi_wx == dm_wx and dm_wx:
            conditions.append({
                'type': 'yue_fan',
                'description': '月令与日主同五行',
                'action': '用忌互换',
            })
            fanduan_yong.extend(yong_ji.get('jishen', []))
            fanduan_ji.extend(yong_ji.get('yongshen', []))

        for kw in kongwang_zhi:
            if kw in [p.get('zhi', '') for p in pillars]:
                conditions.append({
                    'type': 'kongwang_fan',
                    'description': '地支{}空亡'.format(kw),
                    'action': '用忌互换',
                })
                break

        sheng_fu = yong_ji.get('sheng_fu', '')
        if '极' in sheng_fu:
            conditions.append({
                'type': 'wang_ji',
                'description': '{}'.format(sheng_fu),
                'action': '克泄耗反断',
            })

        return {
            'conditions': conditions,
            'fanduan_yong': fanduan_yong,
            'fanduan_ji': fanduan_ji,
            'total_conditions': len(conditions),
        }

    def _judge_dayun_xinpai(self, result: dict, yong_ji: dict, kongwang: dict) -> list:
        dayun_list = result.get('dayun', []) if 'dayun' in result else []
        if not dayun_list:
            dayun_list = self._generate_dayun_from_pillars(result)

        yong_wx_list = yong_ji.get('yongshen', [])
        kongwang_zhi = kongwang.get('kongwang_zhi', [])

        verdicts = []
        for step_info in dayun_list:
            gan = step_info.get('gan', '')
            zhi = step_info.get('zhi', '')
            step = step_info.get('step', 0)

            if not gan:
                continue

            gan_wx = GAN_WUXING.get(gan, '')
            shishen = derive_shishen(result.get('day_master', ''), gan)

            is_kongwang = zhi in kongwang_zhi if zhi else False

            is_yong = gan_wx in yong_wx_list if gan_wx else False

            if is_kongwang:
                verdict = '平'
                detail = '大运地支{}空亡，力量减半'.format(zhi)
            elif is_yong:
                verdict = '吉'
                detail = '大运天干{}({})为用神'.format(gan, gan_wx)
            else:
                verdict = '凶'
                detail = '大运天干{}({})为忌神'.format(gan, gan_wx)

            verdicts.append({
                'step': step,
                'gan': gan,
                'zhi': zhi,
                'shishen': shishen,
                'verdict': verdict,
                'detail': detail,
                'is_kongwang': is_kongwang,
            })

        return verdicts

    def _generate_dayun_from_pillars(self, result: dict) -> list:
        pillars = result.get('pillars', [])
        if not pillars:
            return []

        dayun_list = []
        for i, pillar in enumerate(pillars[1:], 1):
            dayun_list.append({
                'step': i,
                'gan': pillar.get('gan', ''),
                'zhi': pillar.get('zhi', ''),
            })

        return dayun_list

    def _generate_summary(self, yong_ji: dict, kongwang: dict, fanduan: dict) -> dict:
        yong_names = yong_ji.get('yongshen_name', [])
        ji_names = yong_ji.get('jishen_name', [])
        kongwang_list = kongwang.get('kongwang_zhi', [])
        fanduan_count = fanduan.get('total_conditions', 0)

        yong_str = '、'.join(yong_names) if yong_names else '待定'
        ji_str = '、'.join(ji_names) if ji_names else '待定'
        kong_str = '、'.join(kongwang_list) if kongwang_list else '无'

        advice = '新派以用忌神为核心。用神为{}，忌神为{}。'.format(yong_str, ji_str)
        if kongwang_list:
            advice += '空亡{}，力量减半。'.format(kong_str)
        if fanduan_count > 0:
            advice += '存在{}项反断条件，需综合判断。'.format(fanduan_count)

        return {
            'yongshen': yong_str,
            'jishen': ji_str,
            'kongwang': kong_str,
            'fanduan_count': fanduan_count,
            'advice': advice,
        }


register_school('xinpai', XinpaiAnalyzer)
