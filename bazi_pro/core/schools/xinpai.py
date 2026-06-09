"""
新派分析器 — 百神论/空亡论/反断论体系

本模块实现李涵辰新派命理的分析方法，核心逻辑包括：
1. 用忌神判定：基于月令与日主关系，判定身旺/身弱/从强/从弱，推导用忌神
2. 百神论：局中不存在的六亲（虚神）通过局中已有天干代测
3. 空亡论：日柱所在旬的空亡地支力量减半（非归零）——新派核心创新
4. 反断论：特定条件下用忌神互换，包括同五行反断/同宗反断/地支同现反断/纯阳反断
5. 大运吉凶：综合用忌神/空亡/反断/出空判定大运吉凶

核心概念：
- 空亡力量减半（非归零）：新派与传统命理的关键区别，空亡地支力量降为50%
- 反断 = 百神论 + 空亡反断 + 纯阳反断：特定条件下用忌神角色互换
- 同宗对：丙戊同宗、丁己同宗——天干虽异，五行同位
- 出空机制：空亡地支逢冲或逢合时出空，恢复力量

典籍依据：
- 李涵辰《八字预测真踪》：百神论/空亡论/反断论/格局分类
- 同宗对仅丙戊/丁己有典籍依据，庚壬/辛癸无典籍依据已删除

重要规则：
- 空亡力量减半(非归零) — 新派核心创新，区别于传统"空亡即无"的观点
- 反断 = 百神论 + 空亡反断 + 纯阳反断，三种触发条件独立检测
- 同宗对只保留丙戊/丁己，庚壬/辛癸无典籍依据已删除
- 从强/从弱格局用忌神方向与扶抑格相反
"""
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

# ──────────────────────────────────────────────────────────────────────
# 六甲旬空表 — 六十甲子分六旬，每旬末两位地支为空亡
# 键：旬首（甲X），值：该旬空亡的两个地支
# ──────────────────────────────────────────────────────────────────────
LIUJIA_XUN = {
    '甲子': ['戌', '亥'],  # 甲子旬：甲子→癸酉，戌亥空
    '甲戌': ['申', '酉'],  # 甲戌旬：甲戌→癸未，申酉空
    '甲申': ['午', '未'],  # 甲申旬：甲申→癸巳，午未空
    '甲午': ['辰', '巳'],  # 甲午旬：甲午→癸卯，辰巳空
    '甲辰': ['寅', '卯'],  # 甲辰旬：甲辰→癸丑，寅卯空
    '甲寅': ['子', '丑'],  # 甲寅旬：甲寅→癸亥，子丑空
}

# 天干顺序（用于六甲旬空计算）
GAN_ORDER = '甲乙丙丁戊己庚辛壬癸'
# 地支顺序（用于六甲旬空计算）
ZHI_ORDER = '子丑寅卯辰巳午未申酉戌亥'


def _get_kongwang(day_ganzhi: str) -> list:
    """根据日柱干支查六甲旬空

    六甲旬空法：将日柱干支代入六十甲子，找到所属旬首，
    旬首后两位地支即为空亡。

    新派核心创新：空亡地支力量减半（非归零），
    区别于传统命理"空亡即无"的观点。

    Args:
        day_ganzhi: 日柱干支（如"甲子"），长度必须为2

    Returns:
        list: 空亡地支列表（2个元素），如['戌', '亥']；
              输入无效时返回空列表
    """
    if len(day_ganzhi) != 2:
        return []
    gan = day_ganzhi[0]
    zhi = day_ganzhi[1]
    if gan not in GAN_ORDER or zhi not in ZHI_ORDER:
        return []
    # 在六十甲子中找到日柱序号
    day_num = -1
    g_idx, z_idx = 0, 0
    for i in range(60):
        if GAN_ORDER[g_idx] == gan and ZHI_ORDER[z_idx] == zhi:
            day_num = i
            break
        g_idx = (g_idx + 1) % 10
        z_idx = (z_idx + 1) % 12
    if day_num < 0:
        return []
    # 旬首序号 = day_num - (day_num % 10)
    xun_start = day_num - (day_num % 10)
    # 旬首地支序号
    xun_start_zhi_idx = xun_start % 12
    # 空亡地支 = 旬首后第10、11位地支（即旬尾之后的两支）
    kw1 = ZHI_ORDER[(xun_start_zhi_idx + 10) % 12]
    kw2 = ZHI_ORDER[(xun_start_zhi_idx + 11) % 12]
    return [kw1, kw2]

# 五行相克对集合（用于反断中的五行关系判断）
KE_PAIRS_SET = {('木', '土'), ('土', '水'), ('水', '火'), ('火', '金'), ('金', '木')}

# ──────────────────────────────────────────────────────────────────────
# 同宗对 — 依据李涵辰《八字预测真踪》
# 同宗 = 天干不同但五行同位，可互相代测
# 典籍只明确丙戊同宗、丁己同宗（丙戊同属阳火/阳土，丁己同属阴火/阴土）
# 庚壬/辛癸同宗无典籍依据，已删除
# ──────────────────────────────────────────────────────────────────────
TONGZONG_PAIRS = {
    '丙': '戊', '戊': '丙',  # 丙戊同宗：阳火与阳土
    '丁': '己', '己': '丁',  # 丁己同宗：阴火与阴土
}


class XinpaiAnalyzer(SchoolAnalyzer):
    """新派分析器

    实现李涵辰新派命理分析方法，包含：
    - 用忌神判定（_determine_yong_ji）
    - 百神论（_apply_baishen）
    - 空亡论（_apply_kongwang）
    - 反断论（_apply_fanduan）
    - 大运吉凶（_judge_dayun_xinpai）

    继承自 SchoolAnalyzer 基类，通过 register_school 注册到流派注册表。
    """

    @property
    def name(self) -> str:
        return "xinpai"

    @property
    def description(self) -> str:
        return "新派 - 百神论/空亡论/反断论，源自李涵辰新法，以用忌神为核心，强调空亡和反断"

    def analyze(self, mcp_json: dict) -> dict:
        """执行新派完整分析

        Args:
            mcp_json: 八字输入数据，格式遵循 MCP JSON 规范

        Returns:
            dict: 新派分析结果，包含：
                - status: 分析状态
                - school/school_name: 流派标识
                - yong_ji: 用忌神判定结果
                - baishen: 百神论分析
                - kongwang: 空亡论分析
                - fanduan: 反断论分析
                - dayun_verdict: 大运吉凶判断
                - summary: 综合摘要
                - pillars/element_forces: 核心计算结果
        """
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
        """用忌神判定 — 新派核心方法

        基于月令与日主关系，判定身旺/身弱/从强/从弱，推导用忌神。

        格局分类（依据李涵辰《八字预测真踪》）：
        - 从强格：身旺极且无根无印，帮扶≥2倍泄耗 → 用印比，忌官财食
        - 从弱格：身弱极且无根无印，泄耗≥2倍帮扶 → 用官财食，忌印比
        - 扶抑格（身旺）：用官财食，忌印比
        - 扶抑格（身弱）：用印比，忌官财食

        Args:
            result: 核心分析结果

        Returns:
            dict: 用忌神判定结果，含：
                - sheng_fu: 身旺身弱判定（身旺/身弱/从强/从弱）
                - geju_type: 格局类型（扶抑格/从强格/从弱格）
                - yongshen: 用神五行列表
                - yongshen_name: 用神十神名称列表
                - yongshen_gan: 用神天干列表
                - jishen: 忌神五行列表
                - jishen_name: 忌神十神名称列表
                - jishen_gan: 忌神天干列表
                - reason: 判定理由
        """
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
            # 从强格：顺势为用，逆势为忌
            geju_type = '从强格'
            yongshen_names = ['印星', '比劫']
            jishen_names = ['官星', '财星', '食伤']
        elif sheng_fu in ('从弱', '身弱极'):
            # 从弱格：顺势为用，逆势为忌
            geju_type = '从弱格'
            yongshen_names = ['官星', '财星', '食伤']
            jishen_names = ['印星', '比劫']
        elif sheng_fu == '身旺':
            # 扶抑格身旺：克泄耗为用，生扶为忌
            geju_type = '扶抑格'
            yongshen_names = ['官星', '财星', '食伤']
            jishen_names = ['印星', '比劫']
        else:
            # 扶抑格身弱：生扶为用，克泄耗为忌
            geju_type = '扶抑格'
            yongshen_names = ['印星', '比劫']
            jishen_names = ['官星', '财星', '食伤']

        # 将十神名称转换为具体五行
        yong_wx_list = self._names_to_wuxing(dm_wx, yongshen_names)
        ji_wx_list = self._names_to_wuxing(dm_wx, jishen_names)

        # 将五行转换为具体天干
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
        """十神名称列表→五行列表转换

        根据日主五行，将十神类别名称（如"印星"）转换为具体五行（如"水"）。

        Args:
            dm_wx: 日主五行
            names: 十神名称列表（如['印星', '比劫']）

        Returns:
            list: 去重后的五行列表
        """
        result = []
        for name in names:
            if name == '印星':
                wx = SHENG_MAP.get(dm_wx, '')   # 生我
            elif name == '比劫':
                wx = dm_wx                       # 同我
            elif name == '官星':
                wx = KE_MAP.get(dm_wx, '')       # 克我
            elif name == '财星':
                wx = WO_KE_MAP.get(dm_wx, '')    # 我克
            elif name == '食伤':
                wx = WO_SHENG_MAP.get(dm_wx, '') # 我生
            else:
                wx = ''
            if wx and wx not in result:
                result.append(wx)
        return result

    def _judge_sheng_fu(self, dm_wx: str, month_wx: str, pillars: list, day_master: str) -> str:
        """基于规则的身旺身弱判定（李涵辰法）

        判定逻辑（优先级从高到低）：
        1. 月令帮扶 + 帮扶>泄耗 → 身旺/从强
        2. 月令帮扶 + 帮扶≤泄耗 → 身弱
        3. 月令不帮扶 + 泄耗>帮扶 → 身弱/从弱
        4. 月令不帮扶 + 泄耗≤帮扶 → 身旺

        从强条件：帮扶≥2倍泄耗 且 泄耗≤1
        从弱条件：泄耗≥2倍帮扶 且 无根无印

        阳干与阴干判定差异：
        - 阳干有根/印即不从弱
        - 阴干坐印/库亦不从弱

        Args:
            dm_wx: 日主五行
            month_wx: 月令五行
            pillars: 四柱数据列表
            day_master: 日主天干

        Returns:
            str: 身旺身弱判定（'身旺'/'身弱'/'从强'/'从弱'）
        """
        if not dm_wx or not month_wx:
            return '身旺'

        is_yang_gan = day_master in ('甲', '丙', '戊', '庚', '壬')

        # 月令是否帮扶日主（同五行或生我五行）
        if month_wx == dm_wx or month_wx == SHENG_MAP.get(dm_wx, ''):
            month_help = True
        else:
            month_help = False

        all_zhis = [p.get('zhi', '') for p in pillars]
        day_zhi = pillars[2].get('zhi', '') if len(pillars) > 2 else ''
        day_zhi_wx = ZHI_WUXING.get(day_zhi, '')

        # 日主是否有本气根（地支五行与日主同）
        has_root = False
        root_count = 0
        for zhi in all_zhis:
            zhi_wx = ZHI_WUXING.get(zhi, '')
            if zhi_wx == dm_wx:
                has_root = True
                root_count += 1

        # 日主是否有印根（地支五行生日主）
        has_yin_root = False
        yin_wx = SHENG_MAP.get(dm_wx, '')
        for zhi in all_zhis:
            zhi_wx = ZHI_WUXING.get(zhi, '')
            if zhi_wx == yin_wx:
                has_yin_root = True
                break

        # 日支特殊条件：坐印/坐库
        zuoxia_is_yin = day_zhi_wx == yin_wx  # 日支为印
        zuoxia_is_ku = day_zhi in ('辰', '戌', '丑', '未') and day_zhi_wx == dm_wx  # 日支为库且与日主同五行

        # 统计四柱帮扶与泄耗力量
        help_count = 0   # 帮扶：天干/地支为比劫或印星
        drain_count = 0  # 泄耗：天干/地支为食伤/财星/官杀
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

        # ── 判定逻辑 ──
        if month_help and help_count > drain_count:
            # 月令帮扶 + 帮扶>泄耗
            # 排除月支检查其他三支是否有根/印（月支本身已是帮扶源）
            month_zhi = pillars[1].get('zhi', '') if len(pillars) > 1 else ''
            month_zhi_wx = ZHI_WUXING.get(month_zhi, '')
            other_zhis = [z for z in all_zhis if z != month_zhi or all_zhis.count(month_zhi) > 1]
            # 简化：用 has_root/root_count 减去月支贡献判断
            month_is_root = (month_zhi_wx == dm_wx)
            month_is_yin = (month_zhi_wx == yin_wx)
            has_other_root = has_root and (root_count > 1 if month_is_root else root_count > 0)
            has_other_yin = has_yin_root and not month_is_yin  # 有印根但不是月支提供的
            if not has_other_root and not has_other_yin:
                # 除月令外无根无印，但帮扶>泄耗 → 视帮扶/泄耗比例定从强或身旺
                # 《八字预测真踪》从强条件：帮扶≥2倍泄耗
                if help_count >= drain_count * 2:
                    return '从强'
                return '身旺'
            if help_count >= drain_count * 2 and drain_count <= 1:
                return '从强'       # 帮扶≥2倍泄耗且泄耗极少 → 从强
            return '身旺'
        elif month_help and help_count <= drain_count:
            # 月令帮扶但帮扶≤泄耗 → 身弱（月令虽帮扶但整体泄耗更大）
            return '身弱'
        elif not month_help and drain_count > help_count:
            # 月令不帮扶 + 泄耗>帮扶
            if is_yang_gan:
                # 阳干：有根/印/坐印/坐库即不从弱
                if has_root or has_yin_root or zuoxia_is_yin or zuoxia_is_ku:
                    return '身弱'
                if drain_count >= help_count * 2:
                    return '从弱'   # 泄耗≥2倍帮扶且无根 → 从弱
                return '身弱'
            else:
                # 阴干：坐印/坐库即不从弱
                if zuoxia_is_yin or zuoxia_is_ku:
                    return '身弱'
                if has_yin_root and root_count == 0:
                    return '身弱'   # 有印根但无比劫根 → 身弱
                if drain_count >= help_count * 2:
                    return '从弱'
                return '身弱'
        elif not month_help and drain_count <= help_count:
            # 月令不帮扶但泄耗≤帮扶 → 身旺（整体帮扶仍占优）
            return '身旺'

        # 兜底：月令帮扶→身旺，否则→身弱
        return '身旺' if month_help else '身弱'

    def _apply_baishen(self, result: dict) -> dict:
        """百神论 — 局中缺失十神的代测

        百神论：局中不存在的六亲（虚神）通过局中已有天干代测。
        注：完整规则在公开典籍中未详述，此处仅标记缺失十神及可代测位置，
        不做具体代测推断。

        Args:
            result: 核心分析结果

        Returns:
            dict: 百神论分析结果，含：
                - present_shishen: 局中已现十神列表
                - missing_shishen: 局中缺失十神列表
                - proxy_positions: 缺失十神→可代测位置映射
                - shishen_on_gan: 天干→十神映射
                - note: 说明文字
        """
        pillars = result.get('pillars', [])
        day_master = result.get('day_master', '')
        if not pillars:
            return {'present_shishen': [], 'missing_shishen': [], 'proxy_positions': {}}

        gans = [p.get('gan', '') for p in pillars]
        shishen_on_gan = [derive_shishen(day_master, g) for g in gans]

        present_shishen = set(shishen_on_gan)

        # 八字六亲十神（排除比肩——比肩即日主本身，不缺）
        liuqin_shishen = ['正官', '七杀', '正财', '偏财', '正印', '偏印', '食神', '伤官']

        missing = [ss for ss in liuqin_shishen if ss not in present_shishen]

        # 为每个缺失十神找到可代测位置（排除日干——日干为日主本身）
        proxy_positions = {}
        position_names = ['年干', '月干', '日干', '时干']
        for missing_ss in missing:
            proxies = []
            for i, gan in enumerate(gans):
                if i == 2:
                    continue  # 日干不可代测
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
        """空亡论 — 新派核心创新

        空亡地支力量减半（非归零）——新派与传统命理的关键区别。
        传统认为空亡即无，新派认为空亡只是力量减弱50%。

        出空机制：
        - 冲出空：空亡地支被冲则出空，恢复力量
        - 合出空：空亡地支被合则出空，恢复力量

        Args:
            result: 核心分析结果

        Returns:
            dict: 空亡论分析结果，含：
                - kongwang_zhi: 空亡地支列表
                - affected: 受空亡影响的地支列表（含原始/减半力量）
                - power_reduction: 力量减半百分比（50或0）
                - canggan_excluded: 是否排除空亡地支藏干
                - chukong: 出空条件列表
        """
        pillars = result.get('pillars', [])
        if not pillars:
            return {'kongwang_zhi': [], 'affected': [], 'power_reduction': 0, 'chukong': []}

        day_gan = pillars[2].get('gan', '') if len(pillars) > 2 else ''
        day_zhi = pillars[2].get('zhi', '') if len(pillars) > 2 else ''
        day_ganzhi = day_gan + day_zhi

        # 查日柱空亡地支
        kongwang_zhi = _get_kongwang(day_ganzhi)

        all_zhi = [p.get('zhi', '') for p in pillars]

        # 检测四柱中哪些地支落入空亡
        affected = []
        for pillar in pillars:
            zhi = pillar.get('zhi', '')
            if zhi in kongwang_zhi:
                affected.append({
                    'position': pillar.get('position', ''),
                    'zhi': zhi,
                    'original_power': '1.0',    # 原始力量
                    'reduced_power': '0.5',      # 空亡后力量减半
                })

        # 检测出空条件：空亡地支逢冲或逢合
        chukong = []
        for kw_zhi in kongwang_zhi:
            if kw_zhi not in all_zhi:
                continue
            for other_zhi in all_zhi:
                if other_zhi == kw_zhi:
                    continue
                pair = frozenset({kw_zhi, other_zhi})
                # 冲出空：空亡地支被冲则出空
                if pair in ZHI_CHONG:
                    chukong.append({
                        'zhi': kw_zhi,
                        'reason': '{}冲{}出空'.format(other_zhi, kw_zhi),
                        'type': '冲出空',
                    })
                    break
                # 合出空：空亡地支被合则出空
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
            'power_reduction': 50 if len(affected) > 0 else 0,  # 空亡力量减半50%
            'canggan_excluded': len(affected) > 0,  # 空亡地支的藏干也受影响
            'chukong': chukong,
        }

    def _apply_fanduan(self, result: dict, yong_ji: dict) -> dict:
        """反断论 — 特定条件下用忌神互换

        反断 = 百神论 + 空亡反断 + 纯阳反断
        四种触发条件（独立检测，可叠加）：
        1. 同五行反断：局中有两个相同五行的天干（非日干），均反断
        2. 同宗反断：月干与时干为同宗对（丙戊/丁己），时干反断
        3. 地支同现反断：局中有两个相同地支，对应五行天干反断
        4. 纯阳反断：四干全阳且日干生于刃年，年干时干反断

        反断效果：被反断的天干，用神变忌神，忌神变用神。

        Args:
            result: 核心分析结果
            yong_ji: 用忌神判定结果

        Returns:
            dict: 反断论分析结果，含：
                - conditions: 触发条件列表
                - fanduan_details: 反断详情列表（含原角色/反转后角色）
                - total_conditions: 触发条件总数
        """
        pillars = result.get('pillars', [])
        day_master = result.get('day_master', '')

        if not pillars:
            return {'conditions': [], 'fanduan_details': [], 'total_conditions': 0}

        gans = [p.get('gan', '') for p in pillars]
        zhis = [p.get('zhi', '') for p in pillars]
        shishen_list = [derive_shishen(day_master, g) for g in gans]

        conditions = []
        fanduan_targets = set()  # 需要反断的天干索引集合

        gan_wuxing_list = [GAN_WUXING.get(g, '') for g in gans]

        # ── 条件1：同五行反断 ──
        # 两个相同五行的天干（非日干）同现，均反断
        wx_indices = {}
        for i, wx in enumerate(gan_wuxing_list):
            if wx and i != 2:  # 排除日干（索引2）
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

        # ── 条件2：同宗反断 ──
        # 月干与时干为同宗对（丙戊/丁己），时干反断
        month_gan = gans[1] if len(gans) > 1 else ''
        hour_gan = gans[3] if len(gans) > 3 else ''
        if month_gan and hour_gan:
            if TONGZONG_PAIRS.get(month_gan) == hour_gan or TONGZONG_PAIRS.get(hour_gan) == month_gan:
                fanduan_targets.add(3)  # 只反断时干
                conditions.append({
                    'type': 'tongzong_fanduan',
                    'description': '月干{}与时干{}同宗，时干反断'.format(month_gan, hour_gan),
                    'action': '时干用忌互换',
                    'target_indices': [3],
                })

        # ── 条件3：地支同现反断 ──
        # 两个相同地支同现，与该地支同五行的天干反断
        zhi_indices = {}
        for i, zhi in enumerate(zhis):
            if zhi:
                zhi_indices.setdefault(zhi, []).append(i)

        for zhi, indices in zhi_indices.items():
            if len(indices) >= 2:
                for i in range(len(gans)):
                    if i == 2:
                        continue  # 排除日干
                    gan_wx = GAN_WUXING.get(gans[i], '')
                    zhi_wx = ZHI_WUXING.get(zhi, '')
                    # 天干与重复地支同五行 → 反断
                    if gan_wx == zhi_wx and i not in fanduan_targets:
                        fanduan_targets.add(i)
                        conditions.append({
                            'type': 'dizhi_tongxing_fanduan',
                            'description': '局中两{}地支同现，{}干{}反断'.format(
                                zhi, ['年', '月', '日', '时'][i] if i < 4 else '', gans[i]),
                            'action': '相关天干用忌互换',
                            'target_indices': [i],
                        })

        # ── 条件4：纯阳反断 ──
        # 四干全阳 + 日干生于刃年 → 年干时干反断
        is_chunyang = all(g in ('甲', '丙', '戊', '庚', '壬') for g in gans if g)
        if is_chunyang and len(gans) >= 4:
            year_zhi = zhis[0] if zhis else ''
            yangren_zhi = YANGREN_MAP.get(day_master, '')
            if year_zhi == yangren_zhi:
                for i in (0, 3):  # 年干和时干反断
                    if i not in fanduan_targets and i < len(gans):
                        fanduan_targets.add(i)
                conditions.append({
                    'type': 'chunyang_fanduan',
                    'description': '纯阳且日干生于刃年，年干{}、时干{}反断'.format(gans[0], gans[3] if len(gans) > 3 else ''),
                    'action': '年干时干用忌互换',
                    'target_indices': [0, 3],
                })

        # 生成反断详情：被反断天干的原角色与反转后角色
        fanduan_details = []
        for idx in sorted(fanduan_targets):
            if idx < len(gans):
                gan = gans[idx]
                ss = shishen_list[idx]
                wx = GAN_WUXING.get(gan, '')
                is_yong = wx in yong_ji.get('yongshen', [])
                new_role = '忌神' if is_yong else '用神'  # 用忌互换
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
        """新派大运吉凶判断

        综合用忌神/空亡/反断/出空判定大运吉凶：
        1. 反断调整：被反断的天干用忌互换
        2. 空亡判断：大运地支空亡→平（力量减半）
        3. 出空判断：空亡地支已出空→按用忌神正常判断
        4. 用忌神判断：天干为用神→吉，为忌神→凶

        优先级：空亡未出空 > 出空/非空亡的用忌判断

        Args:
            result: 核心分析结果
            yong_ji: 用忌神判定结果
            kongwang: 空亡论分析结果
            fanduan: 反断论分析结果

        Returns:
            list: 大运判断列表，每项含：
                - step/gan/zhi: 大运基本信息
                - shishen: 十神
                - verdict: 吉凶判定（'吉'/'凶'/'平'）
                - detail: 判定详情
                - is_kongwang/is_chukong/is_fanduan: 标记位
        """
        dayun_list = result.get('dayun', []) if 'dayun' in result else []
        if not dayun_list:
            dayun_list = self._generate_dayun_from_pillars(result)

        yong_wx_list = yong_ji.get('yongshen', [])
        kongwang_zhi = kongwang.get('kongwang_zhi', [])
        chukong_zhi = [c.get('zhi', '') for c in kongwang.get('chukong', [])]
        day_master = result.get('day_master', '')

        # 收集被反断的天干
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

            # 反断调整：用忌互换
            if is_fanduan:
                is_yong = not is_yong

            # 判定逻辑（优先级从高到低）
            if is_kongwang and not is_chukong:
                # 空亡未出空 → 平（力量减半，吉凶不明）
                verdict = '平'
                detail = '大运地支{}空亡，力量减半'.format(zhi)
            elif is_kongwang and is_chukong:
                # 空亡已出空 → 按用忌神正常判断
                if is_yong:
                    verdict = '吉'
                    detail = '大运地支{}原空亡已出空，天干{}({})为用神'.format(zhi, gan, gan_wx)
                else:
                    verdict = '凶'
                    detail = '大运地支{}原空亡已出空，天干{}({})为忌神'.format(zhi, gan, gan_wx)
            elif is_yong:
                # 非空亡，天干为用神 → 吉
                verdict = '吉'
                if is_fanduan:
                    detail = '大运天干{}({})为用神（经反断调整）'.format(gan, gan_wx)
                else:
                    detail = '大运天干{}({})为用神'.format(gan, gan_wx)
            else:
                # 非空亡，天干为忌神 → 凶
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
        """从四柱生成简化大运列表（备用方案）

        当核心分析结果中无大运数据时，用四柱天干地支模拟大运。
        仅取月柱/日柱/时柱作为第1/2/3步大运。

        Args:
            result: 核心分析结果

        Returns:
            list: 简化大运列表
        """
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
        """生成新派分析综合摘要

        Args:
            yong_ji: 用忌神判定结果
            kongwang: 空亡论分析结果
            fanduan: 反断论分析结果

        Returns:
            dict: 综合摘要，含：
                - yongshen: 用神名称
                - jishen: 忌神名称
                - kongwang: 空亡地支
                - fanduan_count: 反断条件数
                - geju_type: 格局类型
                - advice: 综合建议文字
        """
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
                advice += '空亡{}，力量减半。出空条件：{}。'.format(kong_str, chukong_str)
            else:
                advice += '空亡{}，力量减半。'.format(kong_str)
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


# 注册新派到流派注册表
register_school('xinpai', XinpaiAnalyzer)
