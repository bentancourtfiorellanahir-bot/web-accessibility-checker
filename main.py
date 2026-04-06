from checker.fetcher import fetch_html
from checker.parser import build_soup
from checker.rules import AccessibilityAuditor
from checker.reporter import save_txt_report, save_csv_report, save_json_report, print_console_summary


def main() -> None:
    print("=" * 65)
    print("WEB ACCESSIBILITY CHECKER")
    print("=" * 65)

    url = input("Enter a URL to analyze: ").strip()

    if not url:
        print("No URL provided. Exiting.")
        return

    try:
        html, final_url, response_time = fetch_html(url)
        soup = build_soup(html)

        auditor = AccessibilityAuditor(final_url, soup, response_time=response_time)
        report = auditor.run_audit()

        print_console_summary(report)

        save_txt_report(report)
        save_csv_report(report)
        save_json_report(report)

        print("\nReports saved in the current project folder.")
        print("- accessibility_report.txt")
        print("- accessibility_issues.csv")
        print("- accessibility_report.json")

    except Exception as exc:
        print(f"\nAn error occurred: {exc}")


if __name__ == "__main__":
    main()