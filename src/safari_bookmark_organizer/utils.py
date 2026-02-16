from __future__ import annotations


def extract_domain(url: str) -> str:
    """Extract domain from URL, stripping protocol, path, and www prefix."""
    if not url:
        return ""

    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    if domain.startswith("www."):
        domain = domain[4:]

    return domain
