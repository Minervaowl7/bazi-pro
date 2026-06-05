"""从 LLM 回答中提取选项字母"""
import re


def extract_answer(text: str) -> str:
    """从 LLM 回答中提取选项字母（A/B/C/D）

    优先级：
    1. 明确声明 "答案是X" / "选择X" / "选X"
    2. 行首/行尾独立出现的字母
    3. 括号中的字母 (A) / 【A】
    4. 第一个出现的选项字母
    """
    if not text:
        return ""
    text = text.strip()

    # 明确声明
    patterns = [
        r'(?:答案|选择|选|应选|应为|应该[是选])\s*[：:]?\s*([A-D])',
        r'(?:answer|Answer)\s*[：:is]*\s*([A-D])',
        r'^\s*([A-D])\s*$',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.MULTILINE | re.IGNORECASE)
        if m:
            return m.group(1).upper()

    # 括号中的字母
    m = re.search(r'[（(【\[]([A-D])[）)】\]]', text)
    if m:
        return m.group(1).upper()

    # 行首独立字母
    m = re.search(r'^([A-D])[.、。：:\s]', text, re.MULTILINE)
    if m:
        return m.group(1).upper()

    # 最后兜底：第一个出现的选项字母
    m = re.search(r'([A-D])', text)
    if m:
        return m.group(1).upper()

    return ""


def load_ground_truth(dataset: list[dict]) -> dict[str, str]:
    """从数据集中提取标准答案 {question_id: answer}"""
    gt = {}
    for person in dataset:
        for q in person.get("questions", []):
            qid = q.get("question_id", "")
            answer = q.get("answer", "")
            if qid and answer:
                gt[qid] = answer.strip().upper()
    return gt
