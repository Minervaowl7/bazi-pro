"""
子平派分析器 — 传统子平法格局用神体系

本模块实现传统子平派（又称"格局派"）的分析方法，核心逻辑包括：
1. 破格用神调整：根据《子平真诠》第九章"论用神成败救应"，
   当格局出现破格条件时，调整用神方向以"救应"格局。
2. 大运吉凶判断：依据《子平真诠》第四十七章"论大运"，
   以用神/喜神/忌神与大运天干地支的生克关系判定吉凶。

核心概念：
- 格局用神法：以月令取格，六层筛查定格局，格局用神优先，扶抑用神次之
- 破格救应：每种破格类型有对应的救应用神方向（见 _BREAK_ADJUST）
- 大运判断：天干地支分别评分，用神/喜神为吉，忌神为凶，生用克忌亦吉

典籍依据：
- 《子平真诠》沈孝瞻著，第九章"论用神成败救应"、第四十七章"论大运"
- 破格类型及救应规则均出自"论用神成败救应"原文

重要规则：
- 破格调整只第一个破格条件调整用神，后续破格只调整喜忌
  （《子平真诠》"因成得败因败得成"——多重破格只取最关键的用神调整）
"""
import copy

from bazi_pro.core import full_analysis
from bazi_pro.core.constants import GAN_WUXING, WUXING_TO_GAN, ZHI_WUXING, derive_shishen
from bazi_pro.core.schools import register_school  # noqa: E402
from bazi_pro.core.schools.base import SchoolAnalyzer
from bazi_pro.core.stems import KE_MAP, SHENG_MAP, WO_KE_MAP, WO_SHENG_MAP

# ──────────────────────────────────────────────────────────────────────
# 破格用神调整表 — 依据《子平真诠》第九章"论用神成败救应"
# 每种破格都有对应的救应用神方向
# 键：破格类型名（与 patterns.py 中 break_conditions 的 type 字段对应）
# 值：救应用神的十神类别（str 或 list，list 时取第一个为首选）
# ──────────────────────────────────────────────────────────────────────
_BREAK_ADJUST = {
    # ── 正格破格 ──
    '伤官见官': '印星',          # "官逢伤而透印以解之"——印星制伤护官
    '比劫争财': ['食伤', '官杀'],  # "财逢食生而身强带比" / 官杀制比劫——两种救应路径
    '财星破印': '比劫',          # "印轻逢财" → 比劫夺财护印
    '枭神夺食': '财星',          # "食逢枭" → 财制枭护食
    '财透七煞': '食神',          # "财透七煞" → 食神制煞
    '生财露煞': '食神',          # 同上，财格生财带煞
    '财党杀无制': '食神',        # "煞逢食制"——食神制煞解财党杀
    '身强印重透煞': '食伤',      # 印格身强印重透煞 → 食伤制杀泄印
    '生财带煞': '食神',          # 伤官格生财带煞 → 食神制煞
    '官星逢冲': '合解',          # "刑冲而会合以解之"——合来解冲
    '官星逢刑': '合解',          # 同上，合来解刑
    '佩印无根': '比劫',          # 印需有根，比劫生印助根
    '孤官无辅': ['财星', '印星'],  # "官逢财印"——财印为官星辅佐
    '透煞印无财官': ['财星', '官星'],  # 建禄月劫需财官——财官为禄劫格用神
    # ── 从格/化气格破格 ──
    '命逢根气': '逆势',          # 从格破格，日主得根气，需重新取扶抑用神
    '余气根': '逆势',            # 同上，余气亦为根
    '争合': '制合',              # 化气格争合——取克制争合方之五行
    '妒合': '制合',              # 化气格妒合——同上
    '克化神': '化神印',          # 化气格克化神 → 取化神之印（生化神的五行）
}

# ──────────────────────────────────────────────────────────────────────
# 破格用神→五行关系映射表
# 将十神类别（如"印星"）转换为日主五行关系（如"生我"），
# 再通过 KE_MAP/SHENG_MAP 等映射表推导出具体五行。
# 特殊键 '_special' 表示需在 _resolve_special_break 中单独处理，
# 无法通过简单的五行关系映射推导。
# ──────────────────────────────────────────────────────────────────────
_BREAK_YONGSHEN_WX = {
    '印星': '生我',       # 印星 = 生我之五行
    '官杀': '克我',       # 官杀 = 克我之五行
    '官星': '克我',       # 官星 = 克我之五行（与官杀同义，用于不同破格类型）
    '比劫': '同我',       # 比劫 = 同我之五行
    '财星': '我克',       # 财星 = 我克之五行
    '食伤': '我生',       # 食伤 = 我生之五行
    '食神': '我生',       # 食神 = 我生之五行（食伤的子集）
    # 特殊键：需在 _adjust_yongshen_for_break 中单独处理
    '合解': '_special',   # 刑冲逢合解，需查冲支的合化五行
    '逆势': '_special',   # 从格破格，需重新取扶抑用神
    '制合': '_special',   # 争合/妒合，需取克制争合方之五行
    '化神印': '_special', # 克化神 → 取化神之印（生化神的五行）
}


class ZipingAnalyzer(SchoolAnalyzer):
    """子平派分析器

    实现传统子平法格局用神体系，包含：
    - 破格用神调整（_adjust_yongshen_for_break）
    - 大运吉凶判断（_judge_dayun）

    继承自 SchoolAnalyzer 基类，通过 register_school 注册到流派注册表。
    """

    @property
    def name(self) -> str:
        return 'ziping'

    @property
    def description(self) -> str:
        return '传统子平法：格局用神法，以月令取格，六层筛查定格局，格局用神优先，扶抑用神次之，调候用神补充'

    def analyze(self, mcp_json: dict) -> dict:
        """执行子平派完整分析

        Args:
            mcp_json: 八字输入数据，格式遵循 MCP JSON 规范
                必含字段：year/month/day/hour（天干地支）

        Returns:
            dict: 子平派分析结果，包含：
                - status: 分析状态（'completed' / 'error'）
                - school: 流派标识（'ziping'）
                - school_name: 流派中文名
                - pattern: 格局信息（含 break_conditions）
                - wangshuai: 旺衰判定
                - yongshen: 调整后的用神/喜神/忌神
                - break_conditions: 破格条件列表
                - tiaohou: 调候用神
                - dayun_verdict: 大运吉凶判断列表
                - pillars/element_forces/relations: 核心计算结果
        """
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

        # 破格用神调整：根据破格条件修正用神方向
        adjusted_yongshen = self._adjust_yongshen_for_break(
            day_master, dm_wx, pattern, yongshen, break_conditions
        )

        # 大运吉凶判断：用调整后的用神评估每步大运
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
        """根据破格条件调整用神方向

        依据《子平真诠》"论用神成败救应"，当格局出现破格时，
        需调整用神以"救应"格局。

        重要规则：只第一个破格条件调整用神，后续破格只调整喜忌。
        原因：《子平真诠》"因成得败因败得成"——多重破格只取最关键的用神调整，
        后续破格通过喜忌微调而非反复更换用神。

        Args:
            day_master: 日主天干（如"甲"）
            dm_wx: 日主五行（如"木"）
            pattern: 格局信息字典，含 pattern_name、break_conditions 等
            yongshen: 原始用神字典，含 yongshen/xishen/jishen 及其天干
            break_conditions: 破格条件列表，每项含 type/severity 等

        Returns:
            dict: 调整后的用神字典，结构与输入 yongshen 相同
        """
        if not break_conditions:
            return yongshen

        result = copy.deepcopy(yongshen)

        first_break = True  # 标记是否为第一个破格条件（第一个调整用神，后续只调喜忌）
        for bc in break_conditions:
            bc_type = bc.get('type', '')
            new_category = _BREAK_ADJUST.get(bc_type)
            if new_category is None:
                continue

            # 列表型取第一个为首选救应方向
            if isinstance(new_category, list):
                new_category = new_category[0]

            # 将十神类别映射为日主五行关系
            rel = _BREAK_YONGSHEN_WX.get(new_category, '')
            if not rel or not dm_wx:
                continue

            # 特殊键处理：合解/逆势/制合/化神印
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
                # 第一个破格条件：调整用神本身
                result['yongshen'] = new_wx
                result['yongshen_gan'] = WUXING_TO_GAN.get(new_wx, '')

                # 原用神降为喜神（若与新用神不同）
                new_xi = [w for w in old_xi if w != new_wx]
                if old_yong and old_yong != new_wx and old_yong not in new_xi:
                    new_xi.append(old_yong)
                result['xishen'] = new_xi
                result['xishen_gan'] = [WUXING_TO_GAN.get(w, '') for w in new_xi]

                # 新用神从忌神中移除
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
        """处理 _BREAK_YONGSHEN_WX 中 '_special' 类型的破格用神调整

        特殊破格类型无法通过简单的五行关系映射推导，需根据具体情况计算。

        Args:
            day_master: 日主天干
            dm_wx: 日主五行
            pattern: 格局信息字典
            bc_type: 破格类型名
            bc: 破格条件详情

        Returns:
            str: 救应用神的五行（如"木"），无法推导时返回空字符串
        """
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
            # 化气格名称→化神五行映射
            hua_names = {'化土格': '土', '化金格': '金', '化水格': '水',
                         '化木格': '木', '化火格': '火'}
            hua_wx = ''
            for name, wx in hua_names.items():
                if name in pattern_name:
                    hua_wx = wx
                    break
            if hua_wx:
                # 化神之印 = 生化神的五行（如化神为火，则印为木）
                return SHENG_MAP.get(hua_wx, '')
            return ''
        return ''

    def _judge_dayun(
        self, day_master: str, dm_wx: str, yongshen: dict, core: dict,
    ) -> list:
        """大运吉凶判断 — 依据《子平真诠》第四十七章"论大运"

        判断逻辑：
        1. 天干地支分别评分（+1/-1/0）
        2. 天干/地支为用神或喜神 → +1（吉）
        3. 天干/地支为忌神 → -1（凶）
        4. 天干/地支生用神 → +1（间接吉）
        5. 天干/地支克忌神 → +1（间接吉）
        6. 天干/地支生忌神 → -1（间接凶）
        7. 总分 > 0 为吉，< 0 为凶，= 0 为平

        Args:
            day_master: 日主天干
            dm_wx: 日主五行
            yongshen: 用神字典（含 yongshen/xishen/jishen）
            core: 核心分析结果（含 dayun 列表）

        Returns:
            list: 大运判断列表，每项含：
                - step: 大运步数
                - gan/zhi: 天干地支
                - shishen: 十神
                - verdict: 吉凶判定（'吉'/'凶'/'平'）
                - detail: 判定详情文字
        """
        dayun_list = core.get('dayun', [])
        if not dayun_list:
            return []

        yong_wx = yongshen.get('yongshen', '')
        ji_list = yongshen.get('jishen', [])
        xi_list = yongshen.get('xishen', [])
        if not yong_wx or not dm_wx:
            return []

        # 有利五行集合 = 用神 + 喜神
        favorable_wx = {yong_wx}
        if xi_list:
            favorable_wx.update(xi_list)

        # 不利五行集合 = 忌神
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

            gan_score = 0  # 天干评分：+1吉/-1凶/0中性
            zhi_score = 0  # 地支评分：+1吉/-1凶/0中性
            details = []

            # ── 天干评分 ──
            if gan_wx in favorable_wx:
                # 天干为用神或喜神 → 直接吉
                gan_score += 1
                details.append('天干{}({})为喜用'.format(gan, gan_wx))
            elif gan_wx in unfavorable_wx:
                # 天干为忌神 → 直接凶
                gan_score -= 1
                details.append('天干{}({})为忌神'.format(gan, gan_wx))
            elif (gan_wx, yong_wx) in _sheng_pairs():
                # 天干生用神 → 间接吉
                gan_score += 1
                details.append('天干{}({})生用神{}'.format(gan, gan_wx, yong_wx))
            else:
                # 检查是否克忌神（间接吉）或生忌神（间接凶）
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

            # ── 地支评分（逻辑与天干对称） ──
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

            # 综合天干地支评分判定吉凶
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


# ──────────────────────────────────────────────────────────────────────
# 五行生克对（延迟初始化，避免模块级重复计算）
# 用于大运判断中"生用神""克忌神"等间接关系判定
# ──────────────────────────────────────────────────────────────────────
_SHENG_PAIRS = None  # 五行相生对：(生方, 被生方)
_KE_PAIRS = None     # 五行相克对：(克方, 被克方)


def _sheng_pairs():
    """五行相生对集合（延迟初始化）

    Returns:
        set: {('木','火'), ('火','土'), ('土','金'), ('金','水'), ('水','木')}
    """
    global _SHENG_PAIRS
    if _SHENG_PAIRS is None:
        _SHENG_PAIRS = {('木', '火'), ('火', '土'), ('土', '金'), ('金', '水'), ('水', '木')}
    return _SHENG_PAIRS


def _ke_pairs():
    """五行相克对集合（延迟初始化）

    Returns:
        set: {('木','土'), ('土','水'), ('水','火'), ('火','金'), ('金','木')}
    """
    global _KE_PAIRS
    if _KE_PAIRS is None:
        _KE_PAIRS = {('木', '土'), ('土', '水'), ('水', '火'), ('火', '金'), ('金', '木')}
    return _KE_PAIRS


# 注册子平派到流派注册表
register_school('ziping', ZipingAnalyzer)
