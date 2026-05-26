"""
bazi-pro 消费级报告渲染器 v1.0
面向普通用户的命理解读报告，结论先行、术语解释、叙事丰富
"""

from html import escape  # noqa: I001

from bazi_pro.ui.glossary import GLOSSARY_CSS, annotate_terms, render_glossary_section
from bazi_pro.view_model import DashboardVM


# ── 五行属性映射 ──

WUXING_TRAITS = {
    '木': {'nature': '生长、向上', 'personality': '仁慈正直、富有同情心',
            'industries': '教育、文化、出版、医疗、环保、农业',
            'colors': '绿色、青色', 'directions': '东方'},
    '火': {'nature': '光明、热情', 'personality': '热情开朗、积极进取',
            'industries': '互联网、能源、餐饮、娱乐、传媒、设计',
            'colors': '红色、紫色', 'directions': '南方'},
    '土': {'nature': '厚重、包容', 'personality': '稳重踏实、诚信可靠',
            'industries': '房地产、建筑、农业、矿业、金融、咨询',
            'colors': '黄色、棕色', 'directions': '中央'},
    '金': {'nature': '坚毅、果断', 'personality': '果断干练、重义守信',
            'industries': '金融、法律、机械、IT硬件、珠宝、军警',
            'colors': '白色、金色', 'directions': '西方'},
    '水': {'nature': '智慧、灵活', 'personality': '聪明机敏、善于变通',
            'industries': '贸易、物流、旅游、水利、传播、咨询',
            'colors': '黑色、蓝色', 'directions': '北方'},
}

STRENGTH_DESC = {
    '身旺': ('自身能量充沛', '您天生精力旺盛、意志坚定，适合主动出击、独立开创。在事业上倾向于领导和掌控，不喜欢被过多约束。'),
    '身弱': ('自身能量偏弱', '您天生善于合作、借力发展，适合在团队中发挥专长。在事业上倾向于专精和深耕，善于利用外部资源。'),
    '极旺': ('自身能量极强', '您个性极为鲜明、意志力超强，适合在需要魄力和决断的领域大展拳脚。'),
    '极弱': ('顺势而为的格局', '您的命局形成了特殊的"从格"，意味着顺应大势发展反而能获得最好的结果。'),
}

def _get_dm_element(vm: DashboardVM) -> str:
    """从日主天干推断五行"""
    gan_wx = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
              '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
    dm = vm.verdict.day_master or ''
    for char in dm:
        if char in gan_wx:
            return gan_wx[char]
    return '火'


def _clean_pattern(raw: str) -> str:
    """清理 VM 提取的格局名称（可能包含多余文本）"""
    if not raw:
        return ''
    known = ['正官格', '七杀格', '食神格', '伤官格', '正财格', '偏财格',
             '正印格', '偏印格', '建禄格', '月劫格', '从强格', '从财格',
             '从官杀格', '从儿格', '专旺格', '化气格', '羊刃格',
             '暗食神格', '暗正官格', '暗七杀格', '暗正财格', '暗偏财格']
    for p in sorted(known, key=len, reverse=True):
        if p in raw:
            return p
    if len(raw) <= 6 and '格' in raw:
        return raw
    return ''


def _get_strength(vm: DashboardVM) -> str:
    """获取旺衰判定"""
    d = vm.verdict.decision or ''
    for key in ('极旺', '极弱', '身旺', '身弱'):
        if key in d:
            return key
    return '身旺' if vm.wuxing and _get_dm_element(vm) == '火' and vm.wuxing.fire > 30 else '身弱'


def _truncate_sentence(text: str, max_len: int) -> str:
    """截断到最近的句末标点，避免断在句中"""
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    for punct in ('。', '，', '、', '；'):
        idx = cut.rfind(punct)
        if idx > max_len // 2:
            return cut[:idx + 1]
    return cut


def _render_cover(vm: DashboardVM) -> str:
    v = vm.verdict
    dm_wx = _get_dm_element(vm)
    pattern = _clean_pattern(v.pattern)
    dm_char = ''
    for c in (v.day_master or ''):
        if c in '甲乙丙丁戊己庚辛壬癸':
            dm_char = c
            break
    subtitle = f'{dm_char}{dm_wx}命 · {pattern or "命理解读"}' if dm_char else '命理解读'
    return f'''<header class="cr-cover">
  <div class="cr-cover-badge">{escape(dm_wx)}</div>
  <h1 class="cr-title">命理解读报告</h1>
  <p class="cr-subtitle">{escape(subtitle)}</p>
  <div class="cr-meta">
    <span>{escape(vm.bazi or '')}</span>
    {f'<span>{escape(vm.gender or "")}</span>' if vm.gender else ''}
    {f'<span>{escape(vm.solar_date or "")}</span>' if vm.solar_date else ''}
  </div>
</header>'''


def _render_reading_guide(vm: DashboardVM) -> str:
    return '''<section class="cr-guide">
  <h2>阅读指南</h2>
  <p>这份报告基于您的出生时间，运用传统命理学理论为您解读性格特质、事业方向、财运模式、感情婚姻、健康提示和近期运势六个维度。</p>
  <p>报告中的专业术语均附有通俗解释（将鼠标悬停在<span class="term-tip" data-tip="带有虚线下划线的词语">带虚线的词语</span>上可查看释义），末尾还有完整的术语小词典供参考。</p>
  <p>命理分析反映的是趋势和倾向，而非确定的命运。它是认识自我、把握节奏的参考工具，不是人生的判决书。</p>
</section>'''


def _render_summary_card(vm: DashboardVM) -> str:
    v = vm.verdict
    dm_wx = _get_dm_element(vm)
    strength = _get_strength(vm)
    strength_info = STRENGTH_DESC.get(strength, STRENGTH_DESC['身旺'])
    traits = WUXING_TRAITS.get(dm_wx, WUXING_TRAITS['火'])
    pattern = _clean_pattern(v.pattern) or '正格'

    yongshen_str = '、'.join(v.yongshen[:2]) if v.yongshen else '待定'
    xishen_str = '、'.join(v.xishen[:2]) if v.xishen else '待定'
    jishen_str = '、'.join(v.jishen[:2]) if v.jishen else '待定'

    strengths = [
        f'{dm_wx}行人天生{traits["personality"].split("、")[0]}',
        f'格局为{pattern}，发展方向明确',
        f'用神为{yongshen_str}，有利方向清晰',
    ]
    challenges = [
        f'忌神为{jishen_str}，需回避相关方向',
        f'{strength_info[0]}，需注意平衡',
        '人生节奏有起伏，把握关键转折期',
    ]

    strengths_html = ''.join(f'<li>{escape(s)}</li>' for s in strengths)
    challenges_html = ''.join(f'<li>{escape(s)}</li>' for s in challenges)

    conf_pct = f'{v.confidence:.0%}' if v.confidence else '—'

    return f'''<section class="cr-summary">
  <h2>核心发现</h2>
  <div class="cr-summary-grid">
    <div class="cr-identity-card">
      <div class="cr-id-label">您的命理身份</div>
      <div class="cr-id-value">{escape(v.day_master or '')}日主 · {escape(dm_wx)}行人</div>
      <div class="cr-id-desc">{escape(traits['nature'])}</div>
    </div>
    <div class="cr-pattern-card">
      <div class="cr-id-label">人生发展模式</div>
      <div class="cr-id-value">{escape(pattern)}</div>
      <div class="cr-id-desc">{escape(_truncate_sentence(strength_info[1], 50))}</div>
    </div>
    <div class="cr-direction-card">
      <div class="cr-id-label">有利方向</div>
      <div class="cr-id-value">用{escape(yongshen_str)} · 喜{escape(xishen_str)}</div>
      <div class="cr-id-desc">忌{escape(jishen_str)} · 置信度 {conf_pct}</div>
    </div>
  </div>
  <div class="cr-pros-cons">
    <div class="cr-pros"><h3>核心优势</h3><ul>{strengths_html}</ul></div>
    <div class="cr-cons"><h3>需要留意</h3><ul>{challenges_html}</ul></div>
  </div>
</section>'''


def _narrative_personality(vm: DashboardVM) -> str:
    dm_wx = _get_dm_element(vm)
    strength = _get_strength(vm)
    v = vm.verdict
    dm = v.day_master or dm_wx

    wx_nature = {
        '木': f'{dm}如参天大树，天性向上生长、追求光明。您内心有一股不断进取的力量，渴望成长和突破。在人际关系中，您往往表现出仁慈和正义感，对弱者有天然的同情心。',
        '火': f'{dm}如太阳之光，天性热情奔放、光明磊落。您内心有一团不灭的火焰，渴望照亮周围的人和事。在人际关系中，您往往表现出热情和感染力，是天生的氛围营造者。',
        '土': f'{dm}如大地之母，天性厚重包容、诚信可靠。您内心有一份沉稳的力量，能够承载和包容各种人事。在人际关系中，您往往表现出可靠和值得信赖的品质。',
        '金': f'{dm}如精钢利刃，天性果断坚毅、重义守信。您内心有一份不可动摇的原则感，对是非黑白有清晰的判断。在人际关系中，您往往表现出义气和担当。',
        '水': f'{dm}如江河之水，天性聪慧灵活、善于变通。您内心有一份流动的智慧，能够在不同环境中找到最佳路径。在人际关系中，您往往表现出机敏和适应力。',
    }

    strength_layer = {
        '身旺': '由于自身能量充沛，您的性格中主动性和掌控欲较强。您不喜欢被动等待，更倾向于自己创造机会。这种特质在事业上是优势，但在人际关系中需要适当收敛，给他人留出空间。',
        '身弱': '由于自身能量偏柔，您的性格中合作性和适应力较强。您善于观察环境、借助外力，在团队中往往能找到最适合自己的位置。这种特质让您在复杂环境中游刃有余。',
        '极旺': '您的个性极为鲜明，意志力和行动力都超出常人。这种强大的内在驱动力让您在需要魄力的场合如鱼得水，但也需要找到合适的释放渠道，避免过于刚强。',
        '极弱': '您的命局形成了特殊的顺势格局，这意味着您天生善于顺应大势、借力而行。与其对抗环境，不如顺应潮流，反而能获得最好的发展。',
    }

    pattern_layer = ''
    pattern = _clean_pattern(v.pattern)
    if pattern:
        pattern_layer = f'从格局来看，您属于{pattern}，'
        if '食神' in pattern or '伤官' in pattern:
            pattern_layer += '这意味着才华和创造力是您性格中最突出的标签。您有独特的审美和表达方式，内心世界丰富。'
        elif '官' in pattern or '杀' in pattern:
            pattern_layer += '这意味着责任感和使命感是您性格中的底色。您天生有领导气质，对自己和他人都有较高的要求。'
        elif '财' in pattern:
            pattern_layer += '这意味着务实和经营能力是您的天赋。您对物质世界有敏锐的感知，善于发现和把握机会。'
        elif '印' in pattern:
            pattern_layer += '这意味着学习力和思考力是您的核心竞争力。您重视内在修养，有深度思考的习惯。'
        else:
            pattern_layer += '这赋予了您独特的发展路径和性格底色。'

    base = wx_nature.get(dm_wx, wx_nature['火'])
    s_layer = strength_layer.get(strength, strength_layer['身旺'])

    return f'''<div class="cr-dimension">
  <h3>性格底色</h3>
  <p>{base}</p>
  <p>{s_layer}</p>
  <p>{pattern_layer}</p>
</div>'''


def _narrative_career(vm: DashboardVM) -> str:
    v = vm.verdict
    dm_wx = _get_dm_element(vm)
    yongshen_wx = v.yongshen[0] if v.yongshen else dm_wx
    traits = WUXING_TRAITS.get(yongshen_wx, WUXING_TRAITS['火'])

    career_intro = f'从命理角度看，您最适合的发展方向与{yongshen_wx}行相关的领域。具体来说，{traits["industries"]}等行业与您的命局能量最为契合。'

    strength = _get_strength(vm)
    if strength in ('身旺', '极旺'):
        style = '您适合独立性强、需要魄力和决断的岗位。创业、管理、独立执业都是不错的选择。在团队中，您更适合做决策者而非执行者。'
    else:
        style = '您适合专业性强、需要深度积累的岗位。技术专家、顾问、合伙人等角色能让您发挥所长。善于借助平台和团队的力量是您的优势。'

    timing = ''
    if vm.dayun:
        good_runs = [d for d in vm.dayun if d.assessment and '吉' in d.assessment]
        if good_runs:
            first_good = good_runs[0]
            timing = f'从大运节奏来看，{first_good.age_range or "中年"}期间是事业发展的黄金期，届时运势与命局形成良好配合，适合大胆推进重要计划。'

    direction = f'有利方位为{traits["directions"]}，有利颜色为{traits["colors"]}。在重要决策（如选择工作城市、办公环境布置）时可作为参考。'

    return f'''<div class="cr-dimension">
  <h3>事业方向</h3>
  <p>{career_intro}</p>
  <p>{style}</p>
  <p>{timing}</p>
  <p>{direction}</p>
</div>'''


def _narrative_wealth(vm: DashboardVM) -> str:
    v = vm.verdict
    strength = _get_strength(vm)

    if strength in ('身旺', '极旺'):
        wealth_type = '您的财运模式属于"主动求财"型。自身能量充沛，有能力去追逐和创造财富。适合通过自己的努力和能力直接获取收入，如创业、投资、承接项目等。'
    else:
        wealth_type = '您的财运模式属于"稳健积累"型。适合通过专业技能和持续积累来获取财富，而非冒险投机。稳定的职业收入加上长期理财是最适合您的财富策略。'

    yongshen_wx = v.yongshen[0] if v.yongshen else '土'
    wx_wealth = {
        '木': '与教育、文化、健康相关的领域是您的财富来源方向。',
        '火': '与科技、能源、创意相关的领域是您的财富来源方向。',
        '土': '与房产、实业、咨询相关的领域是您的财富来源方向。',
        '金': '与金融、法律、技术相关的领域是您的财富来源方向。',
        '水': '与贸易、传播、服务相关的领域是您的财富来源方向。',
    }
    source = wx_wealth.get(yongshen_wx, '多元化发展是您的财富策略。')

    timing = ''
    if vm.dayun:
        for d in vm.dayun:
            if d.assessment and '吉' in d.assessment:
                timing = f'财运较好的阶段在{d.age_range or "中年"}前后，届时适合加大投入、把握机会。在运势平淡期则宜守不宜攻，以积累和学习为主。'
                break

    return f'''<div class="cr-dimension">
  <h3>财运模式</h3>
  <p>{wealth_type}</p>
  <p>{source}</p>
  <p>{timing if timing else "财运随大运起伏，关键是在有利时期果断行动，在平淡时期耐心积累。"}</p>
  <p>理财建议：根据您的命局特点，建议将收入分为"稳健保本"和"适度增值"两部分，比例根据当前运势阶段灵活调整。</p>
</div>'''


def _narrative_love(vm: DashboardVM) -> str:
    v = vm.verdict
    strength = _get_strength(vm)

    if strength in ('身旺', '极旺'):
        love_style = '在感情中，您属于主导型。您有明确的标准和要求，不会轻易妥协。这种特质让您在感情中有魅力，但也需要学会倾听和包容对方的需求。'
    else:
        love_style = '在感情中，您属于配合型。您善于体察对方的感受，愿意为关系付出和调整。这种特质让您在感情中温暖可靠，但也需要注意维护自己的底线和需求。'

    partner_hint = ''
    yongshen = v.yongshen[0] if v.yongshen else ''
    if yongshen:
        partner_traits = WUXING_TRAITS.get(yongshen, {})
        if partner_traits:
            partner_hint = f'从命理配合来看，{yongshen}行特质明显的人（{partner_traits.get("personality", "")}）与您较为契合。'

    timing = ''
    if vm.dayun:
        for d in vm.dayun:
            if d.assessment and '吉' in d.assessment:
                timing = f'感情运势较好的阶段在{d.age_range or ""}前后，届时桃花运旺，适合主动社交和发展感情。'
                break

    advice = '感情建议：命理揭示的是倾向和节奏，而非固定结局。保持开放心态、主动经营关系，比被动等待更有效。'

    return f'''<div class="cr-dimension">
  <h3>感情婚姻</h3>
  <p>{love_style}</p>
  <p>{partner_hint}</p>
  <p>{timing if timing else "感情发展与整体运势节奏相关，在事业上升期往往也是感情机遇期。"}</p>
  <p>{advice}</p>
</div>'''


def _narrative_health(vm: DashboardVM) -> str:
    dm_wx = _get_dm_element(vm)
    strength = _get_strength(vm)

    wx_health = {
        '木': ('肝胆系统、眼睛、筋骨', '保持情绪舒畅，避免长期压抑和熬夜。适合户外运动和伸展类锻炼。'),
        '火': ('心血管系统、小肠、血液循环', '注意心脏保养，避免过度兴奋和情绪波动。适合有氧运动但避免过于剧烈。'),
        '土': ('脾胃消化系统、肌肉', '注意饮食规律，避免暴饮暴食和过度思虑。适合散步、太极等舒缓运动。'),
        '金': ('呼吸系统、皮肤、大肠', '注意呼吸道保养，避免干燥和污染环境。适合游泳、瑜伽等调息运动。'),
        '水': ('肾脏泌尿系统、骨骼、耳朵', '注意肾脏保养，避免过度劳累和寒凉。适合温和的有氧运动。'),
    }

    focus, advice = wx_health.get(dm_wx, wx_health['火'])

    if strength in ('身弱', '极弱'):
        energy = '由于自身能量偏弱，您需要格外注意休息和营养补充。避免长期透支体力，保持规律的作息是健康的基础。'
    else:
        energy = '由于自身能量充沛，您的体质底子较好，但也容易因为精力旺盛而忽视休息。注意劳逸结合，避免过度消耗。'

    return f'''<div class="cr-dimension">
  <h3>健康提示</h3>
  <p>从五行角度看，您需要重点关注的身体系统是：{focus}。</p>
  <p>{advice}</p>
  <p>{energy}</p>
  <p>健康建议：以上为命理角度的倾向性提示，不替代专业医疗诊断。建议定期体检，关注上述系统的早期信号。</p>
</div>'''


def _narrative_current(vm: DashboardVM) -> str:
    v = vm.verdict

    if vm.dayun:
        current = vm.dayun[0] if vm.dayun else None
        if current:
            assessment = current.assessment or '平稳'
            age = current.age_range or ''
            ganzhi = current.gan_zhi or ''
            return f'''<div class="cr-dimension">
  <h3>近期运势</h3>
  <p>当前所处大运为{ganzhi}（{age}），整体运势评估为：{assessment}。</p>
  <p>在这步大运中，您的发展重点应放在与用神{escape("、".join(v.yongshen[:2]) if v.yongshen else "—")}相关的方向上。顺应运势节奏，在有利时期积极进取，在平淡时期沉淀积累。</p>
  <p>近期建议：关注自身状态变化，如果感到顺畅则可加大投入，如果感到阻滞则宜调整节奏、蓄势待发。</p>
</div>'''

    return '''<div class="cr-dimension">
  <h3>近期运势</h3>
  <p>近期运势与整体命局节奏相关。建议关注自身状态变化，顺应内在节奏安排重要事项。</p>
  <p>在运势平稳期，适合学习充电、积累资源；在运势上升期，适合果断行动、把握机会。</p>
</div>'''


def _render_timeline(vm: DashboardVM) -> str:
    if not vm.dayun:
        return ''

    items = ''
    for i, d in enumerate(vm.dayun[:8]):
        assessment = d.assessment or '平'
        color_class = 'tl-good' if '吉' in assessment else ('tl-bad' if '凶' in assessment else 'tl-neutral')
        current_mark = ' tl-current' if i == 0 else ''
        items += (f'<div class="tl-item {color_class}{current_mark}">'
                  f'<div class="tl-age">{escape(d.age_range or "")}</div>'
                  f'<div class="tl-gz">{escape(d.gan_zhi or "")}</div>'
                  f'<div class="tl-assess">{escape(assessment)}</div>'
                  f'</div>')

    return f'''<section class="cr-timeline">
  <h2>人生节奏</h2>
  <p>以下是您人生各阶段的运势走向概览。每步大运为十年，标注了整体运势评估。</p>
  <div class="tl-track">{items}</div>
  <p class="tl-note">标注"吉"的阶段适合积极进取，"凶"的阶段宜守不宜攻、韬光养晦。</p>
</section>'''


def _render_advice(vm: DashboardVM) -> str:
    v = vm.verdict
    dm_wx = _get_dm_element(vm)
    yongshen_wx = v.yongshen[0] if v.yongshen else dm_wx
    jishen_wx = v.jishen[0] if v.jishen else ''
    traits_y = WUXING_TRAITS.get(yongshen_wx, WUXING_TRAITS['火'])
    traits_j = WUXING_TRAITS.get(jishen_wx, {}) if jishen_wx else {}

    do_items = [
        f'多接触{yongshen_wx}行相关的环境和人（{traits_y.get("industries", "")[:20]}等领域）',
        f'日常可多使用{traits_y.get("colors", "")}系的物品和装饰',
        f'有利方位为{traits_y.get("directions", "")}，重要决策可参考',
        '在运势上升期果断行动，把握关键机遇',
    ]
    dont_items = []
    if traits_j:
        # 排除与用神行业重叠的词
        j_industries = traits_j.get('industries', '')
        y_industries = traits_y.get('industries', '')
        if j_industries and j_industries != y_industries:
            dont_items.append(f'减少{jishen_wx}行过旺的环境（{j_industries[:20]}等需谨慎）')
        dont_items.append(f'避免过多使用{traits_j.get("colors", "")}系')
    dont_items.append('运势低迷期避免重大冒险决策')
    dont_items.append('不要过度依赖命理，行动和努力始终是第一位的')

    do_html = ''.join(f'<li>{escape(i)}</li>' for i in do_items)
    dont_html = ''.join(f'<li>{escape(i)}</li>' for i in dont_items)

    return f'''<section class="cr-advice">
  <h2>行动建议</h2>
  <div class="cr-advice-grid">
    <div class="cr-do"><h3>宜</h3><ul>{do_html}</ul></div>
    <div class="cr-dont"><h3>慎</h3><ul>{dont_html}</ul></div>
  </div>
</section>'''


CONSUMER_CSS = '''
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#f7f1e8;--surface:#fffaf2;--surface2:#f1e6d6;--ink:#2c1810;
  --muted:#7a6a58;--accent:#8a3b2a;--gold:#b99a5b;--green:#5f8d72;--red:#b85c4a;
  --radius:16px;--shadow:0 8px 28px rgba(54,35,20,.06)}
@media(prefers-color-scheme:dark){:root{--bg:#1a1612;--surface:#221e18;
  --surface2:#2a241c;--ink:#e8dcc8;--muted:#8a7a60;--accent:#c46a4a;--gold:#c4a85a;
  --green:#6aad82;--red:#d06a5a}}
body{font-family:"Noto Serif SC","STSong","SimSun",serif;background:var(--bg);
  color:var(--ink);line-height:1.85;font-size:15px}
.cr-container{max-width:720px;margin:0 auto;padding:24px 20px 60px}
h2{font-size:20px;color:var(--accent);margin:36px 0 12px;padding-bottom:8px;
  border-bottom:2px solid var(--surface2)}
h3{font-size:16px;color:var(--ink);margin:20px 0 8px}
p{margin:8px 0;text-indent:2em}
ul{margin:8px 0 8px 2em;list-style:disc}
li{margin:4px 0;text-indent:0}

/* Cover */
.cr-cover{text-align:center;padding:48px 24px 32px;border-bottom:2px solid var(--gold)}
.cr-cover-badge{display:inline-flex;align-items:center;justify-content:center;
  width:64px;height:64px;border-radius:50%;background:var(--accent);color:#fff;
  font-size:24px;font-weight:700;margin-bottom:16px}
.cr-title{font-size:28px;color:var(--ink);letter-spacing:4px;margin:8px 0}
.cr-subtitle{font-size:16px;color:var(--muted);margin:8px 0}
.cr-meta{display:flex;justify-content:center;gap:16px;margin-top:12px;
  font-size:13px;color:var(--muted);flex-wrap:wrap}

/* Reading guide */
.cr-guide{margin:32px 0;padding:24px;background:var(--surface);border-radius:var(--radius);
  border-left:4px solid var(--gold)}
.cr-guide h2{margin-top:0;border-bottom:none;font-size:16px}
.cr-guide p{font-size:14px;text-indent:0;margin:6px 0;line-height:1.8}

/* Summary card */
.cr-summary{margin:32px 0}
.cr-summary-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:16px 0}
.cr-identity-card,.cr-pattern-card,.cr-direction-card{padding:20px;background:var(--surface);
  border-radius:var(--radius);box-shadow:var(--shadow)}
.cr-id-label{font-size:11px;color:var(--muted);letter-spacing:2px;margin-bottom:6px}
.cr-id-value{font-size:17px;font-weight:700;color:var(--accent);margin-bottom:4px}
.cr-id-desc{font-size:13px;color:var(--muted)}
.cr-pros-cons{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px}
@media(max-width:540px){.cr-pros-cons{grid-template-columns:1fr}}
.cr-pros,.cr-cons{padding:16px 20px;border-radius:var(--radius)}
.cr-pros{background:rgba(95,141,114,.08);border:1px solid rgba(95,141,114,.2)}
.cr-cons{background:rgba(184,92,74,.06);border:1px solid rgba(184,92,74,.15)}
.cr-pros h3{color:var(--green);font-size:14px}
.cr-cons h3{color:var(--red);font-size:14px}
.cr-pros li,.cr-cons li{font-size:13px;margin:6px 0}

/* Dimensions */
.cr-dimension{margin:24px 0;padding:24px;background:var(--surface);border-radius:var(--radius);
  box-shadow:var(--shadow)}
.cr-dimension h3{margin-top:0;color:var(--accent);font-size:17px;
  padding-bottom:8px;border-bottom:1px solid var(--surface2)}
.cr-dimension p{font-size:14px;line-height:1.9}

/* Timeline */
.cr-timeline{margin:36px 0}
.cr-timeline>p{font-size:14px;color:var(--muted);text-indent:0}
.tl-track{display:flex;gap:8px;overflow-x:auto;padding:16px 0;margin:12px 0}
.tl-item{flex:0 0 auto;min-width:80px;padding:12px;text-align:center;
  border-radius:12px;background:var(--surface);border:2px solid var(--surface2)}
.tl-item.tl-good{border-color:var(--green);background:rgba(95,141,114,.06)}
.tl-item.tl-bad{border-color:var(--red);background:rgba(184,92,74,.05)}
.tl-item.tl-current{box-shadow:0 0 0 3px var(--gold)}
.tl-age{font-size:11px;color:var(--muted)}
.tl-gz{font-size:15px;font-weight:700;margin:4px 0}
.tl-assess{font-size:12px;color:var(--accent)}
.tl-note{font-size:12px;color:var(--muted);text-indent:0;margin-top:8px}

/* Advice */
.cr-advice{margin:36px 0}
.cr-advice-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:540px){.cr-advice-grid{grid-template-columns:1fr}}
.cr-do,.cr-dont{padding:20px;border-radius:var(--radius)}
.cr-do{background:rgba(95,141,114,.08);border:1px solid rgba(95,141,114,.2)}
.cr-dont{background:rgba(184,92,74,.06);border:1px solid rgba(184,92,74,.15)}
.cr-do h3{color:var(--green)}
.cr-dont h3{color:var(--red)}
.cr-do li,.cr-dont li{font-size:13px;margin:6px 0}

/* Appendix */
.cr-appendix{margin:40px 0}
.cr-appendix summary{cursor:pointer;font-size:14px;color:var(--muted);padding:12px 16px;
  background:var(--surface);border-radius:var(--radius);list-style:none}
.cr-appendix summary::-webkit-details-marker{display:none}
.cr-appendix summary::before{content:"\\25B6 ";font-size:10px}
.cr-appendix[open] summary::before{content:"\\25BC "}
.cr-appendix .appendix-body{padding:16px;font-size:13px;line-height:1.7;
  background:var(--surface);border-radius:0 0 var(--radius) var(--radius);
  max-height:600px;overflow-y:auto}

/* Disclaimer */
.cr-disclaimer{margin:40px 0;padding:20px;font-size:12px;color:var(--muted);
  border-top:1px solid var(--surface2);line-height:1.8}

/* Progress bar */
.cr-progress{position:fixed;top:0;left:0;width:0;height:3px;background:var(--gold);
  z-index:9999;transition:width .1s}

/* Print */
@media print{.cr-progress,.cr-appendix summary{display:none}
  .cr-appendix .appendix-body{max-height:none;display:block}
  body{font-size:12px}h2{font-size:16px}}
'''


def render_consumer_report(vm: DashboardVM, raw_markdown: str = '') -> str:
    """渲染消费级命理报告 HTML"""
    cover = _render_cover(vm)
    guide = _render_reading_guide(vm)
    summary = _render_summary_card(vm)

    dimensions = ''.join([
        '<section class="cr-dimensions"><h2>人生六维解读</h2>',
        _narrative_personality(vm),
        _narrative_career(vm),
        _narrative_wealth(vm),
        _narrative_love(vm),
        _narrative_health(vm),
        _narrative_current(vm),
        '</section>',
    ])

    timeline = _render_timeline(vm)
    advice = _render_advice(vm)

    appendix = ''
    if raw_markdown:
        from bazi_pro.ui.report_composer import _simple_md_to_html
        appendix_html = _simple_md_to_html(raw_markdown[:8000])
        appendix = (f'<details class="cr-appendix">'
                    f'<summary>查看完整技术分析（专业人士参考）</summary>'
                    f'<div class="appendix-body">{appendix_html}</div></details>')

    disclaimer = '''<div class="cr-disclaimer">
  <p>免责声明：本报告基于传统命理学理论（参酌《穷通宝鉴》《子平真诠》《三命通会》《滴天髓》《神峰通考》等经典），仅供传统文化学习与自我认知参考，不构成任何人生决策的依据。命理揭示的是趋势和倾向，个人的努力、选择和环境同样重要。</p>
  <p>生成引擎：bazi-pro v5.0</p>
</div>'''

    body_content = f'{cover}{guide}{summary}{dimensions}{timeline}{advice}'
    body_content, used_terms = annotate_terms(body_content)
    glossary = render_glossary_section(used_terms)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>命理解读报告 · {escape(vm.verdict.day_master or "")}</title>
<style>
{CONSUMER_CSS}
{GLOSSARY_CSS}
</style>
</head>
<body>
<div class="cr-progress" id="progress"></div>
<div class="cr-container">
{body_content}
{glossary}
{appendix}
{disclaimer}
</div>
<script>
window.addEventListener('scroll',function(){{
  var h=document.documentElement;
  var pct=h.scrollTop/(h.scrollHeight-h.clientHeight)*100;
  document.getElementById('progress').style.width=pct+'%';
}});
</script>
</body>
</html>'''
