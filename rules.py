from collections import Counter
from bs4 import BeautifulSoup

from checker.models import AccessibilityIssue, AccessibilityReport
from checker.utils import (
    GENERIC_LINK_TEXTS,
    SUSPICIOUS_ALT_TEXTS,
    clamp_score,
    get_tag_path,
    normalize_whitespace,
    rating_from_score,
    safe_text,
)


class AccessibilityAuditor:
    def __init__(self, url: str, soup: BeautifulSoup, response_time: float = 0.0) -> None:
        self.url = url
        self.soup = soup
        self.response_time = response_time
        self.issues: list[AccessibilityIssue] = []
        self.passed_checks: list[str] = []
        self.warnings: list[str] = []
        self.penalty_points = 0

    def run_audit(self) -> AccessibilityReport:
        self.check_page_title()
        self.check_html_lang()
        self.check_missing_h1()
        self.check_heading_structure()
        self.check_images_without_alt()
        self.check_suspicious_alt_text()
        self.check_empty_links()
        self.check_generic_link_text()
        self.check_buttons_without_text()
        self.check_form_inputs_without_labels()
        self.check_duplicate_ids()
        self.check_landmark_regions()
        self.check_tables_without_headers()
        self.check_iframes_without_title()

        stats = self._build_stats()
        score = clamp_score(100 - self.penalty_points)
        rating = rating_from_score(score)
        page_title = self._extract_page_title()

        return AccessibilityReport(
            url=self.url,
            response_time=self.response_time,
            page_title=page_title,
            score=score,
            rating=rating,
            stats=stats,
            issues=self.issues,
            passed_checks=self.passed_checks,
            warnings=self.warnings,
        )

    def add_issue(
        self,
        rule_id: str,
        category: str,
        severity: str,
        message: str,
        element: str,
        recommendation: str,
        wcag_reference: str = "",
        evidence: str = "",
    ) -> None:
        self.issues.append(
            AccessibilityIssue(
                rule_id=rule_id,
                category=category,
                severity=severity,
                message=message,
                element=element,
                recommendation=recommendation,
                wcag_reference=wcag_reference,
                evidence=evidence,
            )
        )

        severity_penalties = {
            "critical": 12,
            "high": 8,
            "medium": 5,
            "low": 2,
        }
        self.penalty_points += severity_penalties.get(severity.lower(), 3)

    def add_pass(self, check_name: str) -> None:
        self.passed_checks.append(check_name)

    def _extract_page_title(self) -> str:
        title_tag = self.soup.find("title")
        return safe_text(title_tag) if title_tag else "Untitled page"

    def _build_stats(self) -> dict:
        return {
            "images": len(self.soup.find_all("img")),
            "links": len(self.soup.find_all("a")),
            "buttons": len(self.soup.find_all("button")),
            "forms": len(self.soup.find_all("form")),
            "inputs": len(self.soup.find_all(["input", "select", "textarea"])),
            "tables": len(self.soup.find_all("table")),
            "iframes": len(self.soup.find_all("iframe")),
            "issues_found": len(self.issues),
            "passed_checks": len(self.passed_checks),
        }

    def check_page_title(self) -> None:
        title_tag = self.soup.find("title")
        title_text = safe_text(title_tag)

        if not title_tag or not title_text:
            self.add_issue(
                rule_id="DOC001",
                category="document",
                severity="high",
                message="The page is missing a meaningful <title>.",
                element="<title>",
                recommendation="Add a descriptive page title inside the <head>.",
                wcag_reference="WCAG 2.4.2 Page Titled",
            )
        else:
            self.add_pass("Page has a title.")

    def check_html_lang(self) -> None:
        html_tag = self.soup.find("html")

        if not html_tag or not html_tag.get("lang"):
            self.add_issue(
                rule_id="DOC002",
                category="document",
                severity="high",
                message="The root <html> element does not define a language.",
                element="<html>",
                recommendation="Add a lang attribute such as lang='en' or lang='es'.",
                wcag_reference="WCAG 3.1.1 Language of Page",
            )
        else:
            self.add_pass("Document language is defined.")

    def check_missing_h1(self) -> None:
        h1_tags = self.soup.find_all("h1")
        if not h1_tags:
            self.add_issue(
                rule_id="HEAD001",
                category="headings",
                severity="medium",
                message="The page does not contain an <h1> heading.",
                element="<h1>",
                recommendation="Include one clear primary heading that describes the page content.",
                wcag_reference="WCAG 1.3.1 Info and Relationships",
            )
        else:
            self.add_pass("Page contains at least one H1 heading.")

    def check_heading_structure(self) -> None:
        headings = self.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if not headings:
            self.warnings.append("No heading structure found in the page.")
            return

        levels = [int(tag.name[1]) for tag in headings]

        jumps_found = False
        for i in range(1, len(levels)):
            if levels[i] - levels[i - 1] > 1:
                jumps_found = True
                self.add_issue(
                    rule_id="HEAD002",
                    category="headings",
                    severity="medium",
                    message=f"Heading level jumps from h{levels[i - 1]} to h{levels[i]}.",
                    element=get_tag_path(headings[i]),
                    recommendation="Use heading levels sequentially to preserve semantic structure.",
                    wcag_reference="WCAG 1.3.1 Info and Relationships",
                    evidence=safe_text(headings[i]),
                )

        if not jumps_found:
            self.add_pass("Heading structure does not show major level jumps.")

    def check_images_without_alt(self) -> None:
        images = self.soup.find_all("img")
        missing_alt = []

        for img in images:
            alt = img.get("alt")
            if alt is None or not alt.strip():
                missing_alt.append(img)

        if missing_alt:
            for img in missing_alt[:10]:
                self.add_issue(
                    rule_id="IMG001",
                    category="images",
                    severity="high",
                    message="Image missing alternative text.",
                    element=get_tag_path(img),
                    recommendation="Add a meaningful alt attribute, or alt='' for decorative images.",
                    wcag_reference="WCAG 1.1.1 Non-text Content",
                    evidence=img.get("src", ""),
                )
            if len(missing_alt) > 10:
                self.warnings.append(
                    f"There are {len(missing_alt)} images without alt text. Only the first 10 are listed."
                )
        else:
            self.add_pass("All images contain alt attributes.")

    def check_suspicious_alt_text(self) -> None:
        images = self.soup.find_all("img")
        suspicious_count = 0

        for img in images:
            alt = normalize_whitespace(img.get("alt", "").lower())
            if alt and alt in SUSPICIOUS_ALT_TEXTS:
                suspicious_count += 1
                self.add_issue(
                    rule_id="IMG002",
                    category="images",
                    severity="low",
                    message="Image alt text is too generic.",
                    element=get_tag_path(img),
                    recommendation="Use alt text that communicates the image purpose or content.",
                    wcag_reference="WCAG 1.1.1 Non-text Content",
                    evidence=alt,
                )

        if suspicious_count == 0 and images:
            self.add_pass("No suspiciously generic alt text detected.")

    def check_empty_links(self) -> None:
        links = self.soup.find_all("a")
        empty_links = []

        for link in links:
            text = safe_text(link)
            aria_label = normalize_whitespace(link.get("aria-label", ""))
            title = normalize_whitespace(link.get("title", ""))
            has_img_with_alt = any(
                normalize_whitespace(img.get("alt", ""))
                for img in link.find_all("img")
            )

            if not text and not aria_label and not title and not has_img_with_alt:
                empty_links.append(link)

        if empty_links:
            for link in empty_links[:10]:
                self.add_issue(
                    rule_id="LINK001",
                    category="links",
                    severity="high",
                    message="Link does not have an accessible name.",
                    element=get_tag_path(link),
                    recommendation="Provide descriptive visible text, aria-label, title, or meaningful image alt text.",
                    wcag_reference="WCAG 2.4.4 Link Purpose",
                    evidence=link.get("href", ""),
                )
        else:
            self.add_pass("No empty links detected.")

    def check_generic_link_text(self) -> None:
        generic_links = []
        for link in self.soup.find_all("a"):
            text = safe_text(link).lower()
            if text in GENERIC_LINK_TEXTS:
                generic_links.append(link)

        if generic_links:
            for link in generic_links[:10]:
                self.add_issue(
                    rule_id="LINK002",
                    category="links",
                    severity="low",
                    message="Link text may be too generic.",
                    element=get_tag_path(link),
                    recommendation="Use descriptive link text that makes sense out of context.",
                    wcag_reference="WCAG 2.4.4 Link Purpose",
                    evidence=safe_text(link),
                )
        elif self.soup.find_all("a"):
            self.add_pass("No obviously generic link texts detected.")

    def check_buttons_without_text(self) -> None:
        buttons = self.soup.find_all("button")
        bad_buttons = []

        for button in buttons:
            text = safe_text(button)
            aria_label = normalize_whitespace(button.get("aria-label", ""))
            title = normalize_whitespace(button.get("title", ""))

            if not text and not aria_label and not title:
                bad_buttons.append(button)

        if bad_buttons:
            for button in bad_buttons[:10]:
                self.add_issue(
                    rule_id="BTN001",
                    category="buttons",
                    severity="high",
                    message="Button does not have an accessible name.",
                    element=get_tag_path(button),
                    recommendation="Add visible text or an aria-label describing the button action.",
                    wcag_reference="WCAG 4.1.2 Name, Role, Value",
                )
        else:
            self.add_pass("All buttons appear to have accessible names.")

    def check_form_inputs_without_labels(self) -> None:
        controls = self.soup.find_all(["input", "select", "textarea"])
        unlabeled_controls = []

        for control in controls:
            input_type = control.get("type", "").lower()
            if input_type in {"hidden", "submit", "reset", "button", "image"}:
                continue

            if self._control_has_accessible_name(control):
                continue

            unlabeled_controls.append(control)

        if unlabeled_controls:
            for control in unlabeled_controls[:10]:
                self.add_issue(
                    rule_id="FORM001",
                    category="forms",
                    severity="critical",
                    message="Form control appears to be missing an accessible label.",
                    element=get_tag_path(control),
                    recommendation="Associate a <label>, aria-label, aria-labelledby, or a clear title with the control.",
                    wcag_reference="WCAG 1.3.1 Info and Relationships / 4.1.2 Name, Role, Value",
                    evidence=str(control.attrs),
                )
        else:
            if controls:
                self.add_pass("All detected form controls appear to have accessible names.")

    def _control_has_accessible_name(self, control) -> bool:
        if normalize_whitespace(control.get("aria-label", "")):
            return True
        if normalize_whitespace(control.get("title", "")):
            return True
        if normalize_whitespace(control.get("placeholder", "")) and control.name == "textarea":
            return True
        if control.get("aria-labelledby"):
            return True

        control_id = control.get("id")
        if control_id:
            label = self.soup.find("label", attrs={"for": control_id})
            if label and safe_text(label):
                return True

        parent_label = control.find_parent("label")
        if parent_label and safe_text(parent_label):
            return True

        return False

    def check_duplicate_ids(self) -> None:
        tags_with_id = self.soup.find_all(attrs={"id": True})
        ids = [tag.get("id") for tag in tags_with_id if tag.get("id")]
        duplicates = [id_value for id_value, count in Counter(ids).items() if count > 1]

        if duplicates:
            for duplicate_id in duplicates[:10]:
                self.add_issue(
                    rule_id="DOC003",
                    category="document",
                    severity="medium",
                    message="Duplicate id value found in the document.",
                    element=f"id='{duplicate_id}'",
                    recommendation="Ensure all id attributes are unique.",
                    wcag_reference="WCAG 4.1.1 Parsing",
                    evidence=duplicate_id,
                )
        else:
            if ids:
                self.add_pass("No duplicate IDs detected.")

    def check_landmark_regions(self) -> None:
        landmark_tags = {"main", "nav", "header", "footer", "aside"}
        found_landmarks = set(tag.name for tag in self.soup.find_all(landmark_tags))

        if "main" not in found_landmarks:
            self.add_issue(
                rule_id="LAND001",
                category="landmarks",
                severity="medium",
                message="Main landmark not found.",
                element="<main>",
                recommendation="Add a <main> region to identify the primary page content.",
                wcag_reference="WCAG 1.3.1 Info and Relationships",
            )
        else:
            self.add_pass("Main landmark is present.")

    def check_tables_without_headers(self) -> None:
        tables = self.soup.find_all("table")
        problematic_tables = []

        for table in tables:
            has_th = bool(table.find("th"))
            if not has_th:
                problematic_tables.append(table)

        if problematic_tables:
            for table in problematic_tables[:10]:
                self.add_issue(
                    rule_id="TABLE001",
                    category="tables",
                    severity="medium",
                    message="Table may be missing header cells.",
                    element=get_tag_path(table),
                    recommendation="Use <th> elements to identify row or column headers where appropriate.",
                    wcag_reference="WCAG 1.3.1 Info and Relationships",
                )
        else:
            if tables:
                self.add_pass("All detected tables include header cells.")

    def check_iframes_without_title(self) -> None:
        iframes = self.soup.find_all("iframe")
        bad_iframes = []

        for iframe in iframes:
            title = normalize_whitespace(iframe.get("title", ""))
            if not title:
                bad_iframes.append(iframe)

        if bad_iframes:
            for iframe in bad_iframes[:10]:
                self.add_issue(
                    rule_id="FRAME001",
                    category="iframes",
                    severity="high",
                    message="Iframe is missing a title attribute.",
                    element=get_tag_path(iframe),
                    recommendation="Add a descriptive title that explains the iframe content or purpose.",
                    wcag_reference="WCAG 4.1.2 Name, Role, Value",
                    evidence=iframe.get("src", ""),
                )
        else:
            if iframes:
                self.add_pass("All iframes include a title attribute.")