from bazi_pro.core.branches import CANGGAN_WEIGHT
from bazi_pro.core.constants import GAN_WUXING
from bazi_pro.core.hidden_stems import get_canggan


def calc_element_forces(bazi_parts: list[str], month_zhi: str) -> dict:
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
            forces[gan_wx] += 1.2 if has_root else 0.5

        for cg, ql in get_canggan(zhi):
            cg_wx = GAN_WUXING.get(cg, '')
            if not cg_wx:
                continue
            weight = CANGGAN_WEIGHT.get(ql, 0)
            if i == 1 and ql == '本气':
                weight *= 1.5
            forces[cg_wx] += weight

    total = max(0.01, sum(forces.values()))
    pct = {k: round(v / total * 100, 1) for k, v in forces.items()}
    return {'raw': forces, 'percent': pct, 'total': round(total, 2)}
