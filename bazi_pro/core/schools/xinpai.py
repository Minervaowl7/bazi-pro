from bazi_pro.core import (
    GAN_WUXING,
    KE_MAP,
    SHENG_MAP,
    WO_KE_MAP,
    WO_SHENG_MAP,
    YANGREN_MAP,
    ZHI_CHONG,
    ZHI_HE,
    ZHI_WUXING,
    derive_shishen,
    full_analysis,
)
from bazi_pro.core.constants import WUXING_TO_GAN
from bazi_pro.core.schools import register_school
from bazi_pro.core.schools.base import SchoolAnalyzer

LIUJIA_XUN = {
    '甲子': ['戌', '亥'], '甲戌': ['申', '酉'], '甲申': ['午', '未'],
    '甲午': ['辰', '巳'], '甲辰': ['寅', '卯'], '甲寅': ['子', '丑'],
}

GAN_ORDER = '甲乙丙丁戊己庚辛壬癸'
ZHI_ORDER = '子丑寅卯辰巳午未申酉戌亥'


def _get_kongwang(day_ganzhi: str) -> list:
    """根据日柱干支查六甲旬空"""
    if len(day_ganzhi) != 2:
        return []
    gan = day_ganzhi[0]
    zhi = day_ganzhi[1]
    if gan not in GAN_ORDER or zhi not in ZHI_ORDER:
        return []
    gan_idx = GAN_ORDER.index(gan)
    zhi_idx = ZHI_ORDER.index(zhi)
    xun_start_gan_idx = (gan_idx - (zhi_idx % 10)) % 10
    xun_start_zhi_idx = (zhi_idx - (zhi_idx % 10)) % 12
    if xun_start_zhi_idx < 0:
        xun_start_zhi_idx += 12
    offset = gan_idx - xun_start_gan_idx
    if offset < 0:
        offset += 10
    xun_start_zhi_idx = (zhi_idx - offset) % 12
    xun_start_gan = GAN_ORDER[xun_start_gan_idx]
    xun_start_zhi = ZHI_ORDER[xun_start_zhi_idx]
    xun_key = xun_start_gan + xun_start_zhi
    return LIUJIA_XUN.get(xun_key, [])

KE_PAIRS_SET = {('木', '土'), ('土', '水'), ('水', '火'), ('火', '金'), ('金', '木')}

TONGZONG_PAIRS = {
    '丙': '戊', '戊': '丙',
    '丁': '己', '己': '丁',
    '庚': '壬', '壬': '庚',
    '辛': '癸', '癸': '辛',
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
        dayun_verdict = self._judge_dayun_xinpai(result, yong_ji, kongwang, fanduan)
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
            return {'sheng_fu': '身旺', 'geju_type': '扶抑格', 'yongshen': [], 'jishen': [], 'reason': '无法确定'}

        month_zhi = pillars[1].get('zhi', '') if len(pillars) > 1 else ''
        month_zhi_wx = ZHI_WUXING.get(month_zhi, '')

        sheng_fu = self._judge_sheng_fu(dm_wx, month_zhi_wx, pillars, day_master)

        yongshen_names = []
        jishen_names = []
        geju_type = '扶抑格'

        if sheng_fu in ('从强', '身旺极'):
            geju_type = '从强格'
            yongshen_names = ['印星', '比劫']
            jishen_names = ['官星', '财星', '食伤']
        elif sheng_fu in ('从弱', '身弱极'):
            geju_type = '从弱格'
            yongshen_names = ['官星', '财星', '食伤']
            jishen_names = ['印星', '比劫']
        elif sheng_fu == '身旺':
            geju_type = '扶抑格'
            yongshen_names = ['官星', '财星', '食伤']
            jishen_names = ['印星', '比劫']
        else:
            geju_type = '扶抑格'
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
            'geju_type': geju_type,
            'yongshen': yong_wx_list,
            'yongshen_name': yongshen_names,
            'yongshen_gan': yongshen_gan,
            'jishen': ji_wx_list,
            'jishen_name': jishen_names,
            'jishen_gan': jishen_gan,
            'reason': '月令{}({})与日主{}关系判定，帮扶克泄综合评分'.format(month_zhi, month_zhi_wx, dm_wx),
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

    def _judge_sheng_fu(self, dm_wx: str, month_wx: str, pillars: list, day_master: str) -> str:
        """基于规则的身旺身弱判定（李涵辰法）：月令为主，区分阴阳干，考虑有根无根"""
        if not dm_wx or not month_wx:
            return '身旺'

        is_yang_gan = day_master in ('甲', '丙', '戊', '庚', '壬')

        if month_wx == dm_wx or month_wx == SHENG_MAP.get(dm_wx, ''):
            month_help = True
        else:
            month_help = False

        all_zhis = [p.get('zhi', '') for p in pillars]
        day_zhi = pillars[2].get('zhi', '') if len(pillars) > 2 else ''
        day_zhi_wx = ZHI_WUXING.get(day_zhi, '')

        has_root = False
        root_count = 0
        for zhi in all_zhis:
            zhi_wx = ZHI_WUXING.get(zhi, '')
            if zhi_wx == dm_wx:
                has_root = True
                root_count += 1

        has_yin_root = False
        yin_wx = SHENG_MAP.get(dm_wx, '')
        for zhi in all_zhis:
            zhi_wx = ZHI_WUXING.get(zhi, '')
            if zhi_wx == yin_wx:
                has_yin_root = True
                break

        zuoxia_is_yin = day_zhi_wx == yin_wx
        zuoxia_is_ku = day_zhi in ('辰', '戌', '丑', '未') and day_zhi_wx == dm_wx

        help_count = 0
        drain_count = 0
        for p in pillars:
            gan = p.get('gan', '')
            zhi = p.get('zhi', '')
            gan_wx = GAN_WUXING.get(gan, '')
            zhi_wx = ZHI_WUXING.get(zhi, '')
            if gan_wx == dm_wx or gan_wx == yin_wx:
                help_count += 1
            elif gan_wx:
                drain_count += 1
            if zhi_wx == dm_wx or zhi_wx == yin_wx:
                help_count += 1
            elif zhi_wx:
                drain_count += 1

        if month_help and help_count > drain_count:
            if not has_root and not has_yin_root:
                if drain_count == 0:
                    return '从强'
                return '身旺'
            if help_count >= drain_count * 2 and drain_count <= 1:
                return '从强'
            return '身旺'
        elif month_help and help_count <= drain_count:
            return '身弱'
        elif not month_help and drain_count > help_count:
            if is_yang_gan:
                if has_root or has_yin_root or zuoxia_is_yin or zuoxia_is_ku:
                    return '身弱'
                if drain_count >= help_count * 2:
                    return '从弱'
                return '身弱'
            else:
                if zuoxia_is_yin or zuoxia_is_ku:
                    return '身弱'
                if has_yin_root and root_count == 0:
                    return '身弱'
                if drain_count >= help_count * 2:
                    return '从弱'
                return '身弱'
        elif not month_help and drain_count <= help_count:
            return '身旺'

        return '身旺' if month_help else '身弱'

    def _apply_baishen(self, result: dict) -> dict:
        """百神论：局中不存在的六亲（虚神）通过局中已有天干代测。
        注：完整规则在公开典籍中未详述，此处仅标记缺失十神及可代测位置。"""
        pillars = result.get('pillars', [])
        day_master = result.get('day_master', '')
        if not pillars:
            return {'present_shishen': [], 'missing_shishen': [], 'proxy_positions': {}}

        gans = [p.get('gan', '') for p in pillars]
        shishen_on_gan = [derive_shishen(day_master, g) for g in gans]

        present_shishen = set(shishen_on_gan)

        liuqin_shishen = ['正官', '七杀', '正财', '偏财', '正印', '偏印', '食神', '伤官']

        missing = [ss for ss in liuqin_shishen if ss not in present_shishen]

        proxy_positions = {}
        position_names = ['年干', '月干', '日干', '时干']
        for missing_ss in missing:
            proxies = []
            for i, gan in enumerate(gans):
                if i == 2:
                    continue
                proxies.append({
                    'position': position_names[i] if i < 4 else '',
                    'gan': gan,
                    'shishen': shishen_on_gan[i] if i < len(shishen_on_gan) else '',
                })
            if proxies:
                proxy_positions[missing_ss] = proxies

        return {
            'present_shishen': list(present_shishen),
            'missing_shishen': missing,
            'proxy_positions': proxy_positions,
            'shishen_on_gan': dict(zip(gans, shishen_on_gan)),
            'note': '百神论完整规则未在公开典籍中详述，此处仅标记缺失十神',
        }

    def _apply_kongwang(self, result: dict) -> dict:
        pillars = result.get('pillars', [])
        if not pillars:
            return {'kongwang_zhi': [], 'affected': [], 'power_reduction': 0, 'chukong': []}

        day_gan = pillars[2].get('gan', '') if len(pillars) > 2 else ''
        day_zhi = pillars[2].get('zhi', '') if len(pillars) > 2 else ''
        day_ganzhi = day_gan + day_zhi

        kongwang_zhi = _get_kongwang(day_ganzhi)

        all_zhi = [p.get('zhi', '') for p in pillars]

        affected = []
        for pillar in pillars:
            zhi = pillar.get('zhi', '')
            if zhi in kongwang_zhi:
                affected.append({
                    'position': pillar.get('position', ''),
                    'zhi': zhi,
                    'original_power': '1.0',
                    'reduced_power': '0',
                })

        chukong = []
        for kw_zhi in kongwang_zhi:
            if kw_zhi not in all_zhi:
                continue
            for other_zhi in all_zhi:
                if other_zhi == kw_zhi:
                    continue
                pair = frozenset({kw_zhi, other_zhi})
                if pair in ZHI_CHONG:
                    chukong.append({
                        'zhi': kw_zhi,
                        'reason': '{}冲{}出空'.format(other_zhi, kw_zhi),
                        'type': '冲出空',
                    })
                    break
                if pair in ZHI_HE:
                    he_wx = ZHI_HE[pair]
                    chukong.append({
                        'zhi': kw_zhi,
                        'reason': '{}合{}出空，化{}'.format(other_zhi, kw_zhi, he_wx),
                        'type': '合出空',
                    })
                    break

        return {
            'kongwang_zhi': kongwang_zhi,
            'affected': affected,
            'power_reduction': 0,
            'canggan_excluded': len(affected) > 0,
            'chukong': chukong,
        }

    def _apply_fanduan(self, result: dict, yong_ji: dict) -> dict:
        pillars = result.get('pillars', [])
        day_master = result.get('day_master', '')

        if not pillars:
            return {'conditions': [], 'fanduan_details': [], 'total_conditions': 0}

        gans = [p.get('gan', '') for p in pillars]
        zhis = [p.get('zhi', '') for p in pillars]
        shishen_list = [derive_shishen(day_master, g) for g in gans]

        conditions = []
        fanduan_targets = set()

        gan_wuxing_list = [GAN_WUXING.get(g, '') for g in gans]

        # 同五行天干反断：两个相同五行天干同现
        wx_indices = {}
        for i, wx in enumerate(gan_wuxing_list):
            if wx and i != 2:
                wx_indices.setdefault(wx, []).append(i)

        for wx, indices in wx_indices.items():
            if len(indices) >= 2:
                for idx in indices:
                    fanduan_targets.add(idx)
                conditions.append({
                    'type': 'tongxing_fanduan',
                    'description': '局中有两{}五行天干（{}），均反断'.format(
                        wx, '、'.join([gans[i] for i in indices])),
                    'action': '相关天干用忌互换',
                    'target_indices': indices,
                })

        # 同宗反断：月干与时干同宗
        month_gan = gans[1] if len(gans) > 1 else ''
        hour_gan = gans[3] if len(gans) > 3 else ''
        if month_gan and hour_gan:
            if TONGZONG_PAIRS.get(month_gan) == hour_gan or TONGZONG_PAIRS.get(hour_gan) == month_gan:
                fanduan_targets.add(3)
                conditions.append({
                    'type': 'tongzong_fanduan',
                    'description': '月干{}与时干{}同宗，时干反断'.format(month_gan, hour_gan),
                    'action': '时干用忌互换',
                    'target_indices': [3],
                })

        # 地支相同触发反断
        zhi_indices = {}
        for i, zhi in enumerate(zhis):
            if zhi:
                zhi_indices.setdefault(zhi, []).append(i)

        for zhi, indices in zhi_indices.items():
            if len(indices) >= 2:
                for i in range(len(gans)):
                    if i == 2:
                        continue
                    gan_wx = GAN_WUXING.get(gans[i], '')
                    zhi_wx = ZHI_WUXING.get(zhi, '')
                    if gan_wx == zhi_wx and i not in fanduan_targets:
                        fanduan_targets.add(i)
                        conditions.append({
                            'type': 'dizhi_tongxing_fanduan',
                            'description': '局中两{}地支同现，{}干{}反断'.format(
                                zhi, ['年', '月', '日', '时'][i] if i < 4 else '', gans[i]),
                            'action': '相关天干用忌互换',
                            'target_indices': [i],
                        })

        # 纯阳反断
        is_chunyang = all(g in ('甲', '丙', '戊', '庚', '壬') for g in gans if g)
        if is_chunyang and len(gans) >= 4:
            year_zhi = zhis[0] if zhis else ''
            yangren_zhi = YANGREN_MAP.get(day_master, '')
            if year_zhi == yangren_zhi:
                for i in (0, 3):
                    if i not in fanduan_targets and i < len(gans):
                        fanduan_targets.add(i)
                conditions.append({
                    'type': 'chunyang_fanduan',
                    'description': '纯阳且日干生于刃年，年干{}、时干{}反断'.format(gans[0], gans[3] if len(gans) > 3 else ''),
                    'action': '年干时干用忌互换',
                    'target_indices': [0, 3],
                })

        fanduan_details = []
        for idx in sorted(fanduan_targets):
            if idx < len(gans):
                gan = gans[idx]
                ss = shishen_list[idx]
                wx = GAN_WUXING.get(gan, '')
                is_yong = wx in yong_ji.get('yongshen', [])
                new_role = '忌神' if is_yong else '用神'
                fanduan_details.append({
                    'gan': gan,
                    'position': ['年干', '月干', '日干', '时干'][idx] if idx < 4 else '',
                    'shishen': ss,
                    'original': '用神' if is_yong else '忌神',
                    'reversed': new_role,
                })

        return {
            'conditions': conditions,
            'fanduan_details': fanduan_details,
            'total_conditions': len(conditions),
        }

    def _judge_dayun_xinpai(self, result: dict, yong_ji: dict, kongwang: dict, fanduan: dict) -> list:
        dayun_list = result.get('dayun', []) if 'dayun' in result else []
        if not dayun_list:
            dayun_list = self._generate_dayun_from_pillars(result)

        yong_wx_list = yong_ji.get('yongshen', [])
        kongwang_zhi = kongwang.get('kongwang_zhi', [])
        chukong_zhi = [c.get('zhi', '') for c in kongwang.get('chukong', [])]
        day_master = result.get('day_master', '')

        fanduan_gans = set()
        for detail in fanduan.get('fanduan_details', []):
            fanduan_gans.add(detail.get('gan', ''))

        verdicts = []
        for step_info in dayun_list:
            gan = step_info.get('gan', '')
            zhi = step_info.get('zhi', '')
            step = step_info.get('step', 0)

            if not gan:
                continue

            gan_wx = GAN_WUXING.get(gan, '')
            shishen = derive_shishen(day_master, gan)

            is_kongwang = zhi in kongwang_zhi if zhi else False
            is_chukong = zhi in chukong_zhi if zhi else False
            is_yong = gan_wx in yong_wx_list if gan_wx else False
            is_fanduan = gan in fanduan_gans

            if is_fanduan:
                is_yong = not is_yong

            if is_kongwang and not is_chukong:
                verdict = '平'
                detail = '大运地支{}空亡，力量减半'.format(zhi)
            elif is_kongwang and is_chukong:
                if is_yong:
                    verdict = '吉'
                    detail = '大运地支{}原空亡已出空，天干{}({})为用神'.format(zhi, gan, gan_wx)
                else:
                    verdict = '凶'
                    detail = '大运地支{}原空亡已出空，天干{}({})为忌神'.format(zhi, gan, gan_wx)
            elif is_yong:
                verdict = '吉'
                if is_fanduan:
                    detail = '大运天干{}({})为用神（经反断调整）'.format(gan, gan_wx)
                else:
                    detail = '大运天干{}({})为用神'.format(gan, gan_wx)
            else:
                verdict = '凶'
                if is_fanduan:
                    detail = '大运天干{}({})为忌神（经反断调整）'.format(gan, gan_wx)
                else:
                    detail = '大运天干{}({})为忌神'.format(gan, gan_wx)

            verdicts.append({
                'step': step,
                'gan': gan,
                'zhi': zhi,
                'shishen': shishen,
                'verdict': verdict,
                'detail': detail,
                'is_kongwang': is_kongwang,
                'is_chukong': is_chukong,
                'is_fanduan': is_fanduan,
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
        geju_type = yong_ji.get('geju_type', '扶抑格')

        yong_str = '、'.join(yong_names) if yong_names else '待定'
        ji_str = '、'.join(ji_names) if ji_names else '待定'
        kong_str = '、'.join(kongwang_list) if kongwang_list else '无'

        advice = '新派以用忌神为核心，格局类型为{}。用神为{}，忌神为{}。'.format(geju_type, yong_str, ji_str)
        if kongwang_list:
            chukong = kongwang.get('chukong', [])
            if chukong:
                chukong_str = '、'.join([c.get('reason', '') for c in chukong])
                advice += '空亡{}，力量归零（不发挥作用）。出空条件：{}。'.format(kong_str, chukong_str)
            else:
                advice += '空亡{}，力量归零（不发挥作用）。'.format(kong_str)
        if fanduan_count > 0:
            advice += '存在{}项反断条件，需综合判断。'.format(fanduan_count)

        return {
            'yongshen': yong_str,
            'jishen': ji_str,
            'kongwang': kong_str,
            'fanduan_count': fanduan_count,
            'geju_type': geju_type,
            'advice': advice,
        }


register_school('xinpai', XinpaiAnalyzer)
