from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class AccessibilityIssue:
    rule_id: str
    category: str
    severity: str
    message: str
    element: str
    recommendation: str
    wcag_reference: str = ""
    evidence: str = ""


@dataclass
class AccessibilityReport:
    url: str
    response_time: float
    page_title: str
    score: int
    rating: str
    stats: Dict[str, int]
    issues: List[AccessibilityIssue] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)