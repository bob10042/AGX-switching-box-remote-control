# AGX Test Box Switching Controller - Detailed Operation Manual

**Revision:** 1.0
**Date:** 2026-03-19
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

The AGX Test Box provides remote-controlled switching between two operating configurations of a Pacific Power Source AGX (or AFX) programmable AC power source:

| Mode | Configuration | Current Rating | Use Case |
|------|--------------|----------------|----------|
| **FORM 3** | Three-phase, individual loads | 40A per phase | Calibrating individual phase loads separately |
| **FORM 1** | Single-phase, all phases commoned | 125A combined | Maximum single-phase current for high-power loads |

The switching is controlled by an ESP32 microcontroller connected to a laptop via USB serial. The operator sends simple single-character commands to switch between modes. The system includes multiple layers of safety protection to prevent dangerous states (both contactors groups energised simultaneously).

### Why This Box Exists

During equipment calibration, you frequently need to switch between:
- **Individual phase testing** (FORM 3): connect a load to one phase at a time for per-phase calibration
- **Maximum current testing** (FORM 1): combine all three phases together for maximum single-phase output

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
                              GPIO25/26/27│ (3.3V logic)
                                          ▼
                                   ┌──────────────┐
                                   │  ULN2003A    │
                                   │  Darlington  │◄── +24VDC (COM pin)
                                   │  Driver      │──► 0V (GND pin)
                                   └──────┬───────┘
                                          │
                              OUT1/OUT2/OUT3 (24V switched)
                                          │
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                   ┌────────────┐  ┌────────────┐  ┌────────────┐
                   │ K3 GROUP   │  │ K1 GROUP   │  │ KSP        │
                   │ (FORM 3)   │  │ (FORM 1    │  │ (FORM 1    │
                   │ K3A/K3B/K3C│  │  combine)  │  │  output)   │
                   │ 3x 40A NO  │  │ K1A/K1B/K1C│  │ 125A NO    │
                   └─────┬──────┘  │ 3x 40A NO  │  └─────┬──────┘
                         │         └──────┬──────┘        │
                         │                │               │
                         ▼                └───────┬───────┘
                   ┌────────────┐                 ▼
                   │ 3-PHASE    │          ┌────────────┐
                   │ LOADS      │          │ 1-PHASE    │
                   │ (40A each) │          │ LOAD       │
                   └────────────┘          │ (125A max) │
                                           └────────────┘
```

---

## 3. Operating Modes

### FORM 3 - Three-Phase (Individual Loads)

- Contactor group K3 energised: K3A, K3B, K3C (all three poles on one contactor, or three individual contactors)
- Each phase (A, B, C) from the AGX is routed to its own separate load terminal
- Current rating: 40A per phase
- Use: connect calibration load to individual phases for per-phase testing
- K1 and KSP groups are DE-ENERGISED (open)

### FORM 1 - Single-Phase (Commoned)

- Contactor group K1 energised: K1A, K1B, K1C combine all three AGX phases onto a single bus (SP_BUS)
- Contactor KSP energised: routes SP_BUS to the single-phase load terminal
- Current rating: 125A (combined output of all three phases)
- Use: maximum single-phase current for high-power load testing
- K3 group is DE-ENERGISED (open)

### OFF State

- All contactor groups de-energised
- All phases disconnected from all loads
- Safe state for wiring changes
- Default state on power-up

---

## 4. Hardware Description

### 4.1 ESP32 DevKit V1

The ESP32 is the central controller. It communicates with the laptop via USB serial (115200 baud) and drives the contactor coils via the ULN2003A.

**GPIO Pin Assignment:**

| GPIO | Direction | Function | Connects To |
|------|-----------|----------|-------------|
| 25 | OUTPUT | FORM 3 drive | ULN2003 IN1 → K3 coils |
| 26 | OUTPUT | K1 drive | ULN2003 IN2 → K1 coils |
| 27 | OUTPUT | KSP drive | ULN2003 IN3 → KSP coil |
| 32 | INPUT | K3 feedback | PC817 opto collector |
| 33 | INPUT | K1 feedback | PC817 opto collector |
| 34 | INPUT | KSP feedback | PC817 opto collector (INPUT ONLY pin) |
| 35 | INPUT | E-stop button | NO pushbutton to GND (INPUT ONLY pin) |
| 18 | OUTPUT | Green LED | 330R → LED → GND (FORM 3 active) |
| 19 | OUTPUT | Blue LED | 330R → LED → GND (FORM 1 active) |
| 21 | OUTPUT | Red LED | 330R → LED → GND (Fault/E-stop) |

**Note:** GPIO 34 and 35 are input-only pins on the ESP32 (no internal pull-up on 34). GPIO 35 uses the internal pull-up resistor.

### 4.2 ULN2003A Darlington Driver

The ULN2003A is a 7-channel Darlington transistor array used as a low-side switch for the 24V contactor coils.

- **Input:** 3.3V logic from ESP32 GPIOs (channels 1-3)
- **Output:** Open-collector, sinks current from contactor coils to ground
- **COM pin:** Connected to +24V for internal flyback diode protection
- **Power:** Each channel rated for 500mA at up to 50V
- **Flyback protection:** Internal diodes clamp inductive kick when coils de-energise

**Connection:**
```
ESP32 GPIO25 ──► IN1 ──► OUT1 ──► K3 coil (low side) ──► 0V
ESP32 GPIO26 ──► IN2 ──► OUT2 ──► K1 coil (low side) ──► 0V
ESP32 GPIO27 ──► IN3 ──► OUT3 ──► KSP coil (low side) ──► 0V
                         COM  ──► +24VDC
                         GND  ──► 0V
```

### 4.3 Contactors

| Designator | Function | Rating | Suggested Part |
|-----------|----------|--------|---------------|
| K3 (K3A/K3B/K3C) | FORM 3 routing | 40A, 3-pole, 24VDC coil | Schneider LC1D40BD |
| K1 (K1A/K1B/K1C) | FORM 1 combine | 40A, 3-pole, 24VDC coil | Schneider LC1D40BD |
| KSP | FORM 1 output | 125A, 4-pole, 24VDC coil | Schneider LP1D80004BD or ABB AF80-40-00-13 |

### 4.4 Optocoupler Feedback (PC817)

Three PC817 optocouplers provide isolated feedback from the contactor auxiliary contacts to the ESP32.

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
- **Current draw:** ~3A peak (all contactors energised simultaneously - should never happen, but PSU sized for margin)

### 0V Rail (GND)
- **Common ground** shared between 24VDC system and ESP32 GND
- **CRITICAL:** The ESP32 GND must be connected to the 24V system 0V rail for the ULN2003A to function correctly
- **Star-point grounding** recommended at the DIN-rail terminal block

### 3.3V (ESP32 Internal)
- **Source:** ESP32 on-board USB regulator
- **Feeds:** ESP32 logic, optocoupler pull-up resistors, LED indicator circuits
- **DO NOT** connect any 24V signals to the 3.3V rail

### 5V USB (ESP32 VIN)
- **Source:** Laptop USB port via USB cable
- **Feeds:** ESP32 internal regulator
- **Typical current:** ~200mA

### Power Distribution Diagram
```
MAINS ──► [24V DIN-RAIL PSU] ──► +24VDC RAIL ──┬── ULN2003 COM pin
                               │                ├── Opto LED circuits (via 4.7k)
                               │                ├── Hardware E-stop (NC, in series)
                               │                └── Interlock NC contacts
                               │
                               └── 0V RAIL ─────┬── ULN2003 GND
                                                 ├── ESP32 GND
                                                 ├── Opto emitters
                                                 └── LED cathodes

USB (Laptop) ──► ESP32 VIN ──► 3.3V regulator ──┬── ESP32 logic
                                                  ├── Opto pull-ups (10k)
                                                  └── LED anodes (via 330R)
```

---

## 6. Wiring and Connections

### 6.1 Phase Wiring (Power Path)

Wire colours per UK convention and user specification:

| Wire | Colour | Rating |
|------|--------|--------|
| Phase A | **RED** | 40A (2.5mm² min for FORM 3, 16mm² for FORM 1 bus) |
| Phase B | **BROWN** | 40A / 125A as above |
| Phase C | **GREY** | 40A / 125A as above |
| Neutral | **BLACK** (broader) | Common return, not switched |

### 6.2 FORM 3 Wiring
```
AGX Phase A (RED)   ──► K3A NO contact ──► Load A terminal
AGX Phase B (BROWN) ──► K3B NO contact ──► Load B terminal
AGX Phase C (GREY)  ──► K3C NO contact ──► Load C terminal
AGX Neutral (BLACK) ──► Neutral bus ──────► All load N terminals
```

### 6.3 FORM 1 Wiring
```
AGX Phase A (RED)   ──► K1A NO contact ──┐
AGX Phase B (BROWN) ──► K1B NO contact ──┼──► SP_BUS ──► KSP NO ──► 1Φ Load terminal
AGX Phase C (GREY)  ──► K1C NO contact ──┘
AGX Neutral (BLACK) ──► Neutral bus ──────────────────────────────► 1Φ Load N terminal
```

### 6.4 Control Wiring

All control wiring uses 0.5-1.0mm² flexible cable:

```
ESP32 GPIO25 ──► ULN2003 IN1
ESP32 GPIO26 ──► ULN2003 IN2
ESP32 GPIO27 ──► ULN2003 IN3
ESP32 GND    ──► ULN2003 GND ──► 0V rail
ULN2003 COM  ──► +24V rail

ULN2003 OUT1 ──► K3 coil terminal (via interlock NC contacts) ──► +24V
ULN2003 OUT2 ──► K1 coil terminal (via interlock NC contacts) ──► +24V
ULN2003 OUT3 ──► KSP coil terminal (via interlock NC contacts) ──► +24V

+24V ──► 4.7kΩ ──► PC817-1 LED ──► K3 AUX(NO) ──► 0V
+24V ──► 4.7kΩ ──► PC817-2 LED ──► K1 AUX(NO) ──► 0V
+24V ──► 4.7kΩ ──► PC817-3 LED ──► KSP AUX(NO) ──► 0V

3.3V ──► 10kΩ ──► PC817-1 collector ──► ESP32 GPIO32
3.3V ──► 10kΩ ──► PC817-2 collector ──► ESP32 GPIO33
3.3V ──► 10kΩ ──► PC817-3 collector ──► ESP32 GPIO34

ESP32 GPIO35 ──► NO pushbutton ──► 0V (internal pull-up enabled)

ESP32 GPIO18 ──► 330Ω ──► Green LED ──► 0V
ESP32 GPIO19 ──► 330Ω ──► Blue LED  ──► 0V
ESP32 GPIO21 ──► 330Ω ──► Red LED   ──► 0V
```

---

## 7. Contactor Interlock System

The hardware interlock uses NC (normally-closed) auxiliary contacts to prevent both contactor groups from being energised simultaneously. This operates independently of the ESP32 firmware - even if the software fails, the hardware interlock prevents a dangerous state.

### Coil Supply Paths

**K3 (FORM 3) coil path:**
```
+24V ──► K1_AUX(NC) ──► KSP_AUX(NC) ──► K3 coil ──► ULN2003 OUT1 ──► 0V
```
If K1 OR KSP is energised, their NC contacts open, breaking the K3 coil supply.

**K1 (FORM 1 combine) coil path:**
```
+24V ──► K3_AUX(NC) ──► K1 coil ──► ULN2003 OUT2 ──► 0V
```
If K3 is energised, its NC contact opens, breaking the K1 coil supply.

**KSP (FORM 1 output) coil path:**
```
+24V ──► K3_AUX(NC) ──► KSP coil ──► ULN2003 OUT3 ──► 0V
```
If K3 is energised, its NC contact opens, breaking the KSP coil supply.

### Why This Works

- To switch to FORM 3: ESP32 drives GPIO25 HIGH. ULN2003 OUT1 sinks current. But K3 coil only energises if K1_AUX(NC) AND KSP_AUX(NC) are both closed (i.e., K1 and KSP are both de-energised).
- To switch to FORM 1: ESP32 drives GPIO26 and GPIO27 HIGH. But K1 and KSP coils only energise if K3_AUX(NC) is closed (i.e., K3 is de-energised).
- **Result:** It is physically impossible for K3 and K1/KSP to be energised at the same time, regardless of software state.

### Auxiliary Contact Blocks

Each contactor requires a Schneider LADN11 (or equivalent) auxiliary contact block providing:
- 1x NO contact (for feedback optocoupler)
- 1x NC contact (for interlock)

---

## 8. Feedback and State Verification

The feedback system provides the ESP32 with real-time knowledge of which contactors are actually closed, independent of the drive signals. This catches:
- Contactor mechanical failure (coil energised but contacts didn't close)
- Wiring faults
- Interlock preventing energisation (drive HIGH but interlock NC contact is open)
- Welded contacts (contactor should be open but feedback shows closed)

### Reading Feedback

| GPIO | Reads LOW | Reads HIGH |
|------|-----------|------------|
| 32 (K3) | K3 contactor is CLOSED | K3 contactor is OPEN |
| 33 (K1) | K1 contactor is CLOSED | K1 contactor is OPEN |
| 34 (KSP) | KSP contactor is CLOSED | KSP contactor is OPEN |

The firmware uses majority-vote sampling (5 reads, accept if 3+ agree) for noise rejection.

---

## 9. Firmware Operation

### State Machine

The firmware implements a simple state machine:

```
                    Power-on
                       │
                       ▼
                  ┌─────────┐
           ┌─────│   OFF    │◄────── '0' command
           │     └────┬─────┘        (from any state)
           │          │
     E-stop│    '3'   │   '1'
     press  │   cmd    │   cmd
           │          │
           │     ┌────▼─────┐
           │     │SWITCHING │──── Feedback mismatch ──► FAULT
           │     └────┬─────┘
           │          │
           │    ┌─────┴──────┐
           │    │            │
           ▼    ▼            ▼
     ┌──────────┐     ┌──────────┐
     │  FORM 3  │     │  FORM 1  │
     │ (Green)  │     │  (Blue)  │
     └──────────┘     └──────────┘
           │                │
           └─── E-stop ─────┘──► ESTOP (Red solid)
                                    │
                              '0' to reset
```

### Startup Sequence

1. All outputs set LOW (safe state)
2. LED test: Green → Blue → Red → Off (200ms each)
3. Banner printed to serial
4. E-stop checked
5. State set to OFF

---

## 10. Serial Command Protocol

**Baud rate:** 115200
**Data:** 8N1
**Flow control:** None

### Commands (Host → ESP32)

| Character | Action | Valid From States |
|-----------|--------|-------------------|
| `3` | Switch to FORM 3 | OFF, FORM1 |
| `1` | Switch to FORM 1 | OFF, FORM3 |
| `0` | All OFF (safe state) | Any state (resets FAULT/ESTOP) |
| `S` or `s` | Query status | Any state |
| `T` or `t` | Run self-test | OFF only |

### Responses (ESP32 → Host)

| Response | Meaning |
|----------|---------|
| `OK:FORM3` | Successfully switched to FORM 3 |
| `OK:FORM1` | Successfully switched to FORM 1 |
| `OK:OFF` | All contactors de-energised |
| `FAULT:<reason>` | Fault detected, all outputs disabled |
| `STATUS:<state>` | Current state (followed by detail lines) |
| `ESTOP` | E-stop pressed, all outputs disabled |
| `SWITCHING:...` | Transition in progress (informational) |
| `SELFTEST:PASS` | Self-test completed successfully |
| `SELFTEST:FAIL` | Self-test failed (reason follows) |

### Example Session

```
> S
────────────────────────────────
STATUS:OFF
  Drive: FORM3=off K1=off KSP=off
  Feedback: K3=open K1=open KSP=open
  E-stop: released
────────────────────────────────

> 3
SWITCHING:OFF -> FORM3...
  Step 1: All outputs OFF
  Step 2: Waited for open
  Step 3: Verified all OPEN
  Step 4: K3 drive HIGH
  Step 5: Waited for close
  Step 6: Verified FORM3 active
OK:FORM3

> 1
SWITCHING:OFF -> FORM1...
  Step 1: All outputs OFF
  Step 2: Waited for open
  Step 3: Verified all OPEN
  Step 4: K1+KSP drive HIGH
  Step 5: Waited for close
  Step 6: Verified FORM1 active
OK:FORM1

> 0
OK:OFF
```

---

## 11. Mode-Change Sequence (Detailed)

Every mode change follows a strict **break-before-make** sequence:

### Step-by-Step

1. **Receive command** from laptop via USB serial
2. **De-energise** current contactor group (set all GPIO outputs LOW)
3. **Wait 150ms** for contactors to mechanically open
4. **Verify feedback**: poll optocouplers for up to 500ms, confirm all contacts are OPEN
5. **If verification fails** → enter FAULT state, all outputs remain OFF, red LED blinks
6. **Energise** new contactor group (set appropriate GPIO outputs HIGH)
7. **Wait 150ms** for contactors to mechanically close
8. **Verify feedback**: poll optocouplers for up to 500ms, confirm correct contacts are CLOSED
9. **If verification fails** → enter FAULT state, all outputs OFF, red LED blinks
10. **Update LED indicators** and **report result** to laptop

### Timing Budget

| Phase | Duration | Purpose |
|-------|----------|---------|
| De-energise | ~1ms | GPIO write |
| Open wait | 150ms | Mechanical opening time |
| Open verify | 0-500ms | Feedback polling (usually immediate) |
| Energise | ~1ms | GPIO write |
| Close wait | 150ms | Mechanical closing time |
| Close verify | 0-500ms | Feedback polling (usually immediate) |
| **Total** | **~300ms typical** | **~1.2s worst case** |

---

## 12. Safety Systems

### Layer 1: Software Interlock (ESP32 Firmware)
- Break-before-make sequencing
- Feedback verification at every step
- Fault state with all outputs disabled
- E-stop input monitoring

### Layer 2: Hardware Interlock (NC Auxiliary Contacts)
- Electrically prevents simultaneous energisation
- Independent of software - works even if ESP32 crashes
- Uses NC contacts in contactor coil supply paths

### Layer 3: Mechanical Interlock (Optional)
- Schneider LA9D4002 or equivalent
- Physical bar between contactors prevents both closing
- Third independent layer of protection

### Layer 4: E-Stop (Two Levels)
- **Software E-stop**: NO pushbutton on GPIO35, ESP32 reads and disables outputs
- **Hardware E-stop**: NC mushroom-head in +24V coil supply line, physically cuts all coil power regardless of ESP32 state

### Fault Conditions

The system enters FAULT state (all outputs OFF, red LED blinking) if:
- Contacts don't open after de-energise command (welded contacts?)
- Contacts don't close after energise command (coil failure? interlock blocking?)
- Unexpected feedback state (wrong contacts closed)
- Self-test failure

To clear a fault: send `0` (OFF command) to reset, then investigate the cause.

---

## 13. LED Indicators

| LED | Colour | State | Meaning |
|-----|--------|-------|---------|
| Green | ON | FORM 3 active | Three-phase mode, K3 energised |
| Blue | ON | FORM 1 active | Single-phase mode, K1+KSP energised |
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
4. **Open serial terminal** at 115200 baud (Arduino Serial Monitor, PuTTY, etc.)
5. **Verify startup banner** appears
6. **Send `S`** - check status shows all drives OFF, all feedback OPEN, E-stop released
7. **Test E-stop**: press the NO pushbutton, verify `ESTOP` message appears
8. **Send `0`** to clear E-stop state
9. **Send `T`** to run self-test - this will:
   - Verify all feedback shows open
   - Switch to FORM 3, verify feedback
   - Switch to OFF, verify feedback
   - Switch to FORM 1, verify feedback
   - Switch to OFF
   - Report PASS/FAIL
10. **If self-test passes**: system is ready for use with loads

### Connecting Loads

1. Ensure system is in OFF state (`0`)
2. Connect calibration loads to appropriate terminals
3. Verify neutral connections
4. Switch to desired mode (`3` or `1`)
5. Verify correct LED indicator
6. Apply power from AGX

---

## 15. Troubleshooting

### FAULT: Contacts did not open

**Possible causes:**
- Welded contacts (contactor failure) - replace contactor
- Feedback wiring fault - check opto circuit
- Opto LED or phototransistor failed - replace PC817

**Action:** Send `0` to clear fault. Send `S` to check feedback state. If feedback still shows contacts closed with drives off, investigate hardware.

### FAULT: Feedback mismatch after energise

**Possible causes:**
- Hardware interlock preventing energisation (opposing group's NC contact is open because that group is still energised - should not happen with break-before-make)
- Contactor coil failure
- +24V supply fault (check PSU)
- Wiring fault in coil path or interlock chain

**Action:** Send `S` to check all drive and feedback states. Verify +24V is present. Check interlock wiring.

### No Response on Serial

- Check USB cable connection
- Verify correct COM port selected
- Verify baud rate is 115200
- Try pressing ESP32 reset button

### E-stop Won't Clear

- Release the physical E-stop button
- Send `0` to reset
- Check that GPIO35 reads HIGH when button is released (`S` command)

---

## 16. Specifications Summary

| Parameter | Value |
|-----------|-------|
| FORM 3 current rating | 40A per phase |
| FORM 1 current rating | 125A combined |
| Control interface | USB serial, 115200 baud |
| Controller | ESP32 DevKit V1 |
| Coil driver | ULN2003A (24V, low-side) |
| Feedback | 3x PC817 optocoupler |
| Supply voltage | +24VDC (contactor coils) |
| Logic voltage | 3.3V (ESP32) |
| Switching time | ~300ms typical |
| Safety layers | 4 (software + hardware interlock + mechanical + E-stop) |
| Phase A wire colour | RED |
| Phase B wire colour | BROWN |
| Phase C wire colour | GREY |
| Neutral wire colour | BLACK |
