"""心性问卷 + 分叉路径生成

10 题问卷计算风险偏好(theta_r)和人际依赖(theta_s)，
用于过滤和排序流年路径建议。
"""

QUESTIONS = [
    {"id": 1, "text": "面对不确定的机会，你更倾向于？", "options": ["果断尝试", "谨慎观望", "看情况"], "dimension": "risk"},
    {"id": 2, "text": "做重大决定时，你通常？", "options": ["独立决策", "征求他人意见", "跟随直觉"], "dimension": "social"},
    {"id": 3, "text": "对于投资理财，你的态度是？", "options": ["高风险高回报", "稳健为主", "不太关注"], "dimension": "risk"},
    {"id": 4, "text": "在团队中，你更喜欢？", "options": ["领导角色", "协作配合", "独立完成"], "dimension": "social"},
    {"id": 5, "text": "遇到困难时，你第一反应是？", "options": ["自己解决", "寻求帮助", "等待时机"], "dimension": "risk"},
    {"id": 6, "text": "对于人际关系，你认为？", "options": ["广交朋友很重要", "几个知己足矣", "独处更自在"], "dimension": "social"},
    {"id": 7, "text": "职业选择上，你更看重？", "options": ["发展空间", "稳定安全", "兴趣热情"], "dimension": "risk"},
    {"id": 8, "text": "面对批评，你通常？", "options": ["虚心接受", "据理力争", "内心消化"], "dimension": "social"},
    {"id": 9, "text": "对于变化，你的态度是？", "options": ["拥抱变化", "适应变化", "抗拒变化"], "dimension": "risk"},
    {"id": 10, "text": "你认为成功更依赖？", "options": ["个人能力", "人脉资源", "时运机遇"], "dimension": "social"},
]


def calc_personality_params(answers: list[int]) -> dict:
    """根据问卷答案计算心性参数。

    Args:
        answers: 10 个答案，每个 0/1/2 对应三个选项

    Returns:
        {"theta_r": float, "theta_s": float, "profile": str}
        theta_r: 风险偏好 (0-1, 越高越冒险)
        theta_s: 人际依赖 (0-1, 越高越依赖他人)
    """
    if len(answers) != 10:
        return {"theta_r": 0.5, "theta_s": 0.5, "profile": "中性"}

    risk_scores = []
    social_scores = []

    for i, ans in enumerate(answers):
        q = QUESTIONS[i]
        score = [1.0, 0.0, 0.5][min(ans, 2)]
        if q["dimension"] == "risk":
            risk_scores.append(score)
        else:
            social_scores.append(score)

    theta_r = sum(risk_scores) / max(len(risk_scores), 1)
    theta_s = sum(social_scores) / max(len(social_scores), 1)

    if theta_r > 0.7:
        profile = "开拓型" if theta_s > 0.5 else "独行侠"
    elif theta_r < 0.3:
        profile = "稳健型" if theta_s > 0.5 else "内敛型"
    else:
        profile = "平衡型"

    return {"theta_r": round(theta_r, 2), "theta_s": round(theta_s, 2), "profile": profile}


def generate_forked_paths(liunian_score: dict, theta_r: float, theta_s: float) -> list[dict]:
    """为某个流年生成 2-3 条分叉路径。

    Args:
        liunian_score: 流年评分数据 {age, year, gan_zhi, score, reason}
        theta_r: 风险偏好
        theta_s: 人际依赖

    Returns:
        路径列表，每条含 {path_name, trigger, trajectory, match_score}
    """
    score = liunian_score.get("score", 50)

    paths = []

    if score >= 65:
        paths.append({
            "path_name": "积极进取",
            "trigger": "主动把握用神到位的机遇",
            "trajectory": "事业上升期，适合拓展新领域",
            "match_score": round(70 + theta_r * 30),
            "risk_level": "中",
        })
        paths.append({
            "path_name": "稳中求进",
            "trigger": "在现有基础上深耕",
            "trajectory": "巩固已有成果，稳步提升",
            "match_score": round(70 + (1 - theta_r) * 30),
            "risk_level": "低",
        })
    elif score <= 35:
        paths.append({
            "path_name": "韬光养晦",
            "trigger": "忌神当令，宜守不宜攻",
            "trajectory": "减少大动作，积蓄力量等待转机",
            "match_score": round(70 + (1 - theta_r) * 30),
            "risk_level": "低",
        })
        paths.append({
            "path_name": "借力化解",
            "trigger": "寻求贵人或团队支持",
            "trajectory": "通过合作分散风险",
            "match_score": round(50 + theta_s * 40),
            "risk_level": "中",
        })
    else:
        paths.append({
            "path_name": "顺势而为",
            "trigger": "中性流年，随机应变",
            "trajectory": "保持现状，关注细节优化",
            "match_score": 70,
            "risk_level": "低",
        })
        paths.append({
            "path_name": "主动求变",
            "trigger": "利用平稳期尝试新方向",
            "trajectory": "小范围试错，为下一步布局",
            "match_score": round(50 + theta_r * 40),
            "risk_level": "中",
        })

    if theta_s > 0.6:
        paths.append({
            "path_name": "合作共赢",
            "trigger": "发挥人际优势",
            "trajectory": "通过合伙、联盟扩大影响力",
            "match_score": round(60 + theta_s * 30),
            "risk_level": "中",
        })

    paths.sort(key=lambda p: p["match_score"], reverse=True)
    return paths[:3]
