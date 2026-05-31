"""三流派交叉验证 — 标注子平/盲派/新派一致和矛盾的结论"""


def cross_validate_schools(school_results: dict) -> dict:
    """对比三流派分析结果，标注一致项和矛盾项。

    Args:
        school_results: school_analyze(mcp_json, 'all') 的返回值

    Returns:
        {
            "consensus": [...],  # 三派一致的结论
            "conflicts": [...],  # 矛盾项
            "confidence_boost": [...],  # 因一致而增强置信度的结论
        }
    """
    ziping = school_results.get("ziping", {})
    mangpai = school_results.get("mangpai", {})
    xinpai = school_results.get("xinpai", {})

    if not ziping or not mangpai or not xinpai:
        return {"consensus": [], "conflicts": [], "confidence_boost": []}

    consensus = []
    conflicts = []
    confidence_boost = []

    z_wangshuai = ziping.get("wangshuai", {}).get("verdict", "")
    x_shengfu = xinpai.get("yong_ji", {}).get("sheng_fu", "")

    z_is_strong = "旺" in z_wangshuai or "强" in z_wangshuai
    x_is_strong = "旺" in x_shengfu or "强" in x_shengfu
    z_is_weak = "弱" in z_wangshuai or "衰" in z_wangshuai
    x_is_weak = "弱" in x_shengfu or "衰" in x_shengfu

    if z_is_strong and x_is_strong:
        consensus.append({
            "dimension": "旺衰",
            "conclusion": "身旺",
            "schools": ["子平", "新派"],
            "note": "两派均判定日主偏旺",
        })
        confidence_boost.append("旺衰判定（身旺）置信度提升")
    elif z_is_weak and x_is_weak:
        consensus.append({
            "dimension": "旺衰",
            "conclusion": "身弱",
            "schools": ["子平", "新派"],
            "note": "两派均判定日主偏弱",
        })
        confidence_boost.append("旺衰判定（身弱）置信度提升")
    elif (z_is_strong and x_is_weak) or (z_is_weak and x_is_strong):
        conflicts.append({
            "dimension": "旺衰",
            "ziping": z_wangshuai,
            "xinpai": x_shengfu,
            "note": "子平与新派旺衰判定矛盾，建议以子平法为主参考",
        })

    z_yongshen = ziping.get("yongshen", {}).get("yongshen", "")
    x_yongshen_list = xinpai.get("yong_ji", {}).get("yongshen_name", [])
    x_yongshen = x_yongshen_list[0] if x_yongshen_list else ""

    if z_yongshen and x_yongshen and z_yongshen == x_yongshen:
        consensus.append({
            "dimension": "用神",
            "conclusion": z_yongshen,
            "schools": ["子平", "新派"],
            "note": f"两派用神一致为{z_yongshen}",
        })
        confidence_boost.append(f"用神（{z_yongshen}）置信度提升")
    elif z_yongshen and x_yongshen and z_yongshen != x_yongshen:
        conflicts.append({
            "dimension": "用神",
            "ziping": z_yongshen,
            "xinpai": x_yongshen,
            "note": "子平与新派用神不同，不强行调和",
        })

    m_gongli = mangpai.get("gongli", {})
    if m_gongli:
        level = m_gongli.get("level", "")
        score = m_gongli.get("score", 0)
        if level and score:
            consensus.append({
                "dimension": "盲派功力",
                "conclusion": f"{level}（{score}分）",
                "schools": ["盲派"],
                "note": "盲派独有的功力评定维度",
            })

    return {
        "consensus": consensus,
        "conflicts": conflicts,
        "confidence_boost": confidence_boost,
    }
