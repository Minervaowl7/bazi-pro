"""神煞查表 — 覆盖 40+ 种常见神煞，含含义说明和流年刑冲合害"""

import json
import os
import re
import tempfile

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
    "甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子",
}
# 注意：阴干（乙丁己辛癸）无羊刃。《渊海子平》羊刃只论阳干，
# 阴干的帝旺位（如乙在寅）不叫羊刃。旧代码将阴干帝旺位也标为羊刃是错误的。

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

TAIJI_GUIREN: dict[str, list[str]] = {
    "甲": ["子", "午"], "乙": ["子", "午"],
    "丙": ["卯", "酉"], "丁": ["卯", "酉"],
    "戊": ["辰", "戌", "丑", "未"], "己": ["辰", "戌", "丑", "未"],
    "庚": ["寅", "亥"], "辛": ["寅", "亥"],
    "壬": ["巳", "申"], "癸": ["巳", "申"],
}

KUIGUI: dict[str, str] = {
    "庚": "辰", "辛": "辰", "壬": "戌", "癸": "戌",
}

TIANLUO: dict[str, str] = {
    "辰": "巳", "巳": "辰",
}

DIWANG: dict[str, str] = {
    "戌": "亥", "亥": "戌",
}

WANGCHEN: dict[str, str] = {
    # 亡神查法 — 《三命通会》亡神=三合局临官位
    # 口诀："寅午戌亡神在巳，申子辰亡神在亥，巳酉丑亡神在申，亥卯未亡神在寅"
    "寅": "巳", "午": "巳", "戌": "巳",
    "申": "亥", "子": "亥", "辰": "亥",
    "巳": "申", "酉": "申", "丑": "申",
    "亥": "寅", "卯": "寅", "未": "寅",
}

TIANCHU_GUIREN: dict[str, str] = {
    # 天厨贵人 = 食神之禄位
    # 甲食丙禄巳、乙食丁禄午、丙食戊禄巳、丁食己禄午、
    # 戊食庚禄申、己食辛禄酉、庚食壬禄亥、辛食癸禄子、
    # 壬食甲禄寅、癸食乙禄卯
    "甲": "巳", "乙": "午", "丙": "巳", "丁": "午",
    "戊": "申", "己": "酉", "庚": "亥", "辛": "子",
    "壬": "寅", "癸": "卯",
}

HONGLUAN: dict[str, str] = {
    # 红鸾以年支查 — 口诀："子年红鸾卯，丑寅，寅丑，卯子，辰亥，巳戌，午酉，未申，申未，酉午，戌巳，亥辰"
    "子": "卯", "丑": "寅", "寅": "丑", "卯": "子",
    "辰": "亥", "巳": "戌", "午": "酉", "未": "申",
    "申": "未", "酉": "午", "戌": "巳", "亥": "辰",
}

TIANXI: dict[str, str] = {
    # 天喜以年支查，与红鸾对冲
    # 子→酉，丑→申，寅→未，卯→午，辰→巳，巳→辰，
    # 午→卯，未→寅，申→丑，酉→子，戌→亥，亥→戌
    "子": "酉", "丑": "申", "寅": "未", "卯": "午",
    "辰": "巳", "巳": "辰", "午": "卯", "未": "寅",
    "申": "丑", "酉": "子", "戌": "亥", "亥": "戌",
}

HONGYAN: dict[str, str] = {
    # 《三命通会》："甲乙逢午、丙寅、丁未、戊子、己辰、庚戌、辛酉、壬巳、癸申"
    "甲": "午", "乙": "午", "丙": "寅", "丁": "未",
    "戊": "子", "己": "辰", "庚": "戌", "辛": "酉",
    "壬": "巳", "癸": "申",
}

LIUXIA: dict[str, str] = {
    # 流霞查法口诀："甲鸡乙犬丙羊加，丁是猴乡戊见蛇，己马庚辛逢鼠地，壬猪癸兔是流霞"
    # 鸡=酉，犬=戌，羊=未，猴=申，蛇=巳，马=午，鼠=子，猪=亥，兔=卯
    "甲": "酉", "乙": "戌", "丙": "未", "丁": "申",
    "戊": "巳", "己": "午", "庚": "子", "辛": "子",
    "壬": "亥", "癸": "卯",
}

XUETANG: dict[str, str] = {
    "甲": "亥", "乙": "午", "丙": "寅", "丁": "酉",
    "戊": "寅", "己": "酉", "庚": "巳", "辛": "子",
    "壬": "申", "癸": "卯",
}

CIGAN: dict[str, str] = {
    # 词馆 = 学堂之对冲（学堂取年干长生位，词馆取其冲位）
    # 甲学堂亥→词馆巳，乙学堂午→词馆子，丙学堂寅→词馆申，
    # 丁学堂酉→词馆卯，戊学堂寅→词馆申，己学堂酉→词馆卯，
    # 庚学堂巳→词馆亥，辛学堂子→词馆午，壬学堂申→词馆寅，
    # 癸学堂卯→词馆酉
    "甲": "巳", "乙": "子", "丙": "申", "丁": "卯",
    "戊": "申", "己": "卯", "庚": "亥", "辛": "午",
    "壬": "寅", "癸": "酉",
}

GUOYIN: dict[str, str] = {
    # 国印查法口诀："甲戌乙亥丙丑丁寅戊丑己寅庚未辛申壬辰癸巳"
    "甲": "戌", "乙": "亥", "丙": "丑", "丁": "寅",
    "戊": "丑", "己": "寅", "庚": "未", "辛": "申",
    "壬": "辰", "癸": "巳",
}

# ===== 新增神煞查表 =====

JIESHA: dict[str, str] = {
    "申": "巳", "子": "巳", "辰": "巳",
    "寅": "亥", "午": "亥", "戌": "亥",
    "巳": "寅", "酉": "寅", "丑": "寅",
    "亥": "申", "卯": "申", "未": "申",
}

ZAISHA: dict[str, str] = {
    # 灾煞 = 劫煞之对冲
    # 申子辰年劫煞巳→灾煞亥，寅午戌年劫煞亥→灾煞巳，
    # 巳酉丑年劫煞寅→灾煞申，亥卯未年劫煞申→灾煞寅
    "寅": "巳", "午": "巳", "戌": "巳",
    "申": "亥", "子": "亥", "辰": "亥",
    "巳": "申", "酉": "申", "丑": "申",
    "亥": "寅", "卯": "寅", "未": "寅",
}

YUANCHEN: dict[str, str] = {
    "子": "辰", "丑": "戌", "寅": "丑", "卯": "辰",
    "辰": "丑", "巳": "辰", "午": "戌", "未": "丑",
    "申": "辰", "酉": "戌", "戌": "丑", "亥": "辰",
}

# 咸池即桃花别名，查法完全相同，不重复建表
XIANCHI = TAOHUA

JIAOSHA: dict[str, str] = {
    # 绞煞查法口诀 — 《协纪辨方书》：
    # "申子辰绞在卯，寅午戌绞在酉，巳酉丑绞在午，亥卯未绞在子"
    "申": "卯", "子": "卯", "辰": "卯",
    "寅": "酉", "午": "酉", "戌": "酉",
    "巳": "午", "酉": "午", "丑": "午",
    "亥": "子", "卯": "子", "未": "子",
}

TIANYI_YI: dict[str, str] = {
    # 天医查法口诀："正卯二辰三巳推，四午五未六申随，七酉八戌九亥位，十子十一丑寅归"
    # 寅月→卯，卯月→辰，辰月→巳，巳月→午，午月→未，未月→申，
    # 申月→酉，酉月→戌，戌月→亥，亥月→子，子月→丑，丑月→寅
    "寅": "卯", "卯": "辰", "辰": "巳", "巳": "午",
    "午": "未", "未": "申", "申": "酉", "酉": "戌",
    "戌": "亥", "亥": "子", "子": "丑", "丑": "寅",
}

SANQI_TIAN: list[str] = ["甲", "戊", "庚"]
SANQI_REN: list[str] = ["乙", "丙", "丁"]
SANQI_DI: list[str] = ["壬", "癸", "辛"]

DE_XIU_TIANDE_HE: dict[str, str] = {
    "丁": "壬", "壬": "丁",
}
DE_XIU_YUEDE_HE: dict[str, str] = {
    "丙": "辛", "辛": "丙", "丁": "壬", "壬": "丁",
    "甲": "己", "己": "甲", "乙": "庚", "庚": "乙",
    "戊": "癸", "癸": "戊",
}

ANLU: dict[str, str] = {
    # 暗禄 = 禄神之对冲
    # 甲禄寅→暗禄申，乙禄卯→暗禄酉，丙禄巳→暗禄亥，丁禄午→暗禄子，
    # 戊禄巳→暗禄亥，己禄午→暗禄子，庚禄申→暗禄寅，辛禄酉→暗禄卯，
    # 壬禄亥→暗禄巳，癸禄子→暗禄午
    "甲": "申", "乙": "酉", "丙": "亥", "丁": "子",
    "戊": "亥", "己": "子", "庚": "寅", "辛": "卯",
    "壬": "巳", "癸": "午",
}

XUEREN: dict[str, str] = {
    # 血刃 = 羊刃同位（帝旺位）。《渊海子平》羊刃只论阳干，阴干无血刃。
    "甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子",
}

JIELU_KONGWANG: dict[str, list[str]] = {
    "甲": ["申"], "乙": ["酉"],
    "丙": ["辰"], "丁": ["巳"],
    "戊": ["辰"], "己": ["巳"],
    "庚": ["寅"], "辛": ["卯"],
    "壬": ["子", "戌"], "癸": ["丑", "亥"],
}

SHENSHA_DESC_EXTRA: dict[str, str] = {
    "太极贵人": "主聪慧好学，近道近佛，利玄学研究",
    "魁罡": "主性格刚毅，聪明果断，有领导才能",
    "天罗": "辰巳见辰巳，主做事多阻碍，宜谨慎行事",
    "地网": "戌亥见戌亥，主做事多牵绊，宜稳中求进",
    "亡神": "主机谋深远，善于策划，亦主暗损",
    "天厨": "主食禄丰厚，利餐饮、厨艺",
    "天喜": "主喜庆之事，利婚嫁、添丁",
    "红鸾": "主婚恋之喜，利婚嫁、感情",
    "红艳": "主容貌出众，异性缘旺，亦主风流",
    "流霞": "主血光之灾，宜注意安全",
    "学堂": "主聪明好学，利学业、考试",
    "词馆": "主文才出众，利文学、写作",
    "国印": "主掌权印信，利公职、管理",
    "劫煞": "三合局之煞位，主破财、官非、意外灾祸，宜守不宜攻",
    "灾煞": "劫煞之对冲，主疾病、灾厄、口舌是非",
    "元辰": "又名大耗，主耗散、破财、小人暗害",
    "咸池": "桃花之别名，又名正桃花，主情欲、风流、人缘",
    "绞煞": "与劫煞同宫不同位，主纠缠、纠纷、牢狱之灾",
    "天医": "主医药、健康、疗愈，利从医、养生",
    "德秀": "天德月德之合化，主福禄双全、品德高尚、逢凶化吉",
    "三奇": "天上/人中/地下三奇，主聪颖异常、才华横溢、贵人多助",
    "暗禄": "羊刃之对宫，暗中得财，不显于外",
    "血刃": "羊刃之变体，更凶猛，主血光、手术、刑伤",
    "截路空亡": "十干截路之空亡，主事多阻滞、半途而废",
    "月德合": "月德贵人之合化，主仁慈宽厚，逢凶化吉",
    "飞刃": "日主羊刃之对冲，主血光、手术、意外伤害",
    "福星贵人": "主福泽深厚，遇事有助，一生少灾",
    "十恶大败": "主祖业难守，败散家财，宜白手起家",
    "披麻": "丧吊煞之一，主孝服、丧事、不利亲友",
    "童子煞": "主性情灵巧，亦主多病多灾，不利婚姻",
    "天厨贵人": "主食禄丰厚，利餐饮、厨艺、享受",
}

SHENSHA_DESC.update(SHENSHA_DESC_EXTRA)


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

    _ZHI_SINGLE = [
        ("文昌贵人", WENCHANG, "day_gan", "吉"),
        ("驿马", YIMA, "day_zhi", "吉"),
        ("桃花", TAOHUA, "day_zhi", "中"),
        ("华盖", HUAGAI, "day_zhi", "吉"),
        ("将星", JIANGXING, "day_zhi", "吉"),
        ("禄神", LUSHEN, "day_gan", "吉"),
        ("羊刃", YANGREN, "day_gan", "凶"),
        ("金舆", JINYU, "day_gan", "吉"),
        ("孤辰", GUCHEN, "year_zhi", "凶"),
        ("寡宿", GUASU, "year_zhi", "凶"),
        ("魁罡", KUIGUI, "day_gan", "吉"),
        ("天喜", TIANXI, "year_zhi", "吉"),
        ("红鸾", HONGLUAN, "year_zhi", "吉"),
        ("红艳", HONGYAN, "day_gan", "中"),
        ("流霞", LIUXIA, "day_gan", "凶"),
        ("学堂", XUETANG, "day_gan", "吉"),
        ("词馆", CIGAN, "day_gan", "吉"),
        ("国印", GUOYIN, "day_gan", "吉"),
        ("天厨", TIANCHU_GUIREN, "day_gan", "吉"),
        ("劫煞", JIESHA, "year_zhi", "凶"),
        ("灾煞", ZAISHA, "year_zhi", "凶"),
        ("元辰", YUANCHEN, "year_zhi", "凶"),
        ("绞煞", JIAOSHA, "year_zhi", "凶"),
        ("天医", TIANYI_YI, "month_zhi", "吉"),
        ("暗禄", ANLU, "day_gan", "吉"),
        ("血刃", XUEREN, "day_gan", "凶"),
        ("天罗", TIANLUO, "month_zhi", "凶"),
        ("地网", DIWANG, "month_zhi", "凶"),
    ]

    _ZHI_MULTI = [
        ("天乙贵人", TIANYI_GUIREN, "day_gan", "吉"),
        ("太极贵人", TAIJI_GUIREN, "day_gan", "吉"),
        ("截路空亡", JIELU_KONGWANG, "day_gan", "凶"),
    ]

    _GAN_SINGLE = [
        ("天德贵人", TIANDE, "month_zhi", "吉"),
        ("月德贵人", YUEDE, "month_zhi", "吉"),
    ]

    key_map = {"day_gan": day_gan, "day_zhi": day_zhi, "year_zhi": year_zhi, "month_zhi": month_zhi}

    for name, table, key, stype in _ZHI_SINGLE:
        lookup_key = key_map[key]
        target = table.get(lookup_key, "")
        if not target:
            continue
        for idx, zhi in enumerate(all_zhis):
            if zhi == target:
                if name == "亡神" and idx == 2:
                    continue
                results.append({"name": name, "position": positions[idx],
                                "type": stype, "desc": SHENSHA_DESC.get(name, "")})

    for name, table, key, stype in _ZHI_MULTI:
        lookup_key = key_map[key]
        targets = table.get(lookup_key, [])
        for idx, zhi in enumerate(all_zhis):
            if zhi in targets:
                results.append({"name": name, "position": positions[idx],
                                "type": stype, "desc": SHENSHA_DESC.get(name, "")})

    for name, table, key, stype in _GAN_SINGLE:
        lookup_key = key_map[key]
        target = table.get(lookup_key, "")
        if not target:
            continue
        for idx, gan in enumerate(all_gans):
            if gan == target:
                results.append({"name": name, "position": positions[idx],
                                "type": stype, "desc": SHENSHA_DESC.get(name, "")})

    wangchen_zhi = WANGCHEN.get(day_zhi, "")
    for idx, zhi in enumerate(all_zhis):
        if zhi == wangchen_zhi and idx != 2:
            results.append({"name": "亡神", "position": positions[idx],
                            "type": "凶", "desc": SHENSHA_DESC.get("亡神", "")})

    SHIE_DA_BAI_DAYS = {"甲辰", "乙巳", "丙申", "丁亥", "庚辰", "戊戌", "癸亥", "辛巳", "己丑"}
    day_pillar = bazi_parts[2] if len(bazi_parts) >= 3 and len(bazi_parts[2]) >= 2 else ""
    if day_pillar in SHIE_DA_BAI_DAYS:
        results.append({"name": "十恶大败", "position": "日",
                        "type": "凶", "desc": SHENSHA_DESC.get("十恶大败", "")})

    # 飞刃 = 羊刃之对冲。《渊海子平》羊刃只论阳干，阴干无羊刃则无飞刃。
    FEIREN: dict[str, str] = {
        "甲": "酉", "丙": "子", "戊": "子", "庚": "卯", "壬": "午",
    }
    feiren_zhi = FEIREN.get(day_gan, "")
    if feiren_zhi:
        for idx, zhi in enumerate(all_zhis):
            if zhi == feiren_zhi:
                results.append({"name": "飞刃", "position": positions[idx],
                                "type": "凶", "desc": SHENSHA_DESC.get("飞刃", "")})

    # 福星贵人 — 《甲丙相邀入虎乡歌》：
    # "甲丙相邀入虎乡，更游鼠穴最高强，戊猴己未丁宜亥，乙癸逢牛卯禄昌，庚赶马头辛到巳，壬骑龙背喜非常"
    FUXING_GUIREN: dict[str, list[str]] = {
        "甲": ["寅", "子"], "乙": ["丑", "卯"],
        "丙": ["寅", "子"], "丁": ["亥"],
        "戊": ["申"], "己": ["未"],
        "庚": ["午"], "辛": ["巳"],
        "壬": ["辰"], "癸": ["丑", "卯"],
    }
    fuxing_targets = FUXING_GUIREN.get(day_gan, [])
    for idx, zhi in enumerate(all_zhis):
        if zhi in fuxing_targets:
            results.append({"name": "福星贵人", "position": positions[idx],
                            "type": "吉", "desc": SHENSHA_DESC.get("福星贵人", "")})

    YUEDE_HE: dict[str, str] = {
        "丙": "辛", "壬": "丁", "庚": "乙", "甲": "己",
    }
    yd_he_target = YUEDE_HE.get(YUEDE.get(month_zhi, ""), "")
    if yd_he_target:
        for idx, gan in enumerate(all_gans):
            if gan == yd_he_target:
                results.append({"name": "月德合", "position": positions[idx],
                                "type": "吉", "desc": SHENSHA_DESC.get("月德合", "")})

    PIMA: dict[str, str] = {
        "子": "寅", "丑": "卯", "寅": "辰", "卯": "巳",
        "辰": "午", "巳": "未", "午": "申", "未": "酉",
        "申": "戌", "酉": "亥", "戌": "子", "亥": "丑",
    }
    pima_zhi = PIMA.get(year_zhi, "")
    if pima_zhi:
        for idx, zhi in enumerate(all_zhis):
            if zhi == pima_zhi:
                results.append({"name": "披麻", "position": positions[idx],
                                "type": "凶", "desc": SHENSHA_DESC.get("披麻", "")})

    TONGZI_SPRING = {"寅": "丑", "卯": "寅", "辰": "卯", "巳": "辰"}
    TONGZI_AUTUMN = {"申": "未", "酉": "申", "戌": "酉", "亥": "戌"}
    tongzi_zhi = TONGZI_SPRING.get(month_zhi, "") or TONGZI_AUTUMN.get(month_zhi, "")
    if tongzi_zhi and day_zhi == tongzi_zhi:
        results.append({"name": "童子煞", "position": "日",
                        "type": "凶", "desc": SHENSHA_DESC.get("童子煞", "")})

    # 三奇：需四柱天干中同时出现同组三干（天上三奇甲戊庚/人中三奇乙丙丁/地下三奇壬癸辛）
    gan_set = set(all_gans)
    sanqi_type = None
    if all(g in gan_set for g in SANQI_TIAN):
        sanqi_type = "天上三奇"
    elif all(g in gan_set for g in SANQI_REN):
        sanqi_type = "人中三奇"
    elif all(g in gan_set for g in SANQI_DI):
        sanqi_type = "地下三奇"
    if sanqi_type:
        results.append({"name": f"三奇（{sanqi_type}）", "position": "日",
                        "type": "吉", "desc": SHENSHA_DESC.get("三奇", "")})

    td_he = DE_XIU_TIANDE_HE.get(day_gan, "")
    yd_he = DE_XIU_YUEDE_HE.get(day_gan, "")
    for gan in all_gans:
        if gan == td_he or gan == yd_he:
            results.append({"name": "德秀", "position": "日",
                            "type": "吉", "desc": SHENSHA_DESC.get("德秀", "")})
            break

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
        if nzhi in xing_targets:
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


_BAZI_MCP_PATH: str | None = None

def _find_bazi_mcp_path() -> str | None:
    global _BAZI_MCP_PATH
    if _BAZI_MCP_PATH is not None:
        return _BAZI_MCP_PATH if _BAZI_MCP_PATH else None
    server_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(server_dir, "tools", "node_modules", "bazi-mcp"),
        os.path.join(os.path.dirname(server_dir), "node_modules", "bazi-mcp"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "npm-cache", "_npx"),
        os.path.join(os.environ.get("USERPROFILE", ""), ".npm", "_npx"),
    ]
    for mcp_dir in candidates:
        if not os.path.isdir(mcp_dir):
            if "_npx" in mcp_dir and os.path.isdir(mcp_dir):
                for entry in os.listdir(mcp_dir):
                    candidate = os.path.join(mcp_dir, entry, "node_modules", "bazi-mcp")
                    if os.path.isfile(os.path.join(candidate, "dist", "index.js")):
                        _BAZI_MCP_PATH = candidate
                        return _BAZI_MCP_PATH
            continue
        if os.path.isfile(os.path.join(mcp_dir, "dist", "index.js")):
            _BAZI_MCP_PATH = mcp_dir
            return _BAZI_MCP_PATH
    _BAZI_MCP_PATH = ""
    return None

SHENSHA_TYPE_MAP: dict[str, str] = {
    "天乙贵人": "吉", "文昌贵人": "吉", "文昌": "吉",
    "驿马": "吉", "桃花": "中", "咸池": "中",
    "华盖": "吉", "将星": "吉", "禄神": "吉",
    "羊刃": "凶", "金舆": "吉",
    "天德贵人": "吉", "天德": "吉",
    "月德贵人": "吉", "月德合": "吉", "月德": "吉",
    "孤辰": "凶", "寡宿": "凶",
    "太极贵人": "吉", "太极": "吉",
    "魁罡": "吉",
    "天罗": "凶", "地网": "凶",
    "亡神": "凶",
    "天厨": "吉", "天厨贵人": "吉",
    "天喜": "吉",
    "红鸾": "吉",
    "红艳": "中",
    "流霞": "凶",
    "学堂": "吉", "词馆": "吉",
    "国印": "吉",
    "劫煞": "凶", "灾煞": "凶",
    "元辰": "凶", "大耗": "凶",
    "绞煞": "凶",
    "天医": "吉",
    "三奇": "吉",
    "德秀": "吉", "德秀贵人": "吉",
    "暗禄": "吉",
    "血刃": "凶",
    "截路空亡": "凶", "空亡": "凶",
    "飞刃": "凶",
    "福星贵人": "吉", "福星": "吉",
    "十恶大败": "凶",
    "披麻": "凶",
    "童子煞": "凶",
}

def _normalize_shensha_name(name: str) -> str:
    mapping = {
        "天厨贵人": "天厨", "太极贵人": "太极", "文昌贵人": "文昌",
        "天德贵人": "天德", "月德贵人": "月德", "福星贵人": "福星",
        "德秀贵人": "德秀",
    }
    return mapping.get(name, name)

def _to_iso_datetime(solar: str | None) -> str:
    if not solar:
        raise ValueError("empty solar_datetime")
    s = solar.strip()
    if 'T' in s:
        if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$', s):
            raise ValueError(f"Invalid datetime format: {s}")
        return s
    parts = s.split()
    if len(parts) >= 1:
        date_part = parts[0]
        time_part = parts[1] if len(parts) > 1 else "00:00"
        time_fields = time_part.split(":")
        hh = time_fields[0] if len(time_fields) >= 1 else "00"
        mm = time_fields[1] if len(time_fields) >= 2 else "00"
        ss = time_fields[2] if len(time_fields) >= 3 else "00"
        result = f"{date_part}T{hh}:{mm}:{ss}+08:00"
        if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$', result):
            raise ValueError(f"Invalid datetime format: {result}")
        return result
    return s

async def calc_shensha_from_mcp(solar_datetime: str, gender: int) -> list[dict]:
    import asyncio
    import logging
    logger = logging.getLogger(__name__)
    mcp_path = _find_bazi_mcp_path()
    if not mcp_path:
        logger.warning("[shensha] bazi-mcp not found")
        return []
    gender_val = 1 if gender == 1 else 0
    try:
        iso_dt = _to_iso_datetime(solar_datetime)
    except (ValueError, AttributeError):
        logger.warning("[shensha] invalid solar_datetime format: %s", solar_datetime)
        return []
    iso_dt_safe = json.dumps(iso_dt)
    mcp_index = os.path.abspath(os.path.join(mcp_path, "dist", "index.js")).replace("\\", "/")
    mcp_url = "file:///" + mcp_index
    js_code = (
        'import("' + mcp_url + '").then(m => {\n'
        '  m.getBaziDetail({\n'
        f'    solarDatetime: {iso_dt_safe},\n'
        f'    gender: {gender_val},\n'
        '    eightCharProviderSect: 2\n'
        '  }).then(r => console.log(JSON.stringify(r.神煞)));\n'
        '});\n'
    )
    script_file = None
    try:
        # 使用唯一文件名避免并发请求互相覆盖
        fd, script_file = tempfile.mkstemp(suffix=".mjs", prefix="_bazi_shensha_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(js_code)
        proc = await asyncio.create_subprocess_exec(
            "node", script_file,
            cwd=mcp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "NODE_ENV": "production"},
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=15)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            logger.warning("[shensha] node timeout")
            return []
        if proc.returncode != 0:
            stderr_preview = (stderr_b.decode("utf-8", errors="replace") if stderr_b else "")[:200]
            logger.warning(f"[shensha] node exit {proc.returncode}, stderr={stderr_preview}")
            return []
        stdout = (stdout_b.decode("utf-8", errors="replace") if stdout_b else "").strip()
        if not stdout:
            logger.warning("[shensha] node stdout empty")
            return []
        data = json.loads(stdout)
    except json.JSONDecodeError as e:
        logger.warning(f"[shensha] JSON decode error: {e}")
        return []
    except (FileNotFoundError, OSError) as e:
        logger.warning(f"[shensha] node exec error: {e}")
        return []
    finally:
        if script_file:
            try:
                os.unlink(script_file)
            except OSError:
                pass

    positions = ["年", "月", "日", "时"]
    pillar_keys = ["年柱", "月柱", "日柱", "时柱"]
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for pidx, pkey in enumerate(pillar_keys):
        names = data.get(pkey, [])
        for name in names:
            norm_name = _normalize_shensha_name(name)
            key = (norm_name, positions[pidx])
            if key in seen:
                continue
            seen.add(key)
            desc_key = name if name in SHENSHA_DESC else norm_name
            results.append({
                "name": name,
                "position": positions[pidx],
                "type": SHENSHA_TYPE_MAP.get(name, SHENSHA_TYPE_MAP.get(norm_name, "中")),
                "desc": SHENSHA_DESC.get(desc_key, SHENSHA_DESC.get(norm_name, "")),
            })
    logger.info(f"[shensha] MCP returned {len(results)} items from {len(data)} pillars")
    return results

async def calc_shensha_enhanced(bazi_parts: list[str], solar_datetime: str = "", gender: int = 1) -> list[dict]:
    mcp_results: list[dict] = []
    if solar_datetime:
        mcp_results = await calc_shensha_from_mcp(solar_datetime, gender)
    if mcp_results:
        return mcp_results
    return calc_shensha(bazi_parts)
