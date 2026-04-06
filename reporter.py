import csv
import json
from pathlib import Path
from checker.models import AccessibilityReport


def print_console_summary(report: AccessibilityReport) -> None:
    print("\n" + "=" * 65)
    print("ACCESSIBILITY AUDIT SUMMARY")
    print("=" * 65)
    print(f"URL:            {report.url}")
    print(f"Title:          {report.page_title}")
    print(f"Response time:  {report.response_time}s")
    print(f"Score:          {report.score}/100")
    print(f"Rating:         {report.rating}")
    print("\nStats:")
    for key, value in report.stats.items():
        print(f"  - {key.replace('_', ' ').title()}: {value}")

    print("\nIssues:")
    if not report.issues:
        print("  No issues found.")
    else:
        for index, issue in enumerate(report.issues[:12], start=1):
            print(
                f"  {index}. [{issue.severity.upper()}] {issue.message} "
                f"({issue.element})"
            )

        remaining = len(report.issues) - 12
        if remaining > 0:
            print(f"  ... and {remaining} more issue(s).")

    if report.passed_checks:
        print("\nPassed checks:")
        for passed in report.passed_checks:
            print(f"  - {passed}")

    if report.warnings:
        print("\nWarnings:")
        for warning in report.warnings:
            print(f"  - {warning}")


def save_txt_report(report: AccessibilityReport, filename: str = "accessibility_report.txt") -> None:
    output_path = Path(filename)

    with output_path.open("w", encoding="utf-8") as file:
        file.write("WEB ACCESSIBILITY CHECKER REPORT\n")
        file.write("=" * 70 + "\n\n")
        file.write(f"URL: {report.url}\n")
        file.write(f"Title: {report.page_title}\n")
        file.write(f"Response time: {report.response_time}s\n")
        file.write(f"Score: {report.score}/100\n")
        file.write(f"Rating: {report.rating}\n\n")

        file.write("STATISTICS\n")
        file.write("-" * 70 + "\n")
        for key, value in report.stats.items():
            file.write(f"{key.replace('_', ' ').title()}: {value}\n")

        file.write("\nISSUES FOUND\n")
        file.write("-" * 70 + "\n")
        if not report.issues:
            file.write("No issues found.\n")
        else:
            for index, issue in enumerate(report.issues, start=1):
                file.write(f"{index}. Rule ID: {issue.rule_id}\n")
                file.write(f"   Category: {issue.category}\n")
                file.write(f"   Severity: {issue.severity}\n")
                file.write(f"   Message: {issue.message}\n")
                file.write(f"   Element: {issue.element}\n")
                file.write(f"   Recommendation: {issue.recommendation}\n")
                if issue.wcag_reference:
                    file.write(f"   WCAG: {issue.wcag_reference}\n")
                if issue.evidence:
                    file.write(f"   Evidence: {issue.evidence}\n")
                file.write("\n")

        file.write("PASSED CHECKS\n")
        file.write("-" * 70 + "\n")
        if report.passed_checks:
            for passed in report.passed_checks:
                file.write(f"- {passed}\n")
        else:
            file.write("No passed checks recorded.\n")

        if report.warnings:
            file.write("\nWARNINGS\n")
            file.write("-" * 70 + "\n")
            for warning in report.warnings:
                file.write(f"- {warning}\n")


def save_csv_report(report: AccessibilityReport, filename: str = "accessibility_issues.csv") -> None:
    output_path = Path(filename)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "rule_id",
                "category",
                "severity",
                "message",
                "element",
                "recommendation",
                "wcag_reference",
                "evidence",
            ]
        )

        for issue in report.issues:
            writer.writerow(
                [
                    issue.rule_id,
                    issue.category,
                    issue.severity,
                    issue.message,
                    issue.element,
                    issue.recommendation,
                    issue.wcag_reference,
                    issue.evidence,
                ]
            )


def save_json_report(report: AccessibilityReport, filename: str = "accessibility_report.json") -> None:
    output_path = Path(filename)

    data = {
        "url": report.url,
        "page_title": report.page_title,
        "response_time": report.response_time,
        "score": report.score,
        "rating": report.rating,
        "stats": report.stats,
        "passed_checks": report.passed_checks,
        "warnings": report.warnings,
        "issues": [
            {
                "rule_id": issue.rule_id,
                "category": issue.category,
                "severity": issue.severity,
                "message": issue.message,
                "element": issue.element,
                "recommendation": issue.recommendation,
                "wcag_reference": issue.wcag_reference,
                "evidence": issue.evidence,
            }
            for issue in report.issues
        ],
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)