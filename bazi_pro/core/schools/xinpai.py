from bazi_pro.core.schools.base import SchoolAnalyzer
from bazi_pro.core import (
    full_analysis, get_canggan, derive_shishen, GAN_WUXING, ZHI_WUXING,
    KE_MAP, WO_KE_MAP, SHENG_MAP, WO_SHENG_MAP,
    JIANLU_MAP, SHIER_CHANGSHENG, CANGGAN_WEIGHT
)
from bazi_pro.core.schools import register_school
from bazi_pro.core.constants import WUXING_TO_GAN


KONGWANG_MAP = {
    '甲子': ['戌', '亥'], '甲寅': ['子', '丑'], '甲辰': ['寅', '卯'],
    '甲午': ['辰', '巳'], '甲申': ['午', '未'], '甲戌': ['申', '酉'],
    '乙丑': ['亥', '子'], '乙卯': ['丑', '寅'], '乙巳': ['卯', '辰'],
    '乙未': ['巳', '午'], '乙酉': ['未', '申'], '乙亥': ['酉', '戌'],
    '丙寅': ['子', '丑'], '丙辰': ['寅', '卯'], '丙午': ['辰', '巳'],
    '丙申': ['午', '未'], '丙戌': ['申', '酉'], '丙子': ['戌', '亥'],
    '丁卯': ['寅', '卯'], '丁巳': ['卯', '辰'], '丁未': ['辰', '巳'],
    '丁酉': ['午', '未'], '丁亥': ['申', '酉'], '丁丑': ['戌', '亥'],
    '戊辰': ['寅', '卯'], '戊午': ['辰', '巳'], '戊申': ['午', '未'],
    '戊戌': ['申', '酉'], '戊子': ['戌', '亥'], '戊寅': ['子', '丑'],
    '己巳': ['卯', '辰'], '己未': ['辰', '巳'], '己酉': ['午', '未'],
    '己亥': ['申', '酉'], '己丑': ['戌', '亥'], '己卯': ['子', '丑'],
    '庚午': ['辰', '巳'], '庚申': ['午', '未'], '庚戌': ['申', '酉'],
    '庚子': ['戌', '亥'], '庚寅': ['子', '丑'], '庚辰': ['寅', '卯'],
    '辛未': ['辰', '巳'], '辛酉': ['午', '未'], '辛亥': ['申', '酉'],
    '辛丑': ['戌', '亥'], '辛卯': ['子', '丑'], '辛巳': ['寅', '卯'],
    '壬申': ['午', '未'], '壬戌': ['申', '酉'], '壬子': ['戌', '亥'],
    '壬寅': ['子', '丑'], '壬辰': ['寅', '卯'], '壬午': ['辰', '巳'],
    '癸酉': ['午', '未'], '癸亥': ['申', '酉'], '癸丑': ['戌', '亥'],
    '癸卯': ['子', '丑'], '癸巳': ['寅', '卯'], '癸未': ['辰', '巳'],
}


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

        yongshen = []
        jishen = []

        if sheng_fu == '身旺':
            yongshen = ['官星', '财星', '食伤']
            jishen = ['印星', '比劫']
        else:
            yongshen = ['印星', '比劫']
            jishen = ['官星', '财星', '食伤']

        if month_zhi_wx == dm_wx and dm_wx:
            sheng_fu = '身旺极'
            yongshen = ['食伤']
            jishen = ['印星', '比劫', '官星', '财星']
        elif self._is_counter(dm_wx, month_zhi_wx):
            sheng_fu = '身弱极'
            yongshen = ['印星', '比劫']
            jishen = ['官星', '财星', '食伤']

        yong_wx_list = []
        for y in yongshen:
            if y == '印星':
                yong_wx_list.append(SHENG_MAP.get(dm_wx, ''))
            elif y == '比劫':
                yong_wx_list.append(dm_wx)
            elif y == '官星':
                yong_wx_list.append(KE_MAP.get(dm_wx, ''))
            elif y == '财星':
                yong_wx_list.append(WO_KE_MAP.get(dm_wx, ''))
            elif y == '食伤':
                yong_wx_list.append(WO_SHENG_MAP.get(dm_wx, ''))

        yongshen_gan = []
        for wx in yong_wx_list:
            if wx:
                yongshen_gan.extend(list(WUXING_TO_GAN.get(wx, '')))

        return {
            'sheng_fu': sheng_fu,
            'yongshen': yong_wx_list,
            'yongshen_name': yongshen,
            'jishen': [],
            'jishen_name': jishen,
            'reason': f'月令{month_zhi}({month_zhi_wx})与日主{dm_wx}关系判定',
        }

    def _judge_sheng_fu(self, dm_wx: str, month_wx: str) -> str:
        if not dm_wx or not month_wx:
            return '身旺'

        if month_wx == dm_wx:
            return '身旺'
        if (dm_wx, month_wx) in [('木', '水'), ('火', '木'), ('土', '火'), ('金', '土'), ('水', '金')]:
            return '身旺'
        if (month_wx, dm_wx) in [('木', '土'), ('土', '水'), ('水', '火'), ('火', '金'), ('金', '木')]:
            return '身弱'
        if month_wx == WO_SHENG_MAP.get(dm_wx, ''):
            return '身旺'
        if month_wx == SHENG_MAP.get(dm_wx, ''):
            return '身旺'

        return '身旺'

    def _is_counter(self, dm_wx: str, month_wx: str) -> bool:
        if not dm_wx or not month_wx:
            return False
        ke_pairs = [('木', '金'), ('金', '木'), ('火', '水'), ('水', '火'), ('土', '木'), ('木', '土')]
        return (dm_wx, month_wx) in ke_pairs

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

        year_gan = pillars[0].get('gan', '') if pillars else ''
        if not year_gan:
            return {'kongwang_zhi': [], 'affected': [], 'power_reduction': 0.5}

        kongwang_zhi = KONGWANG_MAP.get(year_gan, [])

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
                    'description': f'地支{kw}空亡',
                    'action': '用忌互换',
                })
                break

        sheng_fu = yong_ji.get('sheng_fu', '')
        if '极' in sheng_fu:
            conditions.append({
                'type': 'wang_ji',
                'description': f'{sheng_fu}',
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
                detail = f'大运地支{zhi}空亡，力量减半'
            elif is_yong:
                verdict = '吉'
                detail = f'大运天干{gan}({gan_wx})为用神'
            else:
                verdict = '凶'
                detail = f'大运天干{gan}({gan_wx})为忌神'

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

        advice = f'新派以用忌神为核心。用神为{yong_str}，忌神为{ji_str}。'
        if kongwang_list:
            advice += f'空亡{kong_str}，力量减半。'
        if fanduan_count > 0:
            advice += f'存在{fanduan_count}项反断条件，需综合判断。'

        return {
            'yongshen': yong_str,
            'jishen': ji_str,
            'kongwang': kong_str,
            'fanduan_count': fanduan_count,
            'advice': advice,
        }


register_school('xinpai', XinpaiAnalyzer)
