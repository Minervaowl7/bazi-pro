"""神煞查表 — 覆盖 20+ 种常见神煞，含含义说明和流年刑冲合害"""

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

SHENSHA_DESC: dict[str, str] = {
    "天乙贵人": "逢凶化吉，遇难呈祥，主贵人相助",
    "文昌贵人": "主聪明好学，利考试、文艺、学术",
    "驿马": "主奔波流动，利出行、迁移、变动",
    "桃花": "主人缘、异性缘，亦主才艺风流",
    "华盖": "主孤高清雅，利宗教、艺术、学术",
    "将星": "主权威领导，利掌权、管理",
    "禄神": "主衣食丰足，自力更生之福",
    "羊刃": "主刚强果断，过旺则主灾伤刑克",
    "金舆": "主出行安逸，利车马交通",
    "天德贵人": "主逢凶化吉，一生少灾",
    "月德贵人": "主仁慈宽厚，遇事有贵人扶持",
    "孤辰": "主孤独，男命尤忌，主离祖别亲",
    "寡宿": "主孤寡，女命尤忌，主婚姻不顺",
}

LIUNIAN_CHONG: dict[str, str] = {
    "子": "午", "午": "子", "丑": "未", "未": "丑",
    "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}

LIUNIAN_HE: dict[str, str] = {
    "子": "丑", "丑": "子", "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯", "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳", "午": "未", "未": "午",
}

LIUNIAN_XING: dict[str, list[str]] = {
    "子": ["卯"], "卯": ["子"],
    "寅": ["巳", "申"], "巳": ["寅", "申"], "申": ["寅", "巳"],
    "丑": ["未", "戌"], "未": ["丑", "戌"], "戌": ["丑", "未"],
    "辰": ["辰"], "午": ["午"], "酉": ["酉"], "亥": ["亥"],
}

LIUNIAN_HAI: dict[str, str] = {
    "子": "未", "未": "子", "丑": "午", "午": "丑",
    "寅": "巳", "巳": "寅", "卯": "辰", "辰": "卯",
    "申": "亥", "亥": "申", "酉": "戌", "戌": "酉",
}

TIANGAN_HE: dict[str, str] = {
    "甲": "己", "己": "甲", "乙": "庚", "庚": "乙",
    "丙": "辛", "辛": "丙", "丁": "壬", "壬": "丁",
    "戊": "癸", "癸": "戊",
}

TIANGAN_CHONG: dict[str, str] = {
    "甲": "庚", "庚": "甲", "乙": "辛", "辛": "乙",
    "丙": "壬", "壬": "丙", "丁": "癸", "癸": "丁",
}

TIANYI_GUIREN: dict[str, list[str]] = {
    "甲": ["丑", "未"], "戊": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "庚": ["丑", "未"], "辛": ["寅", "午"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
}

WENCHANG: dict[str, str] = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
    "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯",
}

YIMA: dict[str, str] = {
    "寅": "申", "午": "申", "戌": "申",
    "申": "寅", "子": "寅", "辰": "寅",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳",
}

TAOHUA: dict[str, str] = {
    "寅": "卯", "午": "卯", "戌": "卯",
    "申": "酉", "子": "酉", "辰": "酉",
    "巳": "午", "酉": "午", "丑": "午",
    "亥": "子", "卯": "子", "未": "子",
}

HUAGAI: dict[str, str] = {
    "寅": "戌", "午": "戌", "戌": "戌",
    "申": "辰", "子": "辰", "辰": "辰",
    "巳": "丑", "酉": "丑", "丑": "丑",
    "亥": "未", "卯": "未", "未": "未",
}

JIANGXING: dict[str, str] = {
    "寅": "午", "午": "午", "戌": "午",
    "申": "子", "子": "子", "辰": "子",
    "巳": "酉", "酉": "酉", "丑": "酉",
    "亥": "卯", "卯": "卯", "未": "卯",
}

LUSHEN: dict[str, str] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}

YANGREN: dict[str, str] = {
    "甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午",
    "己": "巳", "庚": "酉", "辛": "申", "壬": "子", "癸": "亥",
}

JINYU: dict[str, str] = {
    "甲": "辰", "乙": "巳", "丙": "未", "丁": "申", "戊": "未",
    "己": "申", "庚": "戌", "辛": "亥", "壬": "丑", "癸": "寅",
}

TIANDE: dict[str, str] = {
    "寅": "丁", "卯": "申", "辰": "壬", "巳": "辛",
    "午": "亥", "未": "甲", "申": "癸", "酉": "寅",
    "戌": "丙", "亥": "乙", "子": "巳", "丑": "庚",
}

YUEDE: dict[str, str] = {
    "寅": "丙", "午": "丙", "戌": "丙",
    "申": "壬", "子": "壬", "辰": "壬",
    "巳": "庚", "酉": "庚", "丑": "庚",
    "亥": "甲", "卯": "甲", "未": "甲",
}

GUCHEN: dict[str, str] = {
    "寅": "巳", "卯": "巳", "辰": "巳",
    "巳": "申", "午": "申", "未": "申",
    "申": "亥", "酉": "亥", "戌": "亥",
    "亥": "寅", "子": "寅", "丑": "寅",
}

GUASU: dict[str, str] = {
    "寅": "丑", "卯": "丑", "辰": "丑",
    "巳": "辰", "午": "辰", "未": "辰",
    "申": "未", "酉": "未", "戌": "未",
    "亥": "戌", "子": "戌", "丑": "戌",
}


def calc_shensha(bazi_parts: list[str]) -> list[dict]:
    """计算命盘中的神煞"""
    if len(bazi_parts) < 4:
        return []

    day_gan = bazi_parts[2][0] if len(bazi_parts[2]) >= 2 else ""
    day_zhi = bazi_parts[2][1] if len(bazi_parts[2]) >= 2 else ""
    year_zhi = bazi_parts[0][1] if len(bazi_parts[0]) >= 2 else ""
    month_zhi = bazi_parts[1][1] if len(bazi_parts[1]) >= 2 else ""
    all_zhis = [p[1] for p in bazi_parts if len(p) >= 2]
    all_gans = [p[0] for p in bazi_parts if len(p) >= 2]
    positions = ["年", "月", "日", "时"]

    results: list[dict] = []

    guiren_zhis = TIANYI_GUIREN.get(day_gan, [])
    for idx, zhi in enumerate(all_zhis):
        if zhi in guiren_zhis:
            results.append({"name": "天乙贵人", "position": positions[idx],
                            "type": "吉", "desc": SHENSHA_DESC.get("天乙贵人", "")})

    wc_zhi = WENCHANG.get(day_gan, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == wc_zhi:
            results.append({"name": "文昌贵人", "position": positions[idx],
                            "type": "吉", "desc": SHENSHA_DESC.get("文昌贵人", "")})

    yima_zhi = YIMA.get(day_zhi, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == yima_zhi:
            results.append({"name": "驿马", "position": positions[idx],
                            "type": "吉", "desc": SHENSHA_DESC.get("驿马", "")})

    th_zhi = TAOHUA.get(day_zhi, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == th_zhi:
            results.append({"name": "桃花", "position": positions[idx],
                            "type": "中", "desc": SHENSHA_DESC.get("桃花", "")})

    hg_zhi = HUAGAI.get(day_zhi, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == hg_zhi:
            results.append({"name": "华盖", "position": positions[idx],
                            "type": "吉", "desc": SHENSHA_DESC.get("华盖", "")})

    jx_zhi = JIANGXING.get(day_zhi, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == jx_zhi:
            results.append({"name": "将星", "position": positions[idx],
                            "type": "吉", "desc": SHENSHA_DESC.get("将星", "")})

    lu_zhi = LUSHEN.get(day_gan, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == lu_zhi:
            results.append({"name": "禄神", "position": positions[idx],
                            "type": "吉", "desc": SHENSHA_DESC.get("禄神", "")})

    yr_zhi = YANGREN.get(day_gan, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == yr_zhi:
            results.append({"name": "羊刃", "position": positions[idx],
                            "type": "凶", "desc": SHENSHA_DESC.get("羊刃", "")})

    jy_zhi = JINYU.get(day_gan, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == jy_zhi:
            results.append({"name": "金舆", "position": positions[idx],
                            "type": "吉", "desc": SHENSHA_DESC.get("金舆", "")})

    td_gan = TIANDE.get(month_zhi, "")
    if td_gan:
        for idx, gan in enumerate(all_gans):
            if gan == td_gan:
                results.append({"name": "天德贵人", "position": positions[idx],
                                "type": "吉", "desc": SHENSHA_DESC.get("天德贵人", "")})

    yd_gan = YUEDE.get(month_zhi, "")
    if yd_gan:
        for idx, gan in enumerate(all_gans):
            if gan == yd_gan:
                results.append({"name": "月德贵人", "position": positions[idx],
                                "type": "吉", "desc": SHENSHA_DESC.get("月德贵人", "")})

    gc_zhi = GUCHEN.get(year_zhi, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == gc_zhi:
            results.append({"name": "孤辰", "position": positions[idx],
                            "type": "凶", "desc": SHENSHA_DESC.get("孤辰", "")})

    gs_zhi = GUASU.get(year_zhi, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == gs_zhi:
            results.append({"name": "寡宿", "position": positions[idx],
                            "type": "凶", "desc": SHENSHA_DESC.get("寡宿", "")})

    return results


def calc_liunian_relations(liunian_gan: str, liunian_zhi: str,
                           bazi_parts: list[str]) -> list[dict]:
    """计算流年干支与原局四柱的刑冲合害关系"""
    if len(bazi_parts) < 4:
        return []

    positions = ["年", "月", "日", "时"]
    natal_gans = [p[0] for p in bazi_parts if len(p) >= 2]
    natal_zhis = [p[1] for p in bazi_parts if len(p) >= 2]
    results: list[dict] = []

    for idx, nzhi in enumerate(natal_zhis):
        if LIUNIAN_CHONG.get(liunian_zhi) == nzhi:
            results.append({"type": "冲", "target": f"{positions[idx]}支{nzhi}",
                            "desc": f"流年{liunian_zhi}冲{positions[idx]}支{nzhi}"})
        if LIUNIAN_HE.get(liunian_zhi) == nzhi:
            results.append({"type": "合", "target": f"{positions[idx]}支{nzhi}",
                            "desc": f"流年{liunian_zhi}合{positions[idx]}支{nzhi}"})
        xing_targets = LIUNIAN_XING.get(liunian_zhi, [])
        if nzhi in xing_targets and nzhi != liunian_zhi:
            results.append({"type": "刑", "target": f"{positions[idx]}支{nzhi}",
                            "desc": f"流年{liunian_zhi}刑{positions[idx]}支{nzhi}"})
        if LIUNIAN_HAI.get(liunian_zhi) == nzhi:
            results.append({"type": "害", "target": f"{positions[idx]}支{nzhi}",
                            "desc": f"流年{liunian_zhi}害{positions[idx]}支{nzhi}"})

    for idx, ngan in enumerate(natal_gans):
        if TIANGAN_HE.get(liunian_gan) == ngan:
            results.append({"type": "合", "target": f"{positions[idx]}干{ngan}",
                            "desc": f"流年{liunian_gan}合{positions[idx]}干{ngan}"})
        if TIANGAN_CHONG.get(liunian_gan) == ngan:
            results.append({"type": "冲", "target": f"{positions[idx]}干{ngan}",
                            "desc": f"流年{liunian_gan}冲{positions[idx]}干{ngan}"})

    return results
