"""
五行力量计算模块 — 元素力量核心逻辑

本模块负责计算命盘中五行（木火土金水）的基础力量分布，并根据天干合化、
地支三合/半合/会方等关系进行动态修正，输出原始力量和修正后力量两套数据。

核心概念：
  - 有根天干力量 1.0，无根天干力量 0.4 — 典出《子平真诠》"干多不如根重"
  - 天干合化只转移该天干贡献的力量（1.0 或 0.4），非全局五行转移
  - 三合局权重 0.5、半合局权重 0.2、会方权重 0.3 — 均为藏干级别转移
  - forces_adjusted 负数保护：max(0, ...)，防止合化修正导致力量为负

古籍依据：
  - 《子平真诠》"论合化"：天干合化的月令条件与力量转移规则
  - 《滴天髓》"论方局"：会方三支同气，非化神五行被压制
  - 《三命通会》"三合者，生旺墓之合"：三合局力量归一

数据流：
  bazi_parts + month_zhi → calc_element_forces() → {raw, percent, percent_adjusted, total, hehua}
  其中 percent 为原始百分比，percent_adjusted 为合化修正后百分比（格局筛查用 percent，
  化气格用 percent_adjusted）。
"""

from bazi_pro.core.branches import CANGGAN_WEIGHT, ZHI_BANHE, ZHI_HE, ZHI_HUIFANG, ZHI_SANHE
from bazi_pro.core.constants import GAN_WUXING
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.stems import GAN_HE

# 月令旺地：天干合化成功需要的月支条件
# 典出《子平真诠》"论合化"：合化须得月令旺气方成
# 每组 frozenset 为合化天干对，值为该合化所需的月支集合（化神旺地）
_HE_HUA_YUELING = {
    frozenset({'甲', '己'}): {'辰', '戌', '丑', '未'},  # 甲己合化土 — 土旺于四季
    frozenset({'乙', '庚'}): {'申', '酉'},              # 乙庚合化金 — 金旺于秋
    frozenset({'丙', '辛'}): {'亥', '子'},              # 丙辛合化水 — 水旺于冬
    frozenset({'丁', '壬'}): {'寅', '卯'},              # 丁壬合化木 — 木旺于春
    frozenset({'戊', '癸'}): {'巳', '午'},              # 戊癸合化火 — 火旺于夏
}


def _gan_he_hua_wuxing(gan1: str, gan2: str, month_zhi: str,
                       bazi_parts: list[str]) -> str:
    """判断两个天干合化是否成功，返回化神五行（失败返回空字符串）。

    合化成功的两个条件（满足其一即可）：
      1. 月令为化神旺地 — 《子平真诠》"得令则化"
      2. 时支藏干含化神五行之本气/中气 — 《三命通会》"若不得月中旺气，只时上旺气，亦可"

    参数:
        gan1: 第一个天干（如 '甲'）
        gan2: 第二个天干（如 '己'）
        month_zhi: 月支（判断月令旺地）
        bazi_parts: 四柱列表，如 ['甲子', '丙寅', '己卯', '癸酉']

    返回:
        化神五行字符串（如 '土'），合化不成功则返回空字符串 ''
    """
    pair = frozenset({gan1, gan2})
    if pair not in GAN_HE:
        return ''
    hua_wx = GAN_HE[pair]  # 化神五行
    required_months = _HE_HUA_YUELING.get(pair, set())
    # 条件1：月令为化神旺地
    if month_zhi in required_months:
        return hua_wx
    # 条件2：时支为化神旺地
    # 《三命通会》："若不得月中旺气，只时上旺气，亦可"
    hour_zhi = bazi_parts[3][1] if len(bazi_parts) >= 4 and len(bazi_parts[3]) >= 2 else ''
    if hour_zhi:
        for cg, ql in get_canggan(hour_zhi):
            # 时支藏干含化神五行的本气或中气，方可替代月令
            if GAN_WUXING.get(cg, '') == hua_wx and ql in ('本气', '中气'):
                return hua_wx
    return ''


def _detect_hehua(bazi_parts: list[str], month_zhi: str) -> dict:
    """检测命盘中的合化情况（天干合化 + 地支三合/半合/会方/六合）。

    参数:
        bazi_parts: 四柱列表，如 ['甲子', '丙寅', '己卯', '癸酉']
        month_zhi: 月支，用于判断天干合化的月令条件

    返回:
        合化信息字典，结构如下：
        {
          'gan_he': [         # 天干合化列表
            {'gans': ['甲','己'], 'hua_wx': '土', 'type': '天干合化',
             'adjacent': True, 'positions': [0,1], 'contested': False}
          ],
          'zhi_sanhe': [      # 地支三合局列表
            {'zhis': ['申','子','辰'], 'hua_wx': '水', 'type': '三合局'}
          ],
          'zhi_banhe': [      # 地支半合局列表（三合局子集已排除）
            {'zhis': ['子','辰'], 'hua_wx': '水', 'type': '半合局'}
          ],
          'zhi_huifang': [    # 地支会方列表
            {'zhis': ['寅','卯','辰'], 'hui_wx': '木', 'type': '会方'}
          ],
          'zhi_liuhe': [      # 地支六合列表
            {'zhis': ['巳','申'], 'hua_wx': '水', 'type': '六合'}
          ]
        }
    """
    result = {'gan_he': [], 'zhi_sanhe': [], 'zhi_banhe': [], 'zhi_huifang': [], 'zhi_liuhe': []}
    gans = [p[0] for p in bazi_parts if len(p) >= 1]
    zhis = [p[1] for p in bazi_parts if len(p) >= 2]

    # ── 地支六合检测 ──
    # 《三命通会》"六合者，子合丑、寅合亥" — 六合两支合化一气
    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            pair = frozenset({zhis[i], zhis[j]})
            if pair in ZHI_HE:
                hua_wx = ZHI_HE[pair]
                result['zhi_liuhe'].append({
                    'zhis': [zhis[i], zhis[j]],
                    'hua_wx': hua_wx,
                    'type': '六合',
                })

    # ── 天干合化检测 ──
    # 含位置紧贴检查和争合检测
    # 位置相邻：年-月(0-1)、月-日(1-2)、日-时(2-3)为紧贴，其余为遥合
    for i in range(len(gans)):
        for j in range(i + 1, len(gans)):
            hua_wx = _gan_he_hua_wuxing(gans[i], gans[j], month_zhi, bazi_parts)
            if hua_wx:
                adjacent = (j - i == 1)  # 紧贴合化力量更强，遥合力弱
                result['gan_he'].append({
                    'gans': [gans[i], gans[j]],
                    'hua_wx': hua_wx,
                    'type': '天干合化',
                    'adjacent': adjacent,
                    'positions': [i, j],
                })

    # 争合检测：一天干同时与两个以上天干有合化可能（此合化被削弱或无效）
    # 《子平真诠》"争合"：两干争合一干，合而不化
    gan_he_count = {}
    for item in result['gan_he']:
        for g in item['gans']:
            gan_he_count[g] = gan_he_count.get(g, 0) + 1
    for item in result['gan_he']:
        contested = any(gan_he_count.get(g, 0) > 1 for g in item['gans'])
        if contested:
            item['contested'] = True

    # ── 地支三合局检测 ──
    # 《三命通会》"三合者，生旺墓之合" — 三支齐全方成局
    zhi_set = set(zhis)
    sanhe_groups = []  # 记录已成立的三合局，用于排除半合子集
    for group, he_wx in ZHI_SANHE:
        if group.issubset(zhi_set):
            result['zhi_sanhe'].append({
                'zhis': sorted(group),
                'hua_wx': he_wx,
                'type': '三合局',
            })
            sanhe_groups.append(set(group))

    # ── 半合局检测 ──
    # 两字即可成局，气势弱于三合
    # 当三合局成立时，排除其子集的半合局（避免重复计算）
    # 《三命通会》："若三字缺一则化不成局"——半合为待局
    for group, he_wx in ZHI_BANHE:
        if group.issubset(zhi_set):
            # 检查此半合是否是任一三合局的子集
            is_subset_of_sanhe = False
            for sg in sanhe_groups:
                if group.issubset(sg):
                    is_subset_of_sanhe = True
                    break
            if not is_subset_of_sanhe:
                result['zhi_banhe'].append({
                    'zhis': sorted(group),
                    'hua_wx': he_wx,
                    'type': '半合局',
                })

    # ── 会方检测 ──
    # 《滴天髓》"方是方兮局是局" — 会方三支同气，力量集中
    for group, hui_wx in ZHI_HUIFANG:
        if group.issubset(zhi_set):
            result['zhi_huifang'].append({
                'zhis': sorted(group),
                'hui_wx': hui_wx,
                'type': '会方',
            })

    return result


def calc_element_forces(bazi_parts: list[str], month_zhi: str) -> dict:
    """计算五行基础力量（含合化动态修正）。

    计算流程：
      1. 遍历四柱，累加天干力量（有根1.0/无根0.4）和地支藏干力量
      2. 月支本气乘以1.5倍 — 月令为提纲，力量最重
      3. 检测合化关系，对 forces 进行动态修正得到 forces_adjusted
      4. 分别计算原始百分比和修正后百分比

    参数:
        bazi_parts: 四柱列表，如 ['甲子', '丙寅', '己卯', '癸酉']
        month_zhi: 月支，用于判断天干合化月令条件和月令加成

    返回:
        {
          'raw': {'木': 2.4, '火': 1.0, ...},           # 原始力量值
          'percent': {'木': 30.0, '火': 12.5, ...},      # 原始百分比
          'percent_adjusted': {'木': 35.2, '火': 10.1, ...}, # 合化修正后百分比
          'total': 8.0,                                    # 原始力量总和
          'hehua': {...}                                    # 合化检测详情
        }

    重要说明：
      - 格局筛查用 percent（原始），化气格用 percent_adjusted（合化修正）
      - 有根天干=1.0（与地支本气等同），无根天干=0.4（虚浮无力）
        典出《子平真诠》"干多不如根重"
      - 天干合化只转移该天干贡献的力量（1.0/0.4），非全局五行转移
      - 三合局0.5权重、半合局0.2权重、会方0.3权重 — 均为藏干级别转移
      - forces_adjusted 负数保护：max(0, ...)
    """
    forces = {'木': 0.0, '火': 0.0, '土': 0.0, '金': 0.0, '水': 0.0}

    for i, part in enumerate(bazi_parts):
        if len(part) < 2:
            continue
        gan, zhi = part[0], part[1]

        # ── 天干力量计算 ──
        gan_wx = GAN_WUXING.get(gan, '')
        if gan_wx:
            # 判断天干是否有根：遍历四柱地支藏干，查找同五行的本气/中气
            has_root = False
            for p2 in bazi_parts:
                if len(p2) < 2:
                    continue
                for cg, ql in get_canggan(p2[1]):
                    if GAN_WUXING.get(cg, '') == gan_wx and ql in ('本气', '中气'):
                        has_root = True
                        break
                if has_root:
                    break
            # 《子平真诠》"干多不如根重" — 天干有根只是"不虚浮"，力量不应超过地支本气(1.0)
            # 有根天干=1.0（与地支本气等同），无根天干=0.4（虚浮无力）
            forces[gan_wx] += 1.0 if has_root else 0.4

        # ── 地支藏干力量计算 ──
        for cg, ql in get_canggan(zhi):
            cg_wx = GAN_WUXING.get(cg, '')
            if not cg_wx:
                continue
            weight = CANGGAN_WEIGHT.get(ql, 0)
            # 月支本气乘以1.5倍 — 月令为提纲，力量最重
            # 用 month_zhi 参数判断（比 i==1 更健壮），确保即使 bazi_parts 顺序异常也不误判
            if zhi == month_zhi and ql == '本气':
                weight *= 1.5
            forces[cg_wx] += weight

    # ── 合化动态修正 ──
    hehua = _detect_hehua(bazi_parts, month_zhi)
    forces_adjusted = dict(forces)

    # 天干合化修正：只转移参与合化的天干力量
    # 《子平真诠》"合而化者，两失其本气" — 合化双方各失本气、归化神
    # 关键：只转移该天干贡献的力量（1.0或0.4），而非该五行全部力量
    for item in hehua['gan_he']:
        if not item.get('adjacent', False):
            continue  # 遥合不参与力量修正，只有紧贴合化才转移力量
        hua_wx = item['hua_wx']
        for g in item['gans']:
            g_wx = GAN_WUXING.get(g, '')
            if g_wx and g_wx != hua_wx:
                # 只转移该天干贡献的力量（1.0或0.4），而非该五行全部力量
                # 先计算该天干贡献了多少力量
                has_root = False
                for p2 in bazi_parts:
                    if len(p2) < 2:
                        continue
                    for cg, ql in get_canggan(p2[1]):
                        if GAN_WUXING.get(cg, '') == g_wx and ql in ('本气', '中气'):
                            has_root = True
                            break
                    if has_root:
                        break
                gan_contribution = 1.0 if has_root else 0.4
                # 转移50%的天干力量到化神五行
                # 保留50%是因为合化非完全丧失本气，仍有余气
                transfer = gan_contribution * 0.5
                forces_adjusted[g_wx] -= transfer
                forces_adjusted[hua_wx] += transfer

    # 三合局修正：只转移参与三合的地支中非化神五行的藏干力量
    # 《三命通会》"三合者，生旺墓之合" — 三支合为一气
    # 权重0.5：三合局力量较强，非化神藏干50%力量转移至化神
    for item in hehua['zhi_sanhe']:
        hua_wx = item['hua_wx']
        for zhi in item['zhis']:
            for cg, ql in get_canggan(zhi):
                cg_wx = GAN_WUXING.get(cg, '')
                if cg_wx and cg_wx != hua_wx:
                    weight = CANGGAN_WEIGHT.get(ql, 0)
                    transfer = weight * 0.5
                    forces_adjusted[cg_wx] -= transfer
                    forces_adjusted[hua_wx] += transfer

    # 半合局力量修正：转化率20%，弱于三合局(50%)
    # 《三命通会》："若三字缺一则化不成局"——半合为待局
    for item in hehua['zhi_banhe']:
        hua_wx = item['hua_wx']
        for zhi in item['zhis']:
            for cg, ql in get_canggan(zhi):
                cg_wx = GAN_WUXING.get(cg, '')
                if cg_wx and cg_wx != hua_wx:
                    weight = CANGGAN_WEIGHT.get(ql, 0)
                    transfer = weight * 0.2
                    forces_adjusted[cg_wx] -= transfer
                    forces_adjusted[hua_wx] += transfer

    # 会方修正：《滴天髓》"方是方兮局是局" — 会方三支同气，非化神五行被压制
    # 会方不是凭空加力，而是同方异五行被转化为会方五行
    # 权重0.3：会方力量介于三合(0.5)和半合(0.2)之间
    for item in hehua['zhi_huifang']:
        hui_wx = item['hui_wx']
        for zhi in item['zhis']:
            for cg, ql in get_canggan(zhi):
                cg_wx = GAN_WUXING.get(cg, '')
                if cg_wx and cg_wx != hui_wx:
                    weight = CANGGAN_WEIGHT.get(ql, 0)
                    transfer = weight * 0.3
                    forces_adjusted[cg_wx] -= transfer
                    forces_adjusted[hui_wx] += transfer

    # 六合修正
    # 六合化气出处：
    # 《神峰通考·安星辰法》"寅亥二宫属木，卯戌二宫属火，辰酉二宫属金，
    #   申巳二宫属水，子丑二宫属土"
    # 《欽定協紀辨方書》"所以又以其左右合宫而得：寅亥木、卯戌火、辰酉金、巳申水"
    # 《三命通会·论支元六合》述数理："巳为六阳，申为三阴，六三得九数"、
    #   "已合申福慢，申合巳官气盛"
    # 六合修正仅影响 forces_adjusted（化气格/修正后百分比），不影响原始 forces（正格判定）。
    # 权重0.25：六合力量与半合局相当，两支合力弱于三合（0.5）。
    for item in hehua.get('zhi_liuhe', []):
        hua_wx = item['hua_wx']
        for zhi in item['zhis']:
            for cg, ql in get_canggan(zhi):
                cg_wx = GAN_WUXING.get(cg, '')
                if cg_wx and cg_wx != hua_wx:
                    weight = CANGGAN_WEIGHT.get(ql, 0)
                    transfer = weight * 0.25
                    forces_adjusted[cg_wx] -= transfer
                    forces_adjusted[hua_wx] += transfer

    # ── 计算原始百分比 ──
    total_raw = max(0.01, sum(forces.values()))  # 下限保护，避免除零
    pct_raw = {k: round(v / total_raw * 100, 1) for k, v in forces.items()}

    # 合化修正后力量不可为负 — 防御性保护
    # 极端情况下多次转移可能导致负值，此处截断为0
    for k in forces_adjusted:
        forces_adjusted[k] = max(0, forces_adjusted[k])

    # ── 计算修正后百分比 ──
    total = max(0.01, sum(forces_adjusted.values()))  # 下限保护，避免除零
    pct_adjusted = {k: round(v / total * 100, 1) for k, v in forces_adjusted.items()}

    return {
        'raw': forces,               # 原始力量值（未修正）
        'percent': pct_raw,          # 原始百分比 — 格局筛查使用此值
        'percent_adjusted': pct_adjusted,  # 合化修正后百分比 — 化气格使用此值
        'total': round(total_raw, 2),      # 原始力量总和
        'hehua': hehua,              # 合化检测详情
    }
