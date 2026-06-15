from collections import Counter
from pathlib import Path

REPORT_FILE = Path("report.md")


def generate_report(results: list[dict], errors: list[dict], write_file: bool = True) -> str:
    total = len(results)

    categories = Counter(r["category"] for r in results)
    priorities = Counter(r["priority"] for r in results)
    departments = Counter(r["target_department"] for r in results if r.get("target_department"))
    needs_clarification = [r for r in results if r.get("needs_clarification")]

    lines = [
        "# Request Classification Report\n",
        f"**Total processed:** {total}  ",
        f"**Failed (LLM error):** {len(errors)}\n",
        "## By Category",
        *[f"- {cat}: {count}" for cat, count in categories.most_common()],
        "\n## By Priority",
        *[f"- {p}: {count}" for p, count in priorities.most_common()],
        "\n## By Department",
        *[f"- {dept}: {count}" for dept, count in departments.most_common()],
        "\n## Needs Clarification",
        f"Total: {len(needs_clarification)}\n",
        *[f"- [{r['id']}] {r['short_summary']}" for r in needs_clarification],
    ]

    if errors:
        lines += [
            "\n## Failed Requests",
            *[f"- [{e['id']}] parse/validation error" for e in errors],
        ]

    report_text = "\n".join(lines)

    if write_file:
        REPORT_FILE.write_text(report_text, encoding="utf-8")
        print(f"Report written to {REPORT_FILE}")

    return report_text
