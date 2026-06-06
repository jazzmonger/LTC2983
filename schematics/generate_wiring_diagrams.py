#!/usr/bin/env python3
"""
Schematic of record — CST Temp Module (DC2209A + DC2213A / LTC2983).
Drawn in the formal LTC demo-board drawing style (bordered frame, zone
markers, title block, notes block, IEC component symbols).

Run:  python3 schematics/generate_wiring_diagrams.py
Output: schematics/cst-temp-module-schematic.png
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(__file__).parent
OUTPUT = OUT / "cst-temp-module-schematic.png"

# Engineering-drawing palette: black on white, sparing accent.
K = "#000000"
WHITE = "#FFFFFF"
GREY = "#666666"
NETBLUE = "#0B3D91"


def F(n, bold=False):
    cands = (
        ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/Library/Fonts/Arial Bold.ttf"]
        if bold else
        ["/System/Library/Fonts/Supplemental/Arial.ttf",
         "/Library/Fonts/Arial.ttf"]
    )
    for p in cands:
        try:
            return ImageFont.truetype(p, n)
        except OSError:
            pass
    return ImageFont.load_default()


def MONO(n):
    for p in ["/System/Library/Fonts/Menlo.ttc",
              "/System/Library/Fonts/Courier.ttc"]:
        try:
            return ImageFont.truetype(p, n)
        except OSError:
            pass
    return F(n)


def ctext(d, cx, y, s, font, fill=K):
    w = d.textlength(s, font=font)
    d.text((cx - w / 2, y), s, font=font, fill=fill)


# ── Drawing frame (zone-marked border + title block) ─────────────────────────

def draw_frame(d, W, H):
    m = 26
    d.rectangle([m, m, W - m, H - m], outline=K, width=2)
    inb = m + 14
    d.rectangle([inb, inb, W - inb, H - inb], outline=K, width=1)

    cols = 6  # zone columns 6..1 left→right
    rows = 4  # zone rows A..D (bottom→top in LTC; we label top→bottom D..A)
    cw = (W - 2 * inb) / cols
    rh = (H - 2 * inb) / rows
    fz = F(13, bold=True)
    for i in range(cols):
        label = str(cols - i)
        cx = inb + cw * (i + 0.5)
        ctext(d, cx, m + 1, label, fz)
        ctext(d, cx, H - m - 14, label, fz)
    for j in range(rows):
        label = "DCBA"[j]
        cy = inb + rh * (j + 0.5) - 7
        ctext(d, m + 7, cy, label, fz)
        ctext(d, W - m - 7, cy, label, fz)
    return inb


def draw_title_block(d, x1, y1):
    """Bottom-right title block in LTC style. x1,y1 = bottom-right corner."""
    bw, bh = 560, 168
    x0, y0 = x1 - bw, y1 - bh
    d.rectangle([x0, y0, x1, y1], outline=K, width=2)

    # horizontal dividers
    rows_y = [y0 + 92, y0 + 122]
    for ry in rows_y:
        d.line([(x0, ry), (x1, ry)], fill=K, width=1)
    # vertical split in lower rows
    midx = x0 + 360
    d.line([(midx, rows_y[0]), (midx, y1)], fill=K, width=1)

    d.text((x0 + 12, y0 + 10), "TITLE:", font=F(12, bold=True), fill=K)
    d.text((x0 + 16, y0 + 34), "CST TEMP MODULE — LTC2983",
           font=F(20, bold=True), fill=K)
    d.text((x0 + 16, y0 + 62), "RTD SIMULATOR + DAISY RTD + TYPE-K TC",
           font=F(13), fill=K)

    # lower-left cells
    d.text((x0 + 8, rows_y[0] + 5), "SIZE", font=F(10, bold=True), fill=GREY)
    d.text((x0 + 8, rows_y[0] + 18), "B", font=F(14, bold=True), fill=K)
    d.text((x0 + 70, rows_y[0] + 5), "IC NO.", font=F(10, bold=True), fill=GREY)
    d.text((x0 + 70, rows_y[0] + 18), "LTC2983", font=F(13, bold=True), fill=K)
    d.text((x0 + 210, rows_y[0] + 5), "REV.", font=F(10, bold=True), fill=GREY)
    d.text((x0 + 210, rows_y[0] + 18), "A", font=F(13, bold=True), fill=K)

    d.text((x0 + 8, rows_y[1] + 4), "DATE: 06/06/2026", font=F(11), fill=K)
    d.text((x0 + 8, rows_y[1] + 22), "DC2209A + DC2213A", font=F(11), fill=K)

    # lower-right cells
    d.text((midx + 10, rows_y[0] + 5), "SHEET", font=F(10, bold=True), fill=GREY)
    d.text((midx + 10, rows_y[0] + 18), "1  OF  1", font=F(13, bold=True), fill=K)
    d.text((midx + 10, rows_y[1] + 4), "ESPHome branch: 2210A-board", font=F(11), fill=K)
    d.text((midx + 10, rows_y[1] + 22), "SCALE = NONE", font=F(11), fill=K)


def draw_notes(d, x0, y0):
    bw, bh = 470, 96
    d.rectangle([x0, y0, x0 + bw, y0 + bh], outline=K, width=1)
    d.text((x0 + 10, y0 + 8), "NOTE: UNLESS OTHERWISE SPECIFIED",
           font=F(12, bold=True), fill=K)
    d.text((x0 + 10, y0 + 30), "1. ALL CAPACITORS ARE IN MICROFARADS.",
           font=F(12), fill=K)
    d.text((x0 + 10, y0 + 48), "2. ALL RESISTORS ARE IN OHMS.",
           font=F(12), fill=K)
    d.text((x0 + 10, y0 + 66), "3. TC ASSIGNED/READ ON CH13 (DIFF CH13−CH12).",
           font=F(12), fill=K)


# ── IEC component symbols (black, schematic style) ───────────────────────────

def net_flag(d, x, y, name, side="left"):
    """Small net-label flag (like CHx labels in the LTC sheet)."""
    f = F(13, bold=True)
    w = d.textlength(name, font=f) + 14
    h = 22
    if side == "left":
        pts = [(x, y), (x - 12, y - h / 2), (x - 12 - w, y - h / 2),
               (x - 12 - w, y + h / 2), (x - 12, y + h / 2)]
        d.polygon(pts, outline=K, fill=WHITE)
        d.text((x - 10 - w, y - 8), name, font=f, fill=NETBLUE)
    else:
        pts = [(x, y), (x + 12, y - h / 2), (x + 12 + w, y - h / 2),
               (x + 12 + w, y + h / 2), (x + 12, y + h / 2)]
        d.polygon(pts, outline=K, fill=WHITE)
        d.text((x + 16, y - 8), name, font=f, fill=NETBLUE)


def res_h(d, x0, y, x1, ref, val, sub=""):
    """Horizontal resistor (IEC box)."""
    bl, br = x0 + (x1 - x0) * 0.28, x1 - (x1 - x0) * 0.28
    bh = 12
    d.line([(x0, y), (bl, y)], fill=K, width=2)
    d.rectangle([bl, y - bh, br, y + bh], outline=K, width=2, fill=WHITE)
    d.line([(br, y), (x1, y)], fill=K, width=2)
    cx = (bl + br) / 2
    ctext(d, cx, y - bh - 30, ref, F(13, bold=True))
    ctext(d, cx, y - bh - 15, val, F(12))
    if sub:
        ctext(d, cx, y + bh + 4, sub, F(11), fill=GREY)


def res_v(d, x, y0, y1, ref, val, sub=""):
    """Vertical resistor."""
    bt, bb = y0 + (y1 - y0) * 0.28, y1 - (y1 - y0) * 0.28
    bw = 12
    d.line([(x, y0), (x, bt)], fill=K, width=2)
    d.rectangle([x - bw, bt, x + bw, bb], outline=K, width=2, fill=WHITE)
    d.line([(x, bb), (x, y1)], fill=K, width=2)
    cy = (bt + bb) / 2
    d.text((x + bw + 8, cy - 22), ref, font=F(13, bold=True), fill=K)
    d.text((x + bw + 8, cy - 6), val, font=F(12), fill=K)
    if sub:
        d.text((x + bw + 8, cy + 10), sub, font=F(11), fill=GREY)


def cap_v(d, x, y0, y1, ref, val):
    """Vertical capacitor to (usually) ground."""
    mid = (y0 + y1) / 2
    g = 7
    d.line([(x, y0), (x, mid - g)], fill=K, width=2)
    d.line([(x - 16, mid - g), (x + 16, mid - g)], fill=K, width=2)
    d.line([(x - 16, mid + g), (x + 16, mid + g)], fill=K, width=2)
    d.line([(x, mid + g), (x, y1)], fill=K, width=2)
    d.text((x + 22, mid - 18), ref, font=F(13, bold=True), fill=K)
    d.text((x + 22, mid - 1), val, font=F(12), fill=K)


def gnd(d, x, y, label="EEGND"):
    d.line([(x, y), (x, y + 12)], fill=K, width=2)
    d.line([(x - 18, y + 12), (x + 18, y + 12)], fill=K, width=2)
    d.line([(x - 11, y + 19), (x + 11, y + 19)], fill=K, width=2)
    d.line([(x - 5, y + 26), (x + 5, y + 26)], fill=K, width=2)
    if label:
        ctext(d, x, y + 30, label, F(11), fill=GREY)


def pot_h(d, x0, y, x1, ref, val):
    """Horizontal potentiometer: body with wiper arrow up."""
    bl, br = x0 + 34, x1 - 34
    bh = 16
    d.line([(x0, y), (bl, y)], fill=K, width=2)
    d.rectangle([bl, y - bh, br, y + bh], outline=K, width=2, fill=WHITE)
    d.line([(br, y), (x1, y)], fill=K, width=2)
    wx = (bl + br) / 2
    d.line([(wx, y - bh - 30), (wx, y - bh - 6)], fill=K, width=2)
    d.polygon([(wx, y - bh - 4), (wx - 7, y - bh - 16), (wx + 7, y - bh - 16)], fill=K)
    ctext(d, (bl + br) / 2, y - bh - 52, ref, F(13, bold=True))
    ctext(d, (bl + br) / 2, y - bh - 37, val, F(12))
    d.text((bl - 14, y + bh + 4), "1,3", font=F(10), fill=GREY)
    d.text((wx - 6, y - bh - 70), "2", font=F(10), fill=GREY)


def rtd_h(d, x0, y, x1, ref, val):
    """RTD: resistor box with diagonal arrow through it."""
    bl, br = x0 + (x1 - x0) * 0.25, x1 - (x1 - x0) * 0.25
    bh = 14
    d.line([(x0, y), (bl, y)], fill=K, width=2)
    d.rectangle([bl, y - bh, br, y + bh], outline=K, width=2, fill=WHITE)
    d.line([(br, y), (x1, y)], fill=K, width=2)
    # diagonal arrow
    ax0, ay0 = bl - 6, y + bh + 10
    ax1, ay1 = br + 6, y - bh - 10
    d.line([(ax0, ay0), (ax1, ay1)], fill=K, width=2)
    d.polygon([(ax1, ay1), (ax1 - 12, ay1 + 3), (ax1 - 4, ay1 + 12)], fill=K)
    cx = (bl + br) / 2
    ctext(d, cx, y - bh - 32, ref, F(13, bold=True))
    ctext(d, cx, y - bh - 17, val, F(12))


def thermocouple(d, x, y, ref):
    """Type-K thermocouple connector J2 with + / - terminals."""
    # connector body
    d.rectangle([x, y - 34, x + 56, y + 34], outline=K, width=2, fill=WHITE)
    d.text((x + 8, y - 50), ref, font=F(13, bold=True), fill=K)
    d.text((x + 8, y - 64), "TYPE-K", font=F(11), fill=GREY)
    # junction triangle (two dissimilar metals)
    jx = x + 56
    d.text((x + 64, y - 24), "+", font=F(15, bold=True), fill=K)
    d.text((x + 64, y + 8), "−", font=F(15, bold=True), fill=K)
    return (x, y - 18), (x, y + 18)  # +,- pin coords (left side)


# ── IC block ────────────────────────────────────────────────────────────────

def draw_ic(d, x0, y0, x1, y1, pins_right):
    d.rectangle([x0, y0, x1, y1], outline=K, width=2, fill=WHITE)
    d.text((x0 + 14, y0 + 12), "U2", font=F(15, bold=True), fill=K)
    d.text((x0 + 14, y0 + 34), "LTC2983", font=F(18, bold=True), fill=K)
    d.text((x0 + 14, y0 + 58), "MULTI-SENSOR", font=F(11), fill=GREY)
    d.text((x0 + 14, y0 + 73), "TEMP-TO-BITS", font=F(11), fill=GREY)
    # SPI pins on left
    spi = [("CS / GPIO2", 0), ("SCK / GPIO9", 1), ("SDI / GPIO5", 2), ("SDO / GPIO4", 3)]
    base = y1 - 18
    coords = {}
    for name, i in spi:
        yy = base - i * 26
        d.line([(x0 - 26, yy), (x0, yy)], fill=K, width=2)
        d.text((x0 - 24, yy - 22), name, font=F(10), fill=K)
        coords[name] = (x0 - 26, yy)
    # channel pins on right
    pin_y = {}
    for name, yy in pins_right:
        d.line([(x1, yy), (x1 + 26, yy)], fill=K, width=2)
        d.text((x1 - 52, yy - 8), name, font=F(12, bold=True), fill=K)
        pin_y[name] = (x1 + 26, yy)
    return coords, pin_y


def draw_schematic():
    W, H = 2400, 1500
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    inb = draw_frame(d, W, H)

    # Channel pin layout on the IC (right side). Explicit Y groups so the
    # RTD set and the TC pair are visually separated.
    ic_x0, ic_y0, ic_x1, ic_y1 = 110, 230, 360, 1180
    pins_right = [
        ("CH1", 300), ("CH2", 360),          # return pair
        ("CH3", 470), ("CH4", 590), ("CH5", 700),   # RTD network
        ("CH12", 950), ("CH13", 1050),       # thermocouple pair
    ]
    _, P = draw_ic(d, ic_x0, ic_y0, ic_x1, ic_y1, pins_right)

    def py(ch):
        return P[ch][1]

    def px():
        return ic_x1 + 26

    # ESP32 microcontroller block (top-left, drives SPI)
    d.rectangle([110, 90, 360, 200], outline=K, width=2, fill=WHITE)
    d.text((122, 100), "U1  ESP32-S3", font=F(15, bold=True), fill=K)
    d.text((122, 124), "CST TEMP MODULE", font=F(11), fill=GREY)
    d.text((122, 150), "SPI MASTER → U2", font=F(11), fill=K)
    d.line([(235, 200), (235, 215), (ic_x0 - 26, 215),
            (ic_x0 - 26, ic_y1 - 18)], fill=K, width=2)

    # ── Common RSENSE / return network ───────────────────────────────────
    busx = 560
    # CH1 + CH2 tie
    d.line([(px(), py("CH1")), (busx, py("CH1"))], fill=K, width=2)
    d.line([(px(), py("CH2")), (busx, py("CH2"))], fill=K, width=2)
    d.line([(busx, py("CH1")), (busx, py("CH2"))], fill=K, width=2)
    d.ellipse([busx - 4, py("CH2") - 4, busx + 4, py("CH2") + 4], fill=K)
    midret = (py("CH1") + py("CH2")) // 2
    d.text((busx - 150, midret - 8), "CH1+CH2", font=F(11), fill=GREY)
    # C1 from tie to gnd
    c1x = busx
    cap_v(d, c1x, midret, midret + 90, "C1", "0.01")
    gnd(d, c1x, midret + 90)

    # RSENSE between CH2 hub and CH3
    rs_x = 720
    d.line([(busx, py("CH2")), (rs_x, py("CH2"))], fill=K, width=2)
    res_v(d, rs_x, py("CH2"), py("CH3"), "RSENSE", "2k", "1/8W")
    d.line([(px(), py("CH3")), (rs_x, py("CH3"))], fill=K, width=2)
    d.ellipse([rs_x - 4, py("CH3") - 4, rs_x + 4, py("CH3") + 4], fill=K)
    # C2 on CH3
    cap_v(d, rs_x + 120, py("CH3"), py("CH3") + 90, "C2", "0.01")
    d.line([(rs_x, py("CH3")), (rs_x + 120, py("CH3"))], fill=K, width=2)
    gnd(d, rs_x + 120, py("CH3") + 90)

    hubx = 900
    d.line([(rs_x, py("CH3")), (hubx, py("CH3"))], fill=K, width=2)
    d.ellipse([hubx - 5, py("CH3") - 5, hubx + 5, py("CH3") + 5], fill=K)
    d.text((hubx - 30, py("CH3") + 14), "CH2/CH3 HUB", font=F(11, bold=True), fill=GREY)

    # ── Daisy-chain RTD network (linear excitation path) ───────────────────
    # Physical wiring:  HUB → R6 → CH4 screw → RT1 → CH5 screw
    # LTC2983 reads each RTD as the element between adjacent channels.
    chain_y = (py("CH4") + py("CH5")) // 2
    r6_l, r6_r = hubx + 80, hubx + 380
    ch4_node = r6_r + 100
    rt_l, rt_r = ch4_node + 40, ch4_node + 340
    ch5_node = rt_r + 40

    # hub → R6 (first RTD element: onboard simulator)
    d.line([(hubx, py("CH3")), (hubx, chain_y), (r6_l, chain_y)], fill=K, width=2)
    pot_h(d, r6_l, chain_y, r6_r, "R6", "10k")
    d.text((r6_l, chain_y + 34), "pins 1+3 ← HUB", font=F(10), fill=GREY)
    d.text((r6_r - 30, chain_y + 34), "pin 2 → CH4", font=F(10), fill=GREY)

    # R6 wiper → CH4 node
    d.line([(r6_r, chain_y), (ch4_node, chain_y)], fill=K, width=2)
    d.ellipse([ch4_node - 5, chain_y - 5, ch4_node + 5, chain_y + 5], fill=K)
    d.line([(ch4_node, chain_y), (ch4_node, py("CH4")), (px(), py("CH4"))], fill=K, width=2)
    net_flag(d, ch4_node, chain_y - 18, "CH4", side="left")

    # C6 filter on CH4
    cap_v(d, ch4_node + 30, py("CH4"), py("CH4") + 80, "C6", "0.01")
    d.line([(ch4_node, py("CH4")), (ch4_node + 30, py("CH4"))], fill=K, width=2)
    gnd(d, ch4_node + 30, py("CH4") + 80)

    # CH4 → RT1 → CH5 (second RTD element: external PT1000)
    d.line([(ch4_node, chain_y), (rt_l, chain_y)], fill=K, width=2)
    rtd_h(d, rt_l, chain_y, rt_r, "RT1", "PT1000")
    d.line([(rt_r, chain_y), (ch5_node, chain_y)], fill=K, width=2)
    d.ellipse([ch5_node - 5, chain_y - 5, ch5_node + 5, chain_y + 5], fill=K)
    d.line([(ch5_node, chain_y), (ch5_node, py("CH5")), (px(), py("CH5"))], fill=K, width=2)
    net_flag(d, ch5_node, chain_y - 18, "CH5", side="left")

    # Terminal labels on RT1
    d.text((rt_l - 8, chain_y + 22), "← CH4 screw", font=F(10, bold=True), fill=NETBLUE)
    d.text((rt_r - 52, chain_y + 22), "CH5 screw →", font=F(10, bold=True), fill=NETBLUE)

    # Excitation flow arrow (above chain)
    arr_y = chain_y - 55
    d.line([(hubx, arr_y), (ch5_node, arr_y)], fill=GREY, width=1)
    d.polygon([(ch5_node, arr_y), (ch5_node - 14, arr_y - 6), (ch5_node - 14, arr_y + 6)], fill=GREY)
    ctext(d, (hubx + ch5_node) // 2, arr_y - 18,
          "100 µA excitation:  HUB → R6 → CH4 → RT1 → CH5 → RSENSE → GND",
          F(11), fill=GREY)

    # RTD section outline
    d.rectangle([hubx + 50, chain_y - 110, ch5_node + 80, chain_y + 70],
                outline=GREY, width=1)
    d.text((hubx + 60, chain_y - 106),
           "RTD DAISY CHAIN  —  PT1000 2-WIRE 100 µA  (shared CH2 RSENSE)",
           font=F(12, bold=True), fill=GREY)
    d.text((hubx + 60, chain_y + 52),
           "ESPHome:  RTD CH4 = R6 simulator   |   RTD CH5 = external PT1000 on RT1",
           font=F(10), fill=GREY)

    # ── Thermocouple: J2 + → CH12, − → CH13 + EEGND ──────────────────────
    tc_x = hubx + 180
    tc_y = (py("CH12") + py("CH13")) // 2 + 30
    pplus, pminus = thermocouple(d, tc_x, tc_y, "J2")
    # + terminal to CH12
    d.line([(tc_x, tc_y - 18), (tc_x - 60, tc_y - 18),
            (tc_x - 60, py("CH12")), (px(), py("CH12"))], fill=K, width=2)
    # - terminal to CH13 and to ground
    d.line([(tc_x, tc_y + 18), (tc_x - 110, tc_y + 18),
            (tc_x - 110, py("CH13")), (px(), py("CH13"))], fill=K, width=2)
    d.ellipse([tc_x - 114, py("CH13") - 4, tc_x - 106, py("CH13") + 4], fill=K)
    d.line([(tc_x - 110, py("CH13")), (tc_x - 110, py("CH13") + 60)], fill=K, width=2)
    gnd(d, tc_x - 110, py("CH13") + 60)

    d.rectangle([hubx + 50, py("CH12") - 70, hubx + 420, py("CH13") + 110],
                outline=GREY, width=1)
    d.text((hubx + 60, py("CH12") - 66),
           "THERMOCOUPLE  —  TYPE-K DIFF (READ CH13)",
           font=F(12, bold=True), fill=GREY)
    d.text((hubx + 60, py("CH13") + 86),
           "FIRMWARE POLARITY:  TC = 2·RTD_CH4 − RAW   (CJC = CH4)",
           font=F(10), fill=GREY)

    # ── Notes + title block ──────────────────────────────────────────────
    draw_notes(d, inb + 20, H - inb - 130)
    draw_title_block(d, W - inb - 8, H - inb - 8)

    img.save(OUTPUT, "PNG")
    print(f"wrote {OUTPUT.name}")


if __name__ == "__main__":
    draw_schematic()
