"""Tune line spacing to exactly 10 pages."""
import importlib.util
import time
from pathlib import Path

import win32com.client

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("b", ROOT / "build_multimodal_ca2_report.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

tmp = ROOT / "_tmp_cal.docx"
TARGET = 10


def pages_for(ls, sp):
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = b.build_document(detail_level=2, space_after=sp, line_spacing=ls)
        doc.save(tmp)
        time.sleep(0.5)
        wd = word.Documents.Open(str(tmp.resolve()))
        n = int(wd.ComputeStatistics(2))
        wd.Close(False)
        return n
    finally:
        word.Quit()


for ls_x in range(175, 215, 2):
    ls = ls_x / 100.0
    n = pages_for(ls, 8)
    print(f"ls={ls:.2f} sp=8 -> {n}")
    if n == TARGET:
        print("FOUND")
        break
