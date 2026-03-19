# AGX Switching Box - Remote Control

Remote-controlled contactor switching box for Pacific Power Source AGX/AFX programmable AC power sources. Switches between **FORM 3** (three-phase, 40A/phase, individual loads) and **FORM 1** (single-phase, 125A, all phases commoned) via USB serial from a laptop.

Built for equipment calibration workflows where you need to frequently switch between per-phase testing and maximum single-phase output.

## Overview

```
 LAPTOP  ◄──USB──►  ESP32  ──►  ULN2003A  ──►  CONTACTORS  ──►  LOADS
                    (3.3V)      (24V driver)    (40A / 125A)
```

| Mode | Phases | Current | Contactors | Use Case |
|------|--------|---------|------------|----------|
| **FORM 3** | 3-phase separate | 40A/phase | K3A, K3B, K3C | Individual phase calibration |
| **FORM 1** | 1-phase commoned | 125A | K1A, K1B, K1C + KSP | Max single-phase current |

## Safety

Four independent layers of protection prevent both contactor groups being energised simultaneously:

1. **Software interlock** - Break-before-make sequencing with feedback verification
2. **Hardware interlock** - NC auxiliary contacts in coil supply paths (independent of ESP32)
3. **Mechanical interlock** - Optional physical bar between contactors
4. **E-stop** - NC mushroom-head in +24V supply + NO pushbutton to ESP32

## Repository Structure

```
├── README.md                          ← You are here
├── firmware/
│   └── agx_switch_controller.ino      ← ESP32 Arduino firmware
├── docs/
│   └── OPERATION_MANUAL.md            ← Detailed operation manual
└── diagrams/
    ├── AGX_Test_Box_Circuit.pdf       ← Circuit block diagrams (4 pages)
    └── agx_circuit_pdf.py             ← Python script to regenerate diagrams
```

## Quick Start

### 1. Flash the Firmware

1. Install [Arduino IDE](https://www.arduino.cc/en/software) with ESP32 board support
2. Open `firmware/agx_switch_controller.ino`
3. Select board: **ESP32 Dev Module**
4. Select correct COM port
5. Upload

### 2. Connect Hardware

See the [Operation Manual](docs/OPERATION_MANUAL.md) for full wiring details. Key connections:

| ESP32 Pin | Function | Connects To |
|-----------|----------|-------------|
| GPIO25 | FORM 3 drive | ULN2003 IN1 → K3 coils |
| GPIO26 | K1 drive | ULN2003 IN2 → K1 coils |
| GPIO27 | KSP drive | ULN2003 IN3 → KSP coil |
| GPIO32 | K3 feedback | PC817 opto → K3 AUX(NO) |
| GPIO33 | K1 feedback | PC817 opto → K1 AUX(NO) |
| GPIO34 | KSP feedback | PC817 opto → KSP AUX(NO) |
| GPIO35 | E-stop | NO pushbutton to GND |
| GPIO18/19/21 | LEDs | Green/Blue/Red via 330R |

**Supply rails:** +24VDC from DIN-rail PSU to ULN2003 COM. 0V shared with ESP32 GND.

### 3. Control via Serial

Open a serial terminal at **115200 baud** and send single-character commands:

| Command | Action |
|---------|--------|
| `3` | Switch to FORM 3 (three-phase) |
| `1` | Switch to FORM 1 (single-phase) |
| `0` | All OFF (safe state) |
| `S` | Query status |
| `T` | Run self-test |

## Documentation

- **[Operation Manual](docs/OPERATION_MANUAL.md)** - Comprehensive guide covering:
  - System architecture and block diagrams
  - All operating modes (FORM 3, FORM 1, OFF)
  - Hardware description (ESP32, ULN2003A, contactors, optocouplers)
  - Supply rails and power distribution (+24VDC, 0V, 3.3V)
  - Complete wiring tables and connection diagrams
  - Hardware interlock system (NC auxiliary contacts)
  - Feedback and state verification (PC817 optocouplers)
  - Firmware state machine and timing
  - Serial command protocol with example session
  - Mode-change sequence (step-by-step with timing)
  - Four-layer safety system
  - LED indicator meanings
  - Commissioning procedure
  - Troubleshooting guide

- **[Circuit Diagrams (PDF)](diagrams/AGX_Test_Box_Circuit.pdf)** - 4-page A4 landscape:
  - Page 1: Power path (FORM 3 + FORM 1 routing, phase colours, neutral bus)
  - Page 2: Control system with supply rails (+24V / 0V clearly marked)
  - Page 3: ESP32 GPIO pinout table, mode-change sequence, device list
  - Page 4: Bill of materials with UK suppliers and pricing (~£515-£905)

## Wire Colours

| Wire | Colour | Notes |
|------|--------|-------|
| Phase A | **Red** | 40A / 125A rated |
| Phase B | **Brown** | 40A / 125A rated |
| Phase C | **Grey** | 40A / 125A rated |
| Neutral | **Black** (broader) | Common return, not switched |

## Bill of Materials (Summary)

Key components (see [full BOM in PDF](diagrams/AGX_Test_Box_Circuit.pdf), page 4):

| Item | Part | Approx Price (ex VAT) |
|------|------|-----------------------|
| FORM 3 contactor (40A) | Schneider LC1D40BD | ~£154 |
| FORM 1 combine contactor (40A) | Schneider LC1D40BD | ~£154 |
| FORM 1 output contactor (125A) | Schneider LP1D80004BD | ~£588 |
| ESP32 DevKit V1 | ESP32-WROOM-32 | ~£8-15 |
| ULN2003A Darlington driver | TI ULN2003AN | ~£0.50 |
| 3x PC817 optocoupler | Sharp PC817X | ~£0.30 each |
| 24V DIN-rail PSU | Mean Well HDR-100-24 | ~£30-45 |
| **Total estimate** | | **~£515 - £905** |

UK suppliers: RS Components, Farnell, Mouser, TLA UK, Amazon UK, Screwfix/CEF.

## Regenerating Diagrams

The circuit diagrams are generated from Python using matplotlib:

```bash
pip install matplotlib
python diagrams/agx_circuit_pdf.py
```

This produces `AGX_Test_Box_Circuit.pdf` in the Downloads folder.

## Status

**Discussion document** - verify all ratings, part numbers, and wiring against Pacific Power Source documentation and have the design reviewed by a qualified electrical engineer before building.

## Licence

This project is provided as-is for discussion and development purposes.
