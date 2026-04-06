from urllib.parse import urlparse


GENERIC_LINK_TEXTS = {
    "click here",
    "read more",
    "more",
    "here",
    "learn more",
    "link",
    "this",
    "go",
    "see more",
}


SUSPICIOUS_ALT_TEXTS = {
    "image",
    "photo",
    "picture",
    "img",
    "graphic",
}


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split()).strip()


def get_tag_path(tag) -> str:
    try:
        parts = []
        current = tag
        depth = 0

        while current is not None and getattr(current, "name", None) and depth < 5:
            identifier = current.name
            if current.get("id"):
                identifier += f"#{current.get('id')}"
            elif current.get("class"):
                first_class = current.get("class")[0]
                identifier += f".{first_class}"
            parts.append(identifier)
            current = current.parent
            depth += 1

        return " > ".join(reversed(parts))
    except Exception:
        return "<unknown>"


def safe_text(tag) -> str:
    if tag is None:
        return ""
    return normalize_whitespace(tag.get_text(" ", strip=True))


def clamp_score(score: int) -> int:
    return max(0, min(score, 100))


def rating_from_score(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 55:
        return "Needs Improvement"
    return "Poor"


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        return f"https://{url}"
    return url