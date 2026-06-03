from bazi_pro.core.branches import CANGGAN_WEIGHT, ZHI_BANHE, ZHI_HUIFANG, ZHI_SANHE
from bazi_pro.core.constants import GAN_WUXING
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.stems import GAN_HE

# 月令旺地：天干合化成功需要的月支条件
_HE_HUA_YUELING = {
    frozenset({'甲', '己'}): {'辰', '戌', '丑', '未'},  # 甲己合化土
    frozenset({'乙', '庚'}): {'申', '酉'},              # 乙庚合化金
    frozenset({'丙', '辛'}): {'亥', '子'},              # 丙辛合化水
    frozenset({'丁', '壬'}): {'寅', '卯'},              # 丁壬合化木
    frozenset({'戊', '癸'}): {'巳', '午'},              # 戊癸合化火
}


def _gan_he_hua_wuxing(gan1: str, gan2: str, month_zhi: str,
                       bazi_parts: list[str]) -> str:
    """判断两个天干合化是否成功，返回化神五行（失败返回空字符串）。"""
    pair = frozenset({gan1, gan2})
    if pair not in GAN_HE:
        return ''
    hua_wx = GAN_HE[pair]
    required_months = _HE_HUA_YUELING.get(pair, set())
    # 条件1：月令为化神旺地
    if month_zhi in required_months:
        return hua_wx
    # 条件2：时支为化神旺地
    # 《三命通会》："若不得月中旺气，只时上旺气，亦可"
    hour_zhi = bazi_parts[3][1] if len(bazi_parts) >= 4 and len(bazi_parts[3]) >= 2 else ''
    if hour_zhi:
        for cg, ql in get_canggan(hour_zhi):
            if GAN_WUXING.get(cg, '') == hua_wx and ql in ('本气', '中气'):
                return hua_wx
    return ''


def _detect_hehua(bazi_parts: list[str], month_zhi: str) -> dict:
    """
    检测命盘中的合化情况。
    返回:
        { 'gan_he': [{'gans': [a,b], 'hua_wx': '土', 'type': '天干合化'}, ...],
          'zhi_sanhe': [{'zhis': [...], 'hua_wx': '水'}, ...],
          'zhi_banhe': [{'zhis': [...], 'hua_wx': '水'}, ...],
          'zhi_huifang': [{'zhis': [...], 'hui_wx': '木'}, ...] }
    """
    result = {'gan_he': [], 'zhi_sanhe': [], 'zhi_banhe': [], 'zhi_huifang': []}
    gans = [p[0] for p in bazi_parts if len(p) >= 1]
    zhis = [p[1] for p in bazi_parts if len(p) >= 2]

    # 天干合化（含位置紧贴检查和争合检测）
    # 位置相邻：年-月、月-日、日-时为紧贴，其余为遥合
    for i in range(len(gans)):
        for j in range(i + 1, len(gans)):
            hua_wx = _gan_he_hua_wuxing(gans[i], gans[j], month_zhi, bazi_parts)
            if hua_wx:
                adjacent = (j - i == 1)
                result['gan_he'].append({
                    'gans': [gans[i], gans[j]],
                    'hua_wx': hua_wx,
                    'type': '天干合化',
                    'adjacent': adjacent,
                    'positions': [i, j],
                })

    # 争合检测：一天干同时与两个以上天干有合化可能（此合化被削弱或无效）
    gan_he_count = {}
    for item in result['gan_he']:
        for g in item['gans']:
            gan_he_count[g] = gan_he_count.get(g, 0) + 1
    for item in result['gan_he']:
        contested = any(gan_he_count.get(g, 0) > 1 for g in item['gans'])
        if contested:
            item['contested'] = True

    # 地支三合局
    zhi_set = set(zhis)
    sanhe_groups = []
    for group, he_wx in ZHI_SANHE:
        if group.issubset(zhi_set):
            result['zhi_sanhe'].append({
                'zhis': sorted(group),
                'hua_wx': he_wx,
                'type': '三合局',
            })
            sanhe_groups.append(set(group))

    # 半合局（两字即可成局，气势弱于三合）
    # 当三合局成立时，排除其子集的半合局
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

    # 会方
    for group, hui_wx in ZHI_HUIFANG:
        if group.issubset(zhi_set):
            result['zhi_huifang'].append({
                'zhis': sorted(group),
                'hui_wx': hui_wx,
                'type': '会方',
            })

    return result


def calc_element_forces(bazi_parts: list[str], month_zhi: str) -> dict:
    """计算五行基础力量（含合化动态修正）。"""
    forces = {'木': 0.0, '火': 0.0, '土': 0.0, '金': 0.0, '水': 0.0}

    for i, part in enumerate(bazi_parts):
        if len(part) < 2:
            continue
        gan, zhi = part[0], part[1]

        gan_wx = GAN_WUXING.get(gan, '')
        if gan_wx:
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

        for cg, ql in get_canggan(zhi):
            cg_wx = GAN_WUXING.get(cg, '')
            if not cg_wx:
                continue
            weight = CANGGAN_WEIGHT.get(ql, 0)
            if i == 1 and ql == '本气':
                weight *= 1.5
            forces[cg_wx] += weight

    # 合化动态修正
    hehua = _detect_hehua(bazi_parts, month_zhi)
    forces_adjusted = dict(forces)

    # 天干合化修正：只转移参与合化的天干力量
    # 《子平真诠》"合而化者，两失其本气" — 合化双方各失本气、归化神
    for item in hehua['gan_he']:
        if not item.get('adjacent', False):
            continue
        hua_wx = item['hua_wx']
        for g in item['gans']:
            g_wx = GAN_WUXING.get(g, '')
            if g_wx and g_wx != hua_wx:
                # 只转移该天干贡献的力量（1.2或0.5），而非该五行全部力量
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
                transfer = gan_contribution * 0.5
                forces_adjusted[g_wx] -= transfer
                forces_adjusted[hua_wx] += transfer

    # 三合局修正：只转移参与三合的地支中非化神五行的藏干力量
    # 《三命通会》"三合者，生旺墓之合" — 三支合为一气
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

    total_raw = max(0.01, sum(forces.values()))
    pct_raw = {k: round(v / total_raw * 100, 1) for k, v in forces.items()}

    # 合化修正后力量不可为负 — 防御性保护
    for k in forces_adjusted:
        forces_adjusted[k] = max(0, forces_adjusted[k])

    total = max(0.01, sum(forces_adjusted.values()))
    pct_adjusted = {k: round(v / total * 100, 1) for k, v in forces_adjusted.items()}

    return {
        'raw': forces,
        'percent': pct_raw,
        'percent_adjusted': pct_adjusted,
        'total': round(total_raw, 2),
        'hehua': hehua,
    }
