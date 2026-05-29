import copy

from bazi_pro.core import full_analysis
from bazi_pro.core.constants import GAN_WUXING, WUXING_TO_GAN, ZHI_WUXING, derive_shishen
from bazi_pro.core.schools import register_school  # noqa: E402
from bazi_pro.core.schools.base import SchoolAnalyzer
from bazi_pro.core.stems import KE_MAP, SHENG_MAP, WO_KE_MAP, WO_SHENG_MAP

_BREAK_ADJUST = {
    '伤官见官': '印星',
    '比劫争财': ['食伤', '官杀'],
    '财星破印': '比劫',
    '枭神夺食': '财星',
}

_BREAK_YONGSHEN_WX = {
    '印星': '生我',
    '官杀': '克我',
    '比劫': '同我',
    '财星': '我克',
    '食伤': '我生',
}


class ZipingAnalyzer(SchoolAnalyzer):
    @property
    def name(self) -> str:
        return 'ziping'

    @property
    def description(self) -> str:
        return '传统子平法：格局用神法，以月令取格，六层筛查定格局，格局用神优先，扶抑用神次之，调候用神补充'

    def analyze(self, mcp_json: dict) -> dict:
        core = full_analysis(mcp_json)
        if core.get('status') != 'completed':
            return {'status': 'error', 'school': 'ziping', 'message': '核心分析失败'}

        day_master = core.get('day_master', '')
        dm_wx = GAN_WUXING.get(day_master, '')
        pattern = core.get('pattern', {})
        wangshuai = core.get('wangshuai', {})
        yongshen = core.get('yongshen', {})
        tiaohou = core.get('tiaohou', {})

        break_conditions = pattern.get('break_conditions', [])

        adjusted_yongshen = self._adjust_yongshen_for_break(
            day_master, dm_wx, pattern, yongshen, break_conditions
        )

        dayun_verdict = self._judge_dayun(day_master, dm_wx, adjusted_yongshen, core)

        return {
            'status': 'completed',
            'school': 'ziping',
            'school_name': '传统子平法',
            'pattern': pattern,
            'wangshuai': wangshuai,
            'yongshen': adjusted_yongshen,
            'break_conditions': break_conditions,
            'tiaohou': tiaohou,
            'dayun_verdict': dayun_verdict,
            'pillars': core.get('pillars', []),
            'element_forces': core.get('element_forces', {}),
            'relations': core.get('relations', []),
        }

    def _adjust_yongshen_for_break(
        self, day_master: str, dm_wx: str, pattern: dict,
        yongshen: dict, break_conditions: list,
    ) -> dict:
        if not break_conditions:
            return yongshen

        result = copy.deepcopy(yongshen)

        for bc in break_conditions:
            bc_type = bc.get('type', '')
            new_category = _BREAK_ADJUST.get(bc_type)
            if new_category is None:
                continue

            if isinstance(new_category, list):
                new_category = new_category[0]

            rel = _BREAK_YONGSHEN_WX.get(new_category, '')
            if not rel or not dm_wx:
                continue

            if rel == '生我':
                new_wx = SHENG_MAP.get(dm_wx, '')
            elif rel == '克我':
                new_wx = KE_MAP.get(dm_wx, '')
            elif rel == '同我':
                new_wx = dm_wx
            elif rel == '我克':
                new_wx = WO_KE_MAP.get(dm_wx, '')
            elif rel == '我生':
                new_wx = WO_SHENG_MAP.get(dm_wx, '')
            else:
                continue

            if not new_wx:
                continue

            old_yong = result.get('yongshen', '')
            old_xi = list(result.get('xishen', []))
            old_ji = list(result.get('jishen', []))

            result['yongshen'] = new_wx
            result['yongshen_gan'] = WUXING_TO_GAN.get(new_wx, '')

            new_xi = [w for w in old_xi if w != new_wx]
            if old_yong and old_yong != new_wx and old_yong not in new_xi:
                new_xi.append(old_yong)
            result['xishen'] = new_xi
            result['xishen_gan'] = [WUXING_TO_GAN.get(w, '') for w in new_xi]

            if new_wx in old_ji:
                old_ji.remove(new_wx)
            result['jishen'] = old_ji
            result['jishen_gan'] = [WUXING_TO_GAN.get(w, '') for w in old_ji]

            break

        return result

    def _judge_dayun(
        self, day_master: str, dm_wx: str, yongshen: dict, core: dict,
    ) -> list:
        dayun_list = core.get('dayun', [])
        if not dayun_list:
            return []

        yong_wx = yongshen.get('yongshen', '')
        ji_list = yongshen.get('jishen', [])
        xi_list = yongshen.get('xishen', [])
        if not yong_wx or not dm_wx:
            return []

        favorable_wx = {yong_wx}
        if xi_list:
            favorable_wx.update(xi_list)

        unfavorable_wx = set(ji_list) if ji_list else set()

        verdicts = []
        for step_info in dayun_list:
            gan = step_info.get('gan', '')
            zhi = step_info.get('zhi', '')
            step = step_info.get('step', 0)
            if not gan:
                continue

            gan_wx = GAN_WUXING.get(gan, '')
            zhi_wx = ZHI_WUXING.get(zhi, '') if zhi else ''
            if not gan_wx:
                continue

            shishen = derive_shishen(day_master, gan)

            gan_score = 0
            zhi_score = 0
            details = []

            if gan_wx in favorable_wx:
                gan_score += 1
                details.append('天干{}({})为喜用'.format(gan, gan_wx))
            elif gan_wx in unfavorable_wx:
                gan_score -= 1
                details.append('天干{}({})为忌神'.format(gan, gan_wx))
            elif (gan_wx, yong_wx) in _sheng_pairs():
                gan_score += 1
                details.append('天干{}({})生用神{}'.format(gan, gan_wx, yong_wx))
            else:
                for ji_wx in unfavorable_wx:
                    if (gan_wx, ji_wx) in _ke_pairs():
                        gan_score += 1
                        details.append('天干{}({})克忌神{}'.format(gan, gan_wx, ji_wx))
                        break
                else:
                    for ji_wx in unfavorable_wx:
                        if (gan_wx, ji_wx) in _sheng_pairs():
                            gan_score -= 1
                            details.append('天干{}({})生忌神{}'.format(gan, gan_wx, ji_wx))
                            break

            if zhi_wx:
                if zhi_wx in favorable_wx:
                    zhi_score += 1
                    details.append('地支{}({})为喜用'.format(zhi, zhi_wx))
                elif zhi_wx in unfavorable_wx:
                    zhi_score -= 1
                    details.append('地支{}({})为忌神'.format(zhi, zhi_wx))
                elif (zhi_wx, yong_wx) in _sheng_pairs():
                    zhi_score += 1
                    details.append('地支{}({})生用神{}'.format(zhi, zhi_wx, yong_wx))
                else:
                    for ji_wx in unfavorable_wx:
                        if (zhi_wx, ji_wx) in _ke_pairs():
                            zhi_score += 1
                            details.append('地支{}({})克忌神{}'.format(zhi, zhi_wx, ji_wx))
                            break
                    else:
                        for ji_wx in unfavorable_wx:
                            if (zhi_wx, ji_wx) in _sheng_pairs():
                                zhi_score -= 1
                                details.append('地支{}({})生忌神{}'.format(zhi, zhi_wx, ji_wx))
                                break

            total = gan_score + zhi_score
            if total > 0:
                verdict = '吉'
            elif total < 0:
                verdict = '凶'
            else:
                verdict = '平'

            verdicts.append({
                'step': step,
                'gan': gan,
                'zhi': zhi,
                'shishen': shishen,
                'verdict': verdict,
                'detail': '；'.join(details) if details else '大运{}{}与格局关系待定'.format(gan, zhi),
            })

        return verdicts


_SHENG_PAIRS = None
_KE_PAIRS = None


def _sheng_pairs():
    global _SHENG_PAIRS
    if _SHENG_PAIRS is None:
        _SHENG_PAIRS = {('木', '火'), ('火', '土'), ('土', '金'), ('金', '水'), ('水', '木')}
    return _SHENG_PAIRS


def _ke_pairs():
    global _KE_PAIRS
    if _KE_PAIRS is None:
        _KE_PAIRS = {('木', '土'), ('土', '水'), ('水', '火'), ('火', '金'), ('金', '木')}
    return _KE_PAIRS


register_school('ziping', ZipingAnalyzer)
