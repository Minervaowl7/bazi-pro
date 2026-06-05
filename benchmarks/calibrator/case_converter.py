"""错题转 golden case"""
import json
from pathlib import Path


def _resolve_bazi(person_id: str, dataset: list[dict]) -> str:
    for person in dataset:
        if person.get("person_id") == person_id:
            profile = person.get("profile", {})
            bazi = profile.get("bazi", "")
            if bazi:
                return bazi
            birth = profile.get("birth", {})
            if birth:
                parts = []
                for key in ["year", "month", "day", "hour"]:
                    val = birth.get(key)
                    if val is not None:
                        parts.append(str(val))
                return " ".join(parts) if parts else ""
    return ""


def _resolve_day_master(person_id: str, dataset: list[dict]) -> str:
    for person in dataset:
        if person.get("person_id") == person_id:
            profile = person.get("profile", {})
            return profile.get("day_master", "")
    return ""


def convert_errors_to_golden_cases(
    baseline: dict,
    output_dir: Path,
    dataset: list[dict] | None = None,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    wrong = baseline.get("wrong_questions", [])
    if not wrong:
        return 0

    count = 0
    seen: set[str] = set()

    for w in wrong:
        pid = w.get("person_id", "")
        qid = w.get("question_id", "")
        key = f"{pid}_{qid}"
        if key in seen:
            continue
        seen.add(key)

        expected = w.get("expected", "")
        extracted = w.get("extracted", "")
        question_text = w.get("question_text", "")

        bazi = ""
        day_master = ""
        if dataset:
            bazi = _resolve_bazi(pid, dataset)
            day_master = _resolve_day_master(pid, dataset)

        case = {
            "id": f"benchmark_{pid}_{qid}",
            "description": f"BaziQA 错题: {question_text[:60]}" if len(question_text) > 60 else f"BaziQA 错题: {question_text}",
            "input": {
                "bazi": bazi,
                "day_master": day_master,
            },
            "must_include": [expected] if expected else [],
            "must_not_include": [extracted] if extracted else [],
        }

        filename = f"benchmark_{pid}_{qid}.json"
        case_path = output_dir / filename
        case_path.write_text(
            json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        count += 1

    return count
