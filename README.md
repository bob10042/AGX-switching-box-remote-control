# AGX Switching Box - Remote Control

Remote-controlled contactor switching box for Pacific Power Source AGX/AFX programmable AC power sources. Provides **individual phase selection** (A, B, C independently), **FORM 3** (all three phases, 40A/phase), and **FORM 1** (single-phase, 125A commoned) via USB serial from a laptop.

Built for equipment calibration workflows where you need to frequently switch between per-phase testing and maximum single-phase output.

## Overview

```
 LAPTOP  ◄──USB──►  ESP32  ──►  ULN2003A  ──►  CONTACTORS  ──►  LOADS
                   (3.3V)      (5 channels)    (40A / 125A)
```

| Mode | Phases | Current | Contactors | Use Case |
|------|--------|---------|------------|----------|
| **Phase A** | A only | 40A | K3A | Individual phase A calibration |
| **Phase B** | B only | 40A | K3B | Individual phase B calibration |
| **Phase C** | C only | 40A | K3C | Individual phase C calibration |
| **FORM 3** | All three | 40A/phase | K3A + K3B + K3C | All phases to individual loads |
| **FORM 1** | Commoned | 125A | K1 + KSP | Max single-phase current |

## Safety

Four independent layers of protection prevent dangerous states:

1. **Software interlock** - Break-before-make sequencing with feedback verification (all 5 contactors)
2. **Hardware interlock** - NC auxiliary contacts in coil supply paths (independent of ESP32)
3. **Mechanical interlock** - Optional physical bar between contactors
4. **E-stop** - NC mushroom-head in +24V supply + NO pushbutton to ESP32

## Repository Structure

```
├── README.md                          ← You are here
├── firmware/
│   └── agx_switch_controller.ino      ← ESP32 Arduino firmware (Rev 2.0)
├── docs/
│   ├── OPERATION_MANUAL.md            ← Detailed operation manual
│   └── CONNECTION_SCHEDULE.md         ← Wire-by-wire connection list (101 wires)
└── diagrams/
    ├── AGX_Test_Box_Circuit.pdf       ← Circuit block diagrams (5 pages, A3)
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
| GPIO25 | K3A drive (Phase A) | ULN2003 IN1 → K3A coil |
| GPIO26 | K3B drive (Phase B) | ULN2003 IN2 → K3B coil |
| GPIO27 | K3C drive (Phase C) | ULN2003 IN3 → K3C coil |
| GPIO16 | K1 drive (combine) | ULN2003 IN4 → K1 coil |
| GPIO17 | KSP drive (output) | ULN2003 IN5 → KSP coil |
| GPIO32 | K3A feedback | PC817-1 opto → K3A AUX(NO) |
| GPIO33 | K3B feedback | PC817-2 opto → K3B AUX(NO) |
| GPIO34 | K3C feedback | PC817-3 opto → K3C AUX(NO) |
| GPIO36 | K1 feedback | PC817-4 opto → K1 AUX(NO) |
| GPIO39 | KSP feedback | PC817-5 opto → KSP AUX(NO) |
| GPIO35 | E-stop | NO pushbutton to GND |
| GPIO18/19/21 | LEDs | Green (330Ω) / Blue (100Ω) / Red (330Ω) |

**Mains input:** 230VAC via IEC C14 panel inlet → 6A DIN-rail MCB → 24V PSU (Mean Well HDR-100-24).

**Supply rails:** PSU +V → HW E-stop (NC) → +24VDC rail → ULN2003 COM. PSU −V → 0V rail, shared with ESP32 GND.

### 3. Control via Serial

Open a serial terminal at **115200 baud** and send single-character commands:

| Command | Action | Contactors |
|---------|--------|------------|
| `A` | Phase A only | K3A |
| `B` | Phase B only | K3B |
| `C` | Phase C only | K3C |
| `3` | FORM 3 (all three phases) | K3A + K3B + K3C |
| `1` | FORM 1 (commoned 125A) | K1 + KSP |
| `0` | All OFF (safe state) | None |
| `S` | Query status | - |
| `T` | Run self-test | - |

## Documentation

- **[Connection Schedule](docs/CONNECTION_SCHEDULE.md)** - Wire-by-wire build document:
  - 101 numbered wires (W1–W101) with From/To/Colour/Size
  - Resistor schedule with calculated values
  - LADN11 auxiliary contact block assignments
  - ULN2003A and PC817 pin assignments

- **[Operation Manual](docs/OPERATION_MANUAL.md)** - Comprehensive guide covering:
  - All operating modes (Phase A, B, C, FORM 3, FORM 1, OFF)
  - Hardware description (ESP32, ULN2003A 5-channel, 5x contactors, 5x optocouplers)
  - Mains input wiring (IEC C14 inlet, MCB, PSU, earth bonding)
  - Complete wiring tables and connection diagrams
  - Hardware interlock system (NC auxiliary contacts, two buses)
  - Feedback and state verification
  - Serial command protocol with example session
  - Safety systems and commissioning procedure

- **[Circuit Diagrams (PDF)](diagrams/AGX_Test_Box_Circuit.pdf)** - 6-page A3 landscape:
  - Page 1: Power path (individual K3A/K3B/K3C + FORM 1 + neutral returns)
  - Page 2: Relay drive circuit (ESP32 → ULN2003A → coils with interlock)
  - Page 3: Feedback optocouplers (PC817 4-pin DIP, pin-by-pin connections)
  - Page 4: Status LEDs (with calculated resistors) & E-stop (SW + HW)
  - Page 5: GPIO pinout table, serial commands, BOM
  - Page 6: Mains input, 24V DIN-rail PSU, HW E-stop, earth bonding

## Wire Colours

**Power path (AGX to loads):**

| Wire | Colour | Notes |
|------|--------|-------|
| Phase A | **Red** | 40A / 125A rated |
| Phase B | **Brown** | 40A / 125A rated |
| Phase C | **Grey** | 40A / 125A rated |
| Neutral | **Black** (broader) | Common return, not switched |

**Mains input (UK standard):**

| Wire | Colour | Notes |
|------|--------|-------|
| Live | **Brown** | IEC inlet L → MCB → PSU L |
| Neutral | **Blue** | IEC inlet N → PSU N |
| Earth | **Green/Yellow** | IEC inlet E → enclosure bond → DIN rail → PSU PE |

## Bill of Materials (Summary)

| Item | Part | Qty | Approx Price (ex VAT) |
|------|------|-----|-----------------------|
| Phase A/B/C contactors | Schneider LC1D25BD (40A) | 3 | ~£80 each |
| FORM 1 combine contactor | Schneider LC1D40BD (40A, 3-pole) | 1 | ~£154 |
| FORM 1 output contactor | Schneider LP1D80004BD (125A) | 1 | ~£588 |
| Auxiliary contact blocks | Schneider LADN11 (1NO+1NC) | 5 | ~£8 each |
| ESP32 DevKit V1 | ESP32-WROOM-32 | 1 | ~£10 |
| ULN2003A Darlington driver | TI ULN2003AN | 1 | ~£0.50 |
| PC817 optocoupler | Sharp PC817X | 5 | ~£0.30 each |
| 4.7kΩ resistor | Opto LED current limit | 5 | ~£0.05 each |
| 10kΩ resistor | Pull-up (feedback + E-stop) | 6 | ~£0.05 each |
| 330Ω resistor + LED (green, red) | Status indicators | 2 | ~£0.25 each |
| 100Ω resistor + LED (blue) | FORM1 indicator | 1 | ~£0.25 |
| 24V DIN-rail PSU | Mean Well HDR-100-24 | 1 | ~£35 |
| IEC C14 panel inlet | Mains input (with fuse holder) | 1 | ~£5 |
| DIN-rail MCB 6A type B | Mains overcurrent protection | 1 | ~£8 |
| IEC C13 mains cable | Mains lead (UK 13A plug, 3A fuse) | 1 | ~£5 |
| NC mushroom-head E-stop | HW E-stop in +24V line | 1 | ~£20 |
| NO pushbutton | SW E-stop to ESP32 GPIO35 | 1 | ~£3 |
| Enclosure IP65 | DIN-rail housing | 1 | ~£80 |
| **Total estimate** | | | **~£670 - £1,120** |

UK suppliers: RS Components, Farnell, Mouser, Amazon UK, Screwfix/CEF.

## Regenerating Diagrams

```bash
pip install matplotlib
python diagrams/agx_circuit_pdf.py
```

This produces `AGX_Test_Box_Circuit.pdf` in the Downloads folder.

## Status

**Discussion document** - verify all ratings, part numbers, and wiring against Pacific Power Source documentation and have the design reviewed by a qualified electrical engineer before building.

## Licence

This project is provided as-is for discussion and development purposes.
