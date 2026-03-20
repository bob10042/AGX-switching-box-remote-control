# AGX Test Box Switching Controller - Detailed Operation Manual

**Revision:** 2.0
**Date:** 2026-03-20
**Status:** Discussion Document - Verify with PPS documentation and electrical safety review

---

## Table of Contents

1. [Purpose and Overview](#1-purpose-and-overview)
2. [System Architecture](#2-system-architecture)
3. [Operating Modes](#3-operating-modes)
4. [Hardware Description](#4-hardware-description)
5. [Supply Rails and Power Distribution](#5-supply-rails-and-power-distribution)
6. [Wiring and Connections](#6-wiring-and-connections)
7. [Contactor Interlock System](#7-contactor-interlock-system)
8. [Feedback and State Verification](#8-feedback-and-state-verification)
9. [Firmware Operation](#9-firmware-operation)
10. [Serial Command Protocol](#10-serial-command-protocol)
11. [Mode-Change Sequence (Detailed)](#11-mode-change-sequence-detailed)
12. [Safety Systems](#12-safety-systems)
13. [LED Indicators](#13-led-indicators)
14. [Commissioning Procedure](#14-commissioning-procedure)
15. [Troubleshooting](#15-troubleshooting)
16. [Specifications Summary](#16-specifications-summary)

---

## 1. Purpose and Overview

The AGX Test Box provides remote-controlled switching between individual phase loads and combined modes on a Pacific Power Source AGX (or AFX) programmable AC power source.

| Mode | Configuration | Current Rating | Use Case |
|------|--------------|----------------|----------|
| **Phase A** | Phase A only via K3A | 40A | Single phase A calibration load |
| **Phase B** | Phase B only via K3B | 40A | Single phase B calibration load |
| **Phase C** | Phase C only via K3C | 40A | Single phase C calibration load |
| **FORM 3** | All three phases via K3A+K3B+K3C | 40A per phase | All three phases to individual loads |
| **FORM 1** | Single-phase, all phases commoned | 125A combined | Maximum single-phase current |

The switching is controlled by an ESP32 microcontroller connected to a laptop via USB serial. The operator sends single-character commands to select individual phases or switch between modes. The system includes multiple layers of safety protection.

### Why This Box Exists

During equipment calibration, you frequently need to switch between:
- **Individual phase testing**: connect a load to one specific phase for per-phase calibration
- **All-phase testing** (FORM 3): connect loads to all three phases simultaneously
- **Maximum current testing** (FORM 1): combine all three phases for maximum single-phase output

Manually rewiring between these configurations is time-consuming and error-prone. This box automates the switching with proper break-before-make sequencing, feedback verification, and hardware interlocks.

---

## 2. System Architecture

```
┌─────────────┐     USB Serial     ┌──────────────┐
│   LAPTOP    │◄──────────────────►│    ESP32      │
│  (Control   │   115200 baud      │  DevKit V1   │
│   Software) │                    │              │
└─────────────┘                    └──────┬───────┘
                                          │
                              5x GPIO     │ (3.3V logic)
                              outputs     │
                                          ▼
                                   ┌──────────────┐
                                   │  ULN2003A    │
                                   │  Darlington  │◄── +24VDC (COM pin)
                                   │  Driver      │──► 0V (GND pin)
                                   │  (5 channels)│
                                   └──────┬───────┘
                                          │
                           OUT1/OUT2/OUT3/OUT4/OUT5 (24V switched)
                                          │
                    ┌─────────┬─────────┬─┴───────┬───────────┐
                    ▼         ▼         ▼         ▼           ▼
              ┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐
              │ K3A      ││ K3B      ││ K3C      ││ K1       ││ KSP      │
              │ Phase A  ││ Phase B  ││ Phase C  ││ FORM 1   ││ FORM 1   │
              │ 40A NO   ││ 40A NO   ││ 40A NO   ││ combine  ││ output   │
              └────┬─────┘└────┬─────┘└────┬─────┘│ 3x 40A   ││ 125A NO  │
                   │           │           │      └────┬─────┘└────┬─────┘
                   ▼           ▼           ▼           └─────┬─────┘
              ┌──────────┐┌──────────┐┌──────────┐          ▼
              │ Load A   ││ Load B   ││ Load C   │   ┌────────────┐
              │ (40A)    ││ (40A)    ││ (40A)    │   │ 1-PHASE    │
              └──────────┘└──────────┘└──────────┘   │ LOAD (125A)│
                                                      └────────────┘
```

---

## 3. Operating Modes

### Phase A - Individual Phase A
- Contactor K3A energised (single-pole, Phase A only)
- K3B, K3C, K1, KSP all de-energised
- Current rating: 40A
- Use: connect calibration load to Phase A only

### Phase B - Individual Phase B
- Contactor K3B energised (single-pole, Phase B only)
- K3A, K3C, K1, KSP all de-energised
- Current rating: 40A
- Use: connect calibration load to Phase B only

### Phase C - Individual Phase C
- Contactor K3C energised (single-pole, Phase C only)
- K3A, K3B, K1, KSP all de-energised
- Current rating: 40A
- Use: connect calibration load to Phase C only

### FORM 3 - All Three Phases
- Contactors K3A, K3B, K3C all energised
- K1, KSP de-energised
- Current rating: 40A per phase
- Use: connect calibration loads to all three phases simultaneously

### FORM 1 - Single-Phase (Commoned)
- Contactor K1 energised: K1A, K1B, K1C combine all three AGX phases onto SP_BUS
- Contactor KSP energised: routes SP_BUS to single-phase load terminal
- Current rating: 125A (combined output of all three phases)
- Use: maximum single-phase current for high-power load testing
- K3A, K3B, K3C all de-energised

### OFF State
- All contactors de-energised
- All phases disconnected from all loads
- Safe state for wiring changes
- Default state on power-up

---

## 4. Hardware Description

### 4.1 ESP32 DevKit V1

The ESP32 is the central controller. It communicates with the laptop via USB serial (115200 baud) and drives 5 contactor coils via the ULN2003A.

**GPIO Pin Assignment:**

| GPIO | Direction | Function | Connects To |
|------|-----------|----------|-------------|
| 25 | OUTPUT | K3A drive | ULN2003 IN1 → K3A coil (Phase A) |
| 26 | OUTPUT | K3B drive | ULN2003 IN2 → K3B coil (Phase B) |
| 27 | OUTPUT | K3C drive | ULN2003 IN3 → K3C coil (Phase C) |
| 16 | OUTPUT | K1 drive | ULN2003 IN4 → K1 coil (FORM1 combine) |
| 17 | OUTPUT | KSP drive | ULN2003 IN5 → KSP coil (FORM1 output) |
| 32 | INPUT | K3A feedback | PC817-1 opto collector |
| 33 | INPUT | K3B feedback | PC817-2 opto collector |
| 34 | INPUT | K3C feedback | PC817-3 opto collector (INPUT ONLY) |
| 36 | INPUT | K1 feedback | PC817-4 opto collector (INPUT ONLY, VP) |
| 39 | INPUT | KSP feedback | PC817-5 opto collector (INPUT ONLY, VN) |
| 35 | INPUT | E-stop button | NO pushbutton to GND (INPUT ONLY) |
| 18 | OUTPUT | Green LED | 330R → LED → GND (Phase/FORM3 active) |
| 19 | OUTPUT | Blue LED | 330R → LED → GND (FORM1 active) |
| 21 | OUTPUT | Red LED | 330R → LED → GND (Fault/E-stop) |

**Note:** GPIO 34, 35, 36, 39 are input-only pins with no internal pull-up. External 10k pull-up resistors to 3.3V are required for all feedback inputs and the E-stop input.

### 4.2 ULN2003A Darlington Driver

The ULN2003A is a 7-channel Darlington transistor array. Five channels are used as low-side switches for the 24V contactor coils.

- **Inputs:** 3.3V logic from ESP32 GPIOs (channels 1-5)
- **Outputs:** Open-collector, sinks current from contactor coils to ground
- **COM pin:** Connected to +24V for internal flyback diode protection
- **Power:** Each channel rated for 500mA at up to 50V
- **Flyback protection:** Internal diodes clamp inductive kick when coils de-energise

**Connection:**
```
ESP32 GPIO25 ──► IN1 ──► OUT1 ──► K3A coil (low side) ──► 0V
ESP32 GPIO26 ──► IN2 ──► OUT2 ──► K3B coil (low side) ──► 0V
ESP32 GPIO27 ──► IN3 ──► OUT3 ──► K3C coil (low side) ──► 0V
ESP32 GPIO16 ──► IN4 ──► OUT4 ──► K1  coil (low side) ──► 0V
ESP32 GPIO17 ──► IN5 ──► OUT5 ──► KSP coil (low side) ──► 0V
                         COM  ──► +24VDC
                         GND  ──► 0V
```

### 4.3 Contactors

| Designator | Function | Rating | Suggested Part |
|-----------|----------|--------|---------------|
| K3A | Phase A routing | 40A, 1-pole, 24VDC coil | Schneider LC1D25BD (1 pole used) |
| K3B | Phase B routing | 40A, 1-pole, 24VDC coil | Schneider LC1D25BD (1 pole used) |
| K3C | Phase C routing | 40A, 1-pole, 24VDC coil | Schneider LC1D25BD (1 pole used) |
| K1 (K1A/K1B/K1C) | FORM 1 combine | 40A, 3-pole, 24VDC coil | Schneider LC1D40BD |
| KSP | FORM 1 output | 125A, 4-pole, 24VDC coil | Schneider LP1D80004BD |

### 4.4 Optocoupler Feedback (5x PC817)

Five PC817 optocouplers provide isolated feedback from the contactor auxiliary contacts to the ESP32.

**24V side (LED):**
```
+24VDC ──► 4.7kΩ ──► PC817 LED anode ──► LED cathode ──► AUX contact (NO) ──► 0V
```
When the contactor closes, the NO auxiliary contact closes, current flows through the LED, and the optocoupler conducts.

**3.3V side (phototransistor):**
```
3.3V ──► 10kΩ pull-up ──► PC817 collector ──► ESP32 GPIO
                                             │
                           PC817 emitter ──► GND
```
- **Contactor CLOSED:** Opto conducts → collector pulled LOW → ESP32 reads LOW
- **Contactor OPEN:** Opto off → pull-up pulls HIGH → ESP32 reads HIGH

---

## 5. Supply Rails and Power Distribution

### +24VDC Rail
- **Source:** DIN-rail power supply (Mean Well HDR-100-24 or equivalent, 24VDC 5A)
- **Feeds:** Contactor coils (via ULN2003 and interlock contacts), optocoupler LED circuits, hardware E-stop
- **Protection:** Fused at PSU output

### 0V Rail (GND)
- **Common ground** shared between 24VDC system and ESP32 GND
- **CRITICAL:** The ESP32 GND must be connected to the 24V system 0V rail
- **Star-point grounding** recommended at the DIN-rail terminal block

### 3.3V (ESP32 Internal)
- **Source:** ESP32 on-board USB regulator
- **Feeds:** ESP32 logic, optocoupler pull-up resistors, LED indicator circuits
- **DO NOT** connect any 24V signals to the 3.3V rail

---

## 6. Wiring and Connections

### 6.1 Phase Wiring (Power Path)

Wire colours per UK convention:

| Wire | Colour | Rating |
|------|--------|--------|
| Phase A | **RED** | 40A (2.5mm² min for FORM 3) |
| Phase B | **BROWN** | 40A |
| Phase C | **GREY** | 40A |
| SP_BUS | **RED** or marked | 125A (16mm² for FORM 1 bus) |
| Neutral | **BLACK** (broader) | Common return, not switched |

### 6.2 Individual Phase Wiring (K3A, K3B, K3C)
```
AGX Phase A (RED)   ──► K3A NO contact ──► Load A terminal
AGX Phase B (BROWN) ──► K3B NO contact ──► Load B terminal
AGX Phase C (GREY)  ──► K3C NO contact ──► Load C terminal
AGX Neutral (BLACK) ──► Neutral bus ──────► All load N terminals
```

### 6.3 FORM 1 Wiring (K1 + KSP)
```
AGX Phase A (RED)   ──► K1A NO contact ──┐
AGX Phase B (BROWN) ──► K1B NO contact ──┼──► SP_BUS ──► KSP NO ──► 1Φ Load terminal
AGX Phase C (GREY)  ──► K1C NO contact ──┘
AGX Neutral (BLACK) ──► Neutral bus ──────────────────────────────► 1Φ Load N terminal
```

### 6.4 Control Wiring

All control wiring uses 0.5-1.0mm² flexible cable:

```
DRIVE OUTPUTS (ESP32 → ULN2003A):
ESP32 GPIO25 ──► ULN2003 IN1
ESP32 GPIO26 ──► ULN2003 IN2
ESP32 GPIO27 ──► ULN2003 IN3
ESP32 GPIO16 ──► ULN2003 IN4
ESP32 GPIO17 ──► ULN2003 IN5
ESP32 GND    ──► ULN2003 GND ──► 0V rail
ULN2003 COM  ──► +24V rail

COIL PATHS (ULN2003A → contactors, via interlock):
ULN2003 OUT1 ──► K3A coil ──► K3 COIL BUS ──► KSP_NC ──► K1_NC ──► +24V
ULN2003 OUT2 ──► K3B coil ──► K3 COIL BUS (shared with K3A)
ULN2003 OUT3 ──► K3C coil ──► K3 COIL BUS (shared with K3A)
ULN2003 OUT4 ──► K1 coil  ──► K1/KSP BUS ──► K3C_NC ──► K3B_NC ──► K3A_NC ──► +24V
ULN2003 OUT5 ──► KSP coil ──► K1/KSP BUS (shared with K1)

FEEDBACK (contactor AUX → optocouplers → ESP32):
+24V ──► 4.7kΩ ──► PC817-1 LED ──► K3A AUX(NO) ──► 0V
+24V ──► 4.7kΩ ──► PC817-2 LED ──► K3B AUX(NO) ──► 0V
+24V ──► 4.7kΩ ──► PC817-3 LED ──► K3C AUX(NO) ──► 0V
+24V ──► 4.7kΩ ──► PC817-4 LED ──► K1  AUX(NO) ──► 0V
+24V ──► 4.7kΩ ──► PC817-5 LED ──► KSP AUX(NO) ──► 0V

3.3V ──► 10kΩ ──► PC817-1 collector ──► ESP32 GPIO32
3.3V ──► 10kΩ ──► PC817-2 collector ──► ESP32 GPIO33
3.3V ──► 10kΩ ──► PC817-3 collector ──► ESP32 GPIO34
3.3V ──► 10kΩ ──► PC817-4 collector ──► ESP32 GPIO36
3.3V ──► 10kΩ ──► PC817-5 collector ──► ESP32 GPIO39

E-STOP AND LEDs:
3.3V ──► 10kΩ ──► ESP32 GPIO35 ──► NO pushbutton ──► 0V

ESP32 GPIO18 ──► 330Ω ──► Green LED ──► 0V
ESP32 GPIO19 ──► 330Ω ──► Blue LED  ──► 0V
ESP32 GPIO21 ──► 330Ω ──► Red LED   ──► 0V
```

---

## 7. Contactor Interlock System

The hardware interlock uses NC (normally-closed) auxiliary contacts to prevent K3 and K1/KSP groups from being energised simultaneously. This operates independently of the ESP32 firmware.

### Coil Supply Paths

**K3 coil bus (feeds K3A, K3B, K3C):**
```
+24V ──► [HW E-stop NC] ──► K1_NC ──► KSP_NC ──► K3 COIL BUS
                                                       ├──► K3A coil ──► ULN OUT1 ──► 0V
                                                       ├──► K3B coil ──► ULN OUT2 ──► 0V
                                                       └──► K3C coil ──► ULN OUT3 ──► 0V
```
If K1 OR KSP is energised, their NC contacts open, breaking the K3 coil bus.

**K1/KSP coil bus (feeds K1 and KSP):**
```
+24V ──► [HW E-stop NC] ──► K3A_NC ──► K3B_NC ──► K3C_NC ──► K1/KSP COIL BUS
                                                                    ├──► K1 coil  ──► ULN OUT4 ──► 0V
                                                                    └──► KSP coil ──► ULN OUT5 ──► 0V
```
If ANY K3 contactor is energised, its NC contact opens, breaking the K1/KSP coil bus.

### Auxiliary Contact Blocks

Each contactor requires a Schneider LADN11 (or equivalent) auxiliary contact block providing:
- 1x NO contact (for feedback optocoupler)
- 1x NC contact (for interlock)

Total: 5x LADN11 blocks (one per contactor: K3A, K3B, K3C, K1, KSP)

---

## 8. Feedback and State Verification

The feedback system provides the ESP32 with real-time knowledge of which contactors are actually closed. Five independent optocoupler circuits report the state of each contactor.

### Reading Feedback

| GPIO | Reads LOW | Reads HIGH |
|------|-----------|------------|
| 32 (K3A) | K3A contactor is CLOSED | K3A contactor is OPEN |
| 33 (K3B) | K3B contactor is CLOSED | K3B contactor is OPEN |
| 34 (K3C) | K3C contactor is CLOSED | K3C contactor is OPEN |
| 36 (K1) | K1 contactor is CLOSED | K1 contactor is OPEN |
| 39 (KSP) | KSP contactor is CLOSED | KSP contactor is OPEN |

The firmware uses majority-vote sampling (5 reads, accept if 3+ agree) for noise rejection.

### Expected Feedback States

| Mode | K3A | K3B | K3C | K1 | KSP |
|------|-----|-----|-----|-----|-----|
| OFF | open | open | open | open | open |
| Phase A | CLOSED | open | open | open | open |
| Phase B | open | CLOSED | open | open | open |
| Phase C | open | open | CLOSED | open | open |
| FORM 3 | CLOSED | CLOSED | CLOSED | open | open |
| FORM 1 | open | open | open | CLOSED | CLOSED |

---

## 9. Firmware Operation

### State Machine

```
                    Power-on
                       │
                       ▼
                  ┌─────────┐
           ┌─────│   OFF    │◄────── '0' command (from any state)
           │     └────┬─────┘
           │          │
     E-stop│   'A','B','C'   '3'   '1'
     press  │   individual   all    commoned
           │          │
           │     ┌────▼─────┐
           │     │SWITCHING │──── Feedback mismatch ──► FAULT
           │     └────┬─────┘
           │          │
           │   ┌──────┼──────────────┐
           │   │      │              │
           ▼   ▼      ▼              ▼
     ┌────────┐ ┌──────────┐   ┌──────────┐
     │PHASE A │ │  FORM 3  │   │  FORM 1  │
     │PHASE B │ │ (Green)  │   │  (Blue)  │
     │PHASE C │ └──────────┘   └──────────┘
     │(Green) │       │              │
     └────────┘       └── E-stop ────┘──► ESTOP (Red solid)
           │                                │
           └─────── E-stop ────────────►    │
                                      '0' to reset
```

---

## 10. Serial Command Protocol

**Baud rate:** 115200
**Data:** 8N1
**Flow control:** None

### Commands (Host → ESP32)

| Character | Action | Contactors Energised |
|-----------|--------|---------------------|
| `A` or `a` | Phase A only | K3A |
| `B` or `b` | Phase B only | K3B |
| `C` or `c` | Phase C only | K3C |
| `3` | FORM 3 (all three phases) | K3A + K3B + K3C |
| `1` | FORM 1 (commoned 125A) | K1 + KSP |
| `0` | All OFF (safe state) | None |
| `S` or `s` | Query status | (no change) |
| `T` or `t` | Run self-test | OFF only |

### Responses (ESP32 → Host)

| Response | Meaning |
|----------|---------|
| `OK:PHASE_A` | Phase A active (K3A closed) |
| `OK:PHASE_B` | Phase B active (K3B closed) |
| `OK:PHASE_C` | Phase C active (K3C closed) |
| `OK:FORM3` | All three phases active |
| `OK:FORM1` | Single-phase commoned active |
| `OK:OFF` | All contactors de-energised |
| `FAULT:<reason>` | Fault detected, all outputs disabled |
| `STATUS:<state>` | Current state report |
| `ESTOP` | E-stop pressed, all outputs disabled |
| `SELFTEST:PASS` | Self-test completed (tests A, B, C, FORM3, FORM1) |

### Example Session

```
> S
------------------------------------
STATUS:OFF
  Drive:  K3A=off  K3B=off  K3C=off
          K1=off   KSP=off
  Fback:  K3A=open  K3B=open  K3C=open
          K1=open   KSP=open
  E-stop: released
------------------------------------

> A
SWITCHING:OFF -> PHASE_A...
  Step 1: All outputs OFF
  Step 2: Waited for open
  Step 3: Verified all OPEN
  Step 4: Target drive(s) HIGH
  Step 5: Waited for close
  Step 6: Verified PHASE_A active
OK:PHASE_A

> B
SWITCHING:PHASE_A -> PHASE_B...
  Step 1: All outputs OFF
  Step 2: Waited for open
  Step 3: Verified all OPEN
  Step 4: Target drive(s) HIGH
  Step 5: Waited for close
  Step 6: Verified PHASE_B active
OK:PHASE_B

> 3
SWITCHING:PHASE_B -> FORM3...
  Step 1: All outputs OFF
  Step 2: Waited for open
  Step 3: Verified all OPEN
  Step 4: Target drive(s) HIGH
  Step 5: Waited for close
  Step 6: Verified FORM3 active
OK:FORM3

> 0
OK:OFF
```

---

## 11. Mode-Change Sequence (Detailed)

Every mode change follows a strict **break-before-make** sequence:

1. **Receive command** from laptop via USB serial
2. **De-energise** all contactors (set all GPIO outputs LOW)
3. **Wait 150ms** for contactors to mechanically open
4. **Verify feedback**: poll all 5 optocouplers for up to 500ms, confirm all contacts are OPEN
5. **If verification fails** → enter FAULT state, all outputs remain OFF
6. **Energise** target contactor(s) (set appropriate GPIO outputs HIGH)
7. **Wait 150ms** for contactors to mechanically close
8. **Verify feedback**: poll optocouplers for up to 500ms, confirm correct contacts are CLOSED and others are OPEN
9. **If verification fails** → enter FAULT state, all outputs OFF
10. **Update LED indicators** and **report result** to laptop

---

## 12. Safety Systems

### Layer 1: Software Interlock (ESP32 Firmware)
- Break-before-make sequencing
- Feedback verification at every step (all 5 contactors checked)
- Fault state with all outputs disabled

### Layer 2: Hardware Interlock (NC Auxiliary Contacts)
- K3 coil bus: K1_NC and KSP_NC in series (blocks K3 if K1 or KSP energised)
- K1/KSP coil bus: K3A_NC, K3B_NC, K3C_NC in series (blocks K1/KSP if any K3 energised)
- Independent of software

### Layer 3: Mechanical Interlock (Optional)
- Schneider LA9D4002 or equivalent between K3 and K1 frames

### Layer 4: E-Stop (Two Levels)
- **Software E-stop**: NO pushbutton on GPIO35, ESP32 reads and disables outputs
- **Hardware E-stop**: NC mushroom-head in +24V supply line, physically cuts all coil power

---

## 13. LED Indicators

| LED | Colour | State | Meaning |
|-----|--------|-------|---------|
| Green | ON | Phase A/B/C or FORM 3 | Any K3-group contactor active |
| Blue | ON | FORM 1 active | K1+KSP energised |
| Green+Blue | Both ON | Switching | Transition in progress |
| Red | Blinking | FAULT | Feedback mismatch or other fault |
| Red | Solid | E-STOP | E-stop pressed |
| All OFF | - | OFF | Safe state, no contactors energised |

---

## 14. Commissioning Procedure

### First Power-Up (No Load Connected)

1. **Verify wiring** against this document and the circuit diagrams
2. **Check supply rails**: +24V present at ULN2003 COM pin, 0V at GND
3. **Connect ESP32** to laptop via USB
4. **Open serial terminal** at 115200 baud
5. **Verify startup banner** appears (Rev 2.0, individual phase selection)
6. **Send `S`** - check status shows all drives OFF, all 5 feedbacks OPEN
7. **Test E-stop**: press the NO pushbutton, verify `ESTOP` message
8. **Send `0`** to clear E-stop state
9. **Send `T`** to run self-test - this will:
   - Verify all feedback shows open
   - Switch to Phase A, verify, switch to OFF
   - Switch to Phase B, verify, switch to OFF
   - Switch to Phase C, verify, switch to OFF
   - Switch to FORM 3, verify, switch to OFF
   - Switch to FORM 1, verify, switch to OFF
   - Report PASS/FAIL
10. **If self-test passes**: system is ready for use with loads

---

## 15. Troubleshooting

### FAULT: Contacts did not open

**Possible causes:**
- Welded contacts (contactor failure) - replace contactor
- Feedback wiring fault - check opto circuit
- Opto LED or phototransistor failed - replace PC817

### FAULT: Feedback mismatch after energise

**Possible causes:**
- Hardware interlock preventing energisation (opposing group's NC contact is open)
- Contactor coil failure
- +24V supply fault (check PSU)
- Wiring fault in coil path or interlock chain

### Individual phase won't energise but FORM 3 works

**Possible causes:**
- Check that the specific K3x contactor coil is wired to the correct ULN2003 output
- Verify the feedback optocoupler for that phase is connected to the correct ESP32 GPIO

---

## 16. Specifications Summary

| Parameter | Value |
|-----------|-------|
| Phase A/B/C current rating | 40A per phase |
| FORM 3 current rating | 40A per phase (all three) |
| FORM 1 current rating | 125A combined |
| Control interface | USB serial, 115200 baud |
| Controller | ESP32 DevKit V1 |
| Coil driver | ULN2003A (5 of 7 channels used) |
| Feedback | 5x PC817 optocoupler |
| Supply voltage | +24VDC (contactor coils) |
| Logic voltage | 3.3V (ESP32) |
| Switching time | ~300ms typical |
| Safety layers | 4 (software + hardware interlock + mechanical + E-stop) |
| Phase A wire colour | RED |
| Phase B wire colour | BROWN |
| Phase C wire colour | GREY |
| Neutral wire colour | BLACK |
