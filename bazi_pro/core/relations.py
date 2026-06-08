"""
地支关系与十神冲突检测模块

本模块负责检测命盘中的两类关系：
  1. 十神层面的逻辑冲突（枭神夺食、伤官见官、财破印、食神制杀、官杀混杂）
  2. 地支层面的刑冲合害关系（天干合、地支冲/合/害/刑、三合/半合/会方/三刑）

核心概念：
  - 伤官见官排除金日主 — 典出《子平真诠》"金水伤官喜见官"
  - 财破印需印星"轻"（无本气根），且无官杀通关 — 典出《子平真诠》"印轻逢财"
  - 官杀混杂需无食伤制杀、无印星化杀方成立
  - 有根（rooted）判断：root_weight > 0 或 is_transparent 为 True

古籍依据：
  - 《子平真诠》"论刑冲合害"：刑冲合害的基本规则与破格条件
  - 《子平真诠》"金水伤官喜见官"：金日主伤官见官不忌
  - 《子平真诠》"印轻逢财"：财破印的条件判断
  - 《三命通会》"若三字缺一则化不成局"：半合为待局

数据流：
  day_master + bazi_parts → detect_shishen_relations() → [冲突关系列表]
  bazi_parts → detect_relations() → [地支关系列表]
"""

from bazi_pro.core.branches import ZHI_BANHE, ZHI_CHONG, ZHI_HAI, ZHI_HE, ZHI_HUIFANG, ZHI_SANHE, ZHI_SANXING, ZHI_XING
from bazi_pro.core.disease import _find_shishen_instances, _severity
from bazi_pro.core.stems import GAN_HE


def detect_shishen_relations(day_master: str, bazi_parts: list[str]) -> list[dict]:
    """检测十神层面的逻辑关系（枭神夺食、伤官见官、财破印、食神制杀、官杀混杂）。

    参数:
        day_master: 日主天干（如 '甲'），用于推导十神
        bazi_parts: 四柱列表，如 ['甲子', '丙寅', '己卯', '癸酉']

    返回:
        十神冲突关系列表，每项结构：
        {
          'type': '枭神夺食',           # 冲突类型
          'disease_god': '偏印',         # 发动方十神
          'disease_gan': '壬',           # 发动方天干
          'disease_position': 0,         # 发动方位置（0=年,1=月,2=日,3=时）
          'affected_god': '食神',        # 受害方十神
          'affected_gan': '丙',          # 受害方天干
          'affected_position': 1,        # 受害方位置
          'severity': 'high'             # 严重程度（high/medium/low）
        }

    检测规则：
      - 枭神夺食：偏印有根且强（root_weight>=0.6 或透干）+ 食神有根
      - 伤官见官：排除金日主（庚辛）；需无财星、无印星方成立
      - 财破印：需无官杀通关 + 印星不重（无本气根+透干）
      - 食神制杀：食神有根 + 七杀有根
      - 官杀混杂：正官+七杀同现，需无食伤制杀、无印星化杀
    """
    results = []

    def _rooted(instances):
        """筛选有根的十神实例：root_weight > 0 或天干透出。"""
        return [x for x in instances if x['root_weight'] > 0 or x['is_transparent']]

    def _make(rel_type, disease_god, affected_god, d_inst, a_inst):
        """构造冲突关系字典，包含严重程度评估。"""
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

    # ── 枭神夺食 ──
    # 偏印克制食神，食神受制则无以生财
    # 条件：偏印强（root_weight>=0.6 或透干）+ 食神有根
    py = _rooted(_find_shishen_instances(day_master, '偏印', bazi_parts))
    ss = _rooted(_find_shishen_instances(day_master, '食神', bazi_parts))
    py_strong = [x for x in py if x['root_weight'] >= 0.6 or x['is_transparent']]
    if py_strong and ss:
        from bazi_pro.core.disease import _best_instance
        results.append(_make('枭神夺食', '偏印', '食神',
                             _best_instance(py_strong), _best_instance(ss)))

    # ── 伤官见官 ──
    # 《子平真诠》"金水伤官喜见官" — 庚辛日主除外
    # 金日主（庚辛）的伤官为水，正官为火，水火既济反为吉
    # 非金日主条件下，需无财星（财泄伤官之气）且无印星（印制伤官）方成立
    sg = _rooted(_find_shishen_instances(day_master, '伤官', bazi_parts))
    zg = _rooted(_find_shishen_instances(day_master, '正官', bazi_parts))
    if day_master not in ('庚', '辛'):
        cai = (_rooted(_find_shishen_instances(day_master, '正财', bazi_parts))
               + _rooted(_find_shishen_instances(day_master, '偏财', bazi_parts)))
        yin_sg = (_rooted(_find_shishen_instances(day_master, '正印', bazi_parts))
                  + _rooted(_find_shishen_instances(day_master, '偏印', bazi_parts)))
        # 有财星则伤官生财而不克官，有印星则印制伤官而不犯官
        if sg and zg and not cai and not yin_sg:
            from bazi_pro.core.disease import _best_instance
            results.append(_make('伤官见官', '伤官', '正官',
                                 _best_instance(sg), _best_instance(zg)))

    # ── 财破印 ──
    # 《子平真诠》"印轻逢财" — 印星强旺时财不破印
    # 条件：财星有根 + 印星有根 + 无官杀通关 + 印星不重
    # 官杀通关：财生官→官生印，化解财破印
    # 印星重：有本气根 + 透干，此时印星根基深厚，财星难以破之
    cai_all = (_rooted(_find_shishen_instances(day_master, '正财', bazi_parts))
               + _rooted(_find_shishen_instances(day_master, '偏财', bazi_parts)))
    yin_all = (_rooted(_find_shishen_instances(day_master, '正印', bazi_parts))
               + _rooted(_find_shishen_instances(day_master, '偏印', bazi_parts)))
    # 官杀通关：财生官→官生印，化解财破印
    guan_sha = (_rooted(_find_shishen_instances(day_master, '正官', bazi_parts))
                + _rooted(_find_shishen_instances(day_master, '七杀', bazi_parts)))
    # 印星强旺（有本气根+透干）时财不破印
    # "轻"的定义：无本气根或未透干，即根基不深
    yin_benqi = [x for x in yin_all if x['qi_level'] == '本气']
    yin_transparent = [x for x in yin_all if x['is_transparent']]
    yin_is_heavy = len(yin_benqi) >= 1 and len(yin_transparent) >= 1
    if cai_all and yin_all and not guan_sha and not yin_is_heavy:
        from bazi_pro.core.disease import _best_instance
        results.append(_make('财破印', '财星', '印星',
                             _best_instance(cai_all), _best_instance(yin_all)))

    # ── 食神制杀 ──
    # 食神克制七杀，为吉配（制杀留官）
    # 条件：食神有根 + 七杀有根
    sha = _rooted(_find_shishen_instances(day_master, '七杀', bazi_parts))
    if ss and sha:
        from bazi_pro.core.disease import _best_instance
        results.append(_make('食神制杀', '食神', '七杀',
                             _best_instance(ss), _best_instance(sha)))

    # ── 官杀混杂 ──
    # 正官与七杀同现，正气与偏气交战
    # 条件：正官+七杀同现，且无食伤制杀、无印星化杀
    # 食伤可制七杀（去杀留官），印星可化七杀（杀印相生）
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
    """检测命盘中的地支关系（天干合、地支冲/合/害/刑、三合/半合/会方/三刑）。

    参数:
        bazi_parts: 四柱列表，如 ['甲子', '丙寅', '己卯', '癸酉']

    返回:
        地支关系列表，每项结构：
        {
          'type': '地支冲',              # 关系类型
          'elements': ['子', '午'],       # 参与地支
          'result': '子冲午',            # 关系描述
          'hua_wuxing': '水'             # 化神五行（仅合类关系有此字段）
        }

    检测的关系类型：
      - 天干合：五组天干合化（甲己化土、乙庚化金等）
      - 地支冲：六组对冲（子午冲、丑未冲等）
      - 地支合：六组六合（子丑合土、寅亥合木等）
      - 地支害：六组相害（子未害、丑午害等）
      - 地支刑：三组相刑（寅巳刑、丑戌刑等，两支即可）
      - 三合局：四组三合（申子辰水局等，三支齐备）
      - 半合局：三合的子集（两支即可，三合成立时排除子集）
      - 会方：四组会方（寅卯辰木方等，三支齐备）
      - 三刑：三组三刑（三支齐备）
    """
    relations = []
    gans = [p[0] for p in bazi_parts if len(p) >= 1]
    zhis = [p[1] for p in bazi_parts if len(p) >= 2]

    # ── 天干合 ──
    # 遍历所有天干对，检测是否构成五组合化
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

    # ── 地支两两关系：冲、合、害、刑 ──
    # 遍历所有地支对，依次检测四种关系
    # 提前计算地支集合，用于三刑子集判断
    zhi_set = set(zhis)
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
                # 跳过已属于三刑子集的两两相刑对
                # 《三命通会》"三刑者，三支相刑也"——三刑优先于两两相刑
                in_sanxing = False
                for group, _ in ZHI_SANXING:
                    if pair.issubset(group) and group.issubset(zhi_set):
                        in_sanxing = True
                        break
                if not in_sanxing:
                    relations.append({
                        'type': '地支刑', 'elements': [zhis[i], zhis[j]],
                        'result': f'{zhis[i]}刑{zhis[j]}',
                    })

    # ── 三合局 ──
    # 三支齐备方成局，记录已成立的三合局用于排除半合子集
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

    # ── 半合局 ──
    # 两字即可成半合，气势弱于三合
    # 《三命通会》："若三字缺一则化不成局"——半合为待局，大运流年补全可成
    # 当三合局成立时，排除其子集的半合局（避免重复计算）
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

    # ── 会方 ──
    # 《滴天髓》"方是方兮局是局" — 三支同气成方
    for group, hui_wx in ZHI_HUIFANG:
        if group.issubset(zhi_set):
            relations.append({
                'type': '会方', 'elements': sorted(group),
                'result': f'{" ".join(sorted(group))} 三会{hui_wx}方',
                'hua_wuxing': hui_wx,
            })

    # ── 三刑（三支齐备） ──
    # 与两支刑不同，三刑需三支齐备方成（如寅巳申无恩之刑）
    for group, name in ZHI_SANXING:
        if group.issubset(zhi_set):
            relations.append({
                'type': '三刑', 'elements': sorted(group),
                'result': f'{" ".join(sorted(group))} {name}',
            })

    return relations
