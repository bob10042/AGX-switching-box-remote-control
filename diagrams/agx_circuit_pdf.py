#!/usr/bin/env python3
"""AGX Test Box - multi-page PDF block diagram.
Phase A=RED, B=BROWN, C=GREY, Neutral=BLACK (broad).
Supply rails +24VDC and 0V clearly marked.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import os

OUT = os.path.join(r"C:\Users\bob43\Downloads", "AGX_Test_Box_Circuit.pdf")

# ── Colours ──
C_BLUE    = '#1A237E'
C_DKBLUE  = '#0D47A1'
C_LTBLUE  = '#E3F2FD'
C_ORANGE  = '#FFF3E0'
C_GREEN   = '#E8F5E9'
C_DKGREEN = '#2E7D32'
C_RED_BG  = '#FFEBEE'
C_DKRED   = '#C62828'
C_PURPLE  = '#F3E5F5'
C_YELLOW  = '#FFFDE7'
C_GREY_BG = '#F5F5F5'
C_WIRE    = '#333333'
C_LGREY   = '#9E9E9E'

# Phase wire colours
C_PH_A  = '#CC0000'   # RED
C_PH_B  = '#8B4513'   # BROWN
C_PH_C  = '#696969'   # GREY
C_NEUT  = '#000000'   # BLACK
C_RAIL  = '#D50000'   # +24V rail colour
C_RAIL0 = '#1565C0'   # 0V rail colour

# Line widths (thicker per user request)
LW    = 3.5    # block border
LW_W  = 3.0    # signal wire
LW_PW = 5.0    # power/phase wire
LW_N  = 7.0    # neutral wire (broader)
LW_RL = 2.5    # supply rail


def new_page(pdf, title, subtitle=""):
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    ax.set_xlim(0, 11.69); ax.set_ylim(0, 8.27)
    ax.set_aspect('equal'); ax.axis('off')
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    ax.add_patch(mpatches.Rectangle((0, 7.6), 11.69, 0.67,
                 facecolor=C_BLUE, edgecolor='none'))
    ax.text(5.85, 7.97, title, ha='center', va='center',
            fontsize=20, fontweight='bold', color='white')
    if subtitle:
        ax.text(5.85, 7.72, subtitle, ha='center', va='center',
                fontsize=11, color='#B3E5FC')
    ax.text(5.85, 0.12,
            "DISCUSSION DOCUMENT  |  Rev 3.0  |  2026-03-19",
            ha='center', va='center', fontsize=7, color=C_LGREY, style='italic')
    return fig, ax


def block(ax, x, y, w, h, title, color=C_LTBLUE, border=C_BLUE, title_size=13):
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.08", facecolor=color,
                 edgecolor=border, linewidth=LW))
    ax.text(x + w/2, y + h - 0.15, title, ha='center', va='top',
            fontsize=title_size, fontweight='bold', color=border)


def wire(ax, x1, y1, x2, y2, color=C_WIRE, lw=LW_W):
    ax.plot([x1, x2], [y1, y2], '-', color=color, linewidth=lw,
            solid_capstyle='round', zorder=3)


def dot(ax, x, y, color, sz=9):
    ax.plot(x, y, 'o', color=color, markersize=sz, zorder=5)


def text_list(ax, x, y, items, spacing=0.18, gap=0.08):
    for text, color, is_header in items:
        if not text:
            y -= gap
            continue
        ax.text(x, y, text, ha='left', va='center',
                fontsize=8.5 if is_header else 7.5,
                fontweight='bold' if is_header else 'normal',
                color=color, fontfamily='monospace')
        y -= spacing
    return y


# ══════════════════════════════════════════
# PAGE 1: POWER PATH
# ══════════════════════════════════════════

def page_power_path(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX — POWER PATH",
        "FORM 3: 3-phase 40A/phase  |  FORM 1: 1-phase 125A commoned  |  Supply rails marked")

    phases = [
        ('A', 6.6, C_PH_A),
        ('B', 5.5, C_PH_B),
        ('C', 4.4, C_PH_C),
    ]

    # ─── AGX SOURCE ───
    block(ax, 0.3, 1.5, 2.0, 5.7, "AGX POWER\nSOURCE", C_ORANGE, '#E65100', 14)
    ax.text(1.3, 3.8, "Pacific\nPower\nSource", ha='center', va='center',
            fontsize=10, color='#E65100', style='italic')

    agx_r = 2.4  # pin dot x (right of block)
    for ph, y, col in phases:
        dot(ax, agx_r, y, col)
        ax.text(agx_r - 0.15, y, f"Ph {ph}", ha='right', va='center',
                fontsize=10, fontweight='bold', color=col)
    # Neutral pin
    dot(ax, agx_r, 2.2, C_NEUT, 10)
    ax.text(agx_r - 0.15, 2.2, "N", ha='right', va='center',
            fontsize=11, fontweight='bold', color=C_NEUT)

    # ─── FORM 3 SECTION ───
    ax.text(6.0, 7.35, "FORM 3  —  THREE-PHASE  (40A per phase)",
            ha='center', va='center', fontsize=14, fontweight='bold', color=C_DKBLUE,
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.9, pad=0.1))

    bh = 0.75
    k3x, k3w = 4.3, 2.2
    ldx, ldw = 7.5, 2.0

    for ph, y, col in phases:
        by = y - bh / 2
        block(ax, k3x, by, k3w, bh, f"K3{ph}  (40A NO)", C_LTBLUE, C_BLUE, 12)
        block(ax, ldx, by, ldw, bh, f"Load {ph}  (40A)", C_PURPLE, '#7B1FA2', 12)
        ax.text(ldx + ldw - 0.12, by + 0.1, "N\u2193", ha='right', va='bottom',
                fontsize=8, color=C_NEUT, fontweight='bold')
        # Wires: AGX -> K3 (horizontal)
        wire(ax, agx_r, y, k3x - 0.05, y, col, LW_PW)
        # K3 -> Load (horizontal)
        wire(ax, k3x + k3w + 0.05, y, ldx - 0.05, y, col, LW_PW)
        # Phase label on wire
        ax.text((agx_r + k3x) / 2, y + 0.18, f"Phase {ph}",
                ha='center', va='bottom', fontsize=10, fontweight='bold', color=col,
                bbox=dict(facecolor='white', edgecolor=col, linewidth=1,
                          boxstyle='round,pad=0.05', alpha=0.95))

    # ─── FORM 1 SECTION ───
    ax.text(6.0, 3.85, "FORM 1  —  SINGLE-PHASE  (125A commoned)",
            ha='center', va='center', fontsize=14, fontweight='bold', color=C_DKRED,
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.9, pad=0.1))

    # Junction dots & wires to FORM 1 (routed in gap between AGX and K3 blocks)
    junctions = [
        ('A', 3.0, 6.6, C_PH_A, 3.0),
        ('B', 3.3, 5.5, C_PH_B, 2.55),
        ('C', 3.6, 4.4, C_PH_C, 2.1),
    ]
    f1x, f1w = 4.3, 2.2
    for ph, jx, jy, col, f1y in junctions:
        dot(ax, jx, jy, col)
        wire(ax, jx, jy, jx, f1y, col, LW_PW)
        wire(ax, jx, f1y, f1x - 0.05, f1y, col, LW_PW)
        ax.text(jx + 0.08, (jy + f1y) / 2, ph, ha='left', va='center',
                fontsize=9, fontweight='bold', color=col,
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=0.02))

    # FORM 1 combine
    block(ax, f1x, 1.7, f1w, 1.6, "FORM 1\nCOMBINE", C_RED_BG, C_DKRED, 12)
    ax.text(f1x + f1w/2, 2.05, "K1A+K1B+K1C\n(3\u00d7 40A NO)", ha='center', va='center',
            fontsize=9, color=C_DKRED)
    f1_out_x = f1x + f1w + 0.05
    spy = 2.55
    dot(ax, f1_out_x, spy, C_DKRED)

    # KSP
    block(ax, 7.0, 2.0, 1.5, 1.2, "KSP", '#FFF9C4', '#F57F17', 13)
    ax.text(7.75, 2.3, "125A NO", ha='center', va='center',
            fontsize=10, color='#F57F17', fontweight='bold')

    # 1-phase load
    block(ax, 9.0, 2.0, 1.3, 1.2, "1\u03A6 LOAD", C_PURPLE, '#7B1FA2', 12)
    ax.text(9.65, 2.3, "125A max", ha='center', va='center',
            fontsize=9, color='#7B1FA2')
    ax.text(10.15, 2.05, "N\u2193", ha='right', va='bottom',
            fontsize=8, color=C_NEUT, fontweight='bold')

    # FORM 1 wires
    wire(ax, f1_out_x, spy, 6.95, spy, C_DKRED, LW_PW)
    wire(ax, 8.55, spy, 8.95, spy, C_DKRED, LW_PW)
    ax.text((f1_out_x + 6.95) / 2, spy + 0.12, "SP_BUS",
            ha='center', va='bottom', fontsize=9, fontweight='bold', color=C_DKRED)

    # ─── NEUTRAL BUS (BLACK, BROAD) ───
    ny = 1.15
    wire(ax, agx_r, 2.2, agx_r, ny, C_NEUT, LW_N)
    wire(ax, agx_r, ny, 10.5, ny, C_NEUT, LW_N)
    ax.text(6.5, ny - 0.22,
            "NEUTRAL BUS  (common return \u2014 not switched \u2014 to all loads)",
            ha='center', va='top', fontsize=10, fontweight='bold', color=C_NEUT,
            bbox=dict(boxstyle='round,pad=0.12', facecolor='#E0E0E0',
                      edgecolor=C_NEUT, linewidth=2))

    # ─── INTERLOCK NOTE ───
    ax.text(10.7, 6.2,
            "INTERLOCK\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
            "K3 group and\nK1+KSP group\nMUTUALLY\nEXCLUSIVE\n\nNever both\nclosed!",
            ha='center', va='center', fontsize=9, fontweight='bold', color=C_DKRED,
            bbox=dict(boxstyle='round,pad=0.2', facecolor=C_RED_BG,
                      edgecolor=C_DKRED, linewidth=2))

    # ─── WIRE COLOUR LEGEND ───
    ly = 4.6
    ax.text(10.7, ly, "WIRE COLOURS", ha='center', va='center',
            fontsize=9, fontweight='bold', color='#424242')
    for lbl, c in [("Phase A = RED", C_PH_A), ("Phase B = BROWN", C_PH_B),
                    ("Phase C = GREY", C_PH_C), ("Neutral = BLACK", C_NEUT)]:
        ly -= 0.22
        ax.text(10.7, ly, lbl, ha='center', va='center',
                fontsize=8, fontweight='bold', color=c)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 2: CONTROL SYSTEM + SUPPLY RAILS
# ══════════════════════════════════════════

def page_control(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 CONTROL SYSTEM & SUPPLY RAILS",
        "ESP32 USB\u2192laptop  |  ULN2003 driver  |  +24VDC / 0V rails  |  Opto feedback")

    # ─── SUPPLY RAILS (top strip) ───
    # +24V rail
    wire(ax, 0.3, 7.35, 11.3, 7.35, C_RAIL, LW_RL)
    ax.text(0.3, 7.42, "+24VDC RAIL", ha='left', va='bottom',
            fontsize=9, fontweight='bold', color=C_RAIL)
    ax.text(11.3, 7.42, "(from 24V PSU)", ha='right', va='bottom',
            fontsize=8, color=C_RAIL, style='italic')
    # 0V rail
    wire(ax, 0.3, 7.15, 11.3, 7.15, C_RAIL0, LW_RL)
    ax.text(0.3, 7.08, "0V RAIL (GND)", ha='left', va='top',
            fontsize=9, fontweight='bold', color=C_RAIL0)

    # ─── ESP32 ───
    ex, ey, ew, eh = 0.3, 0.8, 3.8, 6.1
    block(ax, ex, ey, ew, eh, "ESP32 DevKit V1\n(USB \u2192 Laptop)", C_GREEN, C_DKGREEN, 13)
    er = ex + ew + 0.05

    text_list(ax, ex + 0.15, 6.45, [
        ("DRIVE OUTPUTS:", C_DKGREEN, True),
        ("GPIO25 \u2192 ULN IN1 (FORM3 K3)", C_DKGREEN, False),
        ("GPIO26 \u2192 ULN IN2 (K1 comb)", C_DKGREEN, False),
        ("GPIO27 \u2192 ULN IN3 (KSP out)", C_DKGREEN, False),
        ("", None, False),
        ("FEEDBACK INPUTS:", '#E65100', True),
        ("GPIO32 \u2190 K3 opto  (LOW=ON)", '#E65100', False),
        ("GPIO33 \u2190 K1 opto  (LOW=ON)", '#E65100', False),
        ("GPIO34 \u2190 KSP opto (LOW=ON)", '#E65100', False),
        ("GPIO35 \u2190 E-STOP  (LOW=act)", C_DKRED, False),
        ("", None, False),
        ("LED OUTPUTS:", C_DKBLUE, True),
        ("GPIO18 \u2192 330\u03A9 \u2192 GRN [FORM3]", C_DKGREEN, False),
        ("GPIO19 \u2192 330\u03A9 \u2192 BLU [FORM1]", C_DKBLUE, False),
        ("GPIO21 \u2192 330\u03A9 \u2192 RED [fault]", C_DKRED, False),
        ("", None, False),
        ("POWER:", '#424242', True),
        ("3.3V from USB | GND \u2192 0V rail", '#424242', False),
        ("", None, False),
        ("USB SERIAL 115200:", '#424242', True),
        (" '3'=FORM3  '1'=FORM1", '#424242', False),
        (" 'S'=status '0'=ALL OFF", '#424242', False),
    ])

    # Drive pin dots on right edge
    dys = [6.1, 5.7, 5.3]
    for y in dys:
        dot(ax, er, y, C_DKGREEN, 8)

    # ─── ULN2003 ───
    ux, uy, uw, uh = 5.2, 3.9, 2.8, 3.2
    block(ax, ux, uy, uw, uh, "ULN2003A\nDARLINGTON", '#E0F7FA', '#006064', 12)
    ul = ux - 0.05
    for y in dys:
        dot(ax, ul, y, '#006064', 8)

    # Drive wires ESP32 -> ULN2003
    for y, lbl in zip(dys, ["G25\u2192IN1", "G26\u2192IN2", "G27\u2192IN3"]):
        wire(ax, er, y, ul, y, C_DKGREEN, LW_W)
        ax.text((er + ul) / 2, y + 0.1, lbl, ha='center', va='bottom',
                fontsize=7.5, fontweight='bold', color=C_DKGREEN)

    # ULN internal text
    text_list(ax, ux + 0.12, 6.3, [
        ("INPUTS:", '#006064', True),
        ("IN1 \u2190 G25 (FORM3)", '#006064', False),
        ("IN2 \u2190 G26 (K1)", '#006064', False),
        ("IN3 \u2190 G27 (KSP)", '#006064', False),
        ("", None, False),
        ("OUTPUTS:", '#006064', True),
        ("OUT1 \u2192 K3 coil path", '#006064', False),
        ("OUT2 \u2192 K1 coil path", '#006064', False),
        ("OUT3 \u2192 KSP coil path", '#006064', False),
        ("", None, False),
        ("COM \u2192 +24V rail", C_RAIL, False),
        ("GND \u2192 0V rail", C_RAIL0, False),
        ("Low-side, flyback diodes", C_LGREY, False),
    ], spacing=0.16)

    # Supply rail taps on ULN2003
    # +24V tap
    wire(ax, ux + uw/2, uy + uh + 0.05, ux + uw/2, 7.35, C_RAIL, LW_RL)
    dot(ax, ux + uw/2, 7.35, C_RAIL, 6)
    ax.text(ux + uw/2 + 0.08, uy + uh + 0.15, "+24V", ha='left', va='bottom',
            fontsize=7, fontweight='bold', color=C_RAIL)
    # 0V tap
    wire(ax, ux + uw/2 + 0.3, uy - 0.05, ux + uw/2 + 0.3, 3.6, C_RAIL0, LW_RL)

    # Arrow ULN -> Interlock
    ax.annotate('', xy=(6.6, 3.65), xytext=(6.6, 3.85),
                arrowprops=dict(arrowstyle='->', color='#006064', lw=2.5))

    # ─── HARDWARE INTERLOCK ───
    block(ax, 5.2, 0.8, 2.8, 2.7, "HARDWARE INTERLOCK\n(NC AUX CONTACTS)", C_RED_BG, C_DKRED, 10)

    text_list(ax, 5.35, 3.0, [
        ("K3 COIL PATH:", C_DKRED, True),
        ("+24V\u2192K1_NC\u2192KSP_NC\u2192K3coils\u2192OUT1", '#424242', False),
        ("", None, False),
        ("K1 COIL PATH:", C_DKRED, True),
        ("+24V\u2192K3_NC\u2192K1coils\u2192ULN OUT2", '#424242', False),
        ("", None, False),
        ("KSP COIL PATH:", C_DKRED, True),
        ("+24V\u2192K3_NC\u2192KSP coil\u2192ULN OUT3", '#424242', False),
        ("", None, False),
        ("NC contacts block opposing group", C_DKRED, False),
    ], spacing=0.16)

    # ─── FEEDBACK ───
    block(ax, 8.7, 3.9, 2.7, 3.2, "FEEDBACK\n(3\u00d7 PC817 OPTO)", C_ORANGE, '#E65100', 11)

    text_list(ax, 8.85, 6.35, [
        ("24V SIDE:", '#E65100', True),
        ("+24V\u21924.7k\u2192LED\u2192AUX(NO)\u21920V", '#424242', False),
        ("AUX closed = LED lit", C_LGREY, False),
        ("", None, False),
        ("3.3V SIDE:", '#E65100', True),
        ("3.3V\u219210k pull-up\u2192collector", '#424242', False),
        ("Collector \u2192 ESP32 GPIO", '#424242', False),
        ("LOW = ON | HIGH = OFF", '#424242', False),
        ("", None, False),
        ("CONNECTIONS:", '#E65100', True),
        ("K3  AUX(NO) \u2192 opto \u2192 G32", '#E65100', False),
        ("K1  AUX(NO) \u2192 opto \u2192 G33", '#E65100', False),
        ("KSP AUX(NO) \u2192 opto \u2192 G34", '#E65100', False),
    ], spacing=0.15)

    # Supply rail taps on feedback block
    wire(ax, 10.0, 3.9 + 3.2 + 0.05, 10.0, 7.35, C_RAIL, LW_RL)
    dot(ax, 10.0, 7.35, C_RAIL, 6)
    ax.text(10.08, 3.9 + 3.2 + 0.15, "+24V", ha='left', va='bottom',
            fontsize=7, fontweight='bold', color=C_RAIL)
    wire(ax, 10.3, 3.9 - 0.05, 10.3, 3.55, C_RAIL0, LW_RL)

    # ─── LEDs + E-STOP ───
    block(ax, 8.7, 0.8, 2.7, 2.8, "LEDs + E-STOP", C_YELLOW, '#F57F17', 11)

    text_list(ax, 8.85, 3.1, [
        ("STATUS LEDs:", '#F57F17', True),
        ("G18\u2192330\u03A9\u2192GREEN\u21920V [F3]", C_DKGREEN, False),
        ("G19\u2192330\u03A9\u2192BLUE \u21920V [F1]", C_DKBLUE, False),
        ("G21\u2192330\u03A9\u2192RED  \u21920V [flt]", C_DKRED, False),
        ("", None, False),
        ("SOFTWARE E-STOP:", C_DKRED, True),
        ("G35 \u2190 NO btn\u21920V (pull-up)", C_DKRED, False),
        ("Press = ALL outputs OFF", C_LGREY, False),
        ("", None, False),
        ("HARDWARE E-STOP:", C_DKRED, True),
        ("NC mushroom in +24V supply", C_DKRED, False),
        ("Independent of ESP32!", C_LGREY, False),
    ], spacing=0.16)

    # ─── SUPPLY RAIL LEGEND BOX ───
    ax.add_patch(mpatches.FancyBboxPatch((0.3, 0.3), 3.8, 0.4,
                 boxstyle="round,pad=0.05", facecolor='white',
                 edgecolor='#424242', linewidth=1.5))
    ax.plot([0.4, 1.0], [0.55, 0.55], '-', color=C_RAIL, linewidth=LW_RL)
    ax.text(1.1, 0.55, "+24VDC (from PSU)", ha='left', va='center',
            fontsize=8, fontweight='bold', color=C_RAIL)
    ax.plot([0.4, 1.0], [0.4, 0.4], '-', color=C_RAIL0, linewidth=LW_RL)
    ax.text(1.1, 0.4, "0V / GND", ha='left', va='center',
            fontsize=8, fontweight='bold', color=C_RAIL0)
    ax.text(2.8, 0.55, "ESP32 GND tied to 0V rail", ha='left', va='center',
            fontsize=7, color=C_LGREY, style='italic')

    # Note about connections
    ax.text(5.85, 0.35,
            "Matching GPIO labels = connected  |  "
            "Drive wires shown explicitly  |  "
            "Supply rail taps shown with vertical lines",
            ha='center', va='center', fontsize=7, color=C_LGREY, style='italic')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 3: PINOUT TABLE + SEQUENCE + DEVICES
# ══════════════════════════════════════════

def page_pinout_notes(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 PINOUT, SEQUENCE & PARTS",
        "Complete ESP32 GPIO assignment  |  Mode-change firmware logic  |  Suggested devices")

    ax.text(0.3, 7.35, "ESP32 GPIO PINOUT", ha='left', va='center',
            fontsize=16, fontweight='bold', color=C_DKBLUE)

    headers = ["GPIO", "DIR", "FUNCTION", "CONNECTS TO", "NOTES"]
    rows = [
        ["25",  "OUT", "FORM3 drive",   "ULN2003 IN1",          "HIGH = energise K3"],
        ["26",  "OUT", "K1 drive",      "ULN2003 IN2",          "HIGH = energise K1"],
        ["27",  "OUT", "KSP drive",     "ULN2003 IN3",          "HIGH = energise KSP"],
        ["32",  "IN",  "K3 feedback",   "PC817 opto collector", "LOW = K3 energised"],
        ["33",  "IN",  "K1 feedback",   "PC817 opto collector", "LOW = K1 energised"],
        ["34",  "IN",  "KSP feedback",  "PC817 opto collector", "INPUT ONLY pin"],
        ["35",  "IN",  "E-STOP button", "NO pushbutton to GND", "INPUT ONLY, pull-up"],
        ["18",  "OUT", "LED green",     "330R -> LED -> GND",   "FORM 3 active"],
        ["19",  "OUT", "LED blue",      "330R -> LED -> GND",   "FORM 1 active"],
        ["21",  "OUT", "LED red",       "330R -> LED -> GND",   "Fault indicator"],
        ["USB", "I/O", "Serial control","Laptop USB port",      "115200 baud"],
        ["GND", "PWR", "Common ground", "Shared with 24V GND",  "Single ground ref"],
        ["3.3V","PWR", "Logic supply",  "From USB regulator",   "DO NOT connect to 24V"],
    ]

    col_x = [0.4, 1.2, 2.0, 3.8, 6.2]
    col_w = [0.8, 0.8, 1.8, 2.4, 2.8]
    row_h = 0.30
    ty = 7.05

    for j, (cx, hdr) in enumerate(zip(col_x, headers)):
        ax.add_patch(mpatches.Rectangle((cx - 0.05, ty - 0.05), col_w[j], row_h,
                     facecolor=C_DKBLUE, edgecolor='white', linewidth=1))
        ax.text(cx + 0.05, ty + 0.1, hdr, ha='left', va='center',
                fontsize=10, fontweight='bold', color='white', fontfamily='monospace')

    for i, row in enumerate(rows):
        ry = ty - (i + 1) * row_h
        bg = C_GREY_BG if i % 2 == 0 else 'white'
        for j, (cx, val) in enumerate(zip(col_x, row)):
            ax.add_patch(mpatches.Rectangle((cx - 0.05, ry - 0.05), col_w[j], row_h,
                         facecolor=bg, edgecolor='#BDBDBD', linewidth=0.5))
            fc = C_DKRED if val in ('IN', 'INPUT ONLY pin', 'INPUT ONLY, pull-up') else (
                 C_DKGREEN if val == 'OUT' else '#212121')
            ax.text(cx + 0.05, ry + 0.1, val, ha='left', va='center',
                    fontsize=9, color=fc, fontfamily='monospace',
                    fontweight='bold' if j < 2 else 'normal')

    # MODE-CHANGE SEQUENCE
    seq_y = 2.8
    ax.text(0.3, seq_y, "MODE-CHANGE SEQUENCE (FIRMWARE LOGIC)", ha='left', va='center',
            fontsize=16, fontweight='bold', color=C_DKBLUE)

    steps = [
        ("1.", "Receive command from laptop via USB serial"),
        ("2.", "De-energise current contactor group (set GPIOs LOW)"),
        ("3.", "Wait 100ms for contactors to open"),
        ("4.", "Check feedback: verify all contacts in old group are OPEN"),
        ("5.", "If feedback mismatch or timeout -> FAULT, all outputs OFF, red LED"),
        ("6.", "Energise new contactor group (set GPIOs HIGH)"),
        ("7.", "Wait 100ms for contactors to close"),
        ("8.", "Check feedback: verify new group contacts are CLOSED"),
        ("9.", "If feedback mismatch -> FAULT, all outputs OFF, red LED"),
        ("10.", "Update LED indicators, report OK/FAULT to laptop"),
    ]
    for i, (num, text) in enumerate(steps):
        sy = seq_y - 0.35 - i * 0.22
        ax.text(0.5, sy, num, ha='left', va='center', fontsize=10,
                fontweight='bold', color=C_DKBLUE)
        ax.text(1.0, sy, text, ha='left', va='center', fontsize=10,
                color='#212121')

    # DEVICE LIST
    dev_y = 2.8
    ax.text(6.5, dev_y, "SUGGESTED DEVICES", ha='left', va='center',
            fontsize=16, fontweight='bold', color=C_DKBLUE)

    devices = [
        ("FORM 3 contactor:", "Schneider LC1D40BD\n(40A, 3-pole, 24VDC coil)"),
        ("FORM 1 output:", "Schneider LP1D80004BD\n(125A, 4-pole, 24VDC coil)"),
        ("FORM 1 alt:", "ABB AF80-40-00-13\n(125A AC-1, 4-pole)"),
        ("Controller:", "ESP32 DevKit V1\n(USB, Wi-Fi, 3.3V logic)"),
        ("Coil driver:", "TI ULN2003A\n(7x Darlington, 50V, 500mA)"),
        ("Optocouplers:", "3x PC817 / LTV-817\n(24V isolation)"),
        ("24V PSU:", "DIN-rail, 24VDC, 5A min\n(for contactor coils)"),
        ("E-stop:", "NC mushroom in 24V supply\n+ NO button to ESP32 GPIO35"),
    ]
    for i, (label, detail) in enumerate(devices):
        dy = dev_y - 0.4 - i * 0.5
        ax.text(6.7, dy, label, ha='left', va='top', fontsize=10,
                fontweight='bold', color=C_DKBLUE)
        ax.text(8.5, dy, detail, ha='left', va='top', fontsize=9,
                color='#424242')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 4: BILL OF MATERIALS + SUPPLIERS
# ══════════════════════════════════════════

def page_bom(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 BILL OF MATERIALS",
        "Parts list with quantities, suppliers, and indicative pricing  |  Prices checked March 2026 (ex VAT)")

    ax.text(0.3, 7.35, "BILL OF MATERIALS", ha='left', va='center',
            fontsize=16, fontweight='bold', color=C_DKBLUE)

    bom_headers = ["#", "QTY", "DESCRIPTION", "PART NUMBER", "SUPPLIER", "APPROX PRICE"]
    bom_rows = [
        ["1", "1",  "3-pole contactor, 40A, 24VDC coil",
         "Schneider LC1D40BD",           "Farnell / RS Components",     "~\u00a3154 ex VAT"],
        ["",  "",   "(FORM 3 routing \u2014 K3A/K3B/K3C)",
         "or LC1DT40BD (4-pole)",        "farnell.co.uk",               ""],
        ["2", "1",  "3-pole contactor, 40A, 24VDC coil",
         "Schneider LC1D40BD",           "Farnell / RS Components",     "~\u00a3154 ex VAT"],
        ["",  "",   "(FORM 1 combine \u2014 K1A/K1B/K1C)",
         "",                              "",                            ""],
        ["3", "1",  "4-pole contactor, 125A, 24VDC coil",
         "Schneider LP1D80004BD",        "RS Components",               "~\u00a3588 ex VAT"],
        ["",  "",   "(FORM 1 output \u2014 KSP)",
         "",                              "uk.rs-online.com",            "(\u00a3706 inc VAT)"],
        ["4", "1",  "4-pole contactor, 125A (ALTERNATIVE)",
         "ABB AF80-40-00-13",            "TLA UK / ABB distributors",   "~\u00a3314 ex VAT"],
        ["",  "",   "(100-250V AC/DC coil option)",
         "",                              "tla.co.uk",                   "(\u00a3377 inc VAT)"],
        ["5", "3",  "Auxiliary contact block, 1NO+1NC",
         "Schneider LADN11",             "RS Components / Farnell",     "~\u00a38 each"],
        ["",  "",   "(Feedback NO + Interlock NC per contactor)",
         "",                              "",                            ""],
        ["6", "1",  "Mechanical interlock kit",
         "Schneider LA9D4002",            "RS Components",               "~\u00a325"],
        ["",  "",   "(Prevents both contactors closing together)",
         "",                              "",                            ""],
        ["7", "1",  "ESP32 DevKit V1 (USB, Wi-Fi, 3.3V)",
         "ESP32-DevKitC-32D",            "Amazon / AliExpress / Mouser","~\u00a38-15"],
        ["",  "",   "(Controller \u2014 USB serial to laptop)",
         "or ESP32-WROOM-32",            "mouser.co.uk",                ""],
        ["8", "1",  "ULN2003A Darlington driver IC",
         "TI ULN2003AN (DIP-16)",        "Farnell / Mouser / RS",      "~\u00a30.50"],
        ["",  "",   "(Low-side switch for 24V coils)",
         "",                              "mouser.co.uk",                ""],
        ["9", "3",  "PC817 optocoupler (DIP-4)",
         "Sharp PC817X / LTV-817",       "Farnell / Mouser / RS",      "~\u00a30.30 each"],
        ["",  "",   "(24V feedback isolation to 3.3V ESP32)",
         "",                              "",                            ""],
        ["10","3",  "Resistor 4.7k\u03A9 0.25W (opto LED series)",
         "Generic metal film",            "Farnell / RS / Mouser",      "~\u00a30.05 each"],
        ["11","3",  "Resistor 10k\u03A9 0.25W (opto pull-up)",
         "Generic metal film",            "Farnell / RS / Mouser",      "~\u00a30.05 each"],
        ["12","3",  "Resistor 330\u03A9 0.25W (LED series)",
         "Generic metal film",            "Farnell / RS / Mouser",      "~\u00a30.05 each"],
        ["13","3",  "LED indicators (green, blue, red) 5mm",
         "Standard 5mm LED kit",          "Amazon / Farnell",           "~\u00a30.20 each"],
        ["14","1",  "NO pushbutton (E-stop software)",
         "Generic panel-mount",           "RS / Amazon",                "~\u00a33"],
        ["15","1",  "NC mushroom-head E-stop (hardware)",
         "Schneider XB5AS8442",           "RS Components",              "~\u00a320"],
        ["",  "",   "(In +24V coil supply, independent of ESP32)",
         "",                              "uk.rs-online.com",            ""],
        ["16","1",  "24VDC DIN-rail power supply, 5A",
         "Mean Well HDR-100-24",          "RS / Farnell / Mouser",      "~\u00a330-45"],
        ["",  "",   "(Powers contactor coils)",
         "or Phoenix QUINT",              "",                            ""],
        ["17","1",  "DIN-rail terminal blocks (set)",
         "Phoenix Contact UK series",     "RS / Farnell",               "~\u00a320-30 set"],
        ["18","1",  "Enclosure (IP65 or better)",
         "Schneider Spacial or equiv.",   "RS / Farnell / Screwfix",    "~\u00a350-120"],
        ["",  "",   "(Sized for contactors + DIN rail + terminals)",
         "",                              "",                            ""],
        ["19","1",  "Prototype PCB / stripboard for ESP32 circuit",
         "Generic stripboard",            "Amazon / Farnell",           "~\u00a33-5"],
        ["20","--", "Wire, ferrules, cable glands, misc",
         "2.5mm\u00b2 and 16mm\u00b2 rated", "RS / Screwfix / CEF",    "~\u00a330-50"],
    ]

    col_x = [0.3, 0.65, 1.05, 4.2, 6.7, 9.0]
    row_h = 0.21
    ty = 7.05

    for j, (cx, hdr) in enumerate(zip(col_x, bom_headers)):
        w = (col_x[j+1] - cx if j < len(col_x)-1 else 11.3 - cx)
        ax.add_patch(mpatches.Rectangle((cx - 0.05, ty - 0.03), w + 0.1, row_h + 0.02,
                     facecolor=C_DKBLUE, edgecolor='white', linewidth=1))
        ax.text(cx, ty + 0.07, hdr, ha='left', va='center',
                fontsize=9, fontweight='bold', color='white', fontfamily='monospace')

    for i, row in enumerate(bom_rows):
        ry = ty - (i + 1) * row_h
        if ry < 0.5:
            break
        bg = C_GREY_BG if (i // 2) % 2 == 0 else 'white'
        is_main = row[0] != ""
        for j, (cx, val) in enumerate(zip(col_x, row)):
            ax.text(cx, ry + 0.07, val, ha='left', va='center',
                    fontsize=7.5 if is_main else 7,
                    fontweight='bold' if (is_main and j < 3) else 'normal',
                    color='#212121' if is_main else C_LGREY,
                    fontfamily='monospace')
        if is_main and i > 0:
            ax.plot([0.25, 11.2], [ry + row_h - 0.01, ry + row_h - 0.01],
                    '-', color='#E0E0E0', linewidth=0.5)

    by = 0.3
    block(ax, 0.3, by, 5.0, 1.6, "UK SUPPLIERS \u2014 QUICK REFERENCE", C_YELLOW, '#F57F17', 12)
    suppliers = [
        ("RS Components",     "uk.rs-online.com",       "Contactors, aux blocks, PSU, terminals, E-stop"),
        ("Farnell",           "uk.farnell.com",          "Contactors, ICs, passives, connectors"),
        ("Mouser Electronics","mouser.co.uk",            "ESP32, ULN2003, optocouplers, passives"),
        ("TLA UK",            "tla.co.uk",               "ABB contactors (alternative to Schneider)"),
        ("Amazon UK",         "amazon.co.uk",            "ESP32 dev boards, LED kits, pushbuttons"),
        ("Screwfix / CEF",    "screwfix.com / cef.co.uk","Enclosure, cable, glands, DIN rail"),
    ]
    for i, (name, url, what) in enumerate(suppliers):
        sy = by + 1.35 - i * 0.2
        ax.text(0.5, sy, name, ha='left', va='center', fontsize=9,
                fontweight='bold', color='#212121')
        ax.text(2.3, sy, url, ha='left', va='center', fontsize=8,
                color=C_DKBLUE, style='italic')
        ax.text(3.8, sy, what, ha='left', va='center', fontsize=7.5,
                color=C_LGREY)

    block(ax, 5.8, by, 5.0, 1.6, "INDICATIVE BUDGET ESTIMATE (ex VAT)", C_GREEN, C_DKGREEN, 12)
    budget = [
        ("Contactors (3 units + aux + interlock):", "~\u00a3350 - \u00a3600"),
        ("24V PSU + enclosure + terminals:",        "~\u00a3100 - \u00a3200"),
        ("ESP32 + ULN2003 + optos + passives:",     "~\u00a315 - \u00a325"),
        ("LEDs, E-stop, wire, misc:",               "~\u00a350 - \u00a380"),
        ("", ""),
        ("TOTAL ESTIMATE:",                          "~\u00a3515 - \u00a3905"),
    ]
    for i, (item, price) in enumerate(budget):
        sy = by + 1.35 - i * 0.2
        is_total = item.startswith("TOTAL")
        ax.text(6.0, sy, item, ha='left', va='center',
                fontsize=9.5 if is_total else 9,
                fontweight='bold' if is_total else 'normal',
                color=C_DKGREEN if is_total else '#212121')
        ax.text(10.5, sy, price, ha='right', va='center',
                fontsize=10 if is_total else 9,
                fontweight='bold', color=C_DKGREEN if is_total else '#424242')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# GENERATE PDF
# ══════════════════════════════════════════

def main():
    with PdfPages(OUT) as pdf:
        page_power_path(pdf)
        page_control(pdf)
        page_pinout_notes(pdf)
        page_bom(pdf)

    print(f"PDF saved: {OUT}")
    print(f"  4 pages, A4 landscape")
    print(f"  Page 1: Power path (FORM 3 + FORM 1) - phase colours, no wire crossings")
    print(f"  Page 2: Control system + supply rails (+24V / 0V)")
    print(f"  Page 3: Pinout table + mode-change sequence + device list")
    print(f"  Page 4: Bill of Materials + suppliers + budget estimate")


if __name__ == "__main__":
    main()
