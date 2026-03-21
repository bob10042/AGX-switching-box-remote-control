#!/usr/bin/env python3
"""AGX Test Box Rev 2.0 - Multi-page PDF block diagrams.

Individual phase selection: K3A, K3B, K3C driven independently.
5 ULN2003 channels, 5 optocoupler feedback circuits.
Phase A=RED, B=BROWN, C=GREY, Neutral=BLACK.

Pages:
  1. Power Path   - AGX phases through contactors to loads
  2. Relay Drives - ESP32 -> ULN2003A -> contactor coils (with interlock)
  3. Feedback     - Optocoupler circuits, E-stop, LEDs
  4. Pinout, Sequence, BOM
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
C_TEAL    = '#006064'
C_LTTEAL  = '#E0F7FA'

# Phase wire colours
C_PH_A  = '#CC0000'   # RED
C_PH_B  = '#8B4513'   # BROWN
C_PH_C  = '#696969'   # GREY
C_NEUT  = '#000000'   # BLACK
C_RAIL  = '#D50000'   # +24V rail
C_RAIL0 = '#1565C0'   # 0V rail
C_33V   = '#2E7D32'   # 3.3V rail

# Line widths
LW    = 3.0    # block border
LW_W  = 2.5    # signal wire
LW_PW = 5.0    # power/phase wire
LW_N  = 7.0    # neutral wire
LW_RL = 4.0    # supply rail (thicker)
LW_DRV = 3.0   # drive wire

# A3 landscape
PAGE_W, PAGE_H = 16.54, 11.69


def new_page(pdf, title, subtitle=""):
    fig, ax = plt.subplots(figsize=(PAGE_W, PAGE_H))
    ax.set_xlim(0, PAGE_W)
    ax.set_ylim(0, PAGE_H)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    title_y = PAGE_H - 0.8
    ax.add_patch(mpatches.Rectangle((0, title_y), PAGE_W, 0.8,
                 facecolor=C_BLUE, edgecolor='none'))
    ax.text(PAGE_W / 2, title_y + 0.48, title, ha='center', va='center',
            fontsize=24, fontweight='bold', color='white')
    if subtitle:
        ax.text(PAGE_W / 2, title_y + 0.15, subtitle, ha='center', va='center',
                fontsize=13, color='#B3E5FC')
    ax.text(PAGE_W / 2, 0.12,
            "DISCUSSION DOCUMENT  |  Rev 4.0  |  2026-03-20  |  Individual Phase Selection",
            ha='center', va='center', fontsize=7, color=C_LGREY, style='italic')
    return fig, ax


def block(ax, x, y, w, h, title, color=C_LTBLUE, border=C_BLUE,
          title_size=14, title_y_offset=0.22):
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.08", facecolor=color,
                 edgecolor=border, linewidth=LW))
    ax.text(x + w / 2, y + h - title_y_offset, title, ha='center', va='top',
            fontsize=title_size, fontweight='bold', color=border)


def wire(ax, x1, y1, x2, y2, color=C_WIRE, lw=LW_W, zorder=3):
    ax.plot([x1, x2], [y1, y2], '-', color=color, linewidth=lw,
            solid_capstyle='round', zorder=zorder)


def dot(ax, x, y, color, sz=8):
    ax.plot(x, y, 'o', color=color, markersize=sz, zorder=5)


def label(ax, x, y, text, color='#212121', size=10, ha='center',
          va='center', bold=False, mono=False):
    ax.text(x, y, text, ha=ha, va=va, fontsize=size, color=color,
            fontweight='bold' if bold else 'normal',
            fontfamily='monospace' if mono else 'sans-serif')


def draw_supply_rails(ax, rails_y_top=10.2, show_33v=False):
    """Draw prominent supply rail strips with background band."""
    spacing = 0.35
    band_h = (spacing * 3 + 0.15) if show_33v else (spacing + 0.25)
    ax.add_patch(mpatches.Rectangle((0, rails_y_top - band_h),
                 PAGE_W, band_h + 0.15, facecolor='#FAFAFA', edgecolor='#E0E0E0',
                 linewidth=1, zorder=1))
    y24 = rails_y_top
    wire(ax, 0.3, y24, PAGE_W - 0.34, y24, C_RAIL, LW_RL, zorder=4)
    label(ax, PAGE_W / 2, y24 + 0.12,
          "+24VDC RAIL  (from DIN-rail PSU via HW E-stop)",
          C_RAIL, 13, 'center', 'bottom', True)
    y0v = rails_y_top - spacing
    wire(ax, 0.3, y0v, PAGE_W - 0.34, y0v, C_RAIL0, LW_RL, zorder=4)
    label(ax, PAGE_W / 2, y0v + 0.12,
          "0V RAIL  (GND \u2014 shared with ESP32 GND)",
          C_RAIL0, 13, 'center', 'bottom', True)
    if show_33v:
        y33 = y0v - spacing
        wire(ax, 0.3, y33, PAGE_W - 0.34, y33, C_33V, LW_RL, zorder=4)
        label(ax, PAGE_W / 2, y33 + 0.12,
              "3.3V RAIL  (from ESP32 on-board USB regulator \u2014 logic only)",
              C_33V, 13, 'center', 'bottom', True)
        return y24, y0v, y33
    return y24, y0v


def rail_connection(ax, x, y_edge, color, label_text, direction='up'):
    """Short stub at block edge indicating rail connection."""
    stub_len = 0.2
    if direction == 'up':
        y_end = y_edge + stub_len
        wire(ax, x, y_edge, x, y_end, color, LW_RL - 1, zorder=6)
        dot(ax, x, y_end, color, 7)
        label(ax, x, y_end + 0.1, label_text, color, 11, 'center', 'bottom', True)
    else:
        y_end = y_edge - stub_len
        wire(ax, x, y_edge, x, y_end, color, LW_RL - 1, zorder=6)
        dot(ax, x, y_end, color, 7)
        label(ax, x, y_end - 0.1, label_text, color, 11, 'center', 'top', True)


# ══════════════════════════════════════════
# PAGE 1: POWER PATH
# ══════════════════════════════════════════

def page_power_path(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 POWER PATH",
        "Individual phase selection (K3A / K3B / K3C)  |  FORM 3 all phases"
        "  |  FORM 1 commoned 125A")

    # ─── AGX SOURCE (spans both sections) ───
    agx_x, agx_y, agx_w, agx_h = 0.5, 1.5, 3.0, 8.5
    block(ax, agx_x, agx_y, agx_w, agx_h,
          "AGX POWER\nSOURCE", C_ORANGE, '#E65100', 16)
    label(ax, agx_x + agx_w / 2, 5.5,
          "Pacific\nPower\nSource", '#E65100', 13)
    agx_r = agx_x + agx_w  # 3.5

    # Phase wire y-positions
    pha_y, phb_y, phc_y = 9.0, 7.3, 5.6
    phases = [('A', pha_y, C_PH_A), ('B', phb_y, C_PH_B), ('C', phc_y, C_PH_C)]

    for ph, y, col in phases:
        dot(ax, agx_r, y, col, 10)
        label(ax, agx_r - 0.2, y, f"Ph {ph}", col, 12, 'right', 'center', True)

    # Neutral
    neut_y = 2.2
    dot(ax, agx_r, neut_y, C_NEUT, 11)
    label(ax, agx_r - 0.2, neut_y, "N", C_NEUT, 13, 'right', 'center', True)

    # ─── FORM 3: INDIVIDUAL PHASE CONTACTORS (upper section) ───
    label(ax, 8.5, 10.2,
          "FORM 3 \u2014 THREE-PHASE  (40A per phase, individually selectable)",
          C_DKBLUE, 16, 'center', 'center', True)
    label(ax, 8.5, 9.85,
          "Select individually: 'A'  'B'  'C'   |   All three: '3'",
          C_DKBLUE, 11, 'center', 'center', False, True)

    k3x, k3w, k3h = 6.0, 2.8, 1.0
    ldx, ldw, ldh = 11.0, 2.8, 1.0

    for ph, y, col in phases:
        by = y - k3h / 2
        block(ax, k3x, by, k3w, k3h, f"K3{ph}  (40A NO)", C_LTBLUE, C_BLUE, 13)
        block(ax, ldx, by, ldw, ldh, f"Load {ph}  (40A)", C_PURPLE, '#7B1FA2', 13)
        # AGX -> K3x
        wire(ax, agx_r, y, k3x, y, col, LW_PW)
        # K3x -> Load
        wire(ax, k3x + k3w, y, ldx, y, col, LW_PW)
        # Phase label
        mx = (agx_r + k3x) / 2
        label(ax, mx, y + 0.2, f"Phase {ph}", col, 11, 'center', 'bottom', True)
        # Command label
        label(ax, k3x + k3w / 2, by + 0.08,
              f"Cmd: '{ph}'", C_DKBLUE, 10, 'center', 'bottom', False, True)

    # ─── FORM 1: COMMONED (lower section) ───
    label(ax, 8.5, 4.8,
          "FORM 1 \u2014 SINGLE-PHASE  (125A commoned)",
          C_DKRED, 16, 'center', 'center', True)

    # Junction dots drop from phase wires to FORM 1 path
    # (spread x-positions apart so vertical wires don't bunch up)
    k1_x, k1_y, k1_w, k1_h = 6.0, 2.0, 2.8, 2.2
    junctions = [
        ('A', 4.0, pha_y, C_PH_A, 3.6),
        ('B', 4.5, phb_y, C_PH_B, 3.0),
        ('C', 5.0, phc_y, C_PH_C, 2.5),
    ]
    for ph, jx, jy, col, f1y in junctions:
        dot(ax, jx, jy, col)
        wire(ax, jx, jy, jx, f1y, col, LW_PW)
        wire(ax, jx, f1y, k1_x, f1y, col, LW_PW)

    # K1 combine block
    block(ax, k1_x, k1_y, k1_w, k1_h, "K1 COMBINE", C_RED_BG, C_DKRED, 14)
    label(ax, k1_x + k1_w / 2, 2.8,
          "K1A+K1B+K1C\n(3\u00d7 40A NO)", C_DKRED, 11)
    label(ax, k1_x + k1_w / 2, 2.1,
          "Cmd: '1'", C_DKRED, 9, 'center', 'bottom', False, True)

    # SP_BUS wire to KSP
    sp_y = 3.0
    wire(ax, k1_x + k1_w, sp_y, 10.5, sp_y, C_DKRED, LW_PW)
    label(ax, (k1_x + k1_w + 10.5) / 2, sp_y + 0.18,
          "SP_BUS", C_DKRED, 11, 'center', 'bottom', True)

    # KSP block
    ksp_x, ksp_y, ksp_w, ksp_h = 10.5, 2.3, 2.2, 1.5
    block(ax, ksp_x, ksp_y, ksp_w, ksp_h, "KSP", '#FFF9C4', '#F57F17', 14)
    label(ax, ksp_x + ksp_w / 2, 2.7,
          "125A NO", '#F57F17', 12, 'center', 'center', True)

    # Wire to 1-phase load
    wire(ax, ksp_x + ksp_w, sp_y, 13.5, sp_y, C_DKRED, LW_PW)
    block(ax, 13.5, 2.3, 2.5, 1.5, "1\u03A6 LOAD", C_PURPLE, '#7B1FA2', 14)
    label(ax, 14.75, 2.7, "125A max", '#7B1FA2', 11)

    # ─── NEUTRAL BUS ───
    ny = 1.0
    wire(ax, agx_r, neut_y, agx_r, ny, C_NEUT, LW_N)
    wire(ax, agx_r, ny, 16.0, ny, C_NEUT, LW_N)
    label(ax, 9.0, ny - 0.25,
          "NEUTRAL BUS  (common return \u2014 not switched \u2014 to all loads)",
          C_NEUT, 12, 'center', 'top', True)

    # ─── INTERLOCK NOTE (right side) ───
    block(ax, 14.2, 6.2, 2.0, 3.5, "INTERLOCK", C_RED_BG, C_DKRED, 13)
    label(ax, 15.2, 8.8,
          "K3 group and\nK1+KSP group\nMUTUALLY\nEXCLUSIVE",
          C_DKRED, 10, 'center', 'center', True)
    label(ax, 15.2, 7.1,
          "NC aux contacts\nin coil supply\npaths prevent\nboth energised",
          C_DKRED, 9, 'center', 'center')

    # ─── WIRE COLOUR LEGEND ───
    label(ax, 15.2, 5.7, "WIRE COLOURS", '#424242', 11, 'center', 'center', True)
    for i, (lbl, c) in enumerate([
        ("Phase A = RED", C_PH_A), ("Phase B = BROWN", C_PH_B),
        ("Phase C = GREY", C_PH_C), ("Neutral = BLACK", C_NEUT)]):
        label(ax, 15.2, 5.3 - i * 0.3, lbl, c, 10, 'center', 'center', True)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 2: RELAY DRIVE CIRCUIT
# ══════════════════════════════════════════

def page_relay_drives(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 RELAY DRIVE CIRCUIT",
        "ESP32 GPIO \u2192 ULN2003A Darlington driver \u2192 contactor coils"
        "  |  Hardware interlock shown")

    # ─── SUPPLY RAILS ───
    y24, y0v = draw_supply_rails(ax, 10.2)

    # Pin y-positions (shared across ESP32, ULN, buses)
    k3a_y, k3b_y, k3c_y = 8.0, 7.2, 6.5
    k1_y, ksp_y = 4.4, 3.6

    # ─── ESP32 ───
    ex, ey, ew, eh = 0.8, 2.8, 3.0, 6.0
    block(ax, ex, ey, ew, eh, "ESP32\nDevKit V1", C_GREEN, C_DKGREEN, 15)
    er = ex + ew  # 3.8

    drive_pins = [
        ("GPIO25", "K3A", k3a_y, C_PH_A),
        ("GPIO26", "K3B", k3b_y, C_PH_B),
        ("GPIO27", "K3C", k3c_y, C_PH_C),
        ("GPIO16", "K1",  k1_y,  C_DKRED),
        ("GPIO17", "KSP", ksp_y, C_DKRED),
    ]
    for gpio, dest, y, col in drive_pins:
        label(ax, ex + 0.2, y, f"{gpio} \u2192", col, 10,
              'left', 'center', True, True)
        dot(ax, er, y, col, 7)

    label(ax, ex + ew / 2, 3.35,
          "POWERED VIA\nUSB CABLE\nfrom laptop", C_DKGREEN, 10,
          'center', 'center', True)
    label(ax, ex + ew / 2, 2.95, "115200 baud", C_DKGREEN, 9)

    # ─── ULN2003A ───
    ux, uy, uw, uh = 5.8, 2.8, 3.0, 6.0
    block(ax, ux, uy, uw, uh,
          "ULN2003A\nDARLINGTON\nDRIVER", C_LTTEAL, C_TEAL, 14)
    ul, ur = ux, ux + uw  # 5.8, 8.8

    channels = [
        ("IN1", "OUT1", k3a_y, C_PH_A),
        ("IN2", "OUT2", k3b_y, C_PH_B),
        ("IN3", "OUT3", k3c_y, C_PH_C),
        ("IN4", "OUT4", k1_y,  C_DKRED),
        ("IN5", "OUT5", ksp_y, C_DKRED),
    ]
    for inp, outp, y, col in channels:
        dot(ax, ul, y, col, 7)
        label(ax, ul + 0.15, y + 0.16, inp, C_TEAL, 10,
              'left', 'bottom', True, True)
        dot(ax, ur, y, col, 7)
        label(ax, ur - 0.15, y + 0.16, outp, C_TEAL, 10,
              'right', 'bottom', True, True)
        # Wire: ESP32 -> ULN
        wire(ax, er, y, ul, y, col, LW_DRV)

    label(ax, ux + uw / 2, 3.15,
          "COM \u2192 +24V\nGND \u2192 0V", C_TEAL, 11,
          'center', 'center', True, True)

    # ULN rail connections
    rail_connection(ax, ux + uw / 2 - 0.4, uy + uh, C_RAIL,
                    "\u2191 +24V (COM)", 'up')
    rail_connection(ax, ux + uw / 2 + 0.4, uy, C_RAIL0,
                    "\u2193 0V (GND)", 'down')

    # Signal flow labels
    label(ax, (er + ul) / 2, 8.5,
          "3.3V logic", C_DKGREEN, 10, 'center', 'bottom', True)
    label(ax, (ur + 11.0) / 2, 8.5,
          "24V switched", C_TEAL, 10, 'center', 'bottom', True)

    # ─── K3 COIL BUS ───
    ix, iy, iw, ih = 11.0, 6.0, 5.0, 3.2
    block(ax, ix, iy, iw, ih,
          "K3 COIL BUS  (via interlock)", C_LTBLUE, C_BLUE, 13)

    label(ax, ix + 0.2, 8.65,
          "+24V \u2192 K1_NC \u2192 KSP_NC \u2192 K3 BUS",
          C_BLUE, 11, 'left', 'center', True, True)
    label(ax, ix + 0.2, 8.3,
          "If K1 or KSP energised \u2192 K3 coils blocked",
          C_LGREY, 9.5, 'left', 'center')

    # K3 coil labels at wire entry points
    for lbl, uln_y, col in [
        ("K3A coil \u2192 ULN OUT1 \u2192 0V", k3a_y, C_PH_A),
        ("K3B coil \u2192 ULN OUT2 \u2192 0V", k3b_y, C_PH_B),
        ("K3C coil \u2192 ULN OUT3 \u2192 0V", k3c_y, C_PH_C)]:
        label(ax, ix + 0.3, uln_y, lbl, col, 10, 'left', 'center', True, True)
        wire(ax, ur, uln_y, ix, uln_y, col, LW_DRV)
        dot(ax, ix, uln_y, col, 6)

    rail_connection(ax, ix + 0.5, iy + ih, C_RAIL, "\u2191 +24V", 'up')

    # ─── K1/KSP COIL BUS ───
    jx, jy, jw, jh = 11.0, 2.5, 5.0, 3.0
    block(ax, jx, jy, jw, jh,
          "K1/KSP COIL BUS  (via interlock)", C_RED_BG, C_DKRED, 13)

    label(ax, jx + 0.2, 5.05,
          "+24V \u2192 K3A_NC \u2192 K3B_NC \u2192 K3C_NC \u2192 BUS",
          C_DKRED, 11, 'left', 'center', True, True)
    label(ax, jx + 0.2, 4.7,
          "If any K3 contactor energised \u2192 K1/KSP blocked",
          C_LGREY, 9.5, 'left', 'center')

    # K1/KSP coil labels at wire entry points
    label(ax, jx + 0.3, k1_y,
          "K1 coil  \u2192 ULN OUT4 \u2192 0V",
          C_DKRED, 10, 'left', 'center', True, True)
    label(ax, jx + 0.3, ksp_y,
          "KSP coil \u2192 ULN OUT5 \u2192 0V",
          C_DKRED, 10, 'left', 'center', True, True)

    # Wires from ULN to K1/KSP bus (straight horizontal)
    wire(ax, ur, k1_y, jx, k1_y, C_DKRED, LW_DRV)
    dot(ax, jx, k1_y, C_DKRED, 6)
    wire(ax, ur, ksp_y, jx, ksp_y, C_DKRED, LW_DRV)
    dot(ax, jx, ksp_y, C_DKRED, 6)

    rail_connection(ax, jx + 0.5, jy + jh, C_RAIL, "\u2191 +24V", 'up')

    # ─── HARDWARE E-STOP ───
    block(ax, 0.8, 0.3, 8.0, 2.2,
          "HARDWARE E-STOP  (independent of ESP32)",
          C_RED_BG, C_DKRED, 13)
    label(ax, 1.0, 1.95,
          "NC mushroom-head switch in +24V supply line before BOTH interlock buses",
          C_DKRED, 11, 'left', 'center', True)
    label(ax, 1.0, 1.55,
          "When pressed: physically cuts +24V to ALL contactor coils",
          '#424242', 10, 'left', 'center')
    label(ax, 1.0, 1.2,
          "Works even if ESP32 has crashed or firmware is hung",
          '#424242', 10, 'left', 'center')
    label(ax, 1.0, 0.8,
          "See Page 5 for full mains input and 24V PSU wiring",
          '#E65100', 10, 'left', 'center', True)

    # ─── LEGEND ───
    block(ax, 10.0, 0.3, 6.0, 1.5, "", C_GREY_BG, C_LGREY, 10)
    label(ax, 10.3, 1.5,
          "DRIVE SIGNAL FLOW:", '#424242', 10, 'left', 'center', True)
    label(ax, 10.3, 1.1,
          "ESP32 GPIO (3.3V) \u2192 ULN IN \u2192 ULN OUT (24V sink) \u2192 coil \u2192 0V",
          '#424242', 9.5, 'left', 'center', False, True)
    label(ax, 10.3, 0.7,
          "ULN2003: 7-ch Darlington, 500mA/ch, internal flyback diodes",
          C_LGREY, 9, 'left', 'center')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 3: FEEDBACK, LEDs, E-STOP
# ══════════════════════════════════════════

def page_feedback(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 FEEDBACK, LEDs & E-STOP",
        "5\u00d7 PC817 optocoupler feedback  |  3\u00d7 status LEDs"
        "  |  Software + hardware E-stop")

    # ─── SUPPLY RAILS (with 3.3V) ───
    y24, y0v, y33 = draw_supply_rails(ax, 10.2, show_33v=True)

    # Feedback pin y-positions
    fb_ya, fb_yb, fb_yc = 8.0, 7.3, 6.6
    fb_yk1, fb_yksp = 5.8, 5.2

    # ─── CONTACTOR AUX CONTACTS ───
    cx, cy, cw, ch = 0.8, 4.3, 3.5, 4.5
    block(ax, cx, cy, cw, ch,
          "CONTACTOR\nAUX CONTACTS\n(NO)", C_LTBLUE, C_BLUE, 13)
    cr = cx + cw  # 4.3

    aux_contacts = [
        ("K3A AUX (NO)", fb_ya, C_PH_A),
        ("K3B AUX (NO)", fb_yb, C_PH_B),
        ("K3C AUX (NO)", fb_yc, C_PH_C),
        ("K1  AUX (NO)", fb_yk1, C_DKRED),
        ("KSP AUX (NO)", fb_yksp, C_DKRED),
    ]
    for name, y, col in aux_contacts:
        label(ax, cx + 0.2, y, name, col, 10, 'left', 'center', True, True)
        dot(ax, cr, y, col, 6)

    label(ax, cx + cw / 2, 4.55,
          "Close when\ncontactor energised", C_LGREY, 9)

    # ─── OPTOCOUPLER BLOCK ───
    ox, oy, ow, oh = 6.2, 4.3, 4.5, 4.5
    block(ax, ox, oy, ow, oh,
          "5\u00d7 PC817 OPTOCOUPLERS", C_ORANGE, '#E65100', 13)

    label(ax, ox + 0.2, 8.2,
          "24V SIDE (LED):", '#E65100', 11, 'left', 'center', True)
    label(ax, ox + 0.2, 7.85,
          "+24V \u2192 4.7k\u03A9 \u2192 opto LED \u2192 AUX(NO) \u2192 0V",
          '#424242', 10, 'left', 'center', False, True)
    label(ax, ox + 0.2, 7.55,
          "AUX closed = current flows = LED lit",
          C_LGREY, 9, 'left', 'center')

    label(ax, ox + 0.2, 7.1,
          "3.3V SIDE (phototransistor):", '#E65100', 11,
          'left', 'center', True)
    label(ax, ox + 0.2, 6.75,
          "3.3V \u2192 10k\u03A9 pull-up \u2192 collector \u2192 ESP32",
          '#424242', 10, 'left', 'center', False, True)
    label(ax, ox + 0.2, 6.45,
          "Emitter \u2192 GND",
          '#424242', 10, 'left', 'center', False, True)

    label(ax, ox + 0.2, 5.95,
          "OUTPUT LOGIC:", '#E65100', 11, 'left', 'center', True)
    label(ax, ox + 0.2, 5.6,
          "CLOSED \u2192 opto ON  \u2192 GPIO reads LOW",
          C_DKGREEN, 10, 'left', 'center', True, True)
    label(ax, ox + 0.2, 5.3,
          "OPEN   \u2192 opto OFF \u2192 GPIO reads HIGH",
          C_DKRED, 10, 'left', 'center', True, True)
    label(ax, ox + 0.2, 5.0,
          "5 reads, majority vote (3+ agree)",
          C_LGREY, 9, 'left', 'center')

    # Wires from aux contacts to optos
    for name, y, col in aux_contacts:
        wire(ax, cr, y, ox, y, col, LW_W)

    # Rail stubs on opto block
    rail_connection(ax, ox + 0.5, oy + oh, C_RAIL, "\u2191 +24V", 'up')
    rail_connection(ax, ox + 1.5, oy, C_RAIL0, "\u2193 0V", 'down')
    rail_connection(ax, ox + ow - 0.5, oy + oh, C_33V, "\u2191 3.3V", 'up')

    # ─── ESP32 FEEDBACK INPUTS ───
    ex, ey_, ew, eh = 12.5, 4.3, 3.5, 4.5
    block(ax, ex, ey_, ew, eh,
          "ESP32\nFEEDBACK INPUTS", C_GREEN, C_DKGREEN, 13)
    el = ex  # 12.5

    fb_pins = [
        ("GPIO32 \u2190 K3A", fb_ya, C_PH_A),
        ("GPIO33 \u2190 K3B", fb_yb, C_PH_B),
        ("GPIO34 \u2190 K3C", fb_yc, C_PH_C),
        ("GPIO36 \u2190 K1",  fb_yk1, C_DKRED),
        ("GPIO39 \u2190 KSP", fb_yksp, C_DKRED),
    ]
    for pin_name, y, col in fb_pins:
        label(ax, ex + 0.2, y, pin_name, col, 11,
              'left', 'center', True, True)
        dot(ax, el, y, col, 6)

    label(ax, ex + ew / 2, 4.75,
          "GPIO34,36,39: input-only\n(ext 10k pull-up to 3.3V)",
          C_LGREY, 9)
    label(ax, ex + ew / 2, 4.45,
          "ESP32 powered via USB\n(own board, own regulator)",
          C_DKGREEN, 9, 'center', 'center', True)

    # Wires from optos to ESP32
    opr = ox + ow  # 10.7
    for name, y, col in aux_contacts:
        wire(ax, opr, y, el, y, col, LW_W)

    label(ax, (opr + el) / 2, 8.3,
          "3.3V logic", C_DKGREEN, 10, 'center', 'bottom', True)

    # ─── STATUS LEDs ───
    lx, ly, lw_, lh = 0.8, 0.5, 5.0, 3.3
    block(ax, lx, ly, lw_, lh, "STATUS LEDs", C_YELLOW, '#F57F17', 13)

    leds = [
        ("GPIO18 \u2192 330\u03A9 \u2192 GREEN \u2192 0V", C_DKGREEN,
         "ON = any FORM3 phase active"),
        ("GPIO19 \u2192 330\u03A9 \u2192 BLUE  \u2192 0V", C_DKBLUE,
         "ON = FORM1 active"),
        ("GPIO21 \u2192 330\u03A9 \u2192 RED   \u2192 0V", C_DKRED,
         "BLINK = fault  |  SOLID = E-stop"),
    ]
    for i, (pin, col, note) in enumerate(leds):
        ly_ = 3.3 - i * 0.7
        label(ax, lx + 0.2, ly_, pin, col, 10,
              'left', 'center', True, True)
        label(ax, lx + 0.2, ly_ - 0.28, note, C_LGREY, 9,
              'left', 'center')

    # ─── E-STOP ───
    sx, sy, sw, sh = 7.0, 0.5, 9.0, 3.3
    block(ax, sx, sy, sw, sh,
          "E-STOP  (two independent systems)", C_RED_BG, C_DKRED, 13)

    label(ax, sx + 0.3, 3.3,
          "SOFTWARE E-STOP:", C_DKRED, 12, 'left', 'center', True)
    label(ax, sx + 0.3, 2.9,
          "GPIO35 \u2190 NO pushbutton \u2192 GND  (external pull-up to 3.3V)",
          '#424242', 10, 'left', 'center', False, True)
    label(ax, sx + 0.3, 2.5,
          "Press = GPIO reads LOW \u2192 all outputs OFF \u2192 ESTOP state",
          '#424242', 10, 'left', 'center', False, True)

    label(ax, sx + 0.3, 1.9,
          "HARDWARE E-STOP:", C_DKRED, 12, 'left', 'center', True)
    label(ax, sx + 0.3, 1.5,
          "NC mushroom-head in +24V supply (before interlock buses)",
          '#424242', 10, 'left', 'center', False, True)
    label(ax, sx + 0.3, 1.1,
          "Cuts +24V to ALL coils \u2014 independent of ESP32",
          C_DKRED, 10, 'left', 'center', True)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 4: PINOUT TABLE + COMMANDS + BOM
# ══════════════════════════════════════════

def page_pinout_bom(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 PINOUT, COMMANDS & BOM",
        "Complete GPIO assignment  |  Serial commands  |  Bill of materials")

    row_h = 0.34

    # ─── GPIO TABLE (left column) ───
    label(ax, 0.5, 10.2, "ESP32 GPIO PINOUT",
          C_DKBLUE, 16, 'left', 'center', True)

    gpio_headers = ["GPIO", "DIR", "FUNCTION", "CONNECTS TO", "NOTES"]
    gpio_rows = [
        ["25",  "OUT", "K3A drive",     "ULN2003 IN1 \u2192 OUT1", "Phase A contactor"],
        ["26",  "OUT", "K3B drive",     "ULN2003 IN2 \u2192 OUT2", "Phase B contactor"],
        ["27",  "OUT", "K3C drive",     "ULN2003 IN3 \u2192 OUT3", "Phase C contactor"],
        ["16",  "OUT", "K1 drive",      "ULN2003 IN4 \u2192 OUT4", "FORM1 combine"],
        ["17",  "OUT", "KSP drive",     "ULN2003 IN5 \u2192 OUT5", "FORM1 output 125A"],
        ["32",  "IN",  "K3A feedback",  "PC817-1 opto collector",  "LOW = K3A closed"],
        ["33",  "IN",  "K3B feedback",  "PC817-2 opto collector",  "LOW = K3B closed"],
        ["34",  "IN",  "K3C feedback",  "PC817-3 opto collector",  "INPUT ONLY, ext pull-up"],
        ["36",  "IN",  "K1 feedback",   "PC817-4 opto collector",  "INPUT ONLY (VP)"],
        ["39",  "IN",  "KSP feedback",  "PC817-5 opto collector",  "INPUT ONLY (VN)"],
        ["35",  "IN",  "E-STOP button", "NO pushbutton to GND",    "INPUT ONLY, ext pull-up"],
        ["18",  "OUT", "LED green",     "330\u03A9 \u2192 LED \u2192 GND",
         "FORM3/phase active"],
        ["19",  "OUT", "LED blue",      "330\u03A9 \u2192 LED \u2192 GND",
         "FORM1 active"],
        ["21",  "OUT", "LED red",       "330\u03A9 \u2192 LED \u2192 GND",
         "Fault / E-stop"],
    ]

    col_x = [0.5, 1.3, 2.1, 3.8, 6.3]
    col_w = [0.8, 0.8, 1.7, 2.5, 2.0]
    ty = 9.9

    for j, (cx_, hdr) in enumerate(zip(col_x, gpio_headers)):
        ax.add_patch(mpatches.Rectangle(
            (cx_ - 0.05, ty - 0.05), col_w[j], row_h,
            facecolor=C_DKBLUE, edgecolor='white', linewidth=1))
        label(ax, cx_ + 0.08, ty + 0.1, hdr, 'white', 11,
              'left', 'center', True, True)

    for i, row in enumerate(gpio_rows):
        ry = ty - (i + 1) * row_h
        bg = C_GREY_BG if i % 2 == 0 else 'white'
        for j, (cx_, val) in enumerate(zip(col_x, row)):
            ax.add_patch(mpatches.Rectangle(
                (cx_ - 0.05, ry - 0.05), col_w[j], row_h,
                facecolor=bg, edgecolor='#E0E0E0', linewidth=0.5))
            fc = (C_DKRED if val == 'IN'
                  else (C_DKGREEN if val == 'OUT' else '#212121'))
            label(ax, cx_ + 0.08, ry + 0.1, val, fc, 10,
                  'left', 'center', j < 2, True)

    # ─── SERIAL COMMANDS (below GPIO table) ───
    cmd_y_label = 4.6
    label(ax, 0.5, cmd_y_label,
          "SERIAL COMMANDS (115200 baud, 8N1)",
          C_DKBLUE, 16, 'left', 'center', True)

    cmd_headers = ["CMD", "ACTION", "CONTACTORS"]
    cmd_rows = [
        ["A", "Phase A only",           "K3A energised"],
        ["B", "Phase B only",           "K3B energised"],
        ["C", "Phase C only",           "K3C energised"],
        ["3", "FORM 3 (all phases)",    "K3A + K3B + K3C"],
        ["1", "FORM 1 (commoned 125A)", "K1 + KSP"],
        ["0", "All OFF (safe state)",   "All de-energised"],
        ["S", "Query status",           "Reports all states"],
        ["T", "Run self-test",          "Tests A,B,C,F3,F1"],
    ]

    cmd_col_x = [0.5, 1.5, 4.5]
    cmd_col_w = [1.0, 3.0, 3.0]
    cmd_ty = cmd_y_label - 0.35

    for j, (cx_, hdr) in enumerate(zip(cmd_col_x, cmd_headers)):
        ax.add_patch(mpatches.Rectangle(
            (cx_ - 0.05, cmd_ty - 0.05), cmd_col_w[j], row_h,
            facecolor=C_DKBLUE, edgecolor='white', linewidth=1))
        label(ax, cx_ + 0.08, cmd_ty + 0.1, hdr, 'white', 11,
              'left', 'center', True, True)

    for i, row in enumerate(cmd_rows):
        ry = cmd_ty - (i + 1) * row_h
        bg = C_GREY_BG if i % 2 == 0 else 'white'
        for j, (cx_, val) in enumerate(zip(cmd_col_x, row)):
            ax.add_patch(mpatches.Rectangle(
                (cx_ - 0.05, ry - 0.05), cmd_col_w[j], row_h,
                facecolor=bg, edgecolor='#E0E0E0', linewidth=0.5))
            fc = C_DKBLUE if j == 0 else '#212121'
            label(ax, cx_ + 0.08, ry + 0.1, val, fc, 10,
                  'left', 'center', j == 0, True)

    # ─── BOM (right column) ───
    label(ax, 9.0, 10.2, "BILL OF MATERIALS",
          C_DKBLUE, 16, 'left', 'center', True)

    bom_items = [
        ("3\u00d7", "Contactor 40A 1-pole 24VDC",
         "K3A/K3B/K3C",     "~\u00a380 ea"),
        ("1\u00d7", "Contactor 40A 3-pole 24VDC",
         "K1 combine",      "~\u00a3154"),
        ("1\u00d7", "Contactor 125A 4-pole 24VDC",
         "KSP output",      "~\u00a3588"),
        ("5\u00d7", "LADN11 aux (1NO+1NC)",
         "Fback+interlock", "~\u00a38 ea"),
        ("1\u00d7", "Mech interlock (optional)",
         "LA9D4002",        "~\u00a325"),
        ("1\u00d7", "ESP32 DevKit V1",
         "Controller",      "~\u00a310"),
        ("1\u00d7", "ULN2003A DIP-16",
         "Coil driver",     "~\u00a30.50"),
        ("5\u00d7", "PC817 optocoupler",
         "Feedback",        "~\u00a30.30 ea"),
        ("5\u00d7", "4.7k\u03A9 resistor",
         "Opto LED",        "~\u00a30.05 ea"),
        ("5\u00d7", "10k\u03A9 resistor",
         "Pull-up",         "~\u00a30.05 ea"),
        ("3\u00d7", "330\u03A9 + LED",
         "Status LEDs",     "~\u00a30.25 ea"),
        ("1\u00d7", "24VDC DIN-rail PSU 5A",
         "Coil power",      "~\u00a335"),
        ("1\u00d7", "NC mushroom E-stop",
         "HW E-stop",       "~\u00a320"),
        ("1\u00d7", "NO pushbutton",
         "SW E-stop",       "~\u00a33"),
        ("1\u00d7", "IEC C14 panel inlet",
         "Mains input",     "~\u00a35"),
        ("1\u00d7", "DIN-rail MCB 6A type B",
         "Mains protection","~\u00a38"),
        ("1\u00d7", "IEC C13 mains cable",
         "Mains lead",      "~\u00a35"),
        ("1\u00d7", "Enclosure IP65",
         "Housing",         "~\u00a380"),
    ]

    bom_x = 9.0
    bom_ty = 9.9
    bom_row_h = 0.28
    bom_col_defs = [
        (bom_x, 0.6),
        (bom_x + 0.6, 3.0),
        (bom_x + 3.6, 1.5),
        (bom_x + 5.1, 1.2),
    ]

    # BOM header row
    for hdr, (cx_, w) in zip(
        ["QTY", "DESCRIPTION", "FOR", "PRICE"], bom_col_defs):
        ax.add_patch(mpatches.Rectangle(
            (cx_ - 0.05, bom_ty - 0.05), w, bom_row_h,
            facecolor=C_DKBLUE, edgecolor='white', linewidth=1))
        label(ax, cx_ + 0.08, bom_ty + 0.08, hdr, 'white', 10,
              'left', 'center', True, True)

    # BOM rows
    for i, (qty, desc, usage, price) in enumerate(bom_items):
        ry = bom_ty - (i + 1) * bom_row_h
        if ry < 0.5:
            break
        bg = C_GREY_BG if i % 2 == 0 else 'white'
        for cx_, w in bom_col_defs:
            ax.add_patch(mpatches.Rectangle(
                (cx_ - 0.05, ry - 0.05), w, bom_row_h,
                facecolor=bg, edgecolor='#E0E0E0', linewidth=0.5))
        label(ax, bom_x + 0.08, ry + 0.08, qty,
              C_DKBLUE, 9.5, 'left', 'center', True, True)
        label(ax, bom_x + 0.68, ry + 0.08, desc,
              '#212121', 9.5, 'left', 'center', False, True)
        label(ax, bom_x + 3.68, ry + 0.08, usage,
              C_LGREY, 9, 'left', 'center')
        label(ax, bom_x + 5.18, ry + 0.08, price,
              '#424242', 9.5, 'left', 'center', True)

    # Budget estimate
    label(ax, bom_x, 4.3,
          "TOTAL ESTIMATE:  ~\u00a3670 - \u00a31,120 (ex VAT)",
          C_DKGREEN, 12, 'left', 'center', True)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 5: MAINS INPUT & 24V PSU
# ══════════════════════════════════════════

def page_mains_psu(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 MAINS INPUT & 24V POWER SUPPLY",
        "230VAC mains input  |  DIN-rail PSU  |  Hardware E-stop"
        "  |  Earth bonding")

    # Three blocks across the top, safety block at bottom.
    # All wires routed through the 1.5-unit gaps between blocks.

    # ─── BLOCK 1: MAINS INPUT ───
    bm_x, bm_y, bm_w, bm_h = 0.5, 6.2, 4.5, 3.8
    block(ax, bm_x, bm_y, bm_w, bm_h,
          "MAINS INPUT", C_ORANGE, '#E65100', 15)
    label(ax, bm_x + bm_w / 2, 9.2,
          "IEC C14 panel-mount inlet", '#E65100', 11, 'center', 'center', True)
    label(ax, bm_x + bm_w / 2, 8.7,
          "230VAC 50Hz", '#424242', 11, 'center', 'center')
    label(ax, bm_x + bm_w / 2, 8.2,
          "Integral fuse holder (6A)", '#424242', 10, 'center', 'center')
    label(ax, bm_x + bm_w / 2, 7.6,
          "6A DIN-rail MCB (Type B)\nfor overcurrent protection\nand isolation",
          '#424242', 10, 'center', 'center')
    label(ax, bm_x + bm_w / 2, 6.7,
          "IEC C13 mains cable\nfrom UK 13A plug (3A fuse)",
          C_LGREY, 9, 'center', 'center')
    bm_r = bm_x + bm_w  # 5.0

    # ─── BLOCK 2: 24V DIN-RAIL PSU ───
    bp_x, bp_y, bp_w, bp_h = 6.5, 6.2, 4.3, 3.8
    block(ax, bp_x, bp_y, bp_w, bp_h,
          "24V DIN-RAIL PSU", C_LTTEAL, C_TEAL, 15)
    label(ax, bp_x + bp_w / 2, 9.2,
          "Mean Well HDR-100-24", C_TEAL, 12, 'center', 'center', True)
    label(ax, bp_x + bp_w / 2, 8.7,
          "Input: 85\u2013264VAC (universal)", '#424242', 10, 'center', 'center')
    label(ax, bp_x + bp_w / 2, 8.25,
          "Output: 24VDC / 5A", C_TEAL, 12, 'center', 'center', True)
    label(ax, bp_x + bp_w / 2, 7.8,
          "120W continuous", '#424242', 10, 'center', 'center')
    label(ax, bp_x + bp_w / 2, 7.3,
          "DIN-rail mount (TS-35)", C_LGREY, 10, 'center', 'center')
    label(ax, bp_x + bp_w / 2, 6.8,
          "Terminals: L, N, PE, +V, \u2212V", '#424242', 9, 'center', 'center',
          False, True)
    bp_r = bp_x + bp_w  # 10.8

    # ─── BLOCK 3: E-STOP & OUTPUT RAILS ───
    be_x, be_y, be_w, be_h = 12.3, 6.2, 3.7, 3.8
    block(ax, be_x, be_y, be_w, be_h,
          "E-STOP &\nOUTPUT RAILS", C_RED_BG, C_DKRED, 14)
    label(ax, be_x + be_w / 2, 9.0,
          "HW E-STOP", C_DKRED, 12, 'center', 'center', True)
    label(ax, be_x + be_w / 2, 8.55,
          "NC mushroom-head\npanel mount (red)", C_DKRED, 10,
          'center', 'center')
    label(ax, be_x + be_w / 2, 7.9,
          "Physically cuts +24V\nto ALL coils", '#424242', 10,
          'center', 'center')
    label(ax, be_x + be_w / 2, 7.2,
          "+24VDC RAIL", C_RAIL, 12, 'center', 'center', True)
    label(ax, be_x + be_w / 2, 6.85,
          "To interlock buses\n\u2192 contactor coils", '#424242', 9,
          'center', 'center')
    label(ax, be_x + be_w / 2, 6.35,
          "0V RAIL (GND)", C_RAIL0, 12, 'center', 'center', True)

    # ─── WIRES BETWEEN BLOCKS (all in the 1.5-unit gaps) ───

    # Mains → PSU: arrow in the gap
    wire_y1 = 8.5
    wire(ax, bm_r, wire_y1, bp_x, wire_y1, '#8B4513', LW_PW)
    dot(ax, bm_r, wire_y1, '#8B4513', 8)
    dot(ax, bp_x, wire_y1, '#8B4513', 8)
    label(ax, (bm_r + bp_x) / 2, wire_y1 + 0.18,
          "L + N + PE", '#8B4513', 10, 'center', 'bottom', True)
    label(ax, (bm_r + bp_x) / 2, wire_y1 - 0.18,
          "(via MCB for L)", C_LGREY, 8, 'center', 'top')

    # PSU → E-STOP: +24V output in the gap
    wire_y2 = 8.5
    wire(ax, bp_r, wire_y2, be_x, wire_y2, C_RAIL, LW_PW)
    dot(ax, bp_r, wire_y2, C_RAIL, 8)
    dot(ax, be_x, wire_y2, C_RAIL, 8)
    label(ax, (bp_r + be_x) / 2, wire_y2 + 0.18,
          "+V (24VDC)", C_RAIL, 10, 'center', 'bottom', True)

    # PSU → 0V rail: second wire in the gap
    wire_y3 = 7.0
    wire(ax, bp_r, wire_y3, be_x, wire_y3, C_RAIL0, LW_PW)
    dot(ax, bp_r, wire_y3, C_RAIL0, 8)
    dot(ax, be_x, wire_y3, C_RAIL0, 8)
    label(ax, (bp_r + be_x) / 2, wire_y3 + 0.18,
          "\u2212V (0V)", C_RAIL0, 10, 'center', 'bottom', True)

    # ─── BLOCK 4: EARTH BONDING & SAFETY ───
    bs_x, bs_y, bs_w, bs_h = 0.5, 0.5, 15.5, 5.0
    block(ax, bs_x, bs_y, bs_w, bs_h,
          "EARTH BONDING & SAFETY NOTES", '#E8F5E9', C_DKGREEN, 15)

    # Left column: earth bonding
    label(ax, 0.8, 4.7,
          "EARTH BONDING PATH:", C_DKGREEN, 13, 'left', 'center', True)
    label(ax, 0.8, 4.2,
          "IEC inlet E (green/yellow) \u2192 enclosure bonding stud \u2192 DIN rail \u2192 PSU PE terminal",
          '#424242', 10, 'left', 'center', False, True)
    label(ax, 0.8, 3.75,
          "All metal parts of enclosure must be bonded to protective earth",
          C_LGREY, 9, 'left', 'center')

    # Left column: safety notes
    label(ax, 0.8, 3.1,
          "SAFETY REQUIREMENTS:", C_DKRED, 13, 'left', 'center', True)
    notes = [
        "All mains wiring must be performed by a competent person",
        "Earth bonding to metal enclosure and DIN rail is mandatory",
        "Keep mains wiring physically separated from low-voltage control wiring",
        "IEC inlet fuse holder: fit 6A anti-surge fuse (keep spare in lid)",
        "Test earth continuity before first power-on",
        "Label enclosure: 'CAUTION \u2014 230VAC INSIDE'",
    ]
    for i, note in enumerate(notes):
        col = C_DKRED if i == 5 else '#424242'
        bld = i == 5
        label(ax, 0.8, 2.65 - i * 0.35, f"\u2022 {note}",
              col, 10, 'left', 'center', bld)

    # Right column: wire colours and power chain
    label(ax, 9.5, 4.7,
          "MAINS WIRE COLOURS (UK):", '#424242', 13, 'left', 'center', True)
    for i, (lbl, c) in enumerate([
        ("Live = BROWN", '#8B4513'),
        ("Neutral = BLUE", C_DKBLUE),
        ("Earth = GREEN/YELLOW", C_DKGREEN)]):
        label(ax, 9.5, 4.25 - i * 0.35, lbl, c, 11, 'left', 'center', True)

    label(ax, 9.5, 3.1,
          "POWER CHAIN:", '#424242', 13, 'left', 'center', True)
    label(ax, 9.5, 2.6,
          "230VAC mains \u2192 IEC C14 inlet \u2192 6A MCB \u2192 24V PSU",
          '#424242', 10, 'left', 'center', False, True)
    label(ax, 9.5, 2.2,
          "\u2192 HW E-STOP (NC) \u2192 +24VDC RAIL \u2192 interlock buses",
          C_DKRED, 10, 'left', 'center', True, True)
    label(ax, 9.5, 1.8,
          "0V from PSU \u2192 0V RAIL (shared GND with ESP32)",
          C_RAIL0, 10, 'left', 'center', True, True)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# GENERATE PDF
# ══════════════════════════════════════════

def main():
    with PdfPages(OUT) as pdf:
        page_power_path(pdf)
        page_relay_drives(pdf)
        page_feedback(pdf)
        page_pinout_bom(pdf)
        page_mains_psu(pdf)

    print(f"PDF saved: {OUT}")
    print(f"  5 pages, A3 landscape")
    print(f"  Page 1: Power path - individual K3A/K3B/K3C + FORM1")
    print(f"  Page 2: Relay drive circuit - ESP32 -> ULN2003 -> coils + interlock")
    print(f"  Page 3: Feedback optocouplers, LEDs, E-stop")
    print(f"  Page 4: GPIO pinout, serial commands, BOM")
    print(f"  Page 5: Mains input, 24V PSU, HW E-stop, earth bonding")


if __name__ == "__main__":
    main()
