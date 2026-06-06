#!/usr/bin/env python3
"""Generate PT1000 wiring diagrams — block layout (CH3 RSENSE + CH8 RTD)."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(__file__).parent
W, H = 2400, 1500

COLORS = {
    "bg": "#FFFFFF",
    "box": "#F8F8F8",
    "border": "#333333",
    "title": "#1A1A1A",
    "muted": "#555555",
    "ch3": "#E67E22",
    "ch7": "#27AE60",
    "ch8": "#2980B9",
    "sense": "#C0392B",
    "gnd": "#2C3E50",
    "nc": "#8E44AD",
    "info": "#D6EAF8",
    "info_border": "#2874A6",
    "path": "#FDEBD0",
    "path_border": "#CA6F1E",
    "fw": "#E8F8F5",
    "fw_border": "#117A65",
}


def font(size, bold=False):
    names = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def box(draw, xy, text_lines, title=None, fill="#F8F8F8", title_size=28, body_size=22):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=12, fill=fill, outline=COLORS["border"], width=2)
    y = y0 + 16
    if title:
        draw.text((x0 + 16, y), title, fill=COLORS["title"], font=font(title_size, bold=True))
        y += title_size + 10
    for line in text_lines:
        draw.text((x0 + 16, y), line, fill=COLORS["muted"], font=font(body_size))
        y += body_size + 6


def line(draw, p0, p1, color, width=4, label=None, label_offset=(0, -18)):
    draw.line([p0, p1], fill=color, width=width)
    if label:
        mx = (p0[0] + p1[0]) // 2 + label_offset[0]
        my = (p0[1] + p1[1]) // 2 + label_offset[1]
        draw.text((mx, my), label, fill=color, font=font(18, bold=True))


def note_box(draw, xy, title, lines, fill, border):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=10, fill=fill, outline=border, width=2)
    draw.text((x0 + 14, y0 + 12), title, fill=COLORS["title"], font=font(22, bold=True))
    y = y0 + 42
    for line in lines:
        draw.text((x0 + 14, y), line, fill=COLORS["muted"], font=font(20))
        y += 26


def draw_dc2213a():
    img = Image.new("RGB", (W, H), COLORS["bg"])
    d = ImageDraw.Draw(img)
    d.text((W // 2 - 520, 30), "DC2213A PT1000 Wiring — Working Configuration", fill=COLORS["title"], font=font(34, bold=True))

    box(d, (60, 110, 360, 360), [
        "GPIO2  → CS",
        "GPIO9  → SCK",
        "GPIO5  → MOSI",
        "GPIO4  → MISO",
    ], title="CST Temp Module (ESP32-S3)", fill="#EAF2F8")

    box(d, (430, 90, 980, 430), [
        "LTC2983 multi-sensor IC",
        "SPI from ESP32-S3",
        "",
        "CH1  CH2  CH3  CH4",
        "CH5  CH6  CH7  CH8",
        "CH9  ...  EEGND",
    ], title="DC2209A Main Board", fill="#FEF9E7")

    box(d, (1040, 90, 1680, 500), [
        "CH1, CH2 → EEGND",
        "CH3 ↔ 2 kΩ RSENSE ↔ CH2",
        "",
        "J3 screw terminal:",
        "  Pin 4  RTDFH  → CH3",
        "  Pin 3  RTDSH  → CH7",
        "  Pin 2  RTDSL  → CH8",
        "  Pin 1  RTDFL  → CH9  (NC)",
    ], title="DC2213A Daughter Board", fill="#F4ECF7")

    box(d, (1760, 180, 2320, 420), [
        "PT1000 probe",
        "",
        "Leg 1 → J3 pin 4 (CH3)",
        "       + pin 3 (CH7) tied",
        "Leg 2 → J3 pin 2 (CH8)",
        "Pin 1 (CH9) left open",
    ], title="External PT1000", fill="#EBF5FB")

    line(d, (360, 220), (430, 220), COLORS["border"], 3, "SPI")
    line(d, (980, 250), (1040, 250), COLORS["gnd"], 3)
    line(d, (980, 290), (1040, 290), COLORS["ch3"], 4, "CH3")
    line(d, (980, 330), (1040, 330), COLORS["ch7"], 4, "CH7")
    line(d, (980, 370), (1040, 370), COLORS["ch8"], 4, "CH8")
    line(d, (1680, 290), (1760, 250), COLORS["ch3"], 4)
    line(d, (1680, 330), (1760, 280), COLORS["ch7"], 4)
    line(d, (1680, 370), (1760, 340), COLORS["ch8"], 4)
    d.line([(1860, 390), (1920, 430)], fill=COLORS["nc"], width=3)
    d.text((1930, 420), "CH9 NC", fill=COLORS["nc"], font=font(18))

    d.rounded_rectangle((1180, 540, 1540, 640), radius=8, outline=COLORS["sense"], width=2, fill="#FADBD8")
    d.text((1200, 560), "2 kΩ RSENSE (onboard)", fill=COLORS["sense"], font=font(22, bold=True))
    line(d, (1260, 640), (1260, 700), COLORS["ch3"], 4, "CH3")
    line(d, (1460, 640), (1460, 700), COLORS["sense"], 4, "CH2→GND")

    note_box(d, (60, 760, 1120, 920), "Current path", [
        "CH8 → PT1000 → CH7 + CH3 → 2 kΩ → CH2 → EEGND",
    ], COLORS["path"], COLORS["path_border"])

    note_box(d, (60, 960, 1120, 1180), "Firmware channel map (ltc2983_handler.h)", [
        "CH3 = RSENSE   2 kΩ excitation reference          CFG_RSENSE",
        "CH8 = PT1000   4-wire Kelvin, Rsense pointer → CH3   CFG_RTD",
        "Only CH3 and CH8 are configured; all other channels unused.",
    ], COLORS["fw"], COLORS["fw_border"])

    note_box(d, (60, 1220, 1120, 1420), "Wire colors (reference)", [
        "Orange = CH3 / RTDFH     Green = CH7 / RTDSH",
        "Blue   = CH8 / RTDSL     Purple X = CH9 / RTDFL (no connect)",
    ], COLORS["info"], COLORS["info_border"])

    note_box(d, (1180, 760, 2320, 980), "J3 sensor wiring", [
        "Tie RTDFH (pin 4) and RTDSH (pin 3) to PT1000 leg 1.",
        "Connect RTDSL (pin 2) to PT1000 leg 2.",
        "Leave RTDFL (pin 1) open — not used in this 3-terminal hookup.",
    ], COLORS["info"], COLORS["info_border"])

    img.save(OUT / "dc2213a-pt1000-wiring.png", "PNG")
    print("wrote dc2213a-pt1000-wiring.png")


def draw_dc2210a():
    img = Image.new("RGB", (W, H), COLORS["bg"])
    d = ImageDraw.Draw(img)
    d.text((W // 2 - 620, 30), "DC2210A PT1000 Wiring — Same Components, Breadboard Terminals", fill=COLORS["title"], font=font(34, bold=True))

    box(d, (60, 110, 360, 360), [
        "GPIO2  → CS",
        "GPIO9  → SCK",
        "GPIO5  → MOSI",
        "GPIO4  → MISO",
    ], title="CST Temp Module (ESP32-S3)", fill="#EAF2F8")

    box(d, (430, 90, 980, 430), [
        "LTC2983 multi-sensor IC",
        "SPI from ESP32-S3",
    ], title="DC2209A Main Board", fill="#FEF9E7")

    box(d, (1040, 70, 1760, 560), [
        "Screw terminals CH1–CH20",
        "",
        "CH1  → EEGND",
        "CH2  → RSENSE low side → EEGND",
        "CH3  → RSENSE high / RTDFH",
        "CH7  → RTDSH  (jumper to CH3)",
        "CH8  → RTDSL  → PT1000 leg 2",
        "CH9  → NC",
        "",
        "External 2 kΩ between CH2 and CH3",
    ], title="DC2210A Experimenter Board", fill="#F4ECF7")

    box(d, (1820, 180, 2320, 400), [
        "PT1000 probe",
        "Leg 1 → CH3/CH7 tie point",
        "Leg 2 → CH8",
    ], title="External PT1000", fill="#EBF5FB")

    line(d, (360, 220), (430, 220), COLORS["border"], 3, "SPI")
    line(d, (980, 250), (1040, 250), COLORS["gnd"], 3)
    line(d, (980, 300), (1040, 300), COLORS["ch3"], 4, "CH3")
    line(d, (980, 350), (1040, 350), COLORS["ch7"], 4, "CH7")
    line(d, (980, 400), (1040, 400), COLORS["ch8"], 4, "CH8")

    d.rounded_rectangle((1280, 600, 1560, 660), radius=8, outline=COLORS["ch7"], width=2, fill="#D5F5E3")
    d.text((1300, 615), "Jumper: CH3 ↔ CH7", fill=COLORS["ch7"], font=font(22, bold=True))

    d.rounded_rectangle((1080, 700, 1460, 800), radius=8, outline=COLORS["sense"], width=2, fill="#FADBD8")
    d.text((1100, 730), "2 kΩ external RSENSE", fill=COLORS["sense"], font=font(22, bold=True))
    line(d, (1180, 800), (1180, 860), COLORS["ch3"], 4, "CH3")
    line(d, (1360, 800), (1360, 860), COLORS["sense"], 4, "CH2")

    line(d, (1760, 300), (1820, 260), COLORS["ch3"], 4)
    line(d, (1760, 350), (1820, 300), COLORS["ch7"], 4)
    line(d, (1760, 400), (1820, 340), COLORS["ch8"], 4)

    note_box(d, (60, 900, 1160, 1040), "Current path", [
        "CH8 → PT1000 → CH7 + CH3 → 2 kΩ → CH2 → CH1/EEGND",
    ], COLORS["path"], COLORS["path_border"])

    note_box(d, (60, 1080, 1160, 1300), "Firmware channel map (ltc2983_handler.h)", [
        "CH3 = RSENSE   2 kΩ excitation reference          CFG_RSENSE",
        "CH8 = PT1000   4-wire Kelvin, Rsense pointer → CH3   CFG_RTD",
        "Replicates DC2213A J3 topology on breadboard screws.",
    ], COLORS["fw"], COLORS["fw_border"])

    note_box(d, (1180, 900, 2320, 1120), "Terminal hookup", [
        "Bridge CH3 and CH7 for Kelvin sense at PT1000 leg 1.",
        "PT1000 leg 2 to CH8.  CH9 unused.  CH1/CH2 establish RSENSE return.",
    ], COLORS["info"], COLORS["info_border"])

    note_box(d, (60, 1340, 2320, 1460), "Wire colors", [
        "Orange = CH3/RTDFH   Green = CH7/RTDSH   Blue = CH8/RTDSL   Black = EEGND   Purple = CH9 NC",
    ], COLORS["info"], COLORS["info_border"])

    img.save(OUT / "dc2210a-pt1000-wiring.png", "PNG")
    print("wrote dc2210a-pt1000-wiring.png")


if __name__ == "__main__":
    draw_dc2213a()
    draw_dc2210a()
