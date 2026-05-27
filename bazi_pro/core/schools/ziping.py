import copy

from bazi_pro.core import full_analysis
from bazi_pro.core.constants import GAN_WUXING, WUXING_TO_GAN, derive_shishen
from bazi_pro.core.schools import register_school  # noqa: E402
from bazi_pro.core.schools.base import SchoolAnalyzer
from bazi_pro.core.stems import KE_MAP, SHENG_MAP, WO_KE_MAP

_BREAK_ADJUST = {
    '伤官见官': '印星',
    '比劫争财': '官杀',
    '财星破印': '官杀',
    '枭神夺食': '财星',
}

_BREAK_YONGSHEN_WX = {
    '印星': '生我',
    '官杀': '克我',
    '比劫': '同我',
    '财星': '我克',
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
        if not yong_wx or not dm_wx:
            return []

        verdicts = []
        for step_info in dayun_list:
            gan = step_info.get('gan', '')
            zhi = step_info.get('zhi', '')
            step = step_info.get('step', 0)
            if not gan:
                continue

            gan_wx = GAN_WUXING.get(gan, '')
            if not gan_wx:
                continue

            shishen = derive_shishen(day_master, gan)

            if gan_wx == yong_wx:
                verdict = '吉'
                detail = f'大运天干{gan}({gan_wx})与用神{yong_wx}同类'
            elif (gan_wx, yong_wx) in _sheng_pairs():
                verdict = '吉'
                detail = f'大运天干{gan}({gan_wx})生扶用神{yong_wx}'
            elif (yong_wx, gan_wx) in _ke_pairs():
                verdict = '凶'
                detail = f'用神{yong_wx}克大运天干{gan}({gan_wx})，耗用神之力'
            elif (gan_wx, yong_wx) in _ke_pairs():
                verdict = '凶'
                detail = f'大运天干{gan}({gan_wx})克用神{yong_wx}'
            elif (yong_wx, gan_wx) in _sheng_pairs():
                verdict = '凶'
                detail = f'用神{yong_wx}生大运天干{gan}({gan_wx})，泄用神之力'
            else:
                verdict = '平'
                detail = f'大运天干{gan}({gan_wx})与用神{yong_wx}关系待定'

            verdicts.append({
                'step': step,
                'gan': gan,
                'zhi': zhi,
                'shishen': shishen,
                'verdict': verdict,
                'detail': detail,
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
