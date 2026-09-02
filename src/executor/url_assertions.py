"""URL assertion helpers — handle common subdomain ↔ path redirects."""

from __future__ import annotations

import re


def url_matches(page_url: str, expected: str) -> bool:
    """
    Return True when the page URL satisfies an assert_url expected fragment.

    Direct substring match plus common marketing-site redirects, e.g.
    projects.zoho.com -> https://www.zoho.com/projects/
    """
    page_l = page_url.lower()
    expected_l = expected.strip().lower()
    if not expected_l:
        return False
    if expected_l in page_l:
        return True

    # subdomain.example.com -> example.com/subdomain or www.example.com/subdomain
    host_match = re.match(r"^([a-z0-9-]+)\.([a-z0-9.-]+\.[a-z]{2,})$", expected_l)
    if host_match:
        sub, host = host_match.group(1), host_match.group(2)
        for prefix in ("", "www."):
            if f"{prefix}{host}/{sub}" in page_l:
                return True

    return False
