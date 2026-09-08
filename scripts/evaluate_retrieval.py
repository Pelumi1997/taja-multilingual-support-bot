from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from taja_bot.models import LanguageCode
from taja_bot.services.faq import FaqService


ROOT = Path(__file__).resolve().parents[1]
service = FaqService(ROOT / "src" / "taja_bot" / "data" / "faqs.json")
queries = json.loads((ROOT / "examples" / "evaluation_queries.json").read_text(encoding="utf-8"))

correct = 0
by_language: dict[str, Counter[str]] = defaultdict(Counter)
rows: list[dict[str, object]] = []
for item in queries:
    language = LanguageCode(item["language"])
    result = service.match(item["query"], language)
    predicted = result.faq["id"]
    passed = predicted == item["expected_faq_id"]
    correct += int(passed)
    by_language[language.value]["correct" if passed else "incorrect"] += 1
    rows.append({**item, "predicted": predicted, "score": result.score, "passed": passed})

accuracy = correct / len(queries) if queries else 0.0
report = [
    "# Retrieval evaluation",
    "",
    "> Development test only. The dataset is small and hand-curated; this is not a production-accuracy claim.",
    "",
    f"- Queries: **{len(queries)}**",
    f"- Correct top-1 matches: **{correct}**",
    f"- Top-1 accuracy: **{accuracy:.1%}**",
    "",
    "## Results by language",
    "",
    "| Language | Correct | Incorrect | Accuracy |",
    "|---|---:|---:|---:|",
]
for language in ["en", "pcm", "ha", "ig", "yo"]:
    counts = by_language[language]
    total = counts["correct"] + counts["incorrect"]
    language_accuracy = counts["correct"] / total if total else 0.0
    report.append(f"| {language} | {counts['correct']} | {counts['incorrect']} | {language_accuracy:.1%} |")

failures = [row for row in rows if not row["passed"]]
report.extend(["", "## Misclassifications", ""])
if not failures:
    report.append("No misclassifications in this small test set.")
else:
    report.extend(["| Language | Query | Expected | Predicted | Score |", "|---|---|---|---|---:|"])
    for row in failures:
        report.append(
            f"| {row['language']} | {row['query']} | {row['expected_faq_id']} | {row['predicted']} | {row['score']:.3f} |"
        )

output = ROOT / "reports" / "retrieval_evaluation.md"
output.write_text("\n".join(report) + "\n", encoding="utf-8")
print(f"Top-1 accuracy: {accuracy:.1%} ({correct}/{len(queries)})")
print(f"Report written to {output}")
