"""
bazi-pro 术语词典系统
提供命理术语的通俗解释，支持 inline tooltip 标注和末尾词典渲染
"""

import re
from dataclasses import dataclass
from html import escape


@dataclass(frozen=True)
class GlossaryEntry:
    term: str
    short_def: str
    full_def: str
    category: str


GLOSSARY: dict[str, GlossaryEntry] = {}


def _g(term, short_def, full_def, category):
    GLOSSARY[term] = GlossaryEntry(term, short_def, full_def, category)


# ── 十神 ──
_g('比肩', '与自己同类的力量', '五行属性与日主相同、阴阳也相同的天干。代表同辈、朋友、竞争者，象征独立、自主、竞争意识。', '十神')
_g('劫财', '争夺资源的同类', '五行属性与日主相同、阴阳相反的天干。代表兄弟姐妹、合作伙伴，也暗示竞争和分夺。', '十神')
_g('食神', '才华与创造力', '日主所生、阴阳相同的天干。代表才艺、口福、表达能力，是温和的输出方式，象征从容与享受。', '十神')
_g('伤官', '锋芒与叛逆', '日主所生、阴阳相反的天干。代表创新、反叛、口才犀利，是激烈的输出方式，象征不拘一格。', '十神')
_g('偏财', '流动的财富', '日主所克、阴阳相同的天干。代表意外之财、投资收益、人缘广泛，象征慷慨与交际能力。', '十神')
_g('正财', '稳定的收入', '日主所克、阴阳相反的天干。代表正当收入、节俭持家、务实态度，象征勤劳与踏实。', '十神')
_g('七杀', '压力与挑战', '克日主、阴阳相同的天干。代表外部压力、竞争对手、权威挑战，也象征魄力与决断力。', '十神')
_g('正官', '规则与责任', '克日主、阴阳相反的天干。代表上司、法规、社会规范，象征自律、责任感和正统地位。', '十神')
_g('偏印', '非主流的智慧', '生日主、阴阳相同的天干。代表偏门学问、直觉、独特思维，也暗示孤独和不被理解。', '十神')
_g('正印', '传统的庇护', '生日主、阴阳相反的天干。代表母亲、学历、贵人扶持，象征包容、慈爱和传统智慧。', '十神')
_g('比劫', '自身同类力量', '比肩和劫财的统称，代表与自己属性相同的力量，包括朋友、同辈、竞争者。', '十神')
_g('食伤', '才华输出', '食神和伤官的统称，代表个人才华、创造力和表达能力的输出渠道。', '十神')
_g('财星', '财富与物质', '正财和偏财的统称，代表一个人获取和管理物质资源的能力。', '十神')
_g('官杀', '外部约束力', '正官和七杀的统称，代表来自外部的管束、压力和挑战。', '十神')
_g('印星', '内在支撑力', '正印和偏印的统称，代表来自长辈、学识、精神层面的滋养和保护。', '十神')

# ── 旺衰 ──
_g('得令', '生在有利的季节', '日主在出生月份是否处于旺盛状态。得令如同植物生在适合的季节，先天条件好。', '旺衰')
_g('得地', '脚下有根基', '日主在地支中是否有同类五行的根。得地如同大树扎根深处，根基稳固不易动摇。', '旺衰')
_g('得势', '周围有帮手', '天干地支中是否有较多生助日主的力量。得势如同身边有众多支持者。', '旺衰')
_g('身旺', '自身力量充沛', '日主得到较多生助，自身能量充足。性格上往往自信、主动，适合独立开创。', '旺衰')
_g('身弱', '自身力量不足', '日主缺乏生助，自身能量偏弱。性格上往往谨慎、合作型，适合借力发展。', '旺衰')
_g('极旺', '力量极度充沛', '日主得到压倒性的生助，自身能量极强。往往个性鲜明、意志坚定，需要合适的发挥渠道。', '旺衰')
_g('极弱', '力量极度不足', '日主几乎没有生助，自身能量极弱。命理上可能形成"从格"，即顺从大势而非对抗。', '旺衰')

# ── 格局 ──
_g('正官格', '正统权威型格局', '月令透出正官星，代表命主适合在体制、规范内发展，重视秩序和社会地位。', '格局')
_g('七杀格', '开拓进取型格局', '月令透出七杀星，代表命主有魄力和冲劲，适合在竞争激烈的环境中脱颖而出。', '格局')
_g('食神格', '才艺享受型格局', '月令透出食神星，代表命主有艺术天赋和生活品味，适合创意、技术类发展。', '格局')
_g('伤官格', '创新突破型格局', '月令透出伤官星，代表命主思维活跃、不拘常规，适合需要创新和变革的领域。', '格局')
_g('正财格', '稳健积累型格局', '月令透出正财星，代表命主务实勤恳，适合稳步积累财富的发展路径。', '格局')
_g('偏财格', '灵活经营型格局', '月令透出偏财星，代表命主善于交际和把握机会，适合商业和投资领域。', '格局')
_g('正印格', '学术贵人型格局', '月令透出正印星，代表命主重视学问和修养，容易得到贵人提携。', '格局')
_g('偏印格', '独特思维型格局', '月令透出偏印星，代表命主有独特的思考方式和专业技能，适合专精领域。', '格局')
_g('建禄格', '自力更生型格局', '月令为日主的禄位（同类五行），代表命主根基扎实，需要另寻发展方向。', '格局')
_g('月劫格', '竞争合作型格局', '月令为日主的劫财，代表命主身边竞争与合作并存，需要找到独特定位。', '格局')
_g('从强格', '顺势而为型格局', '日主极旺无制，顺从自身强势发展。适合独立创业、领导岗位。', '格局')
_g('从财格', '顺财而行型格局', '日主极弱而财星极旺，顺从财势发展。适合商业、金融领域。', '格局')
_g('从官杀格', '顺势服务型格局', '日主极弱而官杀极旺，顺从权势发展。适合体制内或大型组织。', '格局')
_g('从儿格', '顺才华而行型格局', '日主不论强弱，食伤极旺且生财，顺从才华输出。适合艺术、教育、技术。', '格局')

# ── 关系 ──
_g('六冲', '对立与变动', '两个地支形成对冲关系，代表变动、冲突或转折。不一定是坏事，也可能带来突破。', '关系')
_g('六合', '和谐与合作', '两个地支形成合化关系，代表融合、合作或缘分。通常带来助力和机遇。', '关系')
_g('三合', '三方汇聚的力量', '三个地支形成三合局，代表某种五行力量的强力汇聚，影响深远。', '关系')
_g('半合', '部分汇聚的力量', '三合局中的两个地支相遇，力量部分汇聚，影响较三合局稍弱。', '关系')
_g('三刑', '摩擦与考验', '特定地支组合形成的刑克关系，代表人际摩擦、健康考验或法律纠纷的信号。', '关系')
_g('六害', '暗中的阻碍', '两个地支形成相害关系，代表暗中的不利因素，需要留意人际关系中的隐患。', '关系')
_g('天干五合', '天干的合作关系', '特定天干之间的合化关系，可能改变五行力量分布，影响命局走向。', '关系')
_g('合化', '融合转变', '两个天干或地支相合后转化为新的五行属性，代表关系的深度融合和质变。', '关系')
_g('争合', '多方争夺', '一个天干同时被两个天干争合，导致合而不化，代表选择困难或多方牵扯。', '关系')

# ── 用神体系 ──
_g('用神', '最需要的五行', '命局中最能平衡和改善整体格局的五行元素。是选择职业、方位、颜色等的核心参考。', '用神')
_g('喜神', '有利的辅助五行', '能够生助用神或对命局有正面作用的五行。是用神之外的第二优先选择。', '用神')
_g('忌神', '需要回避的五行', '对命局产生负面影响的五行元素。在选择中应尽量避开相关方向。', '用神')
_g('调候', '季节性的平衡需求', '根据出生季节的寒暖燥湿，命局需要特定五行来调节气候平衡。如冬天生人需火暖。', '用神')
_g('通关', '化解对立的桥梁', '当命局中两种五行严重对立时，用中间五行来疏通调和，化解冲突。', '用神')
_g('病药', '问题与解决方案', '命局中的"病"是主要问题所在，"药"是能够化解该问题的五行力量。', '用神')

# ── 五行 ──
_g('五行', '万物的五种基本属性', '木、火、土、金、水五种元素，是中国传统哲学描述事物属性和关系的基本框架。', '五行')
_g('相生', '滋养促进的关系', '木生火、火生土、土生金、金生水、水生木。前者滋养后者，如母亲养育孩子。', '五行')
_g('相克', '制约控制的关系', '木克土、土克水、水克火、火克金、金克木。前者制约后者，维持平衡。', '五行')

# ── 大运 ──
_g('大运', '人生的大阶段', '每十年为一步大运，代表人生不同阶段的运势主题和环境变化。', '大运')
_g('流年', '每一年的运势', '每年的天干地支对命局的影响，是大运之下更细致的年度运势变化。', '大运')
_g('起运', '大运开始的年龄', '根据出生时间计算出的第一步大运开始年龄，之后每十年换一步运。', '大运')

# ── 其他概念 ──
_g('日主', '命盘的主角', '出生日的天干，代表命主自身。整个命盘都以日主为中心来分析各种关系。', '概念')
_g('月令', '出生月的主导力量', '出生月份的地支，是判断命局强弱和格局的最重要参考。如同一年中的季节。', '概念')
_g('藏干', '地支中隐藏的天干', '每个地支内部包含1-3个天干，代表隐藏的力量和潜在的影响。', '概念')
_g('羊刃', '极旺的标志', '日主在某地支达到最旺状态的标记，代表刚烈、果断，也暗示需要控制锋芒。', '概念')
_g('空亡', '力量暂时缺位', '特定地支处于"空"的状态，代表该位置的力量暂时不实，可能晚发或有波折。', '概念')
_g('天德', '天赐的福星', '命局中的吉祥标记，代表天生有化解灾厄的能力，遇难呈祥。', '概念')
_g('月德', '月份的福星', '与天德类似的吉祥标记，代表品性端正、有贵人缘。', '概念')
_g('华盖', '孤高与智慧', '代表精神世界丰富、有宗教或哲学倾向，也暗示性格偏孤独清高。', '概念')
_g('食神制杀', '用才华化解压力', '食神克制七杀，代表用自身才华和能力来化解外部压力和挑战。是一种优雅的应对方式。', '概念')
_g('官杀混杂', '多重压力并存', '正官和七杀同时出现在命局中，代表来自不同方向的压力和约束同时存在。', '概念')
_g('伤官见官', '才华与规则的冲突', '伤官与正官同时出现，代表个人创新欲望与外部规范之间的张力。', '概念')
_g('杀印相生', '压力转化为动力', '七杀生偏印，代表外部压力能够转化为学习动力和成长机会。', '概念')
_g('食伤生财', '才华变现', '食神伤官生财星，代表个人才华和创造力能够转化为实际收入。', '概念')

del _g


# ── 标注函数 ──

def annotate_terms(html: str, extra_terms: set[str] | None = None) -> tuple[str, set[str]]:
    """在 HTML 文本中为已知术语添加 tooltip 标注

    只替换标签外的文本内容，不替换属性值或已标注区域内的文本。
    每个术语在整个文档中只标注首次出现。
    返回 (标注后的 HTML, 已标注的术语集合)
    """
    used_terms: set[str] = set()
    terms_by_length = sorted(GLOSSARY.keys(), key=len, reverse=True)

    for term in terms_by_length:
        entry = GLOSSARY.get(term)
        if not entry:
            continue
        if term not in html:
            continue

        tip_text = escape(entry.short_def)
        replacement = f'<span class="term-tip" data-tip="{tip_text}">{term}</span>'

        # 只替换第一个出现在标签外文本中的匹配
        # 策略：按 < 和 > 分割，只在标签外部分替换
        parts = re.split(r'(<[^>]*>)', html)
        replaced = False
        for i, part in enumerate(parts):
            if replaced:
                break
            # 跳过 HTML 标签本身
            if part.startswith('<'):
                continue
            # 跳过已在 term-tip span 内的文本（前一个标签是 term-tip 开标签）
            if i >= 2 and 'term-tip' in parts[i - 1]:
                continue
            if term in part:
                parts[i] = part.replace(term, replacement, 1)
                replaced = True
                used_terms.add(term)
        if replaced:
            html = ''.join(parts)

    return html, used_terms


def render_glossary_section(used_terms: set[str]) -> str:
    """渲染术语小词典 HTML 区块"""
    if not used_terms:
        return ''

    by_category: dict[str, list[GlossaryEntry]] = {}
    for term in sorted(used_terms):
        entry = GLOSSARY.get(term)
        if entry:
            by_category.setdefault(entry.category, []).append(entry)

    category_order = ['十神', '旺衰', '格局', '用神', '关系', '五行', '大运', '概念']
    category_labels = {
        '十神': '十神（人际关系与能力类型）',
        '旺衰': '旺衰（自身力量强弱）',
        '格局': '格局（人生发展模式）',
        '用神': '用神体系（有利与不利方向）',
        '关系': '关系（地支互动）',
        '五行': '五行基础',
        '大运': '大运流年（时间节奏）',
        '概念': '其他概念',
    }

    sections = ''
    for cat in category_order:
        entries = by_category.get(cat, [])
        if not entries:
            continue
        items = ''
        for e in entries:
            items += (f'<div class="gloss-item">'
                      f'<span class="gloss-term">{escape(e.term)}</span>'
                      f'<span class="gloss-def">{escape(e.full_def)}</span>'
                      f'</div>')
        label = category_labels.get(cat, cat)
        sections += f'<div class="gloss-category"><h4>{escape(label)}</h4>{items}</div>'

    return f'<section class="glossary-section"><h2>术语小词典</h2><p class="gloss-intro">以下是本报告中出现的命理术语解释，帮助您更好地理解报告内容。</p>{sections}</section>'


GLOSSARY_CSS = '''
.term-tip{border-bottom:1px dotted var(--gold,#b99a5b);cursor:help;position:relative;white-space:nowrap}
.term-tip::after{content:attr(data-tip);position:absolute;bottom:calc(100% + 6px);left:50%;
  transform:translateX(-50%);padding:6px 12px;background:var(--ink,#241a14);color:var(--bg,#f7f1e8);
  font-size:12px;line-height:1.5;border-radius:6px;white-space:normal;min-width:120px;max-width:240px;
  text-align:center;opacity:0;pointer-events:none;transition:opacity .2s;z-index:100;box-shadow:0 4px 12px rgba(0,0,0,.15)}
.term-tip:hover::after{opacity:1}
@media(max-width:640px){.term-tip::after{left:0;transform:none;min-width:160px}}
.glossary-section{margin:40px 0;padding:32px 24px;background:var(--surface,#fffaf2);border-radius:16px}
.glossary-section h2{font-size:20px;color:var(--accent,#8a3b2a);margin-bottom:8px}
.gloss-intro{font-size:14px;color:var(--muted,#7a6a58);margin-bottom:20px}
.gloss-category{margin-bottom:20px}
.gloss-category h4{font-size:13px;color:var(--muted,#7a6a58);letter-spacing:2px;margin-bottom:8px;
  padding-bottom:4px;border-bottom:1px solid var(--surface2,#f1e6d6)}
.gloss-item{display:flex;gap:12px;padding:8px 0;border-bottom:1px solid var(--surface2,#f1e6d6);align-items:baseline}
.gloss-item:last-child{border-bottom:none}
.gloss-term{font-weight:700;color:var(--accent,#8a3b2a);min-width:72px;flex-shrink:0;font-size:14px}
.gloss-def{font-size:13px;color:var(--ink,#241a14);line-height:1.7}
'''
