import copy

from bazi_pro.core import full_analysis
from bazi_pro.core.constants import GAN_WUXING, WUXING_TO_GAN, ZHI_WUXING, derive_shishen
from bazi_pro.core.schools import register_school  # noqa: E402
from bazi_pro.core.schools.base import SchoolAnalyzer
from bazi_pro.core.stems import KE_MAP, SHENG_MAP, WO_KE_MAP, WO_SHENG_MAP

# 破格用神调整表 — 依据《子平真诠》第九章"论用神成败救应"
# 每种破格都有对应的救应用神
_BREAK_ADJUST = {
    # 正格破格
    '伤官见官': '印星',          # "官逢伤而透印以解之"
    '比劫争财': ['食伤', '官杀'],  # "财逢食生而身强带比" / 官杀制比劫
    '财星破印': '比劫',          # "印轻逢财" → 比劫护印
    '枭神夺食': '财星',          # "食逢枭" → 财制枭
    '财透七煞': '食神',          # "财透七煞" → 食神制煞
    '生财露煞': '食神',          # 同上
    '财党杀无制': '食神',        # "煞逢食制"
    '官星逢冲': '合解',          # "刑冲而会合以解之"
    '官星逢刑': '合解',          # 同上
    '佩印无根': '比劫',          # 印需有根，比劫生印
    '孤官无辅': ['财星', '印星'],  # "官逢财印"
    '透煞印无财官': ['财星', '官星'],  # 建禄月劫需财官
    # 从格/化气格破格
    '命逢根气': '逆势',          # 从格破格，需重新取用
    '余气根': '逆势',            # 同上
    '争合': '制合',              # 化气格争合
    '妒合': '制合',              # 化气格妒合
    '克化神': '化神印',          # 化气格克化神 → 化神之印
}

_BREAK_YONGSHEN_WX = {
    '印星': '生我',
    '官杀': '克我',
    '官星': '克我',
    '比劫': '同我',
    '财星': '我克',
    '食伤': '我生',
    '食神': '我生',
    # 特殊键：需在 _adjust_yongshen_for_break 中单独处理
    '合解': '_special',       # 刑冲逢合解，需查冲支的合化五行
    '逆势': '_special',       # 从格破格，需重新取扶抑用神
    '制合': '_special',       # 争合/妒合，需取克制争合方之五行
    '化神印': '_special',     # 克化神 → 取化神之印（生化神的五行）
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

        first_break = True
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

            # 特殊键处理
            if rel == '_special':
                new_wx = self._resolve_special_break(day_master, dm_wx, pattern, bc_type, bc)
                if not new_wx:
                    continue
            elif rel == '生我':
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

            if first_break:
                # 第一个破格条件：调整用神
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
                first_break = False
            else:
                # 后续破格条件：只调整喜忌，不覆盖用神
                # 《子平真诠》"因成得败因败得成" — 多重破格只取最关键的用神调整
                if new_wx not in result.get('xishen', []) and new_wx != result.get('yongshen', ''):
                    xi = list(result.get('xishen', []))
                    xi.append(new_wx)
                    result['xishen'] = xi
                    result['xishen_gan'] = [WUXING_TO_GAN.get(w, '') for w in xi]

        return result

    def _resolve_special_break(self, day_master: str, dm_wx: str,
                                pattern: dict, bc_type: str, bc: dict) -> str:
        """处理 _BREAK_YONGSHEN_WX 中 '_special' 类型的破格用神调整。"""
        if bc_type == '逆势':
            # 从格破格 → 重新取扶抑用神：身弱取印，身旺取官杀
            # 从格破格后日主通常身弱，取印星为用
            return SHENG_MAP.get(dm_wx, '')
        if bc_type == '合解':
            # 刑冲逢合解 → 取合化之五行为用（如子午冲逢丑合子，取土）
            # 简化处理：取印星护身为用（合解本身已化解冲刑，取印稳固）
            return SHENG_MAP.get(dm_wx, '')
        if bc_type == '制合':
            # 争合/妒合 → 取克制争合方之五行
            # 争合方为与日主争合的天干五行，取克该五行者为用
            # 简化处理：取食伤泄秀为用（食伤化解争合之纷）
            return WO_SHENG_MAP.get(dm_wx, '')
        if bc_type == '化神印':
            # 克化神 → 取化神之印（生化神的五行）
            # 化气格 pattern_name 含化X格，提取化神五行
            pattern_name = pattern.get('pattern', '')
            hua_names = {'化土格': '土', '化金格': '金', '化水格': '水',
                         '化木格': '木', '化火格': '火'}
            hua_wx = ''
            for name, wx in hua_names.items():
                if name in pattern_name:
                    hua_wx = wx
                    break
            if hua_wx:
                # 化神之印 = 生化神的五行
                return SHENG_MAP.get(hua_wx, '')
            return ''
        return ''

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
