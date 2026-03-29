#!/usr/bin/env python3
"""AGX Test Box Rev 2.0 - Multi-page PDF circuit schematics.

Uses schemdraw for proper electrical schematic symbols on matplotlib pages.
Individual phase selection: K3A, K3B, K3C driven independently.
5 ULN2003 channels, 5 optocoupler feedback circuits.

Pages:
  1. Power Path   - contactor switch symbols on phase wires
  2. Relay Drives - ESP32/ULN2003A ICs, coil symbols, interlock chains
  3. Feedback     - PC817 optocoupler symbols with resistors
  4. LEDs & E-Stop - LED/resistor/ground circuits, push-button switches
  5. Pinout, Commands, BOM - tables (unchanged)
  6. Mains Input & PSU - breaker, PSU, earth symbols
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import schemdraw
import schemdraw.elements as elm
import os
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

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

# Line widths (for matplotlib elements: rails, buses)
LW    = 3.0    # block border
LW_W  = 2.5    # signal wire
LW_PW = 5.0    # power/phase wire
LW_N  = 7.0    # neutral wire
LW_RL = 4.0    # supply rail
LW_DRV = 3.0   # drive wire

# A3 landscape
PAGE_W, PAGE_H = 16.54, 11.69


# ══════════════════════════════════════════
# UTILITY FUNCTIONS (matplotlib)
# ══════════════════════════════════════════

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
            "DISCUSSION DOCUMENT  |  Rev 5.0  |  2026-03-29  |  Schematic Symbols",
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
# SCHEMDRAW HELPERS
# ══════════════════════════════════════════

def new_drawing(ax, unit=1.5, fontsize=11):
    """Create a configured schemdraw Drawing on the given matplotlib axes."""
    d = schemdraw.Drawing(canvas=ax, show=False)
    d.config(unit=unit, fontsize=fontsize)
    return d


def finish_drawing(d, ax):
    """Render schemdraw drawing and restore axes limits."""
    d.draw()
    ax.set_xlim(0, PAGE_W)
    ax.set_ylim(0, PAGE_H)
    ax.set_aspect('equal')


# ══════════════════════════════════════════
# PAGE 1: POWER PATH
# ══════════════════════════════════════════

def page_power_path(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 POWER PATH",
        "Individual phase selection (K3A / K3B / K3C)  |  FORM 3 all phases"
        "  |  FORM 1 commoned 125A")

    # ─── AGX SOURCE ───
    agx_x, agx_y, agx_w, agx_h = 0.5, 1.5, 2.5, 8.5
    block(ax, agx_x, agx_y, agx_w, agx_h,
          "AGX POWER\nSOURCE", C_ORANGE, '#E65100', 16)
    label(ax, agx_x + agx_w / 2, 5.5,
          "Pacific\nPower\nSource", '#E65100', 13)
    agx_r = agx_x + agx_w  # 3.0

    # Phase wire y-positions
    pha_y, phb_y, phc_y = 9.0, 7.3, 5.6
    phases = [('A', pha_y, C_PH_A), ('B', phb_y, C_PH_B), ('C', phc_y, C_PH_C)]

    for ph, y, col in phases:
        dot(ax, agx_r, y, col, 10)
        label(ax, agx_r - 0.3, y, f"Ph {ph}", col, 12, 'right', 'center', True)

    # Neutral
    neut_y = 2.2
    dot(ax, agx_r, neut_y, C_NEUT, 11)
    label(ax, agx_r - 0.3, neut_y, "N", C_NEUT, 13, 'right', 'center', True)

    # ─── FORM 3: SWITCH SYMBOLS ───
    label(ax, 8.0, 10.2,
          "FORM 3 \u2014 THREE-PHASE  (40A per phase, individually selectable)",
          C_DKBLUE, 16, 'center', 'center', True)
    label(ax, 8.0, 9.85,
          "Select individually: 'A'  'B'  'C'   |   All three: '3'",
          C_DKBLUE, 12, 'center', 'center', False, True)

    d = new_drawing(ax, unit=2.0, fontsize=10)

    # Contactor switch positions
    sw_x = 5.0   # switch start x
    ld_x = 10.5  # load start x

    for ph, y, col in phases:
        # AGX → switch lead-in
        wire(ax, agx_r, y, sw_x, y, col, LW_PW)
        label(ax, (agx_r + sw_x) / 2, y + 0.2, f"Phase {ph}", col, 11,
              'center', 'bottom', True)

        # Contactor switch symbol (NO)
        sw = elm.Switch().at((sw_x, y)).right().color(col)
        d += sw
        sw_end_x = sw_x + 2.0  # switch length at unit=2.0

        # Switch → load lead wire
        wire(ax, sw_end_x, y, ld_x, y, col, LW_PW)

        # Switch label
        label(ax, sw_x + 1.0, y + 0.35, f"K3{ph}  (40A NO)", col, 11,
              'center', 'bottom', True)
        label(ax, sw_x + 1.0, y - 0.35, f"Cmd: '{ph}'", col, 10,
              'center', 'top', False, True)

    finish_drawing(d, ax)

    # ─── LOAD BLOCKS (external devices) ───
    ldw, ldh = 2.2, 1.1
    for ph, y, col in phases:
        block(ax, ld_x, y - ldh / 2, ldw, ldh,
              f"Load {ph}  (40A)", C_PURPLE, '#7B1FA2', 13)

    # ─── FORM 1: COMMONED ───
    label(ax, 8.0, 4.8,
          "FORM 1 \u2014 SINGLE-PHASE  (125A commoned)",
          C_DKRED, 16, 'center', 'center', True)

    d2 = new_drawing(ax, unit=1.8, fontsize=10)

    # Junction dots drop from phase wires to FORM 1 path
    k1_sw_x = 6.0
    junctions = [
        ('A', 3.8, pha_y, C_PH_A, 3.8),
        ('B', 4.3, phb_y, C_PH_B, 3.2),
        ('C', 4.8, phc_y, C_PH_C, 2.6),
    ]
    for ph, jx, jy, col, f1y in junctions:
        dot(ax, jx, jy, col)
        wire(ax, jx, jy, jx, f1y, col, LW_PW)
        wire(ax, jx, f1y, k1_sw_x, f1y, col, LW_PW)

        # K1 switch symbol for each phase
        sw = elm.Switch().at((k1_sw_x, f1y)).right().color(col)
        d2 += sw
        k1_end = k1_sw_x + 1.8

        # All outputs merge at SP_BUS
        wire(ax, k1_end, f1y, 9.0, f1y, col, LW_PW)

    # Labels for K1 group
    label(ax, k1_sw_x + 0.9, 4.3, "K1 COMBINE", C_DKRED, 12,
          'center', 'bottom', True)
    label(ax, k1_sw_x + 0.9, 2.1, "3\u00d7 40A NO\nCmd: '1'", C_DKRED, 10,
          'center', 'top', False, True)

    # Dashed line indicating mechanical linkage between K1 switches
    ax.plot([k1_sw_x + 0.9, k1_sw_x + 0.9], [2.6, 3.8], '--',
            color=C_DKRED, linewidth=1.5, zorder=6)

    # SP_BUS merge point + wire to KSP
    sp_y = 3.2
    dot(ax, 9.0, 3.8, C_DKRED, 7)
    dot(ax, 9.0, 3.2, C_DKRED, 7)
    dot(ax, 9.0, 2.6, C_DKRED, 7)
    wire(ax, 9.0, 2.6, 9.0, 3.8, C_DKRED, LW_PW)
    wire(ax, 9.0, sp_y, 10.0, sp_y, C_DKRED, LW_PW)
    label(ax, 9.5, sp_y + 0.2, "SP_BUS", C_DKRED, 10, 'center', 'bottom', True)

    # KSP switch
    ksp_sw = elm.Switch().at((10.0, sp_y)).right().color(C_DKRED)
    d2 += ksp_sw
    ksp_end = 10.0 + 1.8

    label(ax, 10.9, sp_y + 0.35, "KSP  (125A NO)", '#F57F17', 11,
          'center', 'bottom', True)

    finish_drawing(d2, ax)

    # KSP → 1-phase load
    wire(ax, ksp_end, sp_y, 13.5, sp_y, C_DKRED, LW_PW)
    block(ax, 13.5, sp_y - 0.75, 2.5, 1.5,
          "1\u03A6 LOAD", C_PURPLE, '#7B1FA2', 14)
    label(ax, 14.75, sp_y - 0.3, "125A max", '#7B1FA2', 12)

    # ─── NEUTRAL BUS ───
    ny = 1.0
    wire(ax, agx_r, neut_y, agx_r, ny, C_NEUT, LW_N)
    wire(ax, agx_r, ny, 16.0, ny, C_NEUT, LW_N)
    label(ax, 7.0, ny - 0.25,
          "NEUTRAL BUS  (common return \u2014 not switched \u2014 to all loads)",
          C_NEUT, 12, 'center', 'top', True)

    ld_r = ld_x + ldw  # 12.7
    nr_x = 13.0

    wire(ax, nr_x, ny, nr_x, pha_y, C_NEUT, LW_N)
    dot(ax, nr_x, ny, C_NEUT, 10)
    label(ax, nr_x - 0.15, 4.75, "NEUTRAL", C_NEUT, 11, 'right', 'center', True)
    label(ax, nr_x - 0.15, 4.4, "(permanent,", C_NEUT, 9, 'right', 'center')
    label(ax, nr_x - 0.15, 4.15, "not switched)", C_NEUT, 9, 'right', 'center')

    for ph, y, col in phases:
        wire(ax, ld_r, y, nr_x, y, C_NEUT, LW_N)
        dot(ax, ld_r, y, C_NEUT, 9)
        dot(ax, nr_x, y, C_NEUT, 9)

    f1_nr_x = 16.1
    wire(ax, 16.0, sp_y, f1_nr_x, sp_y, C_NEUT, LW_N)
    wire(ax, f1_nr_x, sp_y, f1_nr_x, ny, C_NEUT, LW_N)
    dot(ax, 16.0, sp_y, C_NEUT, 9)
    dot(ax, f1_nr_x, ny, C_NEUT, 9)

    # ─── INTERLOCK & WIRE COLOURS ───
    label(ax, 15.3, 9.5, "INTERLOCK", C_DKRED, 13, 'center', 'center', True)
    label(ax, 15.3, 9.0,
          "K3 group and K1+KSP\nare MUTUALLY EXCLUSIVE",
          C_DKRED, 10, 'center', 'center', True)
    label(ax, 15.3, 8.3,
          "NC aux contacts in\ncoil supply paths\nprevent both energised",
          C_DKRED, 9, 'center', 'center')

    label(ax, 15.3, 7.4, "WIRE COLOURS", '#424242', 12, 'center', 'center', True)
    for i, (lbl, c) in enumerate([
        ("Phase A = RED", C_PH_A), ("Phase B = BROWN", C_PH_B),
        ("Phase C = GREY", C_PH_C), ("Neutral = BLACK", C_NEUT)]):
        label(ax, 15.3, 7.0 - i * 0.35, lbl, c, 11, 'center', 'center', True)

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

    y24, y0v = draw_supply_rails(ax, 10.2)

    k3a_y, k3b_y, k3c_y = 8.0, 7.2, 6.5
    k1_y, ksp_y = 4.4, 3.6

    d = new_drawing(ax, unit=1.5, fontsize=10)

    # ─── ESP32 IC ───
    esp = (elm.Ic()
        .side('L', spacing=0.8, pad=0.4, leadlen=0.8)
        .side('R', spacing=0.8, pad=0.4, leadlen=0.8)
        .pin(name='G25', side='right', pin='GPIO25')
        .pin(name='G26', side='right', pin='GPIO26')
        .pin(name='G27', side='right', pin='GPIO27')
        .pin(name='G16', side='right', pin='GPIO16')
        .pin(name='G17', side='right', pin='GPIO17')
        .label('ESP32\nDevKit V1'))
    d += esp.at((0.5, 3.2))

    # ─── ULN2003A IC ───
    uln = (elm.Ic()
        .side('L', spacing=0.8, pad=0.4, leadlen=0.8)
        .side('R', spacing=0.8, pad=0.4, leadlen=0.8)
        .pin(name='I1', side='left', pin='IN1')
        .pin(name='I2', side='left', pin='IN2')
        .pin(name='I3', side='left', pin='IN3')
        .pin(name='I4', side='left', pin='IN4')
        .pin(name='I5', side='left', pin='IN5')
        .side('T', spacing=1.0, pad=0.5, leadlen=0.5)
        .side('B', spacing=1.0, pad=0.5, leadlen=0.5)
        .pin(name='COM', side='top', pin='+24V')
        .pin(name='GND', side='bot', pin='0V')
        .label('ULN2003A\nDarlington'))
    d += uln.at((5.5, 3.2))

    finish_drawing(d, ax)

    # ─── Drive wires ESP32 → ULN (matplotlib for control) ───
    drive_pins = [
        ("K3A", k3a_y, C_PH_A),
        ("K3B", k3b_y, C_PH_B),
        ("K3C", k3c_y, C_PH_C),
        ("K1",  k1_y,  C_DKRED),
        ("KSP", ksp_y, C_DKRED),
    ]

    # Get IC anchor positions from the drawn elements
    esp_pins_x = 3.6   # approx right edge of ESP32 IC
    uln_l_x = 5.5      # approx left edge of ULN IC
    uln_r_x = 9.0      # approx right edge of ULN IC

    for i, (name, y, col) in enumerate(drive_pins):
        # Approximate pin y-positions (IC pins are evenly spaced)
        pin_y = 7.6 - i * 0.8
        wire(ax, esp_pins_x, pin_y, uln_l_x, pin_y, col, LW_DRV)
        dot(ax, esp_pins_x, pin_y, col, 5)
        dot(ax, uln_l_x, pin_y, col, 5)

    label(ax, (esp_pins_x + uln_l_x) / 2, 8.2,
          "3.3V logic", C_DKGREEN, 10, 'center', 'bottom', True)

    # ─── K3 COIL BUS with interlock chain ───
    d3 = new_drawing(ax, unit=1.2, fontsize=9)

    # Interlock: +24V → K1_NC → KSP_NC → K3 bus
    label(ax, 11.5, 9.0, "K3 COIL BUS (via interlock)", C_BLUE, 13,
          'center', 'center', True)

    # NC switch symbols in series for interlock
    intlk_y = 8.5
    wire(ax, 9.5, intlk_y, 10.0, intlk_y, C_RAIL, LW_DRV)
    dot(ax, 9.5, intlk_y, C_RAIL, 6)
    label(ax, 9.5, intlk_y + 0.15, "+24V", C_RAIL, 9, 'center', 'bottom', True)

    nc1 = elm.Switch(action='close').at((10.0, intlk_y)).right().color(C_BLUE)
    d3 += nc1
    label(ax, 10.6, intlk_y - 0.25, "K1_NC", C_BLUE, 9, 'center', 'top', True)

    wire(ax, 11.2, intlk_y, 11.5, intlk_y, C_BLUE, LW_DRV)

    nc2 = elm.Switch(action='close').at((11.5, intlk_y)).right().color(C_BLUE)
    d3 += nc2
    label(ax, 12.1, intlk_y - 0.25, "KSP_NC", C_BLUE, 9, 'center', 'top', True)

    # K3 coils (inductor symbols)
    for name, uy, col in [("K3A", 7.8, C_PH_A), ("K3B", 7.2, C_PH_B),
                           ("K3C", 6.6, C_PH_C)]:
        wire(ax, uln_r_x, uy, 10.5, uy, col, LW_DRV)
        coil = elm.Inductor2(loops=3).at((10.5, uy)).right().color(col)
        d3 += coil
        label(ax, 11.8, uy + 0.15, f"{name} coil", col, 10,
              'left', 'bottom', True)
        # Coil to 0V
        wire(ax, 12.0, uy, 13.5, uy, C_RAIL0, 1.5)
        label(ax, 13.5, uy, "0V", C_RAIL0, 9, 'left', 'center', True)

    # Bus drop from interlock to coils
    wire(ax, 12.7, intlk_y, 12.7, 6.6, C_BLUE, LW_DRV)
    label(ax, 12.9, 8.0, "K3 BUS", C_BLUE, 9, 'left', 'center', True)
    for uy in [7.8, 7.2, 6.6]:
        dot(ax, 12.7, uy, C_BLUE, 5)
        wire(ax, 10.5, uy, 10.5, uy, C_BLUE, 1.0)

    # ─── K1/KSP COIL BUS with interlock chain ───
    label(ax, 11.5, 5.6, "K1/KSP COIL BUS (via interlock)", C_DKRED, 13,
          'center', 'center', True)

    intlk2_y = 5.2
    wire(ax, 9.5, intlk2_y, 10.0, intlk2_y, C_RAIL, LW_DRV)
    dot(ax, 9.5, intlk2_y, C_RAIL, 6)
    label(ax, 9.5, intlk2_y + 0.15, "+24V", C_RAIL, 9, 'center', 'bottom', True)

    nc3 = elm.Switch(action='close').at((10.0, intlk2_y)).right().color(C_DKRED)
    d3 += nc3
    label(ax, 10.6, intlk2_y - 0.25, "K3A_NC", C_DKRED, 9, 'center', 'top', True)

    nc4 = elm.Switch(action='close').at((11.5, intlk2_y)).right().color(C_DKRED)
    d3 += nc4
    label(ax, 12.1, intlk2_y - 0.25, "K3B_NC", C_DKRED, 9, 'center', 'top', True)

    nc5 = elm.Switch(action='close').at((13.0, intlk2_y)).right().color(C_DKRED)
    d3 += nc5
    label(ax, 13.6, intlk2_y - 0.25, "K3C_NC", C_DKRED, 9, 'center', 'top', True)

    wire(ax, 11.2, intlk2_y, 11.5, intlk2_y, C_DKRED, LW_DRV)
    wire(ax, 12.7, intlk2_y, 13.0, intlk2_y, C_DKRED, LW_DRV)

    # K1 and KSP coils
    for name, uy, col in [("K1", 4.4, C_DKRED), ("KSP", 3.6, C_DKRED)]:
        wire(ax, uln_r_x, uy, 10.5, uy, col, LW_DRV)
        coil = elm.Inductor2(loops=3).at((10.5, uy)).right().color(col)
        d3 += coil
        label(ax, 11.8, uy + 0.15, f"{name} coil", col, 10,
              'left', 'bottom', True)
        wire(ax, 12.0, uy, 13.5, uy, C_RAIL0, 1.5)
        label(ax, 13.5, uy, "0V", C_RAIL0, 9, 'left', 'center', True)

    # Bus drop from interlock to K1/KSP coils
    wire(ax, 14.2, intlk2_y, 14.2, 3.6, C_DKRED, LW_DRV)
    label(ax, 14.4, 4.6, "K1/KSP\nBUS", C_DKRED, 9, 'left', 'center', True)
    for uy in [4.4, 3.6]:
        dot(ax, 14.2, uy, C_DKRED, 5)

    finish_drawing(d3, ax)

    # ─── HARDWARE E-STOP (info panel) ───
    block(ax, 0.5, 0.3, 8.5, 2.6,
          "HARDWARE E-STOP  (independent of ESP32)",
          C_RED_BG, C_DKRED, 13)
    label(ax, 0.7, 2.3,
          "NC mushroom-head switch in +24V supply line before BOTH interlock buses",
          C_DKRED, 11, 'left', 'center', True)
    label(ax, 0.7, 1.85,
          "When pressed: physically cuts +24V to ALL contactor coils",
          '#424242', 10, 'left', 'center')
    label(ax, 0.7, 1.5,
          "Works even if ESP32 has crashed or firmware is hung",
          '#424242', 10, 'left', 'center')
    label(ax, 0.7, 1.1,
          "See Page 6 for full mains input and 24V PSU wiring",
          '#E65100', 10, 'left', 'center', True)

    # ─── LEGEND ───
    block(ax, 10.0, 0.3, 6.0, 2.6, "", C_GREY_BG, C_LGREY, 10)
    label(ax, 10.3, 2.5,
          "DRIVE SIGNAL FLOW:", '#424242', 10, 'left', 'center', True)
    label(ax, 10.3, 2.1,
          "ESP32 GPIO (3.3V) \u2192 ULN IN \u2192 ULN OUT (24V sink) \u2192 coil \u2192 0V",
          '#424242', 9.5, 'left', 'center', False, True)
    label(ax, 10.3, 1.7,
          "ULN2003: 7-ch Darlington, 500mA/ch, internal flyback diodes",
          C_LGREY, 9, 'left', 'center')
    label(ax, 10.3, 1.2,
          "NC switches shown CLOSED (normal state: interlocks allowing operation)",
          C_BLUE, 9, 'left', 'center', True)
    label(ax, 10.3, 0.8,
          "When contactor energises, its NC aux opens \u2192 blocks opposing bus",
          C_LGREY, 9, 'left', 'center')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 3: FEEDBACK OPTOCOUPLERS
# ══════════════════════════════════════════

def page_feedback(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 FEEDBACK OPTOCOUPLERS",
        "5\u00d7 PC817 (4-pin DIP)  |  Isolated contactor state sensing"
        "  |  24V \u2192 3.3V level shift")

    y24, y0v, y33 = draw_supply_rails(ax, 10.2, show_33v=True)

    d = new_drawing(ax, unit=1.3, fontsize=9)

    # 5 optocoupler circuits stacked vertically — 1.7 unit spacing avoids overlap
    opto_data = [
        ("PC817-1", "K3A", "GPIO32", 8.5, C_PH_A),
        ("PC817-2", "K3B", "GPIO33", 6.8, C_PH_B),
        ("PC817-3", "K3C", "GPIO34", 5.1, C_PH_C),
        ("PC817-4", "K1",  "GPIO36", 3.4, C_DKRED),
        ("PC817-5", "KSP", "GPIO39", 1.7, C_DKRED),
    ]

    for pc_name, contactor, gpio, cy, col in opto_data:
        # ─── Optocoupler symbol ───
        opto = elm.Optocoupler().at((6.5, cy)).anchor('anode')
        d += opto

        # ─── 24V side (left): +24V → 4.7kΩ → anode ───
        d += elm.Resistor().at((4.0, cy)).right().label('4.7k\u03A9', loc='top').color(col)
        res_end_x = 4.0 + 1.3  # unit=1.3
        wire(ax, res_end_x, cy, 6.5, cy, col, LW_W)

        # +24V connection stub
        wire(ax, 3.2, cy, 4.0, cy, C_RAIL, LW_W)
        dot(ax, 3.2, cy, C_RAIL, 5)
        label(ax, 3.0, cy, "+24V", C_RAIL, 8, 'right', 'center', True)

        # cathode → AUX switch → 0V
        cath_y = cy - 0.75  # cathode offset (from anchor data)
        wire(ax, 6.05, cath_y, 4.5, cath_y, col, LW_W)
        sw = elm.Switch(action='close').at((3.2, cath_y)).right().color(col)
        d += sw
        label(ax, 3.8, cath_y - 0.25, f"{contactor}\nAUX(NO)", col, 8,
              'center', 'top', True)
        wire(ax, 2.5, cath_y, 3.2, cath_y, C_RAIL0, LW_W)
        dot(ax, 2.5, cath_y, C_RAIL0, 5)
        label(ax, 2.3, cath_y, "0V", C_RAIL0, 8, 'right', 'center', True)

        # ─── 3.3V side (right): 3.3V → 10kΩ → collector junction → GPIO ───
        coll_y = cy - 0.025  # collector offset
        coll_x = 6.5 + 2.4   # collector x position

        # 10kΩ pull-up from 3.3V to collector
        wire(ax, coll_x, coll_y, 10.0, coll_y, col, LW_W)
        d += elm.Resistor().at((10.0, coll_y)).right().label('10k\u03A9', loc='top').color(col)
        res2_end = 10.0 + 1.3
        wire(ax, res2_end, coll_y, 12.5, coll_y, C_33V, LW_W)
        dot(ax, 12.5, coll_y, C_33V, 5)
        label(ax, 12.7, coll_y, "3.3V", C_33V, 8, 'left', 'center', True)

        # GPIO tap from collector junction
        dot(ax, 10.0, coll_y, col, 5)
        wire(ax, 10.0, coll_y, 10.0, coll_y + 0.4, col, LW_W)
        label(ax, 10.0, coll_y + 0.5, gpio, col, 9, 'center', 'bottom', True)

        # emitter → 0V/GND (placed directly at emitter to save vertical space)
        emit_y = cy - 0.725
        emit_x = coll_x
        d += elm.Ground().at((emit_x, emit_y)).color(col)

        # Label
        label(ax, 7.5, cy + 0.3, pc_name, '#E65100', 9, 'center', 'bottom', True)

    finish_drawing(d, ax)

    # ─── LOGIC NOTES ───
    block(ax, 13.5, 1.5, 3.0, 7.8, "LOGIC", C_GREY_BG, C_LGREY, 12)
    label(ax, 13.7, 8.6,
          "AUX CLOSED:", C_DKGREEN, 10, 'left', 'center', True)
    label(ax, 13.7, 8.2,
          "LED biased ON\n\u2192 opto conducts\n\u2192 GPIO reads LOW",
          C_DKGREEN, 9, 'left', 'center')
    label(ax, 13.7, 7.2,
          "AUX OPEN:", C_DKRED, 10, 'left', 'center', True)
    label(ax, 13.7, 6.8,
          "LED has no bias\n\u2192 opto off\n\u2192 pull-up \u2192 HIGH",
          C_DKRED, 9, 'left', 'center')
    label(ax, 13.7, 5.8,
          "GPIO is INPUT\nonly \u2014 does not\ndrive anything",
          C_LGREY, 9, 'left', 'center')
    label(ax, 13.7, 4.6,
          "LADN11 blocks:\nNO = feedback\nNC = interlock\n(see Page 2)",
          C_LGREY, 9, 'left', 'center')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 4: LEDs & E-STOP
# ══════════════════════════════════════════

def page_leds_estop(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 STATUS LEDs & E-STOP",
        "3\u00d7 status LEDs with calculated resistors"
        "  |  Software + hardware E-stop")

    # ─── STATUS LEDs (upper section) ───
    label(ax, 8.0, 10.2,
          "STATUS LEDs", '#F57F17', 18, 'center', 'center', True)
    label(ax, 8.0, 9.85,
          "ESP32 3.3V GPIO \u2192 resistor \u2192 LED \u2192 GND",
          '#F57F17', 12, 'center', 'center', False, True)

    d = new_drawing(ax, unit=2.0, fontsize=11)

    led_data = [
        ("GREEN", "GPIO18", "330\u03A9", "green", 9.0,
         "Vf\u22482.0V  I=(3.3\u22122.0)/330=3.9mA",
         "ON = any FORM3 phase active", C_DKGREEN),
        ("BLUE",  "GPIO19", "100\u03A9", "blue", 7.5,
         "Vf\u22483.0V  I=(3.3\u22123.0)/100=3.0mA",
         "ON = FORM1 active (K1+KSP)", C_DKBLUE),
        ("RED",   "GPIO21", "330\u03A9", "red", 6.0,
         "Vf\u22481.8V  I=(3.3\u22121.8)/330=4.5mA",
         "BLINK = fault  |  SOLID = E-stop", C_DKRED),
    ]

    for colour, gpio, res, fill, cy, calc, note, col in led_data:
        # GPIO label
        label(ax, 1.5, cy, gpio, col, 12, 'right', 'center', True, True)

        # GPIO dot → resistor → LED → ground
        d += elm.Dot(open=True).at((2.0, cy)).color(col)
        d += elm.Line().right().length(0.5).color(col)
        d += elm.Resistor().right().label(res, loc='top').color(col)
        d += elm.LED(fill=fill).right().label(f"{colour}", loc='top').color(col)
        d += elm.Line().down().length(0.5).color(col)
        d += elm.Ground().color(col)

        # Annotations
        label(ax, 8.5, cy, calc, '#424242', 10, 'left', 'center', False, True)
        label(ax, 12.0, cy, note, C_LGREY, 10, 'left', 'center')

    finish_drawing(d, ax)

    # ─── Divider ───
    wire(ax, 0.5, 5.2, 16.0, 5.2, C_LGREY, 1.5)

    # ─── E-STOP (lower section) ───
    label(ax, 8.0, 4.9,
          "E-STOP  (two independent systems)", C_DKRED, 18,
          'center', 'center', True)

    d2 = new_drawing(ax, unit=1.8, fontsize=10)

    # ── SOFTWARE E-STOP (left side) ──
    label(ax, 4.0, 4.4, "SOFTWARE E-STOP", C_DKRED, 14,
          'center', 'center', True)

    # 3.3V → 10kΩ pull-up → junction → GPIO35
    label(ax, 1.0, 3.5, "3.3V", C_33V, 11, 'right', 'center', True)
    d2 += elm.Dot(open=True).at((1.3, 3.5)).color(C_33V)
    d2 += elm.Resistor().right().label('10k\u03A9\npull-up', loc='top').color(C_WIRE)
    # Junction point
    d2 += elm.Dot().color(C_WIRE)
    junc_x = 1.3 + 1.8  # after resistor

    # Junction → GPIO35
    d2 += elm.Line().right().length(1.5).color(C_WIRE)
    label(ax, junc_x + 1.8, 3.5, "GPIO35", C_DKRED, 11, 'left', 'center', True, True)

    # Junction → button → GND (downward)
    d2 += elm.Button().at((junc_x, 3.5)).down().label('NO\npushbutton', loc='right').color(C_DKRED)
    d2 += elm.Ground().color(C_DKRED)

    label(ax, 1.5, 1.5,
          "Press \u2192 GPIO reads LOW \u2192 firmware disables all outputs",
          '#424242', 10, 'left', 'center')
    label(ax, 1.5, 1.1,
          "Send '0' command to reset from ESTOP state",
          C_LGREY, 9, 'left', 'center')

    # ── HARDWARE E-STOP (right side) ──
    label(ax, 12.0, 4.4, "HARDWARE E-STOP", C_DKRED, 14,
          'center', 'center', True)

    # +24V → NC mushroom-head → +24V RAIL
    label(ax, 8.5, 3.5, "+24V\n(from PSU)", C_RAIL, 10,
          'right', 'center', True)
    d2 += elm.Dot(open=True).at((9.0, 3.5)).color(C_RAIL)
    d2 += elm.Line().right().length(0.5).color(C_RAIL)
    d2 += elm.Button(nc=True).right().label('NC mushroom-head\nE-STOP', loc='top').color(C_DKRED)
    d2 += elm.Line().right().length(0.5).color(C_RAIL)
    label(ax, 13.5, 3.5, "+24V RAIL\n(to interlock\nbuses)", C_RAIL, 10,
          'left', 'center', True)

    finish_drawing(d2, ax)

    label(ax, 9.0, 1.5,
          "When pressed: physically cuts +24V to ALL contactor coils",
          C_DKRED, 10, 'left', 'center', True)
    label(ax, 9.0, 1.1,
          "Works even if ESP32 has crashed or firmware is hung",
          '#424242', 10, 'left', 'center')
    label(ax, 9.0, 0.7,
          "Twist to release, then send '0' to clear firmware state",
          C_LGREY, 9, 'left', 'center')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 5: PINOUT TABLE + COMMANDS + BOM
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
        ["19",  "OUT", "LED blue",      "100\u03A9 \u2192 LED \u2192 GND",
         "FORM1 active (3mA)"],
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

    # ─── SERIAL COMMANDS ───
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
        ("2\u00d7", "330\u03A9 + LED (green, red)",
         "Status LEDs",     "~\u00a30.25 ea"),
        ("1\u00d7", "100\u03A9 + LED (blue)",
         "FORM1 indicator", "~\u00a30.25"),
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

    for hdr, (cx_, w) in zip(
        ["QTY", "DESCRIPTION", "FOR", "PRICE"], bom_col_defs):
        ax.add_patch(mpatches.Rectangle(
            (cx_ - 0.05, bom_ty - 0.05), w, bom_row_h,
            facecolor=C_DKBLUE, edgecolor='white', linewidth=1))
        label(ax, cx_ + 0.08, bom_ty + 0.08, hdr, 'white', 10,
              'left', 'center', True, True)

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

    label(ax, bom_x, 4.3,
          "TOTAL ESTIMATE:  ~\u00a3670 - \u00a31,120 (ex VAT)",
          C_DKGREEN, 12, 'left', 'center', True)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════
# PAGE 6: MAINS INPUT & 24V PSU
# ══════════════════════════════════════════

def page_mains_psu(pdf):
    fig, ax = new_page(pdf,
        "AGX TEST BOX \u2014 MAINS INPUT & 24V POWER SUPPLY",
        "230VAC mains input  |  DIN-rail PSU  |  Hardware E-stop"
        "  |  Earth bonding")

    # ─── POWER CHAIN (upper section) ───
    label(ax, 8.0, 10.2,
          "MAINS TO 24V POWER CHAIN", C_TEAL, 16, 'center', 'center', True)

    d = new_drawing(ax, unit=2.0, fontsize=10)

    # IEC inlet → Fuse → MCB → PSU → E-stop → +24V rail
    chain_y = 8.5

    # IEC C14 inlet (terminal)
    label(ax, 0.5, chain_y + 0.5, "230VAC MAINS INPUT", '#E65100', 12,
          'left', 'bottom', True)
    label(ax, 0.5, chain_y, "IEC C14\npanel inlet", '#E65100', 10,
          'left', 'center')
    d += elm.Dot(open=True).at((2.5, chain_y)).color('#8B4513')
    label(ax, 2.3, chain_y + 0.15, "L", '#8B4513', 10, 'right', 'bottom', True)

    # Fuse
    d += elm.Fuse().right().label('6A fuse', loc='top').color('#8B4513')

    # MCB (breaker)
    d += elm.Breaker().right().label('MCB 6A\nType B', loc='top').color('#8B4513')

    # PSU as IC
    psu = (elm.Ic()
        .side('L', spacing=0.6, pad=0.3, leadlen=0.5)
        .side('R', spacing=0.6, pad=0.3, leadlen=0.5)
        .pin(name='Lin', side='left', pin='L')
        .pin(name='Nin', side='left', pin='N')
        .pin(name='PEin', side='left', pin='PE')
        .pin(name='Vp', side='right', pin='+V')
        .pin(name='Vm', side='right', pin='\u2212V')
        .label('HDR-100-24\n24VDC 5A'))
    d += psu.at((8.0, chain_y - 1.5))

    finish_drawing(d, ax)

    # Wire from breaker end to PSU L input (approximate)
    wire(ax, 6.5, chain_y, 7.5, chain_y, '#8B4513', LW_PW)
    # Show the PSU connections with labels
    label(ax, 8.0, chain_y + 1.2, "24V DIN-RAIL PSU", C_TEAL, 14,
          'left', 'bottom', True)
    label(ax, 8.0, chain_y + 0.8, "Mean Well HDR-100-24", C_TEAL, 10,
          'left', 'bottom')
    label(ax, 8.2, chain_y - 0.2, "Input: 85\u2013264VAC", '#424242', 9,
          'left', 'center')
    label(ax, 8.2, chain_y - 0.5, "Output: 24VDC / 5A (120W)", C_TEAL, 9,
          'left', 'center', True)

    # +V output → E-stop → +24V rail
    d2 = new_drawing(ax, unit=1.8, fontsize=10)

    psu_r = 11.5  # approx right edge of PSU IC
    estop_y = 8.0
    wire(ax, psu_r, estop_y, 12.0, estop_y, C_RAIL, LW_PW)
    label(ax, psu_r + 0.1, estop_y + 0.15, "+V", C_RAIL, 9, 'left', 'bottom', True)

    d2 += elm.Button(nc=True).at((12.0, estop_y)).right().label('HW E-STOP\n(NC)', loc='top').color(C_DKRED)

    finish_drawing(d2, ax)

    estop_end = 12.0 + 1.8
    wire(ax, estop_end, estop_y, 15.5, estop_y, C_RAIL, LW_PW)
    label(ax, 15.5, estop_y, "+24VDC\nRAIL", C_RAIL, 11, 'left', 'center', True)

    # -V output → 0V rail
    ov_y = 7.0
    wire(ax, psu_r, ov_y, 15.5, ov_y, C_RAIL0, LW_PW)
    label(ax, psu_r + 0.1, ov_y + 0.15, "\u2212V", C_RAIL0, 9, 'left', 'bottom', True)
    label(ax, 15.5, ov_y, "0V RAIL\n(GND)", C_RAIL0, 11, 'left', 'center', True)

    # Neutral wire
    n_y = chain_y - 0.6
    wire(ax, 2.5, n_y, 7.5, n_y, '#1565C0', LW_PW)
    dot(ax, 2.5, n_y, '#1565C0', 8)
    label(ax, 2.3, n_y + 0.15, "N", '#1565C0', 10, 'right', 'bottom', True)

    # Earth wire
    d3 = new_drawing(ax, unit=1.5, fontsize=10)
    e_y = chain_y - 1.2
    wire(ax, 2.5, e_y, 5.0, e_y, C_DKGREEN, LW_PW)
    dot(ax, 2.5, e_y, C_DKGREEN, 8)
    label(ax, 2.3, e_y + 0.15, "PE", C_DKGREEN, 10, 'right', 'bottom', True)
    d3 += elm.Ground().at((5.5, e_y)).color(C_DKGREEN)
    label(ax, 5.8, e_y - 0.3, "Enclosure\nbonding stud", C_DKGREEN, 9,
          'left', 'center')

    # Earth to DIN rail
    d3 += elm.Ground().at((7.5, e_y)).color(C_DKGREEN)
    wire(ax, 5.5, e_y, 7.5, e_y, C_DKGREEN, LW_PW)
    label(ax, 7.8, e_y - 0.3, "DIN rail", C_DKGREEN, 9, 'left', 'center')

    finish_drawing(d3, ax)

    # ─── EARTH BONDING & SAFETY NOTES (lower section) ───
    block(ax, 0.5, 0.5, 15.5, 5.0,
          "EARTH BONDING & SAFETY NOTES", '#E8F5E9', C_DKGREEN, 15)

    label(ax, 0.8, 4.7,
          "EARTH BONDING PATH:", C_DKGREEN, 13, 'left', 'center', True)
    label(ax, 0.8, 4.2,
          "IEC inlet E (green/yellow) \u2192 enclosure bonding stud \u2192 DIN rail \u2192 PSU PE terminal",
          '#424242', 10, 'left', 'center', False, True)
    label(ax, 0.8, 3.75,
          "All metal parts of enclosure must be bonded to protective earth",
          C_LGREY, 9, 'left', 'center')

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
        page_leds_estop(pdf)
        page_pinout_bom(pdf)
        page_mains_psu(pdf)

    print(f"PDF saved: {OUT}")
    print(f"  6 pages, A3 landscape, schemdraw circuit symbols")
    print(f"  Page 1: Power path - switch symbols for K3A/K3B/K3C + K1/KSP")
    print(f"  Page 2: Relay drive - ESP32/ULN2003A ICs, coil symbols, interlock")
    print(f"  Page 3: Feedback - PC817 optocoupler symbols with resistors")
    print(f"  Page 4: LEDs & E-stop - LED/resistor/ground + button circuits")
    print(f"  Page 5: GPIO pinout, serial commands, BOM")
    print(f"  Page 6: Mains input - fuse, breaker, PSU, E-stop, earth symbols")


if __name__ == "__main__":
    main()
