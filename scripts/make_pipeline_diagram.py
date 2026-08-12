"""Generate DS1 pipeline diagram PNG for CA1 PPT insertion."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"C:\Users\shwet\Projects\agentic-webapp-test-executor\docs\ca1_assets\ds1_pipeline_diagram.png")
OUT_DL = Path(r"C:\Users\shwet\Downloads\ds1_pipeline_diagram.png")

# Palette (clean academic / matches PPT navy/red accents)
BG = (255, 255, 255)
TITLE = (26, 26, 26)
SUB = (90, 90, 90)
BOXES = [
    ((196, 30, 58), "Plain-Text\nTest Steps"),          # red
    ((31, 78, 121), "Step Parser\n(Rules / LLM)"),      # blue
    ((30, 122, 70), "Playwright\nExecutor"),            # green
    ((198, 90, 18), "Assertion\nEngine"),               # orange
    ((91, 44, 111), "Pass/Fail\nReport Store"),         # purple
    ((47, 64, 80), "Notify Agent\n(Team Alert)"),       # slate
]
ARROW = (120, 120, 120)
FOOTER = (100, 100, 100)


def font(size: int, bold: bool = False):
    paths = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def rounded_box(draw, xy, radius, fill):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def center_multiline(draw, text, box, fnt, fill=(255, 255, 255), line_gap=6):
    x1, y1, x2, y2 = box
    lines = text.split("\n")
    heights = []
    widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=fnt)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    total_h = sum(heights) + line_gap * (len(lines) - 1)
    ty = y1 + (y2 - y1 - total_h) / 2
    for i, line in enumerate(lines):
        tw = widths[i]
        draw.text((x1 + (x2 - x1 - tw) / 2, ty), line, font=fnt, fill=fill)
        ty += heights[i] + line_gap


def draw_arrow(draw, x0, y, x1):
    # shaft
    draw.line([(x0, y), (x1 - 18, y)], fill=ARROW, width=6)
    # head
    draw.polygon([(x1, y), (x1 - 22, y - 12), (x1 - 22, y + 12)], fill=ARROW)


def main():
    W, H = 2400, 900
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    f_title = font(44, bold=True)
    f_box = font(28, bold=True)
    f_sub = font(24, bold=False)
    f_small = font(22, bold=False)

    # Title
    title = "Agentic Web-App Test Executor — Pipeline"
    tb = draw.textbbox((0, 0), title, font=f_title)
    draw.text(((W - (tb[2] - tb[0])) / 2, 40), title, font=f_title, fill=TITLE)

    subtitle = "Text steps → execute → verify → document → notify owning team"
    sb = draw.textbbox((0, 0), subtitle, font=f_sub)
    draw.text(((W - (sb[2] - sb[0])) / 2, 110), subtitle, font=f_sub, fill=SUB)

    # Pipeline boxes
    n = len(BOXES)
    margin_x = 60
    gap = 36
    box_w = (W - 2 * margin_x - gap * (n - 1)) / n
    box_h = 210
    top = 280

    centers = []
    for i, (color, label) in enumerate(BOXES):
        x1 = margin_x + i * (box_w + gap)
        x2 = x1 + box_w
        y1 = top
        y2 = top + box_h
        rounded_box(draw, [x1, y1, x2, y2], radius=28, fill=color)
        # subtle bottom shadow edge
        draw.rounded_rectangle([x1, y1, x2, y2], radius=28, outline=(0, 0, 0, 40), width=2)
        center_multiline(draw, label, (x1 + 10, y1 + 10, x2 - 10, y2 - 10), f_box)
        centers.append(((x1 + x2) / 2, (y1 + y2) / 2, x1, x2, y1, y2))

    # Arrows between boxes
    for i in range(n - 1):
        x0 = centers[i][3] + 4
        x1 = centers[i + 1][2] - 4
        y = top + box_h / 2
        draw_arrow(draw, x0, y, x1)

    # Step numbers above boxes
    f_num = font(22, bold=True)
    for i, c in enumerate(centers):
        num = str(i + 1)
        nb = draw.textbbox((0, 0), num, font=f_num)
        nw = nb[2] - nb[0]
        nh = nb[3] - nb[1]
        cx = c[0]
        cy = top - 50
        r = 22
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(47, 64, 80))
        draw.text((cx - nw / 2, cy - nh / 2 - 1), num, font=f_num, fill=(255, 255, 255))

    # Bottom annotations
    notes = [
        "Input: numbered plain-text cases",
        "Schema-validated JSON actions",
        "Browser automation (Chromium)",
        "Expected vs actual checks",
        "JSON + Markdown evidence",
        "Module → team ticket/alert",
    ]
    note_top = top + box_h + 55
    for i, note in enumerate(notes):
        x1 = centers[i][2]
        x2 = centers[i][3]
        # wrap-ish by centering short text
        nb = draw.textbbox((0, 0), note, font=f_small)
        nw = nb[2] - nb[0]
        draw.text((x1 + (x2 - x1 - nw) / 2, note_top), note, font=f_small, fill=FOOTER)

    # Footer brand line
    foot = "DS 1 | Dassault Systemes (ENOVIA) | Quality Engineering"
    fb = draw.textbbox((0, 0), foot, font=f_small)
    draw.text(((W - (fb[2] - fb[0])) / 2, H - 60), foot, font=f_small, fill=SUB)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    img.save(OUT_DL, "PNG")
    print("Saved:", OUT)
    print("Saved:", OUT_DL)


if __name__ == "__main__":
    main()
