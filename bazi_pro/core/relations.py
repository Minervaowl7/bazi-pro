from bazi_pro.core.stems import GAN_HE
from bazi_pro.core.branches import ZHI_CHONG, ZHI_HE, ZHI_HAI, ZHI_XING, ZHI_SANHE


def detect_relations(bazi_parts: list[str]) -> list[dict]:
    relations = []
    gans = [p[0] for p in bazi_parts if len(p) >= 1]
    zhis = [p[1] for p in bazi_parts if len(p) >= 2]

    for i in range(len(gans)):
        for j in range(i + 1, len(gans)):
            pair = frozenset({gans[i], gans[j]})
            if pair in GAN_HE:
                he_wx = GAN_HE[pair]
                relations.append({
                    'type': '天干合', 'elements': [gans[i], gans[j]],
                    'result': f'{gans[i]}合{gans[j]}→化{he_wx}',
                    'hua_wuxing': he_wx,
                })

    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            pair = frozenset({zhis[i], zhis[j]})
            if pair in ZHI_CHONG:
                relations.append({
                    'type': '地支冲', 'elements': [zhis[i], zhis[j]],
                    'result': f'{zhis[i]}冲{zhis[j]}',
                })
            if pair in ZHI_HE:
                he_wx = ZHI_HE[pair]
                relations.append({
                    'type': '地支合', 'elements': [zhis[i], zhis[j]],
                    'result': f'{zhis[i]}合{zhis[j]}→化{he_wx}',
                    'hua_wuxing': he_wx,
                })
            if pair in ZHI_HAI:
                relations.append({
                    'type': '地支害', 'elements': [zhis[i], zhis[j]],
                    'result': f'{zhis[i]}害{zhis[j]}',
                })
            if pair in ZHI_XING:
                relations.append({
                    'type': '地支刑', 'elements': [zhis[i], zhis[j]],
                    'result': f'{zhis[i]}刑{zhis[j]}',
                })

    zhi_set = set(zhis)
    for group, he_wx in ZHI_SANHE:
        if group.issubset(zhi_set):
            relations.append({
                'type': '三合局', 'elements': sorted(group),
                'result': f'{" ".join(sorted(group))} 三合成{he_wx}局',
                'hua_wuxing': he_wx,
            })

    return relations
