"""Tests for Excel structured prompt import."""

from __future__ import annotations

import io

from openpyxl import Workbook

from src.importers.excel_importer import parse_excel_bytes


def _workbook_bytes(rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_parse_excel_multiline_steps():
    data = _workbook_bytes(
        [
            [
                "Test ID",
                "Site URL",
                "Feature",
                "Test Name",
                "Objective",
                "Expected Outcome",
                "Steps",
            ],
            [
                "TC_EXCEL_01",
                "https://www.saucedemo.com/",
                "login",
                "Login test",
                "Verify login",
                "Products visible",
                "Open https://www.saucedemo.com/\nFill username with standard_user",
            ],
        ]
    )
    prompts = parse_excel_bytes(data)
    assert len(prompts) == 1
    assert prompts[0].test_id == "TC_EXCEL_01"
    assert len(prompts[0].steps) == 2


def test_parse_excel_step_columns():
    data = _workbook_bytes(
        [
            ["test_id", "site_url", "feature", "test_name", "objective", "expected_outcome", "Step 1", "Step 2"],
            [
                "TC02",
                "https://example.com",
                "auth",
                "Name",
                "Obj",
                "Exp",
                "Click Login",
                "Verify URL contains example.com",
            ],
        ]
    )
    prompts = parse_excel_bytes(data)
    assert prompts[0].steps == ["Click Login", "Verify URL contains example.com"]
