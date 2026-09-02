"""Shared login-field selector hints for discovery, parser, and healer."""

from __future__ import annotations

LOGIN_FIELD_SELECTORS: dict[str, list[str]] = {
    "email": ["#login_id", "input[type='email']", "input[name='email']", "input[name='login_id']"],
    "e-mail": ["#login_id", "input[type='email']", "input[name='email']"],
    "username": ["#user-name", "#login_id", "input[name='username']", "input[type='email']"],
    "user name": ["#user-name", "#login_id"],
    "password": ["#password", "input[type='password']", "input[name='password']"],
    "sign in": ["#nextbtn", "#signin", "button[type='submit']", "input[type='submit']"],
    "login": ["#login-button", "#nextbtn", "button[type='submit']"],
}


def normalize_field_label(label: str) -> str:
    return label.strip().lower()


def login_field_selector_candidates(label: str) -> list[str]:
    """Return CSS selectors to try for a login/form field label."""
    key = normalize_field_label(label)
    if key in LOGIN_FIELD_SELECTORS:
        return list(LOGIN_FIELD_SELECTORS[key])
    if "password" in key:
        return list(LOGIN_FIELD_SELECTORS["password"])
    if "email" in key or "e-mail" in key:
        return list(LOGIN_FIELD_SELECTORS["email"])
    if "user" in key:
        return list(LOGIN_FIELD_SELECTORS["username"])
    return []


def best_guess_selector(label: str) -> str:
    """Default selector guess — prefer stable login selectors over text=."""
    candidates = login_field_selector_candidates(label)
    if candidates:
        return candidates[0]
    raw = label.strip().lower()
    mapping = {
        "login button": "#login-button",
        "checkout": "#checkout",
        "continue": "#continue",
        "shopping cart": ".shopping_cart_link",
        "shopping cart link": ".shopping_cart_link",
        "first name": "#first-name",
        "last name": "#last-name",
        "zip/postal code": "#postal-code",
        "zip": "#postal-code",
        "menu button": "#react-burger-menu-btn",
        "logout": "#logout_sidebar_link",
        "remove": "button.cart_button",
        "product sort dropdown": "[data-test='product-sort-container']",
    }
    if raw in mapping:
        return mapping[raw]
    if "add to cart" in raw:
        return "button.btn_inventory"
    return f"text={label.strip()}"
