from bazi_pro.core.branches import ZHI_BANHE, ZHI_CHONG, ZHI_HAI, ZHI_HE, ZHI_HUIFANG, ZHI_SANHE, ZHI_XING
from bazi_pro.core.disease import _find_shishen_instances, _severity
from bazi_pro.core.stems import GAN_HE


def detect_shishen_relations(day_master: str, bazi_parts: list[str]) -> list[dict]:
    """检测十神层面的逻辑关系（枭神夺食、伤官见官、财破印、食神制杀、官杀混杂）。"""
    results = []

    def _rooted(instances):
        return [x for x in instances if x['root_weight'] > 0 or x['is_transparent']]

    def _make(rel_type, disease_god, affected_god, d_inst, a_inst):
        sev = _severity([d_inst])
        return {
            'type': rel_type,
            'disease_god': disease_god,
            'disease_gan': d_inst['gan'],
            'disease_position': d_inst['position'],
            'affected_god': affected_god,
            'affected_gan': a_inst['gan'],
            'affected_position': a_inst['position'],
            'severity': sev,
        }

    # 枭神夺食
    py = _rooted(_find_shishen_instances(day_master, '偏印', bazi_parts))
    ss = _rooted(_find_shishen_instances(day_master, '食神', bazi_parts))
    py_strong = [x for x in py if x['root_weight'] >= 0.6 or x['is_transparent']]
    if py_strong and ss:
        from bazi_pro.core.disease import _best_instance
        results.append(_make('枭神夺食', '偏印', '食神',
                             _best_instance(py_strong), _best_instance(ss)))

    # 伤官见官
    sg = _rooted(_find_shishen_instances(day_master, '伤官', bazi_parts))
    zg = _rooted(_find_shishen_instances(day_master, '正官', bazi_parts))
    cai = (_rooted(_find_shishen_instances(day_master, '正财', bazi_parts))
           + _rooted(_find_shishen_instances(day_master, '偏财', bazi_parts)))
    yin_sg = (_rooted(_find_shishen_instances(day_master, '正印', bazi_parts))
              + _rooted(_find_shishen_instances(day_master, '偏印', bazi_parts)))
    if sg and zg and not cai and not yin_sg:
        from bazi_pro.core.disease import _best_instance
        results.append(_make('伤官见官', '伤官', '正官',
                             _best_instance(sg), _best_instance(zg)))

    # 财破印（需检查官杀通关：财生官→官生印，财不破印）
    cai_all = (_rooted(_find_shishen_instances(day_master, '正财', bazi_parts))
               + _rooted(_find_shishen_instances(day_master, '偏财', bazi_parts)))
    yin_all = (_rooted(_find_shishen_instances(day_master, '正印', bazi_parts))
               + _rooted(_find_shishen_instances(day_master, '偏印', bazi_parts)))
    # 官杀通关：财生官→官生印，化解财破印
    guan_sha = (_rooted(_find_shishen_instances(day_master, '正官', bazi_parts))
                + _rooted(_find_shishen_instances(day_master, '七杀', bazi_parts)))
    if cai_all and yin_all and not guan_sha:
        from bazi_pro.core.disease import _best_instance
        results.append(_make('财破印', '财星', '印星',
                             _best_instance(cai_all), _best_instance(yin_all)))

    # 食神制杀
    sha = _rooted(_find_shishen_instances(day_master, '七杀', bazi_parts))
    if ss and sha:
        from bazi_pro.core.disease import _best_instance
        results.append(_make('食神制杀', '食神', '七杀',
                             _best_instance(ss), _best_instance(sha)))

    # 官杀混杂
    si = (_rooted(_find_shishen_instances(day_master, '食神', bazi_parts))
          + _rooted(_find_shishen_instances(day_master, '伤官', bazi_parts)))
    yin2 = (_rooted(_find_shishen_instances(day_master, '正印', bazi_parts))
            + _rooted(_find_shishen_instances(day_master, '偏印', bazi_parts)))
    if zg and sha and not si and not yin2:
        from bazi_pro.core.disease import _best_instance
        results.append(_make('官杀混杂', '七杀', '正官',
                             _best_instance(sha), _best_instance(zg)))

    return results


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
    sanhe_groups = []
    for group, he_wx in ZHI_SANHE:
        if group.issubset(zhi_set):
            relations.append({
                'type': '三合局', 'elements': sorted(group),
                'result': f'{" ".join(sorted(group))} 三合成{he_wx}局',
                'hua_wuxing': he_wx,
            })
            sanhe_groups.append(set(group))

    # 半合局：两字即可成半合，气势弱于三合局
    # 《三命通会》："若三字缺一则化不成局"——半合为待局，大运流年补全可成
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
                relations.append({
                    'type': '半合局', 'elements': sorted(group),
                    'result': f'{" ".join(sorted(group))} 半合{he_wx}局',
                    'hua_wuxing': he_wx,
                })

    for group, hui_wx in ZHI_HUIFANG:
        if group.issubset(zhi_set):
            relations.append({
                'type': '会方', 'elements': sorted(group),
                'result': f'{" ".join(sorted(group))} 三会{hui_wx}方',
                'hua_wuxing': hui_wx,
            })

    return relations
