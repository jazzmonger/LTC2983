#!/usr/bin/env python3
"""
Wiring diagram generator — style faithful to dc2210a-5rtd-5tc-wiring.png reference.
Run:  python3 schematics/generate_wiring_diagrams.py
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

OUT = Path(__file__).parent

# ── Palette ────────────────────────────────────────────────────────────────
C = {
    "bg":       "#FFFFFF",
    "title":    "#111111",
    "txt":      "#222222",
    "muted":    "#555555",
    # board boxes
    "esp_f":    "#F1FAF1", "esp_b": "#2E7D32",
    "ltc_f":    "#EBF5FB", "ltc_b": "#154360",
    # RTD section
    "rtd_f":    "#EBF5FB", "rtd_b": "#1565C0", "rtd_lbl": "#1565C0",
    "rtd_w":    "#1E88E5",  # RTD wire blue
    # TC section
    "tc_f":     "#FDEDEC", "tc_b": "#922B21", "tc_lbl": "#922B21",
    "tc_pos":   "#C0392B",  # red
    "tc_neg":   "#D4AC0D",  # yellow
    # channels
    "ch3":      "#E67E22", "ch7": "#27AE60",
    "ch8":      "#2980B9", "ch9": "#8E44AD",
    "ch1":      "#5D6D7E", "ch2":      "#566573",
    "ch10":     "#16A085", "ch11":     "#2980B9",
    # misc
    "gnd":      "#1A1A1A",
    "term_f":   "#ECEFF1", "term_b": "#546E7A",
    # table
    "th_bg":    "#00ACC1", "th_txt": "#FFFFFF",
    "td_a":     "#EAF7FB", "tbl_b": "#90A4AE",
    "hdr_bg":   "#263238", "hdr_txt": "#FFFFFF",
}


def F(n, bold=False):
    for p in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        try:
            return ImageFont.truetype(p, n)
        except OSError:
            pass
    return ImageFont.load_default()


# ── Schematic primitives ────────────────────────────────────────────────────

def gnd_sym(d, x, y, label="EEGND", color=None):
    color = color or C["gnd"]
    d.line([(x, y), (x, y + 14)], fill=color, width=3)
    d.line([(x - 22, y + 14), (x + 22, y + 14)], fill=color, width=4)
    d.line([(x - 15, y + 22), (x + 15, y + 22)], fill=color, width=3)
    d.line([(x - 8,  y + 29), (x + 8,  y + 29)], fill=color, width=2)
    if label:
        tw = d.textlength(label, font=F(15))
        d.text((x - tw / 2, y + 37), label, fill=color, font=F(15))


def dot(d, x, y, r=6, color=None):
    color = color or C["rtd_w"]
    d.ellipse([x - r, y - r, x + r, y + r], fill=color)


def no_connect(d, x, y, size=13, color=None):
    color = color or C["ch9"]
    d.line([(x - size, y - size), (x + size, y + size)], fill=color, width=3)
    d.line([(x + size, y - size), (x - size, y + size)], fill=color, width=3)


def pot_sym_h(d, x0, y, x1, label="10 kΩ", sublabel="R6", color=None, wiper_right=True):
    """Horizontal potentiometer — DC2213A R6: pins 1+3 left, wiper pin 2 right."""
    color = color or C["rtd_w"]
    mid = (x0 + x1) // 2
    h = 28
    body_l, body_r = x0 + 36, x1 - 36
    d.line([(x0, y), (body_l, y)], fill=color, width=3)
    d.rectangle([body_l, y - h, body_r, y + h], outline=color, width=2, fill="#FFFFFF")
    d.line([(body_r, y), (x1, y)], fill=color, width=3)
    # wiper arrow at pin 2 (right end on R6)
    wx = x1 if wiper_right else x0
    d.line([(wx, y - h - 6), (wx, y - h - 28)], fill=color, width=2)
    d.polygon([(wx, y - h - 34), (wx - 8, y - h - 22), (wx + 8, y - h - 22)],
              fill=color)
    d.text((body_l - 4, y + h + 8), "pins 1+3", fill=C["muted"], font=F(12))
    d.text((body_r - 28, y + h + 8), "pin 2", fill=C["muted"], font=F(12))
    d.text((mid - 36, y + h + 28), label, fill=color, font=F(15, bold=True))
    d.text((mid - 12, y + h + 48), sublabel, fill=C["muted"], font=F(13))


def cap_sym_v(d, x, y0, y1, label="0.01 µF", sublabel="C6", color=None):
    """Vertical capacitor symbol."""
    color = color or C["rtd_w"]
    gap = 10
    d.line([(x, y0), (x, y0 + 30)], fill=color, width=3)
    d.line([(x - 18, y0 + 30), (x + 18, y0 + 30)], fill=color, width=3)
    d.line([(x - 18, y0 + 30 + gap), (x + 18, y0 + 30 + gap)], fill=color, width=3)
    d.line([(x, y0 + 30 + gap), (x, y1)], fill=color, width=3)
    d.text((x + 22, y0 + 18), label, fill=color, font=F(14, bold=True))
    d.text((x + 22, y0 + 36), sublabel, fill=C["muted"], font=F(13))


def resistor_rect_v(d, x, y0, y1, color=None):
    """Vertical rectangle resistor (RSENSE)."""
    color = color or C["rtd_w"]
    pad = (y1 - y0) // 4
    by0, by1 = y0 + pad, y1 - pad
    bw = 24
    d.line([(x, y0), (x, by0)], fill=color, width=3)
    d.rectangle([x - bw, by0, x + bw, by1], outline=color, width=2, fill="#FFFFFF")
    d.line([(x, by1), (x, y1)], fill=color, width=3)
    mid = (by0 + by1) // 2
    d.text((x + bw + 10, mid - 22), "2.00 kΩ", fill=color, font=F(16, bold=True))
    d.text((x + bw + 10, mid + 4),  "RSENSE",  fill=C["muted"],  font=F(14))


def rtd_sym_v(d, x, y0, y1, label="", sublabel="", color=None):
    """Vertical zigzag RTD with diagonal arrow — matches reference style."""
    color = color or C["rtd_w"]
    pad = (y1 - y0) // 5
    by0, by1 = y0 + pad, y1 - pad
    bw = 16
    d.line([(x, y0), (x, by0)], fill=color, width=3)
    n = 6
    pts = [(x, by0)]
    for i in range(n):
        xi = x + bw if i % 2 == 0 else x - bw
        yi = by0 + (by1 - by0) * (i + 0.5) / n
        pts.append((xi, int(yi)))
    pts.append((x, by1))
    d.line(pts, fill=color, width=3)
    d.line([(x, by1), (x, y1)], fill=color, width=3)
    # diagonal arrow
    ax0, ay0 = x - bw - 8, by1 - 6
    ax1, ay1 = x + bw + 8, by0 + 6
    d.line([(ax0, ay0), (ax1, ay1)], fill=color, width=2)
    ang = math.atan2(ay1 - ay0, ax1 - ax0)
    for da in (-0.45, 0.45):
        d.line([(ax1, ay1),
                (int(ax1 - 10 * math.cos(ang + da)),
                 int(ay1 - 10 * math.sin(ang + da)))], fill=color, width=2)
    if label:
        lw = d.textlength(label, font=F(15, bold=True))
        d.text((x - lw / 2, y0 - 22), label, fill=color, font=F(15, bold=True))
    if sublabel:
        lw2 = d.textlength(sublabel, font=F(13))
        d.text((x - lw2 / 2, y1 + 4), sublabel, fill=C["muted"], font=F(13))


def rtd_sym_h(d, x0, y, x1, label="PT1000", color=None):
    """Horizontal zigzag RTD with diagonal arrow."""
    color = color or C["rtd_w"]
    pad = (x1 - x0) // 6
    bx0, bx1 = x0 + pad, x1 - pad
    bh = 13
    d.line([(x0, y), (bx0, y)], fill=color, width=3)
    n = 8
    pts = [(bx0, y)]
    for i in range(n):
        xi = bx0 + (bx1 - bx0) * (i + 0.5) / n
        yi = y - bh if i % 2 == 0 else y + bh
        pts.append((int(xi), yi))
    pts.append((bx1, y))
    d.line(pts, fill=color, width=3)
    d.line([(bx1, y), (x1, y)], fill=color, width=3)
    ax0, ay0 = bx0 + 14, y + 20
    ax1, ay1 = bx1 - 14, y - 20
    d.line([(ax0, ay0), (ax1, ay1)], fill=color, width=2)
    ang = math.atan2(ay1 - ay0, ax1 - ax0)
    for da in (-0.45, 0.45):
        d.line([(ax1, ay1),
                (int(ax1 - 10 * math.cos(ang + da)),
                 int(ay1 - 10 * math.sin(ang + da)))], fill=color, width=2)
    if label:
        tw = d.textlength(label, font=F(17, bold=True))
        d.text(((x0 + x1) / 2 - tw / 2, y - 40), label, fill=color, font=F(17, bold=True))


def tc_sym(d, cx, cy, r=22, pc=None, nc_=None):
    """Thermocouple circle symbol."""
    pc = pc or C["tc_pos"]
    nc_ = nc_ or C["tc_neg"]
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#444444", width=2, fill="#FFFFFF")
    d.text((cx - 7, cy - 16), "+", fill=pc,  font=F(18, bold=True))
    d.text((cx - 6, cy + 1),  "−", fill=nc_, font=F(18, bold=True))


def screw_terminal(d, x0, y0, w, h, label="", screw_side="right", color=None):
    """Single screw terminal rectangle with circle-slot symbol."""
    color = color or C["term_b"]
    x1, y1 = x0 + w, y0 + h
    d.rectangle([x0, y0, x1, y1], outline=color, width=2, fill=C["term_f"])
    r = h // 2 - 4
    scx = (x0 + x1 * 3) // 4 if screw_side == "right" else (x0 * 3 + x1) // 4
    scy = (y0 + y1) // 2
    d.ellipse([scx - r, scy - r, scx + r, scy + r], outline="#455A64", width=1, fill="#B0BEC5")
    d.line([(scx - r + 3, scy - r + 3), (scx + r - 3, scy + r - 3)],
           fill="#263238", width=2)
    if label:
        tw = d.textlength(label, font=F(14, bold=True))
        if screw_side == "right":
            d.text((x0 + 4, scy - 10), label, fill=C["txt"], font=F(14, bold=True))
        else:
            d.text((x1 - tw - 4, scy - 10), label, fill=C["txt"], font=F(14, bold=True))
    return scy  # center y for wire attachment


def dashed_rect(d, xy, fill, border, width=3, dash=16, gap=8):
    """Section box with dashed border, like reference RTD/TC boxes."""
    x0, y0, x1, y1 = xy
    d.rectangle([x0, y0, x1, y1], fill=fill)
    for sx, sy, ex, ey, ddx, ddy in [
        (x0, y0, x1, y0,  1,  0),
        (x1, y0, x1, y1,  0,  1),
        (x1, y1, x0, y1, -1,  0),
        (x0, y1, x0, y0,  0, -1),
    ]:
        total = abs(ex - sx) + abs(ey - sy)
        pos, on, cx_, cy_ = 0, True, sx, sy
        while pos < total:
            seg = min(dash if on else gap, total - pos)
            nx_, ny_ = cx_ + ddx * seg, cy_ + ddy * seg
            if on:
                d.line([(cx_, cy_), (nx_, ny_)], fill=border, width=width)
            cx_, cy_, pos, on = nx_, ny_, pos + seg, not on


# ── Board header boxes ──────────────────────────────────────────────────────

def esp_box(d, xy):
    x0, y0, x1, y1 = xy
    d.rounded_rectangle(xy, radius=10, fill=C["esp_f"], outline=C["esp_b"], width=3)
    d.text((x0 + 14, y0 + 10), 'ESP32-S3  "CST Temp Module"',
           fill=C["esp_b"], font=F(21, bold=True))
    # Simplified chip outline
    cr = [x0 + 14, y0 + 50, x0 + 110, y1 - 14]
    d.rounded_rectangle(cr, radius=4, fill="#78909C", outline="#455A64", width=2)
    cmy = (cr[1] + cr[3]) // 2
    d.text((cr[0] + 10, cmy - 15), "ESP32", fill="#FFFFFF", font=F(14, bold=True))
    d.text((cr[0] + 16, cmy + 4),  "S3",    fill="#CFD8DC", font=F(12))
    py = y0 + 54
    for p in ["GPIO2 = CS", "GPIO9 = SCK", "GPIO5 = MOSI", "GPIO4 = MISO"]:
        d.text((x0 + 124, py), p, fill=C["txt"], font=F(18))
        py += 28


def ltc_box(d, xy):
    x0, y0, x1, y1 = xy
    d.rounded_rectangle(xy, radius=10, fill=C["ltc_f"], outline=C["ltc_b"], width=3)
    d.text((x0 + 14, y0 + 10), "DC2209A  LTC2983 Main Board",
           fill=C["ltc_b"], font=F(21, bold=True))
    br = [x0 + 14, y0 + 50, x1 - 14, y1 - 14]
    d.rounded_rectangle(br, radius=4, fill="#D6EAF8", outline=C["ltc_b"], width=2)
    bw = br[2] - br[0]
    d.text((br[0] + bw // 2 - 66, br[1] + 10), "ANALOG DEVICES",
           fill="#1A5276", font=F(15, bold=True))
    d.text((br[0] + bw // 2 - 34, br[1] + 34), "DC2209A",
           fill="#1A5276", font=F(20, bold=True))
    d.text((br[0] + bw // 2 - 28, br[1] + 60), "LTC2983",
           fill="#2471A3", font=F(17))


def spi_block(d, x0, x1, y_top):
    cx = (x0 + x1) // 2
    d.text((cx - 16, y_top - 30), "SPI", fill=C["muted"], font=F(18, bold=True))
    for i, lbl in enumerate(["CS", "SCK", "MOSI", "MISO"]):
        y = y_top + i * 36
        d.line([(x0, y), (x1, y)], fill=C["txt"], width=2)
        d.polygon([(x1, y), (x1 - 14, y - 7), (x1 - 14, y + 7)], fill=C["txt"])
        d.text((x0 + 8, y - 22), lbl, fill=C["muted"], font=F(15))


# ── Tables ──────────────────────────────────────────────────────────────────

def fw_table(d, xy, col_headers, row_data):
    """Firmware assignments table — dark title + cyan column headers."""
    x0, y0, x1, y1 = xy
    n = len(col_headers)
    cw = (x1 - x0) / n
    hdr_h = 32
    row_h = (y1 - y0 - hdr_h) / len(row_data)

    # Dark title bar
    d.rectangle([x0, y0 - 36, x1, y0], fill=C["hdr_bg"])
    title = "FIRMWARE ASSIGNMENTS"
    tw = d.textlength(title, font=F(17, bold=True))
    d.text(((x0 + x1) / 2 - tw / 2, y0 - 32), title, fill=C["hdr_txt"], font=F(17, bold=True))

    # Column headers (cyan)
    for i, h in enumerate(col_headers):
        cx0 = x0 + i * cw
        d.rectangle([cx0, y0, cx0 + cw, y0 + hdr_h], fill=C["th_bg"], outline="#FFFFFF", width=1)
        tw = d.textlength(h, font=F(15, bold=True))
        d.text((cx0 + (cw - tw) / 2, y0 + 6), h, fill=C["th_txt"], font=F(15, bold=True))

    # Data rows
    for ri, row in enumerate(row_data):
        ry0 = y0 + hdr_h + ri * row_h
        ry1 = ry0 + row_h
        bg = C["td_a"] if ri % 2 == 0 else "#FFFFFF"
        d.rectangle([x0, ry0, x1, ry1], fill=bg, outline=C["tbl_b"], width=1)
        for ci, cell in enumerate(row):
            cx0 = x0 + ci * cw
            lines = cell.split("|")
            ty = ry0 + (row_h - len(lines) * 20) / 2
            for line in lines:
                tw = d.textlength(line, font=F(14))
                d.text((cx0 + (cw - tw) / 2, ty), line, fill=C["txt"], font=F(14))
                ty += 20
    d.rectangle([x0, y0, x1, y1], outline=C["tbl_b"], width=2)


def legend_table(d, xy, wire_entries, sym_entries):
    """Color code / legend table — two sub-columns."""
    x0, y0, x1, y1 = xy
    # Dark title bar
    d.rectangle([x0, y0 - 36, x1, y0], fill=C["hdr_bg"])
    title = "COLOR CODE / LEGEND"
    tw = d.textlength(title, font=F(17, bold=True))
    d.text(((x0 + x1) / 2 - tw / 2, y0 - 32), title, fill=C["hdr_txt"], font=F(17, bold=True))
    d.rectangle([x0, y0, x1, y1], fill="#FAFAFA", outline=C["tbl_b"], width=2)

    mid = (x0 + x1) // 2
    # Left: wire colors
    y = y0 + 14
    for color, text in wire_entries:
        d.line([(x0 + 14, y + 9), (x0 + 52, y + 9)], fill=color, width=4)
        d.text((x0 + 60, y), text, fill=C["txt"], font=F(15))
        y += 28
    # Right: symbols
    y = y0 + 14
    for sym_label, sym_fn in sym_entries:
        sym_fn(d, mid + 14, y + 8)
        d.text((mid + 84, y), sym_label, fill=C["muted"], font=F(14))
        y += 32


# ── Diagram 1: DC2213A single PT1000 (working config, simplified) ──────────

def draw_dc2213a_pt1000():
    W, H = 2400, 1600
    img = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(img)

    # Title
    title = "DC2213A — PT1000 Wiring  (Simplified 4-Wire Kelvin)"
    tw = d.textlength(title, font=F(36, bold=True))
    d.text(((W - tw) / 2, 20), title, fill=C["title"], font=F(36, bold=True))

    # Board boxes + SPI
    esp_box(d, (60, 74, 520, 272))
    ltc_box(d, (1500, 74, 2320, 272))
    spi_block(d, 540, 1480, 108)

    # ── Circuit section ──────────────────────────────────────────────────
    dashed_rect(d, (60, 290, W - 60, 1210),
                fill=C["rtd_f"], border=C["rtd_b"])
    d.text((80, 302), "PT1000 Measurement Circuit",
           fill=C["rtd_lbl"], font=F(20, bold=True))
    d.text((80, 328),
           "CH3 = RSENSE (onboard 2 kΩ)   |   CH7 = Kelvin sense (tied to CH3 at probe)   |   CH8 = PT1000",
           fill=C["muted"], font=F(14))

    # RSENSE vertical at x=280
    gnd_sym(d, 280, 358)
    rs_y0, rs_y1 = 414, 620
    d.line([(280, 358 + 53), (280, rs_y0)], fill=C["gnd"], width=3)
    resistor_rect_v(d, 280, rs_y0, rs_y1)
    ch3_y = rs_y1  # CH3 node exits bottom of RSENSE

    dot(d, 280, ch3_y, color=C["ch3"])

    # J3 connector block
    J3X = 720         # left edge
    J3W = 190         # width
    PIN_H = 72        # height per pin slot
    N_PINS = 4
    j3_top = ch3_y - 16
    j3_bot = j3_top + N_PINS * PIN_H

    d.rounded_rectangle([J3X, j3_top - 28, J3X + J3W, j3_bot + 4],
                        radius=6, fill="#ECEFF1", outline="#546E7A", width=2)
    d.text((J3X + 6, j3_top - 24), "J3 (DC2213A Daughter Board)",
           fill="#37474F", font=F(15, bold=True))

    pins = [
        ("Pin 4  RTDFH", C["ch3"]),
        ("Pin 3  RTDSH", C["ch7"]),
        ("Pin 2  RTDSL", C["ch8"]),
        ("Pin 1  RTDFL", C["ch9"]),
    ]
    pcys = []
    for i, (lbl, col) in enumerate(pins):
        py0 = j3_top + i * PIN_H + 2
        py1 = py0 + PIN_H - 4
        pcy = (py0 + py1) // 2
        pcys.append(pcy)
        d.rectangle([J3X + 4, py0, J3X + J3W - 4, py1], outline=col, width=2, fill="#FFFFFF")
        # Screw on right
        cr = (PIN_H - 12) // 2
        scx = J3X + J3W - 4 - cr - 6
        d.ellipse([scx - cr, pcy - cr, scx + cr, pcy + cr],
                  outline="#455A64", width=1, fill="#B0BEC5")
        d.line([(scx - cr + 4, pcy - cr + 4), (scx + cr - 4, pcy + cr - 4)],
               fill="#263238", width=2)
        d.text((J3X + 8, pcy - 10), lbl, fill=col, font=F(14, bold=True))

    p4y, p3y, p2y, p1y = pcys
    J3R = J3X + J3W  # right edge

    # CH3 wire from RSENSE bottom → left of J3 pin 4
    d.line([(280, ch3_y), (J3X, p4y)], fill=C["ch3"], width=3)

    # ── Probe wiring to the right of J3 ──────────────────────────────────
    TIE_X = J3R + 100   # where CH3 and CH7 tie together
    PROBE_L = TIE_X     # left end of PT1000
    PROBE_R = TIE_X + 400  # right end

    # CH3 (pin 4) right from J3 → tie point
    d.line([(J3R, p4y), (TIE_X, p4y)], fill=C["ch3"], width=3)
    # CH7 (pin 3) right from J3 → tie point
    d.line([(J3R, p3y), (TIE_X, p3y)], fill=C["ch7"], width=3)
    # Vertical join at tie x
    d.line([(TIE_X, p4y), (TIE_X, p3y)], fill=C["rtd_w"], width=3)
    dot(d, TIE_X, p4y, color=C["ch3"])
    dot(d, TIE_X, p3y, color=C["ch7"])

    d.text((TIE_X + 8, p4y - 22), "Probe leg 1", fill=C["muted"], font=F(14))
    d.text((TIE_X + 8, p4y +  2), "(CH3 + CH7 tied)", fill=C["muted"], font=F(13))

    # Route down from tie to RTD mid y
    rtd_y = (p3y + p2y) // 2
    d.line([(TIE_X, p3y), (TIE_X, rtd_y)], fill=C["rtd_w"], width=3)

    # PT1000 horizontal zigzag
    rtd_sym_h(d, PROBE_L, rtd_y, PROBE_R, label="PT1000  (J3 probe)")

    # Right end of RTD → CH8 y
    d.line([(PROBE_R, rtd_y), (PROBE_R, p2y)], fill=C["rtd_w"], width=3)
    dot(d, PROBE_R, p2y, color=C["ch8"])

    # CH8 (pin 2) right from J3 → probe leg 2
    d.line([(J3R, p2y), (PROBE_R, p2y)], fill=C["ch8"], width=3)
    d.text((PROBE_R + 10, p2y - 10), "Probe leg 2", fill=C["muted"], font=F(14))

    # CH9 NC
    nc_x = J3R + 55
    d.line([(J3R, p1y), (nc_x, p1y)], fill=C["ch9"], width=3)
    no_connect(d, nc_x + 14, p1y)
    d.text((nc_x + 34, p1y - 10), "NC  (pin 1, leave open)", fill=C["ch9"], font=F(14))

    # Excitation path note
    note_y = j3_bot + 48
    d.text((J3X, note_y), "Excitation path:",
           fill=C["rtd_lbl"], font=F(16, bold=True))
    d.text((J3X + 170, note_y),
           "CH8 → PT1000 → CH7 + CH3 (Kelvin tie) → 2 kΩ RSENSE → EEGND",
           fill=C["rtd_w"], font=F(16))
    d.text((J3X, note_y + 26),
           "NOTE 1: CH7 and CH3 are physically tied at probe leg 1 — only CH3 and CH8 are firmware-configured.",
           fill=C["muted"], font=F(14))

    # ── Bottom tables ─────────────────────────────────────────────────────
    T0, T1 = 1230, 1558
    fw_table(d, (60, T0, 1160, T1),
             col_headers=["CH3", "CH7", "CH8", "CH9"],
             row_data=[
                 ["2 kΩ RSENSE|CFG_RSENSE",
                  "Kelvin sense|(physical only)",
                  "PT1000 RTD|CFG_RTD",
                  "Unused|(NC)"],
             ])

    def sym_rtd(d, x, y):
        rtd_sym_h(d, x, y, x + 64, label="", color=C["rtd_w"])

    def sym_res(d, x, y):
        d.line([(x, y), (x + 16, y)], fill=C["rtd_w"], width=2)
        d.rectangle([x + 16, y - 8, x + 52, y + 8], outline=C["rtd_w"], width=2, fill="#FFFFFF")
        d.line([(x + 52, y), (x + 68, y)], fill=C["rtd_w"], width=2)

    def sym_gnd(d, x, y):
        gnd_sym(d, x + 22, y - 10, label="")

    legend_table(d, (1180, T0, W - 60, T1),
                 wire_entries=[
                     (C["rtd_w"], "RTD excitation / shared"),
                     (C["ch3"],  "CH3 — RTDFH (RSENSE high side)"),
                     (C["ch7"],  "CH7 — RTDSH (Kelvin sense)"),
                     (C["ch8"],  "CH8 — RTDSL (probe leg 2)"),
                     (C["ch9"],  "CH9 — NC"),
                     (C["gnd"],  "EEGND"),
                 ],
                 sym_entries=[
                     ("PT1000 RTD (2-wire sym.)", sym_rtd),
                     ("2.00 kΩ RSENSE",          sym_res),
                     ("EEGND (Earth / Shield)",   sym_gnd),
                 ])

    img.save(OUT / "dc2213a-pt1000-wiring.png", "PNG")
    print("wrote dc2213a-pt1000-wiring.png")


# ── Diagram 1b: DC2213A adjustable RTD simulator (onboard R6) ───────────────

def draw_dc2213a_rtd_simulator():
    W, H = 2400, 1600
    img = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(img)

    title = "DC2213A — Adjustable RTD Simulator  (R6: pins 1+3 = CH3+CH10, wiper = CH11)"
    tw = d.textlength(title, font=F(36, bold=True))
    d.text(((W - tw) / 2, 20), title, fill=C["title"], font=F(36, bold=True))

    esp_box(d, (60, 74, 520, 272))
    ltc_box(d, (1500, 74, 2320, 272))
    spi_block(d, 540, 1480, 108)

    dashed_rect(d, (60, 290, W - 60, 1210), fill=C["rtd_f"], border=C["rtd_b"])
    d.text((80, 302), "Adjustable RTD Simulator Circuit",
           fill=C["rtd_lbl"], font=F(20, bold=True))
    d.text((80, 328),
           "CH1 + CH2 tied (C1→GND only)   |   2 kΩ RSENSE: CH1/CH2–CH3   |   R6 pins 1+3 = CH3+CH10, wiper → CH11",
           fill=C["muted"], font=F(14))

    BUS_X = 260
    ch12_y = 470
    ch3_y = 640
    rs_y0, rs_y1 = ch12_y, ch3_y

    # CH1 + CH2 tied (return node — not a hard GND short)
    dot(d, BUS_X, ch12_y, color=C["ch2"])
    d.text((BUS_X + 14, ch12_y - 38), "CH1 + CH2 tied", fill=C["muted"], font=F(14))
    d.text((BUS_X + 14, ch12_y - 18), "(not direct GND)", fill=C["muted"], font=F(13))

    # C1: CH1/CH2 node → GND (filter only)
    c1_x = BUS_X + 120
    d.line([(BUS_X, ch12_y), (c1_x, ch12_y)], fill=C["ch2"], width=3)
    cap_sym_v(d, c1_x, ch12_y + 20, ch12_y + 110, label="0.01 µF", sublabel="C1")
    gnd_sym(d, c1_x, ch12_y + 116)

    # 2 kΩ RSENSE between CH1/CH2 node and CH3
    resistor_rect_v(d, BUS_X, rs_y0, rs_y1)
    dot(d, BUS_X, ch3_y, color=C["ch3"])

    # C2: CH3 → GND
    c2_x = BUS_X + 120
    d.line([(BUS_X, ch3_y), (c2_x, ch3_y)], fill=C["ch3"], width=3)
    cap_sym_v(d, c2_x, ch3_y + 20, ch3_y + 110, label="0.01 µF", sublabel="C2")
    gnd_sym(d, c2_x, ch3_y + 116)

    # Terminal strip: CH1, CH2, CH3, CH10, CH11
    TERM_X = 620
    TW, TH, GAP = 130, 52, 12
    active = [
        ("CH1", C["ch1"]), ("CH2", C["ch2"]), ("CH3", C["ch3"]),
        ("CH10", C["ch10"]), ("CH11", C["ch11"]),
    ]
    tys = []
    y0 = 400
    for i, (lbl, col) in enumerate(active):
        ty = y0 + i * (TH + GAP)
        tys.append(ty)
        d.rounded_rectangle([TERM_X, ty, TERM_X + TW, ty + TH],
                            radius=6, outline=col, width=2, fill="#FFFFFF")
        d.text((TERM_X + 10, ty + 14), lbl, fill=col, font=F(16, bold=True))
        cr = 14
        scx = TERM_X + TW - cr - 8
        scy = ty + TH // 2
        d.ellipse([scx - cr, scy - cr, scx + cr, scy + cr],
                  outline="#455A64", width=1, fill="#B0BEC5")
        d.line([(scx - 8, scy - 8), (scx + 8, scy + 8)], fill="#263238", width=2)

    ch1_ty, ch2_ty, ch3_ty, ch10_ty, ch11_ty = [ty + TH // 2 for ty in tys]
    TR = TERM_X + TW

    # Bus → terminals
    d.line([(BUS_X, ch12_y), (TERM_X, ch2_ty)], fill=C["ch2"], width=3)
    d.line([(TERM_X, ch1_ty), (TERM_X - 40, ch1_ty), (TERM_X - 40, ch2_ty),
            (BUS_X, ch12_y)], fill=C["ch1"], width=3)
    d.text((TERM_X - 36, (ch1_ty + ch2_ty) // 2 - 8), "tie", fill=C["muted"], font=F(12))
    d.line([(BUS_X, ch3_y), (TERM_X, ch3_ty)], fill=C["ch3"], width=3)

    # CH3 + CH10 → R6 pins 1+3 (left side of pot)
    TIE_X = TR + 120
    POT_Y = (ch3_ty + ch10_ty) // 2
    d.line([(TR, ch3_ty), (TIE_X, ch3_ty)], fill=C["ch3"], width=3)
    d.line([(TR, ch10_ty), (TIE_X, ch10_ty)], fill=C["ch10"], width=3)
    d.line([(TIE_X, ch3_ty), (TIE_X, ch10_ty)], fill=C["rtd_w"], width=3)
    dot(d, TIE_X, ch3_ty, color=C["ch3"])
    dot(d, TIE_X, ch10_ty, color=C["ch10"])
    d.text((TIE_X + 10, ch3_ty - 24), "CH3 + CH10 tied", fill=C["muted"], font=F(14))
    d.text((TIE_X + 10, ch10_ty + 6), "(→ R6 pins 1 + 3)", fill=C["muted"], font=F(13))

    # R6: pins 1+3 left, wiper pin 2 → CH11
    POT_L = TIE_X + 40
    POT_R = POT_L + 420
    pot_sym_h(d, POT_L, POT_Y, POT_R, label="10 kΩ", sublabel="R6 (adj. RTD)")
    d.line([(TIE_X, POT_Y), (POT_L, POT_Y)], fill=C["rtd_w"], width=3)
    d.line([(POT_R, POT_Y), (TR, ch11_ty)], fill=C["ch11"], width=3)
    d.text((POT_R + 8, POT_Y - 22), "wiper pin 2 → CH11", fill=C["ch11"], font=F(13))
    dot(d, TR, ch11_ty, color=C["ch11"])

    # C6 on CH11 → GND
    cap_x = POT_R + 160
    cap_y0 = ch11_ty + 30
    cap_y1 = cap_y0 + 90
    d.line([(cap_x, ch11_ty), (cap_x, cap_y0)], fill=C["ch11"], width=3)
    cap_sym_v(d, cap_x, cap_y0, cap_y1)
    gnd_sym(d, cap_x, cap_y1 + 6)

    note_y = tys[-1] + TH + 50
    d.text((TERM_X, note_y), "Excitation path:",
           fill=C["rtd_lbl"], font=F(16, bold=True))
    d.text((TERM_X + 170, note_y),
           "CH11 ← R6 wiper ← CH3+CH10 ← 2 kΩ RSENSE ← CH1+CH2 (C1→GND)",
           fill=C["rtd_w"], font=F(16))
    d.text((TERM_X, note_y + 26),
           "CH1/CH2 are tied together but NOT hard-shorted to GND — only C1 (0.01 µF) to GND.",
           fill=C["muted"], font=F(14))
    d.text((TERM_X, note_y + 48),
           "On DC2213A these are onboard. On DC2210A: jumper CH1↔CH2, add 2 kΩ CH2–CH3.",
           fill=C["muted"], font=F(14))

    T0, T1 = 1230, 1558
    fw_table(d, (60, T0, 1260, T1),
             col_headers=["CH1", "CH2", "CH3", "CH10", "CH11"],
             row_data=[
                 ["Tied to CH2|C1→GND",
                  "RSENSE low|(w/ CH1)",
                  "2 kΩ RSENSE|CFG_RSENSE",
                  "Kelvin → R6|(pins 1+3)",
                  "R6 wiper|CFG_RTD"],
             ])

    def sym_pot(d, x, y):
        pot_sym_h(d, x, y, x + 90, label="10 kΩ", sublabel="R6")

    def sym_cap(d, x, y):
        cap_sym_v(d, x + 22, y - 10, y + 34)

    def sym_res(d, x, y):
        d.line([(x, y), (x + 16, y)], fill=C["rtd_w"], width=2)
        d.rectangle([x + 16, y - 8, x + 52, y + 8], outline=C["rtd_w"], width=2, fill="#FFFFFF")
        d.line([(x + 52, y), (x + 68, y)], fill=C["rtd_w"], width=2)

    def sym_gnd(d, x, y):
        gnd_sym(d, x + 22, y - 10, label="")

    legend_table(d, (1280, T0, W - 60, T1),
                 wire_entries=[
                     (C["rtd_w"],  "Simulator / excitation"),
                     (C["ch1"],   "CH1 — tied to CH2"),
                     (C["ch2"],   "CH2 — RSENSE return (w/ CH1)"),
                     (C["ch3"],   "CH3 — RSENSE high / R6 pins 1+3"),
                     (C["ch10"],  "CH10 — RTDSH (Kelvin, tied to CH3)"),
                     (C["ch11"],  "CH11 — R6 wiper (pin 2)"),
                     (C["gnd"],   "EEGND"),
                 ],
                 sym_entries=[
                     ("10 kΩ Potentiometer R6", sym_pot),
                     ("0.01 µF Capacitor (C1/C2/C6)", sym_cap),
                     ("2.00 kΩ RSENSE",         sym_res),
                     ("EEGND",                  sym_gnd),
                 ])

    img.save(OUT / "dc2213a-rtd-simulator-wiring.png", "PNG")
    print("wrote dc2213a-rtd-simulator-wiring.png")


# ── Diagram 1c: DC2213A dual RTD — working firmware (CH8 J3 + CH11 R6) ────

def draw_dc2213a_dual_rtd():
    W, H = 2800, 1900
    img = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(img)

    title = "DC2213A — Dual RTD Configuration  (CH8 J3 PT1000 + CH11 R6 Simulator)"
    tw = d.textlength(title, font=F(36, bold=True))
    d.text(((W - tw) / 2, 20), title, fill=C["title"], font=F(36, bold=True))

    esp_box(d, (60, 74, 520, 272))
    ltc_box(d, (1500, 74, 2320, 272))
    spi_block(d, 540, 1480, 108)

    # ── Shared RSENSE (left) ─────────────────────────────────────────────
    dashed_rect(d, (60, 290, 520, 1480), fill=C["rtd_f"], border=C["rtd_b"])
    d.text((80, 302), "Shared Excitation — CH3 RSENSE",
           fill=C["rtd_lbl"], font=F(20, bold=True))
    d.text((80, 328), "CH1 + CH2 tied (C1→GND)  |  2 kΩ between CH1/CH2 and CH3",
           fill=C["muted"], font=F(14))

    BUS_X = 280
    ch12_y = 420
    ch3_y = 620

    dot(d, BUS_X, ch12_y, color=C["ch2"])
    d.text((BUS_X + 16, ch12_y - 36), "CH1 + CH2", fill=C["muted"], font=F(14, bold=True))

    c1_x = BUS_X + 100
    d.line([(BUS_X, ch12_y), (c1_x, ch12_y)], fill=C["ch2"], width=3)
    cap_sym_v(d, c1_x, ch12_y + 18, ch12_y + 100, label="0.01 µF", sublabel="C1")
    gnd_sym(d, c1_x, ch12_y + 106)

    resistor_rect_v(d, BUS_X, ch12_y, ch3_y)
    dot(d, BUS_X, ch3_y, color=C["ch3"], r=8)
    d.text((BUS_X + 18, ch3_y - 10), "CH3", fill=C["ch3"], font=F(15, bold=True))

    c2_x = BUS_X + 100
    d.line([(BUS_X, ch3_y), (c2_x, ch3_y)], fill=C["ch3"], width=3)
    cap_sym_v(d, c2_x, ch3_y + 18, ch3_y + 100, label="0.01 µF", sublabel="C2")
    gnd_sym(d, c2_x, ch3_y + 106)

    # Channel labels on bus
    for lbl, col, ty in [("CH1", C["ch1"], ch12_y - 55), ("CH2", C["ch2"], ch12_y + 8),
                         ("CH3", C["ch3"], ch3_y + 14)]:
        d.text((80, ty), lbl, fill=col, font=F(14, bold=True))

    HUB_X = 560
    d.line([(BUS_X, ch3_y), (HUB_X, ch3_y)], fill=C["ch3"], width=4)
    dot(d, HUB_X, ch3_y, color=C["ch3"], r=8)

    # ── J3 External PT1000 (upper right) ───────────────────────────────────
    J3_Y0, J3_Y1 = 300, 820
    dashed_rect(d, (540, J3_Y0, W - 60, J3_Y1), fill=C["rtd_f"], border=C["rtd_b"])
    d.text((560, J3_Y0 + 12), "J3 External PT1000  →  firmware CH8 (CFG_RTD_KELVIN)",
           fill=C["rtd_lbl"], font=F(20, bold=True))
    d.text((560, J3_Y0 + 38),
           "CH7 tied to CH3 at probe leg 1  |  CH8 = probe leg 2  |  CH9 NC",
           fill=C["muted"], font=F(14))

    J3X = 600
    J3W = 200
    PIN_H = 68
    j3_top = J3_Y0 + 80
    d.rounded_rectangle([J3X, j3_top - 26, J3X + J3W, j3_top + 4 * PIN_H + 4],
                        radius=6, fill="#ECEFF1", outline="#546E7A", width=2)
    d.text((J3X + 8, j3_top - 22), "J3 Connector", fill="#37474F", font=F(15, bold=True))

    pins = [("Pin 4  RTDFH  (CH3)", C["ch3"]), ("Pin 3  RTDSH  (CH7)", C["ch7"]),
            ("Pin 2  RTDSL  (CH8)", C["ch8"]), ("Pin 1  RTDFL  (CH9)", C["ch9"])]
    pcys = []
    for i, (lbl, col) in enumerate(pins):
        py0 = j3_top + i * PIN_H
        pcy = py0 + PIN_H // 2
        pcys.append(pcy)
        d.rectangle([J3X + 4, py0 + 2, J3X + J3W - 4, py0 + PIN_H - 2],
                    outline=col, width=2, fill="#FFFFFF")
        d.text((J3X + 10, pcy - 10), lbl, fill=col, font=F(13, bold=True))

    p4y, p3y, p2y, p1y = pcys
    J3R = J3X + J3W

    d.line([(HUB_X, ch3_y), (J3X, p4y)], fill=C["ch3"], width=3)

    TIE_J3 = J3R + 90
    PROBE_R = TIE_J3 + 380
    rtd_y = (p3y + p2y) // 2

    d.line([(J3R, p4y), (TIE_J3, p4y)], fill=C["ch3"], width=3)
    d.line([(J3R, p3y), (TIE_J3, p3y)], fill=C["ch7"], width=3)
    d.line([(TIE_J3, p4y), (TIE_J3, p3y)], fill=C["rtd_w"], width=3)
    dot(d, TIE_J3, p4y, color=C["ch3"])
    dot(d, TIE_J3, p3y, color=C["ch7"])
    d.text((TIE_J3 + 8, p4y - 20), "CH3 + CH7 tied", fill=C["muted"], font=F(13))

    d.line([(TIE_J3, p3y), (TIE_J3, rtd_y)], fill=C["rtd_w"], width=3)
    rtd_sym_h(d, TIE_J3, rtd_y, PROBE_R, label="PT1000")
    d.line([(PROBE_R, rtd_y), (PROBE_R, p2y)], fill=C["rtd_w"], width=3)
    d.line([(J3R, p2y), (PROBE_R, p2y)], fill=C["ch8"], width=3)
    dot(d, PROBE_R, p2y, color=C["ch8"])

    nc_x = J3R + 50
    d.line([(J3R, p1y), (nc_x, p1y)], fill=C["ch9"], width=3)
    no_connect(d, nc_x + 12, p1y)
    d.text((nc_x + 30, p1y - 10), "NC", fill=C["ch9"], font=F(13))

    # ── R6 Adjustable Simulator (lower right) ────────────────────────────
    R6_Y0, R6_Y1 = 860, 1480
    dashed_rect(d, (540, R6_Y0, W - 60, R6_Y1), fill="#E8F6FF", border=C["rtd_b"])
    d.text((560, R6_Y0 + 12), "Onboard R6 Adjustable RTD Simulator  →  firmware CH11",
           fill=C["rtd_lbl"], font=F(20, bold=True))
    d.text((560, R6_Y0 + 38),
           "R6 pins 1+3 → CH3 + CH10 (Kelvin)  |  R6 wiper pin 2 → CH11  |  C6 on CH11",
           fill=C["muted"], font=F(14))

    TERM_X = 600
    TW, TH, GAP = 140, 50, 14
    ch10_ty = R6_Y0 + 130
    ch11_ty = ch10_ty + TH + GAP + 40
    ch3_r6_ty = ch10_ty - TH - GAP

    for lbl, col, ty in [("CH3", C["ch3"], ch3_r6_ty), ("CH10", C["ch10"], ch10_ty),
                         ("CH11", C["ch11"], ch11_ty)]:
        d.rounded_rectangle([TERM_X, ty, TERM_X + TW, ty + TH],
                              radius=6, outline=col, width=2, fill="#FFFFFF")
        d.text((TERM_X + 12, ty + 14), lbl, fill=col, font=F(16, bold=True))

    TR = TERM_X + TW
    d.line([(HUB_X, ch3_y), (TERM_X, ch3_r6_ty + TH // 2)], fill=C["ch3"], width=3)

    TIE_R6 = TR + 100
    POT_Y = (ch10_ty + ch11_ty + TH) // 2
    d.line([(TR, ch3_r6_ty + TH // 2), (TIE_R6, ch3_r6_ty + TH // 2)], fill=C["ch3"], width=3)
    d.line([(TR, ch10_ty + TH // 2), (TIE_R6, ch10_ty + TH // 2)], fill=C["ch10"], width=3)
    d.line([(TIE_R6, ch3_r6_ty + TH // 2), (TIE_R6, ch10_ty + TH // 2)], fill=C["rtd_w"], width=3)
    dot(d, TIE_R6, ch10_ty + TH // 2, color=C["ch10"])
    d.text((TIE_R6 + 10, ch10_ty - 8), "CH3 + CH10 → R6 pins 1+3", fill=C["muted"], font=F(13))

    POT_L = TIE_R6 + 50
    POT_R = POT_L + 400
    pot_sym_h(d, POT_L, POT_Y, POT_R, label="10 kΩ", sublabel="R6")
    d.line([(TIE_R6, POT_Y), (POT_L, POT_Y)], fill=C["rtd_w"], width=3)
    d.line([(POT_R, POT_Y), (TR, ch11_ty + TH // 2)], fill=C["ch11"], width=3)
    d.text((POT_R + 6, POT_Y - 22), "wiper pin 2 → CH11", fill=C["ch11"], font=F(13))

    cap_x = POT_R + 140
    d.line([(cap_x, ch11_ty + TH // 2), (cap_x, ch11_ty + TH // 2 + 24)],
           fill=C["ch11"], width=3)
    cap_sym_v(d, cap_x, ch11_ty + TH // 2 + 24, ch11_ty + TH // 2 + 110,
              label="0.01 µF", sublabel="C6")
    gnd_sym(d, cap_x, ch11_ty + TH // 2 + 116)

    # ── Notes ────────────────────────────────────────────────────────────
    d.text((560, 1500), "Shared excitation:",
           fill=C["rtd_lbl"], font=F(16, bold=True))
    d.text((760, 1500),
           "Both RTDs share CH3 RSENSE (250 µA Kelvin, rotation/sharing enabled)",
           fill=C["rtd_w"], font=F(15))
    d.text((560, 1528),
           "ESPHome:  PT1000 Temperature (CH8)  |  RTD Simulator Temperature (CH11)",
           fill=C["muted"], font=F(14))

    T0, T1 = 1560, 1860
    fw_table(d, (60, T0, 1500, T1),
             col_headers=["CH1", "CH2", "CH3", "CH7", "CH8", "CH9", "CH10", "CH11"],
             row_data=[
                 ["Tied→CH2|C1→GND", "RSENSE rtn", "2kΩ RSENSE|shared",
                  "Kelvin|(→CH3)", "PT1000|CFG_RTD_KELVIN", "NC",
                  "Kelvin|(→CH3,R6 p1+3)", "R6 wiper|2-wire 100µA"],
             ])

    def sym_rtd(d, x, y):
        rtd_sym_h(d, x, y, x + 58, label="", color=C["rtd_w"])

    def sym_pot(d, x, y):
        pot_sym_h(d, x, y, x + 80, label="10k", sublabel="R6")

    def sym_res(d, x, y):
        d.line([(x, y), (x + 14, y)], fill=C["rtd_w"], width=2)
        d.rectangle([x + 14, y - 7, x + 48, y + 7], outline=C["rtd_w"], width=2, fill="#FFFFFF")
        d.line([(x + 48, y), (x + 62, y)], fill=C["rtd_w"], width=2)

    def sym_cap(d, x, y):
        cap_sym_v(d, x + 18, y - 8, y + 28)

    def sym_gnd(d, x, y):
        gnd_sym(d, x + 18, y - 8, label="")

    legend_table(d, (1520, T0, W - 60, T1),
                 wire_entries=[
                     (C["rtd_w"],  "RTD excitation (shared)"),
                     (C["ch3"],   "CH3 — RSENSE / RTDFH / R6 pins 1+3"),
                     (C["ch7"],   "CH7 — J3 Kelvin sense"),
                     (C["ch8"],   "CH8 — J3 PT1000 leg 2"),
                     (C["ch10"],  "CH10 — R6 Kelvin (tied to CH3)"),
                     (C["ch11"],  "CH11 — R6 wiper"),
                     (C["gnd"],   "EEGND"),
                 ],
                 sym_entries=[
                     ("PT1000 RTD", sym_rtd),
                     ("10 kΩ Pot R6", sym_pot),
                     ("2.00 kΩ RSENSE", sym_res),
                     ("0.01 µF Cap", sym_cap),
                     ("EEGND", sym_gnd),
                 ])

    img.save(OUT / "dc2213a-dual-rtd-wiring.png", "PNG")
    print("wrote dc2213a-dual-rtd-wiring.png")


# ── Stick diagram: dual RTD (working firmware) ─────────────────────────────

def draw_dc2213a_stick_dual_rtd():
    """Compact stick schematic — CH8 J3 PT1000 + CH11 R6 simulator."""
    W, H = 2000, 1100
    img = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(img)

    title = "DC2213A Stick Diagram — Dual RTD  (CH8 PT1000 + CH11 R6 Simulator)"
    tw = d.textlength(title, font=F(32, bold=True))
    d.text(((W - tw) / 2, 24), title, fill=C["title"], font=F(32, bold=True))
    d.text((60, 68),
           "Shared CH3 RSENSE  |  CH8 = 4-wire Kelvin 250 µA  |  CH11 = 2-wire 100 µA",
           fill=C["muted"], font=F(15))

    # LTC2983 channel block (left)
    ltc_x0, ltc_y0, ltc_x1, ltc_y1 = 60, 120, 340, 980
    d.rounded_rectangle([ltc_x0, ltc_y0, ltc_x1, ltc_y1],
                        radius=10, outline=C["ltc_b"], width=3, fill=C["ltc_f"])
    d.text((ltc_x0 + 20, ltc_y0 + 14), "LTC2983", fill=C["ltc_b"], font=F(22, bold=True))
    d.text((ltc_x0 + 20, ltc_y0 + 44), "DC2209A + DC2213A", fill=C["muted"], font=F(14))

    pin_x = ltc_x1 - 8
    channels = [
        (180, "CH1",  C["ch1"],  "tie→CH2"),
        (240, "CH2",  C["ch2"],  "RSENSE rtn"),
        (380, "CH3",  C["ch3"],  "2 kΩ RSENSE"),
        (520, "CH7",  C["ch7"],  "J3 Kelvin"),
        (580, "CH8",  C["ch8"],  "PT1000"),
        (640, "CH9",  C["ch9"],  "NC"),
        (700, "CH10", C["ch10"], "→R6 p1+3"),
        (760, "CH11", C["ch11"], "R6 wiper"),
    ]
    for y, lbl, col, note in channels:
        d.line([(ltc_x0 + 30, y), (pin_x, y)], fill=col, width=2)
        d.text((ltc_x0 + 36, y - 10), lbl, fill=col, font=F(14, bold=True))
        d.text((ltc_x0 + 100, y + 2), note, fill=C["muted"], font=F(12))

    bus_x = 420
    ch12_y, ch3_y = 210, 380

    # CH1 + CH2 tied
    d.line([(pin_x, 180), (bus_x, ch12_y)], fill=C["ch1"], width=3)
    d.line([(pin_x, 240), (bus_x, ch12_y)], fill=C["ch2"], width=3)
    dot(d, bus_x, ch12_y, color=C["ch2"])
    d.text((bus_x + 12, ch12_y - 28), "CH1 + CH2 tied", fill=C["muted"], font=F(13))

    # C1 filter to GND
    c1_x = bus_x + 90
    d.line([(bus_x, ch12_y), (c1_x, ch12_y)], fill=C["ch2"], width=3)
    cap_sym_v(d, c1_x, ch12_y + 16, ch12_y + 90, label="0.01 µF", sublabel="C1")
    gnd_sym(d, c1_x, ch12_y + 96, label="")

    # RSENSE CH1/CH2 → CH3
    resistor_rect_v(d, bus_x, ch12_y, ch3_y)
    d.line([(pin_x, 380), (bus_x, ch3_y)], fill=C["ch3"], width=3)
    dot(d, bus_x, ch3_y, r=8, color=C["ch3"])

    # C2 on CH3
    c2_x = bus_x + 90
    d.line([(bus_x, ch3_y), (c2_x, ch3_y)], fill=C["ch3"], width=3)
    cap_sym_v(d, c2_x, ch3_y + 16, ch3_y + 90, label="0.01 µF", sublabel="C2")
    gnd_sym(d, c2_x, ch3_y + 96, label="")

    hub_x = 560
    d.line([(bus_x, ch3_y), (hub_x, ch3_y)], fill=C["ch3"], width=4)
    dot(d, hub_x, ch3_y, r=8, color=C["ch3"])

    # ── Upper branch: J3 PT1000 → CH8 ────────────────────────────────────
    j3_y = 520
    tie_j3 = hub_x + 120
    probe_r = tie_j3 + 340

    d.line([(hub_x, ch3_y), (hub_x, j3_y - 40), (tie_j3, j3_y - 40)], fill=C["ch3"], width=3)
    d.line([(pin_x, 520), (tie_j3, j3_y)], fill=C["ch7"], width=3)
    d.line([(tie_j3, j3_y - 40), (tie_j3, j3_y)], fill=C["rtd_w"], width=3)
    dot(d, tie_j3, j3_y - 40, color=C["ch3"])
    dot(d, tie_j3, j3_y, color=C["ch7"])
    d.text((tie_j3 + 8, j3_y - 58), "CH3 + CH7", fill=C["muted"], font=F(13))

    rtd_sym_h(d, tie_j3, j3_y, probe_r, label="PT1000")
    d.line([(probe_r, j3_y), (probe_r, j3_y + 60)], fill=C["rtd_w"], width=3)
    d.line([(pin_x, 580), (probe_r, j3_y + 60)], fill=C["ch8"], width=3)
    dot(d, probe_r, j3_y + 60, color=C["ch8"])
    d.text((probe_r + 10, j3_y + 44), "→ CH8", fill=C["ch8"], font=F(13, bold=True))

    d.rounded_rectangle([hub_x + 40, 460, 1880, 640], radius=8,
                        outline=C["rtd_b"], width=2, fill="#F5FAFF")
    d.text((hub_x + 56, 468), "J3 External PT1000  (CFG_RTD_KELVIN, 250 µA)",
           fill=C["rtd_lbl"], font=F(16, bold=True))

    # CH9 NC
    d.line([(pin_x, 640), (probe_r - 80, 640)], fill=C["ch9"], width=2)
    no_connect(d, probe_r - 60, 640)
    d.text((probe_r - 40, 628), "CH9 NC", fill=C["ch9"], font=F(12))

    # ── Lower branch: R6 simulator → CH11 ────────────────────────────────
    r6_y = 820
    tie_r6 = hub_x + 120
    pot_l = tie_r6 + 60
    pot_r = pot_l + 360

    d.line([(hub_x, ch3_y), (hub_x, r6_y - 50), (tie_r6, r6_y - 50)], fill=C["ch3"], width=3)
    d.line([(pin_x, 700), (tie_r6, r6_y)], fill=C["ch10"], width=3)
    d.line([(tie_r6, r6_y - 50), (tie_r6, r6_y)], fill=C["rtd_w"], width=3)
    dot(d, tie_r6, r6_y - 50, color=C["ch3"])
    dot(d, tie_r6, r6_y, color=C["ch10"])
    d.text((tie_r6 + 8, r6_y - 68), "CH3 + CH10 → R6 pins 1+3", fill=C["muted"], font=F(13))

    pot_sym_h(d, pot_l, r6_y, pot_r, label="10 kΩ", sublabel="R6")
    d.line([(tie_r6, r6_y), (pot_l, r6_y)], fill=C["rtd_w"], width=3)
    d.line([(pot_r, r6_y), (pin_x, 760)], fill=C["ch11"], width=3)
    dot(d, pot_r, r6_y, color=C["ch11"])
    d.text((pot_r + 8, r6_y - 24), "wiper pin 2 → CH11", fill=C["ch11"], font=F(13))

    cap_x = pot_r + 120
    d.line([(cap_x, r6_y), (cap_x, r6_y + 20)], fill=C["ch11"], width=3)
    cap_sym_v(d, cap_x, r6_y + 20, r6_y + 100, label="0.01 µF", sublabel="C6")
    gnd_sym(d, cap_x, r6_y + 106, label="")

    d.rounded_rectangle([hub_x + 40, 700, 1880, 960], radius=8,
                        outline="#1565C0", width=2, fill="#E8F6FF")
    d.text((hub_x + 56, 708), "Onboard R6 Adjustable RTD Simulator  (CFG_RTD_SIM, 2-wire 100 µA)",
           fill=C["rtd_lbl"], font=F(16, bold=True))

    # Excitation path note
    d.text((60, 1010), "Excitation return:",
           fill=C["rtd_lbl"], font=F(15, bold=True))
    d.text((220, 1010),
           "CH8/CH11 → sensor → CH3 hub → 2 kΩ RSENSE → CH1+CH2 (C1→GND)",
           fill=C["rtd_w"], font=F(15))
    d.text((60, 1040),
           "ESPHome:  PT1000 Temperature (CH8)  |  RTD Simulator Temperature (CH11)",
           fill=C["muted"], font=F(14))

    img.save(OUT / "dc2213a-dual-rtd-stick.png", "PNG")
    print("wrote dc2213a-dual-rtd-stick.png")


# ── Diagram 2: DC2210A single PT1000 (simplified, breadboard terminals) ────

def draw_dc2210a_pt1000():
    W, H = 2400, 1600
    img = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(img)

    title = "DC2210A — PT1000 Wiring  (Breadboard Terminals, Simplified)"
    tw = d.textlength(title, font=F(36, bold=True))
    d.text(((W - tw) / 2, 20), title, fill=C["title"], font=F(36, bold=True))

    esp_box(d, (60, 74, 520, 272))
    ltc_box(d, (1500, 74, 2320, 272))
    spi_block(d, 540, 1480, 108)

    dashed_rect(d, (60, 290, W - 60, 1210), fill=C["rtd_f"], border=C["rtd_b"])
    d.text((80, 302), "PT1000 Measurement Circuit",
           fill=C["rtd_lbl"], font=F(20, bold=True))
    d.text((80, 328),
           "External 2 kΩ RSENSE between CH2 and CH3   |   CH7 jumpered to CH3   |   CH8 = PT1000",
           fill=C["muted"], font=F(14))

    # Screw terminal strip — show only active channels: CH1 CH2 CH3 CH7 CH8 CH9
    TERM_X = 680       # left edge of strip
    TW = 130           # terminal width
    TH = 52            # terminal height
    GAP = 14           # gap between terminals
    active_chs = ["CH1", "CH2", "CH3", "CH7", "CH8", "CH9"]
    n_terms = len(active_chs)
    strip_h = n_terms * TH + (n_terms - 1) * GAP
    strip_top = 380

    # Strip header
    d.rounded_rectangle([TERM_X - 6, strip_top - 36, TERM_X + TW + 6, strip_top - 2],
                        radius=4, fill=C["term_b"], outline=C["term_b"])
    hdr = "DC2210A"
    tw2 = d.textlength(hdr, font=F(14, bold=True))
    d.text((TERM_X + (TW - tw2) / 2, strip_top - 30), hdr, fill="#FFFFFF", font=F(14, bold=True))

    term_cys = {}
    for i, ch in enumerate(active_chs):
        ty = strip_top + i * (TH + GAP)
        ccy = screw_terminal(d, TERM_X, ty, TW, TH, label=ch, screw_side="right")
        term_cys[ch] = ccy

    # ── Left side: RSENSE and ground ────────────────────────────────────
    BUS_X = 400   # vertical wire x

    # EEGND at top, wire down to CH1 level
    gnd_sym(d, BUS_X, 340)
    d.line([(BUS_X, 340 + 53), (BUS_X, term_cys["CH1"])], fill=C["gnd"], width=3)
    d.line([(BUS_X, term_cys["CH1"]), (TERM_X, term_cys["CH1"])], fill=C["gnd"], width=3)
    dot(d, BUS_X, term_cys["CH1"], color=C["gnd"])
    d.text((BUS_X + 10, term_cys["CH1"] - 20), "→ CH1 (EEGND)", fill=C["muted"], font=F(13))

    # RSENSE between BUS (CH2 level) and CH3 level
    rs_y0 = term_cys["CH2"] - 20
    rs_y1 = term_cys["CH3"] + 20
    d.line([(BUS_X, term_cys["CH1"]), (BUS_X, rs_y0)], fill=C["rtd_w"], width=3)
    resistor_rect_v(d, BUS_X, rs_y0, rs_y1)
    d.line([(BUS_X, term_cys["CH2"]), (TERM_X, term_cys["CH2"])], fill=C["rtd_w"], width=3)
    d.line([(BUS_X, term_cys["CH3"]), (TERM_X, term_cys["CH3"])], fill=C["ch3"], width=3)
    dot(d, BUS_X, term_cys["CH2"], color=C["rtd_w"])
    dot(d, BUS_X, term_cys["CH3"], color=C["ch3"])

    # CH3–CH7 jumper (vertical line between the two terminal wire stubs)
    JP_X = TERM_X - 50
    d.line([(TERM_X, term_cys["CH3"]), (JP_X, term_cys["CH3"])], fill=C["ch3"], width=3)
    d.line([(TERM_X, term_cys["CH7"]), (JP_X, term_cys["CH7"])], fill=C["ch7"], width=3)
    d.line([(JP_X, term_cys["CH3"]), (JP_X, term_cys["CH7"])], fill=C["rtd_w"], width=3)
    dot(d, JP_X, term_cys["CH3"], color=C["ch3"])
    dot(d, JP_X, term_cys["CH7"], color=C["ch7"])
    d.rounded_rectangle([JP_X - 40, term_cys["CH3"] + 10,
                          JP_X + 4, term_cys["CH7"] - 10],
                        radius=4, outline=C["ch7"], width=2, fill="#D5F5E3")
    lbl = "Jumper\nCH3↔CH7"
    d.text((JP_X - 36, term_cys["CH3"] + 16), "Jumper", fill=C["ch7"], font=F(12, bold=True))
    d.text((JP_X - 36, term_cys["CH3"] + 32), "CH3↔CH7", fill=C["ch7"], font=F(12, bold=True))

    # ── Right side: PT1000 and CH8 ───────────────────────────────────────
    TERM_R = TERM_X + TW
    TIE_X = TERM_R + 120

    # CH3 and CH7 come out right side → tie point
    d.line([(TERM_R, term_cys["CH3"]), (TIE_X, term_cys["CH3"])], fill=C["ch3"], width=3)
    d.line([(TERM_R, term_cys["CH7"]), (TIE_X, term_cys["CH7"])], fill=C["ch7"], width=3)
    d.line([(TIE_X, term_cys["CH3"]), (TIE_X, term_cys["CH7"])], fill=C["rtd_w"], width=3)
    dot(d, TIE_X, term_cys["CH3"])
    dot(d, TIE_X, term_cys["CH7"])
    d.text((TIE_X + 8, term_cys["CH3"] - 22), "Probe leg 1  (CH3+CH7 tied)", fill=C["muted"], font=F(13))

    rtd_y = (term_cys["CH7"] + term_cys["CH8"]) // 2
    d.line([(TIE_X, term_cys["CH7"]), (TIE_X, rtd_y)], fill=C["rtd_w"], width=3)
    PROBE_R = TIE_X + 380
    rtd_sym_h(d, TIE_X, rtd_y, PROBE_R, label="PT1000")
    d.line([(PROBE_R, rtd_y), (PROBE_R, term_cys["CH8"])], fill=C["rtd_w"], width=3)
    dot(d, PROBE_R, term_cys["CH8"], color=C["ch8"])
    d.line([(TERM_R, term_cys["CH8"]), (PROBE_R, term_cys["CH8"])], fill=C["ch8"], width=3)
    d.text((PROBE_R + 10, term_cys["CH8"] - 10), "Probe leg 2", fill=C["muted"], font=F(14))

    # CH9 NC
    nc_x2 = TERM_R + 55
    d.line([(TERM_R, term_cys["CH9"]), (nc_x2, term_cys["CH9"])], fill=C["ch9"], width=3)
    no_connect(d, nc_x2 + 14, term_cys["CH9"])
    d.text((nc_x2 + 34, term_cys["CH9"] - 10), "NC", fill=C["ch9"], font=F(14))

    # Current path
    note_y = strip_top + strip_h + 44
    d.text((TERM_X, note_y), "Excitation path:", fill=C["rtd_lbl"], font=F(16, bold=True))
    d.text((TERM_X + 170, note_y),
           "CH8 → PT1000 → CH7+CH3 (tied) → 2 kΩ → CH2 → CH1/EEGND",
           fill=C["rtd_w"], font=F(16))
    d.text((TERM_X, note_y + 24),
           "Replicates DC2213A J3 topology on breadboard screws.  CH3 = CFG_RSENSE,  CH8 = CFG_RTD",
           fill=C["muted"], font=F(14))

    T0, T1 = 1230, 1558
    fw_table(d, (60, T0, 1160, T1),
             col_headers=["CH2", "CH3", "CH7", "CH8", "CH9"],
             row_data=[
                 ["RSENSE return|(EEGND side)",
                  "RSENSE high|(CFG_RSENSE)",
                  "Kelvin sense|(jumper→CH3)",
                  "PT1000 RTD|(CFG_RTD)",
                  "NC|(unused)"],
             ])

    def sym_rtd(d, x, y):
        rtd_sym_h(d, x, y, x + 64, label="", color=C["rtd_w"])

    def sym_res(d, x, y):
        d.line([(x, y), (x + 16, y)], fill=C["rtd_w"], width=2)
        d.rectangle([x + 16, y - 8, x + 52, y + 8], outline=C["rtd_w"], width=2, fill="#FFFFFF")
        d.line([(x + 52, y), (x + 68, y)], fill=C["rtd_w"], width=2)

    def sym_gnd(d, x, y):
        gnd_sym(d, x + 22, y - 10, label="")

    legend_table(d, (1180, T0, W - 60, T1),
                 wire_entries=[
                     (C["rtd_w"], "RTD excitation / shared"),
                     (C["ch3"],  "CH3 — RSENSE high / RTDFH"),
                     (C["ch7"],  "CH7 — RTDSH (Kelvin sense)"),
                     (C["ch8"],  "CH8 — RTDSL (probe leg 2)"),
                     (C["ch9"],  "CH9 — NC"),
                     (C["gnd"],  "EEGND"),
                 ],
                 sym_entries=[
                     ("PT1000 RTD (2-wire sym.)", sym_rtd),
                     ("2.00 kΩ RSENSE",          sym_res),
                     ("EEGND (Earth / Shield)",   sym_gnd),
                 ])

    img.save(OUT / "dc2210a-pt1000-wiring.png", "PNG")
    print("wrote dc2210a-pt1000-wiring.png")


# ── Diagram 3: DC2210A 5× RTD + 5× TC (reference format) ──────────────────

def draw_dc2210a_5rtd_5tc():
    # Canvas height is computed after layout constants are known; pre-declare W
    W = 2700
    # Height calculated below after layout vars are set
    STRIP_TOP_ = 310
    N_ROWS_ = 10
    ROW_H_ = 44
    SEC_BOT_ = STRIP_TOP_ + N_ROWS_ * ROW_H_ + 60
    T0_ = SEC_BOT_ + 50
    T1_ = T0_ + 180
    H = T1_ + 40
    img = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(img)

    title = "DC2210A — 5× PT1000 RTD + 5× K-Type Thermocouple Wiring"
    tw = d.textlength(title, font=F(36, bold=True))
    d.text(((W - tw) / 2, 20), title, fill=C["title"], font=F(36, bold=True))

    esp_box(d, (60, 74, 520, 272))
    ltc_box(d, (1700, 74, 2620, 272))
    spi_block(d, 540, 1680, 108)

    # ── Terminal strip center ─────────────────────────────────────────────
    TCOL_L = 1030   # left column x0
    TCOL_R = 1200   # right column x0
    TW2, TH2 = 120, 40
    GAP2 = 4
    N_ROWS = 10
    STRIP_TOP = 310
    ROW_H = TH2 + GAP2

    # Board header
    strip_lx = TCOL_L - 4
    strip_rx = TCOL_R + TW2 + 4
    d.rounded_rectangle([strip_lx, STRIP_TOP - 36, strip_rx, STRIP_TOP - 2],
                        radius=4, fill=C["term_b"], outline=C["term_b"])
    hdr3 = "DC2210A EXPERIMENTER BOARD"
    tw3 = d.textlength(hdr3, font=F(13, bold=True))
    d.text(((strip_lx + strip_rx) / 2 - tw3 / 2, STRIP_TOP - 30),
           hdr3, fill="#FFFFFF", font=F(13, bold=True))

    # Draw all 20 terminals
    term_cys2 = {}  # ch -> (wire_x, wire_y)
    for i in range(N_ROWS):
        ch_l = i + 1       # CH1-CH10
        ch_r = i + 11      # CH11-CH20
        ty = STRIP_TOP + i * ROW_H
        # Left col (wire exits left)
        scy_l = screw_terminal(d, TCOL_L, ty, TW2, TH2,
                               label=f"CH{ch_l}", screw_side="right")
        term_cys2[ch_l] = (TCOL_L, scy_l)  # wire exit left edge
        # Right col (wire exits right)
        scy_r = screw_terminal(d, TCOL_R, ty, TW2, TH2,
                               label=f"CH{ch_r}", screw_side="left")
        term_cys2[ch_r] = (TCOL_R + TW2, scy_r)  # wire exit right edge

    def ch_left(n):   return term_cys2[n][0], term_cys2[n][1]
    def ch_right(n):  return term_cys2[n][0], term_cys2[n][1]

    # ── RTD section (left blue dashed box) ───────────────────────────────
    RTD_SECX0, RTD_SECX1 = 60, TCOL_L - 10
    dashed_rect(d, (RTD_SECX0, 290, RTD_SECX1, STRIP_TOP + N_ROWS * ROW_H + 20),
                fill=C["rtd_f"], border=C["rtd_b"])
    d.text((RTD_SECX0 + 12, 296), "RTD DAISY CHAIN",
           fill=C["rtd_lbl"], font=F(17, bold=True))
    d.text((RTD_SECX0 + 12, 320),
           "(2-wire stacked topology,\nshared 2kΩ RSENSE,\nrotation/sharing excitation)",
           fill=C["muted"], font=F(13))
    # Actually PIL doesn't do multiline. Let me split:
    for li, line in enumerate(["(2-wire stacked topology,",
                                 "shared 2kΩ RSENSE,",
                                 "rotation/sharing excitation)"]):
        d.text((RTD_SECX0 + 12, 320 + li * 18), line, fill=C["muted"], font=F(13))

    # Vertical bus wire x
    BUS_X2 = RTD_SECX0 + 200
    BUS_TOP = STRIP_TOP + 0
    BUS_BOT = STRIP_TOP + N_ROWS * ROW_H - ROW_H // 2

    gnd_sym(d, BUS_X2, BUS_TOP - 50)
    d.line([(BUS_X2, BUS_TOP - 50 + 53), (BUS_X2, BUS_BOT)], fill=C["rtd_w"], width=3)
    gnd_sym(d, BUS_X2, BUS_BOT + 8, label="EEGND")

    # RSENSE between BUS and CH1 wire
    _, ch1y = term_cys2[1]
    _, ch2y = term_cys2[2]
    RSENSE_X = BUS_X2 - 80
    d.line([(BUS_X2, ch1y), (RSENSE_X, ch1y)], fill=C["rtd_w"], width=3)
    d.line([(BUS_X2, ch2y), (RSENSE_X, ch2y)], fill=C["rtd_w"], width=3)
    d.line([(RSENSE_X, ch1y), (RSENSE_X, ch2y)], fill=C["rtd_w"], width=3)
    # RSENSE rectangle on the vertical segment
    rsm = (ch1y + ch2y) // 2
    bw_rs = 18
    pad_rs = (ch2y - ch1y) // 4
    d.rectangle([RSENSE_X - bw_rs, ch1y + pad_rs, RSENSE_X + bw_rs, ch2y - pad_rs],
                outline=C["rtd_w"], width=2, fill="#FFFFFF")
    d.text((RSENSE_X + bw_rs + 6, rsm - 18), "2.00 kΩ", fill=C["rtd_w"], font=F(13, bold=True))
    d.text((RSENSE_X + bw_rs + 6, rsm + 2), "RSENSE —", fill=C["muted"], font=F(12))
    d.text((RSENSE_X + bw_rs + 6, rsm + 16), "firmware CH1", fill=C["muted"], font=F(12))

    # Horizontal wire CH1 to terminal left edge
    d.line([(RSENSE_X, ch1y), (TCOL_L, ch1y)], fill=C["rtd_w"], width=3)
    dot(d, BUS_X2, ch1y, color=C["rtd_w"])

    # EEGND label near CH1
    d.text((TCOL_L - 90, ch1y - 18), "EEGND", fill=C["gnd"], font=F(13, bold=True))

    # 5 RTD symbols between adjacent channels (CH2-CH3, CH3-CH4, ..., CH6-CH7)
    rtd_labels = [
        ("PT1000 RTD #1 (CJC)", "RTD1 / CJC —\nfirmware CH3"),
        ("PT1000 RTD #2", "RTD2 —\nfirmware CH4"),
        ("PT1000 RTD #3", "RTD3 —\nfirmware CH5"),
        ("PT1000 RTD #4", "RTD4 —\nfirmware CH6"),
        ("PT1000 RTD #5", "RTD5 —\nfirmware CH7"),
    ]
    RTD_X = BUS_X2 + 100

    for idx, (rtd_top_ch, rtd_bot_ch) in enumerate([(2,3),(3,4),(4,5),(5,6),(6,7)]):
        _, top_y = term_cys2[rtd_top_ch]
        _, bot_y = term_cys2[rtd_bot_ch]
        lbl_top, lbl_sub = rtd_labels[idx]

        # Vertical RTD symbol
        rtd_sym_v(d, RTD_X, top_y, bot_y, color=C["rtd_w"])

        # Horizontal wires from bus to RTD
        d.line([(BUS_X2, top_y), (RTD_X, top_y)], fill=C["rtd_w"], width=3)
        d.line([(BUS_X2, bot_y), (RTD_X, bot_y)], fill=C["rtd_w"], width=3)

        # Horizontal wire from RTD left to terminal
        d.line([(TCOL_L, top_y), (BUS_X2, top_y)], fill=C["rtd_w"], width=2)
        dot(d, BUS_X2, top_y, color=C["rtd_w"])

        # Label to left of RTD
        lbl_x = RTD_SECX0 + 14
        mid_y = (top_y + bot_y) // 2
        d.text((lbl_x, mid_y - 22), lbl_top, fill=C["rtd_lbl"], font=F(13, bold=True))
        for li, ln in enumerate(lbl_sub.replace("\n", "|").split("|")):
            d.text((lbl_x, mid_y + li * 16), ln, fill=C["muted"], font=F(12))

    # Wire from CH7 terminal back to bus (bottom of chain)
    _, ch7y = term_cys2[7]
    d.line([(TCOL_L, ch7y), (BUS_X2, ch7y)], fill=C["rtd_w"], width=3)
    dot(d, BUS_X2, ch7y, color=C["rtd_w"])

    # ── TC section (right red solid box) ─────────────────────────────────
    TC_SECX0 = TCOL_R + TW2 + 10
    TC_SECX1 = W - 60
    dashed_rect(d, (TC_SECX0, 290, TC_SECX1, STRIP_TOP + N_ROWS * ROW_H + 20),
                fill=C["tc_f"], border=C["tc_b"], dash=0)  # solid
    # Actually use solid border:
    d.rectangle([TC_SECX0, 290, TC_SECX1, STRIP_TOP + N_ROWS * ROW_H + 20],
                fill=C["tc_f"], outline=C["tc_b"])
    d.rectangle([TC_SECX0, 290, TC_SECX1, STRIP_TOP + N_ROWS * ROW_H + 20],
                outline=C["tc_b"], width=2)
    d.text((TC_SECX0 + 12, 298), "5× K-TYPE THERMOCOUPLES",
           fill=C["tc_lbl"], font=F(17, bold=True))

    # TC section: 5 TCs, each spanning two adjacent rows of the terminal strip
    # Row mapping: CH8=row8, CH9=row9 (left col), CH10=row10 left, CH11=row1 right, etc.
    # Instead of matching to strip rows (which don't align), we space TCs evenly.
    TC_SYM_X = TC_SECX0 + 220  # x center of all TC circles
    TC_BOX_X = TC_SECX0 + 12   # x of CH label boxes
    tc_pairs = [(8, 9), (10, 11), (12, 13), (14, 15), (16, 17)]
    TC_SECTION_TOP = STRIP_TOP + ROW_H
    TC_SECTION_H = (N_ROWS - 2) * ROW_H  # rows 2-9 for TCs
    TC_SLOT = TC_SECTION_H // 5

    for tc_idx, (pos_ch, neg_ch) in enumerate(tc_pairs):
        tc_label = f"TC{tc_idx + 1}"
        tc_cy = TC_SECTION_TOP + tc_idx * TC_SLOT + TC_SLOT // 2

        # y positions in terminal strip for the two channels
        _, wy_p = term_cys2[pos_ch]
        _, wy_n = term_cys2[neg_ch]

        # TC circle
        tc_sym(d, TC_SYM_X, tc_cy, r=24)
        d.text((TC_SYM_X - 18, tc_cy - 52), tc_label, fill=C["tc_lbl"], font=F(15, bold=True))

        # Channel label boxes (colored rounded rects) at terminal y
        for ch_n, wy_ch, col in [(pos_ch, wy_p, C["tc_pos"]), (neg_ch, wy_n, C["tc_neg"])]:
            d.rounded_rectangle([TC_BOX_X, wy_ch - 11, TC_BOX_X + 46, wy_ch + 11],
                                radius=4, fill=col, outline=col)
            lbl2 = f"CH{ch_n}"
            tw4 = d.textlength(lbl2, font=F(13, bold=True))
            d.text((TC_BOX_X + (46 - tw4) / 2, wy_ch - 9), lbl2,
                   fill="#FFFFFF", font=F(13, bold=True))

        # Route wires: from terminal right edge → TC circle
        wx_p, _ = term_cys2[pos_ch]
        wx_n, _ = term_cys2[neg_ch]
        route_x = TC_BOX_X + 60 + tc_idx * 14

        # Positive (red)
        d.line([(wx_p, wy_p), (route_x, wy_p)], fill=C["tc_pos"], width=3)
        d.line([(route_x, wy_p), (route_x, tc_cy - 12)], fill=C["tc_pos"], width=3)
        d.line([(route_x, tc_cy - 12), (TC_SYM_X - 24, tc_cy - 12)], fill=C["tc_pos"], width=3)

        # Negative (yellow)
        rn_x = route_x + 8
        d.line([(wx_n, wy_n), (rn_x, wy_n)], fill=C["tc_neg"], width=3)
        d.line([(rn_x, wy_n), (rn_x, tc_cy + 12)], fill=C["tc_neg"], width=3)
        d.line([(rn_x, tc_cy + 12), (TC_SYM_X - 24, tc_cy + 12)], fill=C["tc_neg"], width=3)

        # Labels right of circle
        d.text((TC_SYM_X + 32, tc_cy - 24), "TC+ (Type-K)", fill=C["tc_pos"], font=F(13))
        d.text((TC_SYM_X + 32, tc_cy + 6),  "TC− (Type-K)", fill=C["tc_neg"], font=F(13))

    # Unused CH18-20
    for ch_u in (18, 19, 20):
        _, uy = term_cys2[ch_u]
        d.text((TC_SECX0 + 14, uy - 9), "unused", fill=C["muted"], font=F(13))

    # Notes
    note_y2 = STRIP_TOP + N_ROWS * ROW_H + 30
    d.text((TC_SECX0 + 12, note_y2),
           "NOTE 1: CJC = RTD1 at CH2/CH3 junction,", fill=C["muted"], font=F(13))
    d.text((TC_SECX0 + 12, note_y2 + 16),
           "firmware CJC pointer = CH2", fill=C["muted"], font=F(13))
    d.text((TC_SECX0 + 12, note_y2 + 34),
           "NOTE 2: CH18, CH19, CH20 — unused", fill=C["muted"], font=F(13))

    # ── Bottom tables ─────────────────────────────────────────────────────
    SEC_BOT = STRIP_TOP + N_ROWS * ROW_H + 60  # just below circuit section + notes
    T0_5 = SEC_BOT + 50
    T1_5 = T0_5 + 180

    fw_table(d, (60, T0_5, 1260, T1_5),
             col_headers=["CH1", "CH3–CH7", "CH8,10,12,14,16",
                          "CH9,11,13,15,17", "CH18,19,20"],
             row_data=[
                 ["2kΩ RSENSE", "PT1000 2-wire|(RTD1–5)",
                  "Type-K TC (+)", "Type-K TC (−)", "Unused"],
             ])

    def sym_rtd2(d, x, y):
        rtd_sym_h(d, x, y, x + 64, label="", color=C["rtd_w"])

    def sym_res2(d, x, y):
        d.line([(x, y), (x + 14, y)], fill=C["rtd_w"], width=2)
        d.rectangle([x + 14, y - 7, x + 52, y + 7], outline=C["rtd_w"], width=2, fill="#FFFFFF")
        d.line([(x + 52, y), (x + 68, y)], fill=C["rtd_w"], width=2)

    def sym_tc2(d, x, y):
        tc_sym(d, x + 22, y, r=18)

    def sym_gnd2(d, x, y):
        gnd_sym(d, x + 22, y - 10, label="")

    legend_table(d, (1280, T0_5, W - 60, T1_5),
                 wire_entries=[
                     (C["rtd_w"],  "RTD chain / excitation (shared)"),
                     (C["tc_pos"], "Thermocouple positive (TC+)"),
                     (C["tc_neg"], "Thermocouple negative (TC−)"),
                     (C["gnd"],    "Ground (EEGND)"),
                 ],
                 sym_entries=[
                     ("PT1000 RTD (2-wire)", sym_rtd2),
                     ("2.00 kΩ Resistor (RSENSE)", sym_res2),
                     ("Type-K Thermocouple", sym_tc2),
                     ("EEGND (Earth / Shield Ground)", sym_gnd2),
                 ])

    img.save(OUT / "dc2210a-5rtd-5tc-wiring.png", "PNG")
    print("wrote dc2210a-5rtd-5tc-wiring.png")


if __name__ == "__main__":
    draw_dc2213a_stick_dual_rtd()
    draw_dc2213a_dual_rtd()
    draw_dc2213a_pt1000()
    draw_dc2213a_rtd_simulator()
    draw_dc2210a_pt1000()
    draw_dc2210a_5rtd_5tc()
