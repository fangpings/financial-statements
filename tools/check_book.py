#!/usr/bin/env python3
"""Check the book manifest, navigation, exercises, Markdown links and case math."""

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from accounting_lab import equal, load, verify_case, verify_other_examples, verify_real

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "textbook"


def table_rows(path):
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows.setdefault(cells[0], []).append(cells[1:])
    return rows


def verify_printed_tables():
    """Catch divergence between the actual printed problem tables and JSON inputs."""
    rows = table_rows(BOOK / "36-capstone.md")
    case = load("northstar.json")
    income_fields = {"收入": "revenue", "销售成本": "cogs", "其他经营费用 不含折旧": "opex_ex_depreciation",
                     "折旧": "depreciation", "利息费用": "interest", "所得税费用及现金税": "tax",
                     "净利润": "net_income", "CFO": "cfo", "现金购建设备": "capex",
                     "借款收入": "borrowings", "偿还本金": "principal_repaid", "现金分红": "dividends"}
    balance_fields = {"现金": "cash", "应收账款": "receivables", "存货": "inventory",
                      "固定资产净额": "ppe_net", "资产合计": "assets", "应付账款": "payables",
                      "应计经营费用": "accruals", "有息债务": "debt", "股东权益": "equity"}
    for labels, periods in ((income_fields, case["years"][1:]), (balance_fields, case["years"])):
        for label, field in labels.items():
            printed = rows[label][0]
            if len(printed) != len(periods):
                raise ValueError(f"Printed {label}: wrong number of periods")
            for cell, period in zip(printed, periods):
                equal(f"Printed {period['year']} {label}", float(cell.replace(",", "")), period[field])
    real = load("real-extracts.json")
    rows = table_rows(BOOK / "35-guided-report.md")
    annual_fields = {"收入": "revenue", "营业利润": "operating_income", "净利润": "net_income",
                     "经营现金流": "cfo", "现金购建固定资产支出正值": "capex"}
    for label, field in annual_fields.items():
        for cell, period in zip(rows[label][0], ("current", "prior")):
            equal(f"Printed annual {label} {period}", float(cell.replace(",", "")), real["annual"][period][field])
    quarterly_fields = {"收入": ("revenue", 1), "CFO": ("cfo", 0), "现金购建设备支出正值": ("capex", 0)}
    for label, (field, occurrence) in quarterly_fields.items():
        for cell, period in zip(rows[label][occurrence], ("current", "prior")):
            equal(f"Printed quarter {label} {period}", float(cell.replace(",", "")), real["quarter"][period][field])
    for label, expected in real["annual"]["bridges"]["cfo_adjustments"]:
        cell = rows[label][0][0]
        actual = float(cell.replace(",", "").replace("−", "-"))
        equal(f"Printed annual CFO adjustment {label}", actual, expected)


def main():
    errors = []
    warnings = []
    chapters = sorted(BOOK.glob("[0-9][0-9]-*.md"))
    appendices = sorted(BOOK.glob("appendix-*.md"))
    manifest = json.loads((BOOK / "curriculum.json").read_text(encoding="utf-8"))
    entries = [c for section in manifest for c in section["chapters"]]
    if len(manifest) != 8 or len(chapters) != 36 or len(appendices) != 6:
        errors.append("Expected 8 parts, 36 chapters and 6 appendices")
    if [p.name for p in chapters] != [c["file"] for c in entries]:
        errors.append("Manifest filenames/order differ from chapter files")
    if [c["number"] for c in entries] != list(range(1, 37)):
        errors.append("Chapter sequence must be 01 through 36")
    index = (BOOK / "README.md").read_text(encoding="utf-8")
    exercises = 0
    for i, chapter in enumerate(chapters):
        body = chapter.read_text(encoding="utf-8")
        if body.splitlines()[0] != "# " + entries[i]["title"]:
            errors.append(f"{chapter.name}: title differs from manifest")
        if f"]({chapter.name})" not in index:
            errors.append(f"{chapter.name}: not linked in reading index")
        if len(body) < 1200:
            errors.append(f"{chapter.name}: unexpectedly short chapter")
        required = ("<details>", "参考") if chapter.name.startswith("36-") else ("<details>", "参考", "https://")
        for token in required:
            if token not in body:
                errors.append(f"{chapter.name}: missing {token}")
        if "目录](README.md)" not in body:
            errors.append(f"{chapter.name}: missing index navigation")
        if i and f"]({chapters[i-1].name})" not in body:
            errors.append(f"{chapter.name}: missing previous chapter navigation")
        if i + 1 < len(chapters) and f"]({chapters[i+1].name})" not in body:
            errors.append(f"{chapter.name}: missing next chapter navigation")
        question_sections = re.findall(r"^#{2,3} (?:单元)?练习\s*\n(.*?)(?=<details>)", body, re.M | re.S)
        count = sum(len(re.findall(r"^\d+\. ", section, re.M)) for section in question_sections)
        minimum = 6 if chapter.name.startswith("34-") else 4
        if count < minimum:
            errors.append(f"{chapter.name}: expected at least {minimum} numbered exercise questions, got {count}")
        exercises += count
    for appendix in appendices:
        if f"]({appendix.name})" not in index:
            errors.append(f"{appendix.name}: not in reading index")
    external = set()
    docs = ([ROOT / "README.md", ROOT / "data" / "README.md"] +
            sorted(BOOK.glob("*.md")) + sorted((ROOT / "reviews").glob("*.md")))
    for path in docs:
        body = path.read_text(encoding="utf-8")
        if body.count("<details>") != body.count("</details>"):
            errors.append(f"{path.name}: unbalanced answer elements")
        if len(re.findall(r"^~~~", body, re.M)) % 2 or len(re.findall(r"^```", body, re.M)) % 2:
            errors.append(f"{path.name}: unbalanced code fences")
        if re.search(r"TODO|TBD|待补写|正文待写|占位章节", body):
            errors.append(f"{path.name}: unresolved drafting marker")
        for href in re.findall(r"\[[^\]]*\]\(([^)]+)\)", body):
            parsed = urlsplit(href)
            if parsed.scheme in ("http", "https"):
                external.add(href)
                continue
            if parsed.scheme or not parsed.path:
                continue
            destination = (path.parent / unquote(parsed.path)).resolve()
            if not destination.exists():
                message = f"{path.name}: missing target {href}"
                if not destination.is_relative_to(ROOT):
                    warnings.append("Optional adjacent repository: " + message)
                else:
                    errors.append(message)
    for ending in ("04-", "10-", "15-", "22-", "26-", "30-", "34-", "36-"):
        path = next(p for p in chapters if p.name.startswith(ending))
        if "综合作业" not in path.read_text(encoding="utf-8"):
            errors.append(f"{path.name}: missing part assignment")
    try:
        verify_case(load("northstar.json"))
        verify_real(load("real-extracts.json"))
        verify_other_examples()
        verify_printed_tables()
    except (ValueError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    for warning in warnings:
        print("WARNING:", warning)
    if errors:
        for error in errors:
            print("ERROR:", error)
        raise SystemExit(1)
    characters = sum(len(p.read_text(encoding="utf-8")) for p in BOOK.glob("*.md"))
    print(f"PASS: {len(chapters)} chapters, {len(appendices)} appendices, 8 parts")
    print(f"PASS: {exercises} numbered questions in chapter exercise sections; answer elements present")
    print("PASS: local links, navigation, answer markup, printed case tables and specified accounting checks")
    print(f"Textbook Markdown characters: {characters:,}; distinct external links: {len(external)}")
    print("External URLs are inventoried, not fetched by this offline check.")


if __name__ == "__main__":
    main()
