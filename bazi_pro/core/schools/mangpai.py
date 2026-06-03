"""
盲派分析器 — 做功/宾主/象法体系

本模块实现盲派命理的分析方法，核心逻辑包括：
1. 宾主分析：年月为宾（他），日时为主（我），分析宾主之间的生克关系
2. 体用分析：将十神分为体（比肩/劫财/正印/偏印/食神）和用（正财/偏财/正官/七杀/伤官）
3. 做功分析：检测6种做功类型（制用/化用/生用/合用/墓用/复合）
4. 功力评估：根据做功数量和体用强弱评估功力等级
5. 应期预测：大运流年引动做功地支时为应期
6. 贼神捕神：体旺用弱时，用神为贼神，体方为捕神
7. 五党成势：检测命局中是否形成五行势党

核心概念：
- 宾主：日时为体（我），年月为宾（他）——盲派最基本的空间划分
- 做功：宾主之间通过五行生克完成能量交换，是盲派判断命运的核心方法
- 贼神捕神：体旺用弱时，用神被体方控制，如小偷出现时警察才能抓
- 墓库收神：辰戌丑未四墓库可收特定地支入墓，形成墓用做功
- 五党成势：命局中3个以上同党五行形成势，决定命局基本方向

典籍依据：
- 段建业《盲派初级命理学》：宾主/体用/做功/贼神捕神/势
- 段建业《命理珍宝瑰宝50期》：做功类型细化/应期规则

重要规则：
- 做功 = 宾主之间通过五行生克完成能量交换
- 贼神捕神 = 体旺用弱时，用神被体方控制
- 墓库收神需按 MU_KU 表严格匹配，非任意地支可入墓
- 复合做功 = 同时存在2种以上做功类型
"""
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

# ──────────────────────────────────────────────────────────────────────
# 盲派体用分类 — 依据段建业《盲派初级命理学》
# "我们把日主、印星、禄神、比劫当体，财星、官杀星当用"
# "食神与伤官既可以是体，也可以是用……食神更近于体，伤官则接近于用"
# ──────────────────────────────────────────────────────────────────────
TI_STEMS = {'比肩', '劫财', '正印', '偏印', '食神'}   # 体：我方、自身力量
YONG_STEMS = {'正财', '偏财', '正官', '七杀', '伤官'}  # 用：他方、获取对象

# 五行相克对：(克方, 被克方)
KE_PAIRS = {('木', '土'), ('土', '水'), ('水', '火'), ('火', '金'), ('金', '木')}
# 五行相生对：(生方, 被生方)
SHENG_PAIRS = {('木', '火'), ('火', '土'), ('土', '金'), ('金', '水'), ('水', '木')}

# ──────────────────────────────────────────────────────────────────────
# 墓库收神表 — 依据段建业《盲派初级命理学》
# 四墓库（辰戌丑未）各自收纳特定地支入墓，形成"墓用"做功。
# 每个墓库有对应的五行属性和可收纳的地支集合。
#
# 收纳规则：
# - 辰为水库，收水长生(亥)及水之余气相关地支(丑/未)
# - 戌为火库，收火长生(巳)及火之余气相关地支(未)
# - 丑为金库，收金长生(申)及金旺地(酉)
# - 未为木库，收木长生(寅)及木旺地(卯)
# ──────────────────────────────────────────────────────────────────────
MU_KU = {
    '辰': {'wx': '水', 'collects': {'亥', '丑', '未'}},  # 辰墓收水：亥(水长生)、丑(水余气/金库)、未(火余气)
    '戌': {'wx': '火', 'collects': {'巳', '未'}},         # 戌墓收火：巳(火长生)、未(火余气/木库)
    '丑': {'wx': '金', 'collects': {'申', '酉'}},         # 丑墓收金：申(金长生)、酉(金旺地)
    '未': {'wx': '木', 'collects': {'寅', '卯'}},         # 未墓收木：寅(木长生)、卯(木旺地)
}

# ──────────────────────────────────────────────────────────────────────
# 五党成势表 — 依据段建业《盲派初级命理学》
# 盲派将命局五行按党派划分，3个以上同党即成"势"。
# sub_cond 为土五行的附加条件：燥土(戌未)属火党，湿土(丑辰)属金/水党。
# ──────────────────────────────────────────────────────────────────────
SHI_PARTIES = [
    {'name': '木火势', 'wx': ['木', '火']},                                     # 木火相生党
    {'name': '金水势', 'wx': ['金', '水']},                                     # 金水相生党
    {'name': '水木势', 'wx': ['水', '木']},                                     # 水木相生党
    {'name': '火燥土势', 'wx': ['火', '土'], 'sub_cond': {'土': ['戌', '未']}},  # 火配燥土
    {'name': '金湿土势', 'wx': ['金', '土'], 'sub_cond': {'土': ['丑', '辰']}},  # 金配湿土
    {'name': '水湿土势', 'wx': ['水', '土'], 'sub_cond': {'土': ['丑', '辰']}},  # 水配湿土
]


def _shishen_to_wuxing(day_master: str, shishen: str) -> str:
    """十神名称→五行映射

    根据日主五行和十神名称，推导该十神对应的五行。
    如日主为甲(木)，正财对应土（木克土）。

    Args:
        day_master: 日主天干
        shishen: 十神名称（如"正财"）

    Returns:
        str: 对应五行（如"土"），无法推导时返回空字符串
    """
    dm_wx = GAN_WUXING.get(day_master, '')
    if not dm_wx:
        return ''
    if shishen in ('比肩', '劫财'):
        return dm_wx                    # 同我
    if shishen in ('食神', '伤官'):
        return WO_SHENG_MAP.get(dm_wx, '')  # 我生
    if shishen in ('正财', '偏财'):
        return WO_KE_MAP.get(dm_wx, '')     # 我克
    if shishen in ('正官', '七杀'):
        return KE_MAP.get(dm_wx, '')        # 克我
    if shishen in ('正印', '偏印'):
        return SHENG_MAP.get(dm_wx, '')     # 生我
    return ''


class MangpaiAnalyzer(SchoolAnalyzer):
    """盲派分析器

    实现盲派命理分析方法，包含：
    - 宾主分析（_analyze_binzhu）
    - 体用分析（_analyze_tiyong）
    - 做功分析（_analyze_zuogong，含6种做功类型检测）
    - 功力评估（_evaluate_gongli）
    - 应期预测（_predict_yingqi）
    - 贼神捕神（_analyze_zeishen）
    - 五党成势（_analyze_shi）

    继承自 SchoolAnalyzer 基类，通过 register_school 注册到流派注册表。
    """

    @property
    def name(self) -> str:
        return "mangpai"

    @property
    def description(self) -> str:
        return "盲派 - 做功/宾主/象法，源自民间盲派命理传统，以体用、宾主、做功为核心分析方法"

    def analyze(self, mcp_json: dict) -> dict:
        """执行盲派完整分析

        Args:
            mcp_json: 八字输入数据，格式遵循 MCP JSON 规范

        Returns:
            dict: 盲派分析结果，包含：
                - status: 分析状态
                - school/school_name: 流派标识
                - binzhu: 宾主分析（宾位/主位十神及交战关系）
                - tiyong: 体用分析（体方/用方十神及力量）
                - zuogong: 做功分析（6种做功类型检测结果）
                - gongli: 功力评估（等级/分数/功神/废神）
                - yingqi: 应期预测（触发条件列表）
                - zeishen: 贼神捕神分析
                - shi: 五党成势分析
                - summary: 综合摘要文字
        """
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
        """宾主分析 — 盲派空间划分

        盲派将四柱分为宾主两方：
        - 宾（年月）：外部环境、他人、社会
        - 主（日时）：自身、家庭、内在

        分析宾主之间天干地支（含藏干）的五行生克关系，
        判断"宾克主"或"主克宾"及其吉凶含义。

        Args:
            day_master: 日主天干
            result: 核心分析结果

        Returns:
            dict: 宾主分析结果，含：
                - bin: 宾位十神列表
                - zhu: 主位十神列表
                - interpretations: 宾主交战解读列表
        """
        pillars = result.get('pillars', [])

        bin_positions = []  # 宾位四柱（年、月）
        zhu_positions = []  # 主位四柱（日、时）

        for p in pillars:
            pos = p.get('position', '')
            if pos in ('年', '月'):
                bin_positions.append(p)
            elif pos in ('日', '时'):
                zhu_positions.append(p)

        # 收集宾位十神（天干 + 藏干）
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

        # 收集主位十神（天干 + 藏干）
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

        # 分析宾主之间的五行相克关系
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
                    # 宾克主：宾位五行克主位五行
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
                    # 主克宾：主位五行克宾位五行
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
        """体用分析 — 盲派十神分类

        将四柱天干地支（含藏干）的十神按 TI_STEMS/YONG_STEMS 分为体用两方，
        并计算各自的五行力量值。

        体方（TI_STEMS）：比肩/劫财/正印/偏印/食神 — 自身力量
        用方（YONG_STEMS）：正财/偏财/正官/七杀/伤官 — 获取对象

        Args:
            day_master: 日主天干
            result: 核心分析结果

        Returns:
            dict: 体用分析结果，含：
                - ti: 体方十神列表（去重后）
                - yong: 用方十神列表（去重后）
                - ti_strength: 体方五行力量总和
                - yong_strength: 用方五行力量总和
        """
        pillars = result.get('pillars', [])

        ti_items = []   # 体方十神
        yong_items = []  # 用方十神

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

            # 藏干同样按体用分类
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

        # 按 (position, gan) 去重，避免同一位置同一天干重复计算
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

        # 计算体用双方五行力量
        ti_strength = self._calc_strength(deduped_ti, result)
        yong_strength = self._calc_strength(deduped_yong, result)

        return {
            'ti': deduped_ti,
            'yong': deduped_yong,
            'ti_strength': ti_strength,
            'yong_strength': yong_strength,
        }

    def _analyze_zuogong(self, day_master: str, result: dict) -> dict:
        """做功分析 — 盲派核心判断方法

        做功 = 宾主之间通过五行生克完成能量交换。
        检测6种做功类型：
        1. 制用：体方克用方（如比劫克财、食伤制杀）
        2. 化用：体方生用方（泄秀做功）
        3. 生用：体方生用方（与化用方向相同但视角不同）
        4. 合用：天干合/地支合，将用方合为我用
        5. 墓用：墓库收用方地支入墓
        6. 复合：同时存在2种以上做功类型

        Args:
            day_master: 日主天干
            result: 核心分析结果

        Returns:
            dict: 做功分析结果，键为做功类型名，值为该类型的做功列表
        """
        pillars = result.get('pillars', [])
        relations = result.get('relations', [])

        # 6种做功类型的容器
        gong_types = {
            'zhiyong': [],   # 制用：体克用
            'huayong': [],   # 化用：用泄体
            'shengyong': [], # 生用：体生用
            'heyong': [],    # 合用：天干合/地支合
            'muyong': [],    # 墓用：墓库收神
            'fuhe': [],      # 复合：多种做功并存
        }

        # ── 天干与藏干之间的做功检测 ──
        for p in pillars:
            gan = p.get('gan', '')
            gan_wx = GAN_WUXING.get(gan, '')
            gan_shishen = p.get('shishen', '')

            canggan_list = p.get('canggan', [])

            for cg_item in canggan_list:
                cg = cg_item.get('gan', '')
                cg_wx = GAN_WUXING.get(cg, '')
                cg_shishen = derive_shishen(day_master, cg)

                # 制用：天干为体，藏干为用，天干克藏干
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

                # 生用：天干为体，藏干为用，天干生藏干
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

                # 化用：藏干为体，天干为用，藏干生天干（体泄秀为用）
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

            # 食伤制杀：食神/伤官天干克制七杀/正官藏干（特殊制用）
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

        # ── 天干合做功检测 ──
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
                    # 体方合用方 → 合用做功（将用方合为我用）
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

        # ── 地支做功检测（冲/穿/合/刑） ──
        self._detect_dizhi_zuogong(pillars, day_master, gong_types)
        # ── 墓库收神检测 ──
        self._detect_muyong(pillars, gong_types)
        # ── 复合做功检测 ──
        self._detect_fuhe(gong_types)

        return gong_types

    def _detect_dizhi_zuogong(self, pillars: list, day_master: str, gong_types: dict) -> None:
        """地支间做功检测：冲、穿(害)、合、刑

        盲派做功以地支为主——地支之间的冲合刑害是做功的重要形式。
        只检测主位地支与宾位地支之间的关系（宾主做功）。

        Args:
            pillars: 四柱数据列表
            day_master: 日主天干
            gong_types: 做功类型容器（就地修改）
        """
        zhu_zhis = []  # 主位地支（日、时）
        bin_zhis = []  # 宾位地支（年、月）
        for p in pillars:
            pos = p.get('position', '')
            zhi = p.get('zhi', '')
            if not zhi:
                continue
            if pos in ('日', '时'):
                zhu_zhis.append((pos, zhi))
            elif pos in ('年', '月'):
                bin_zhis.append((pos, zhi))

        # 遍历主位与宾位地支对，检测四种关系
        for zhu_pos, zhu_zhi in zhu_zhis:
            zhu_wx = ZHI_WUXING.get(zhu_zhi, '')
            for bin_pos, bin_zhi in bin_zhis:
                bin_wx = ZHI_WUXING.get(bin_zhi, '')
                pair = frozenset({zhu_zhi, bin_zhi})

                # 冲 → 制用（主冲宾为制）
                if pair in ZHI_CHONG:
                    gong_types['zhiyong'].append({
                        'type': '制用',
                        'tool': {'position': zhu_pos, 'zhi': zhu_zhi, 'wuxing': zhu_wx},
                        'target': {'position': bin_pos, 'zhi': bin_zhi, 'wuxing': bin_wx},
                        'description': '主位{}冲宾位{}（地支冲做功）'.format(zhu_zhi, bin_zhi),
                        'mechanism': '地支冲',
                    })

                # 穿(害) → 制用
                if pair in ZHI_HAI:
                    gong_types['zhiyong'].append({
                        'type': '制用',
                        'tool': {'position': zhu_pos, 'zhi': zhu_zhi, 'wuxing': zhu_wx},
                        'target': {'position': bin_pos, 'zhi': bin_zhi, 'wuxing': bin_wx},
                        'description': '主位{}穿宾位{}（地支穿做功）'.format(zhu_zhi, bin_zhi),
                        'mechanism': '地支穿',
                    })

                # 合 → 合用（主合宾为我用）
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

                # 刑 → 制用
                if pair in ZHI_XING:
                    gong_types['zhiyong'].append({
                        'type': '制用',
                        'tool': {'position': zhu_pos, 'zhi': zhu_zhi, 'wuxing': zhu_wx},
                        'target': {'position': bin_pos, 'zhi': bin_zhi, 'wuxing': bin_wx},
                        'description': '主位{}刑宾位{}（地支刑做功）'.format(zhu_zhi, bin_zhi),
                        'mechanism': '地支刑',
                    })

    def _detect_muyong(self, pillars: list, gong_types: dict) -> None:
        """墓库收神检测 — 主位墓库收宾位地支入墓

        按MU_KU表严格匹配：只有特定地支可被特定墓库收纳。
        如辰墓只收亥/丑/未，戌墓只收巳/未。

        Args:
            pillars: 四柱数据列表
            gong_types: 做功类型容器（就地修改）
        """
        zhu_zhis = []  # 主位地支
        bin_zhis = []  # 宾位地支
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
        """复合做功检测 — 同时存在2种以上做功类型

        复合做功意味着命局做功方式多样，能量交换路径丰富，
        通常代表命主能力多元或命运复杂。

        Args:
            gong_types: 做功类型容器（就地修改）
        """
        active_types = []
        for gtype in ('zhiyong', 'huayong', 'shengyong', 'heyong', 'muyong'):
            if gong_types.get(gtype):
                active_types.append(gtype)

        # 2种以上做功类型并存即为复合结构
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
        """功力评估 — 根据做功数量和体用强弱评估功力等级

        功力等级判定规则：
        - 高功(85分)：做功≥3项 且 体强于用
        - 中功(70分)：做功≥2项 且 体≥用
        - 低功(50分)：做功≥1项
        - 无功(0分)：无做功

        同时识别功神（参与做功的干支）和废神（未参与做功的干支）。

        Args:
            zuogong: 做功分析结果
            tiyong: 体用分析结果
            day_master: 日主天干
            result: 核心分析结果

        Returns:
            dict: 功力评估结果，含：
                - level: 功力等级（高功/中功/低功/无功）
                - score: 功力分数（0-85）
                - analysis: 分析说明文字
                - gongshen: 功神列表（参与做功的干支）
                - feishen: 废神列表（未参与做功的干支）
        """
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

        # 功力等级判定：做功数量 + 体用强弱
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

        # 识别功神：参与做功的天干/地支
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

        # 识别废神：未参与做功的天干/藏干
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
        """应期预测 — 大运流年引动做功的时机

        应期三种触发机制：
        1. 大运/流年地支与做功地支发生冲合刑害 → 引动做功
        2. 贼神在大运/流年出现 → 贼神出现为应期
        3. 太岁天干与做功地支见比（同五行） → 反客为主确定应期

        Args:
            zuogong: 做功分析结果
            result: 核心分析结果
            tiyong: 体用分析结果

        Returns:
            dict: 应期预测结果，含：
                - triggers: 触发条件列表（最多10条）
                - note: 应期规则说明
        """
        all_gong = []
        for gong_list in zuogong.values():
            all_gong.extend(gong_list)

        if not all_gong:
            return {'triggers': [], 'note': '无功可应'}

        triggers = []
        relations = result.get('relations', [])

        # 收集做功涉及的地支
        gong_zhis = set()
        for g in all_gong:
            tool_pos = g.get('tool', {}).get('position', '')
            if '藏' in tool_pos:
                tool_pos = tool_pos.replace('藏', '')
            if tool_pos in ('年', '月', '日', '时'):
                for p in result.get('pillars', []):
                    if p.get('position', '') == tool_pos:
                        gong_zhis.add(p.get('zhi', ''))

        # 触发机制1：大运/流年地支与做功地支发生冲合刑害
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

        # 触发机制2：贼神出现为应期
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

        # 触发机制3：太岁见比反客为主
        pillars = result.get('pillars', [])
        for p in pillars:
            zhi = p.get('zhi', '')
            pos = p.get('position', '')
            for p2 in pillars:
                gan2 = p2.get('gan', '')
                gan2_wx = GAN_WUXING.get(gan2, '')
                zhi_wx = ZHI_WUXING.get(zhi, '')
                # 太岁天干与地支同五行 → 反客为主
                if gan2_wx and zhi_wx and gan2_wx == zhi_wx:
                    triggers.append({
                        'type': '反客为主',
                        'zhi': zhi,
                        'description': '太岁天干与{}支{}见比时确定应期'.format(pos, zhi),
                    })

        return {
            'triggers': triggers[:10],  # 限制最多10条，避免信息过载
            'note': '大运地支与原局做功地支发生冲合刑害时为应期；贼神出现为应；太岁见比反客为主' if triggers else '待大运流年引动',
        }

    def _analyze_zeishen(self, tiyong: dict, day_master: str, result: dict) -> dict:
        """贼神捕神分析 — 体旺用弱时的特殊格局

        《盲派初级命理学》："如果这个主或者体比较旺，宾或者用相对弱，
        那么这时候，我们就把它们叫做贼神和捕神"

        条件：体旺 + 用弱 → 贼神捕神格局
        - 捕神（体方）：力量强，等待时机
        - 贼神（用方）：力量弱，被体方控制
        - 应期：贼神在大运流年出现时为应期（如小偷出现时警察才能抓）

        Args:
            tiyong: 体用分析结果
            day_master: 日主天干
            result: 核心分析结果

        Returns:
            dict: 贼神捕神分析结果，含：
                - is_zeishen_pattern: 是否为贼神捕神格局
                - bushen: 捕神列表（体方十神）
                - zeishen: 贼神列表（用方十神）
                - yingqi_note: 应期说明
        """
        yong_items = tiyong.get('yong', [])
        ti_items = tiyong.get('ti', [])

        if not yong_items or not ti_items:
            return {'is_zeishen_pattern': False, 'bushen': [], 'zeishen': [], 'yingqi_note': ''}

        # 判定条件：体方力量 > 用方力量 且 用方存在
        ti_strength = self._calc_strength(ti_items, result)
        yong_strength = self._calc_strength(yong_items, result)
        is_zeishen_pattern = ti_strength > yong_strength and len(yong_items) > 0

        bushen = []  # 捕神（体方）
        zeishen = []  # 贼神（用方）

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
        """五党成势分析 — 检测命局中的五行势党

        盲派将命局五行按党派划分，3个以上同党即成"势"。
        势决定了命局的基本方向和做功方式。

        检测顺序：
        1. 先按 SHI_PARTIES 表检测双五行势（如木火势、金水势）
        2. 若无双五行势，检测单五行势（如木势、火势，需≥3个）

        土五行有附加条件（sub_cond）：燥土(戌未)属火党，湿土(丑辰)属金/水党。

        Args:
            result: 核心分析结果

        Returns:
            dict: 五党成势分析结果，含：
                - dominant_shi: 主导势名称（如"木火势"）
                - shi_type: 势类型（同 dominant_shi）
                - shi_elements: 组成势的五行元素列表
        """
        pillars = result.get('pillars', [])
        # 收集所有地支和藏干的五行
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

        # 先检测双五行势（按 SHI_PARTIES 表顺序，匹配即停）
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
                    # 土五行有附加条件：只计特定地支（如燥土只计戌未）
                    allowed_zhis = sub_cond[wx]
                    filtered = [e for e in wx_elements.get(wx, []) if e['zhi'] in allowed_zhis]
                    count = len(filtered)
                    party_elems.extend(filtered)
                else:
                    party_elems.extend(wx_elements.get(wx, []))
                total += count

            # 3个以上同党即成势
            if total >= 3 and meets_sub_cond:
                dominant_shi = party_name
                shi_type = party_name
                shi_elements = party_elems
                break

        # 若无双五行势，检测单五行势
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
        """生成盲派分析综合摘要

        Args:
            binzhu: 宾主分析结果
            tiyong: 体用分析结果
            zuogong: 做功分析结果
            gongli: 功力评估结果
            zeishen: 贼神捕神分析结果
            shi: 五党成势分析结果

        Returns:
            str: 综合摘要文字，以分号分隔各维度
        """
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
        """计算十神列表的五行力量总和

        力量来源：
        1. 十二长生状态权重（DELING_SCORE）：如长生=0.8, 帝旺=1.0
        2. 藏干气位权重（CANGGAN_WEIGHT）：如本气=0.6, 中气=0.3, 余气=0.1

        两种权重各乘0.5后累加，避免单方面权重过大。

        Args:
            items: 十神列表，每项含 gan/position
            result: 核心分析结果（含四柱数据）

        Returns:
            float: 五行力量总和（保留2位小数）
        """
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


# 注册盲派到流派注册表
register_school('mangpai', MangpaiAnalyzer)
