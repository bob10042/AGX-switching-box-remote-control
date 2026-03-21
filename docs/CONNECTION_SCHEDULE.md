# AGX Test Box - Detailed Connection Schedule

**Revision:** 2.0
**Date:** 2026-03-21
**Status:** Discussion Document - Verify before building

This document lists every wire in the box, point-to-point. Use alongside the circuit diagrams (Pages 1-5) and Operation Manual.

---

## 1. Mains Input (230VAC) — Cable: 1.0mm² flex, mains rated

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W1 | IEC C14 inlet L | MCB input (top) | Brown | Live, fused at inlet (6A) |
| W2 | MCB output (bottom) | PSU terminal L | Brown | Switched live |
| W3 | IEC C14 inlet N | PSU terminal N | Blue | Neutral, direct |
| W4 | IEC C14 inlet E | Enclosure bonding stud | Green/Yellow | Protective earth |
| W5 | Enclosure bonding stud | DIN rail earth clamp | Green/Yellow | DIN rail bond |
| W6 | DIN rail earth clamp | PSU terminal PE | Green/Yellow | PSU earth |

---

## 2. 24V Supply & E-Stop — Cable: 1.0mm² flex

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W7 | PSU +V terminal | HW E-stop NC (com) | Red | +24V output |
| W8 | HW E-stop NC (NO) | +24V rail terminal | Red | E-stop output → rail |
| W9 | PSU −V terminal | 0V rail terminal | Blue or Black | 0V / GND |
| W10 | 0V rail terminal | ESP32 GND pin | Black | Shared ground (CRITICAL) |
| W11 | 0V rail terminal | ULN2003A pin 8 (GND) | Black | Driver ground |
| W12 | +24V rail terminal | ULN2003A pin 9 (COM) | Red | Flyback diode supply |

---

## 3. ESP32 → ULN2003A Drive Outputs — Cable: 0.5mm² flex

| Wire | From | To | Colour | Signal |
|------|------|----|--------|--------|
| W13 | ESP32 GPIO25 | ULN2003A pin 1 (IN1) | Any | K3A drive |
| W14 | ESP32 GPIO26 | ULN2003A pin 2 (IN2) | Any | K3B drive |
| W15 | ESP32 GPIO27 | ULN2003A pin 3 (IN3) | Any | K3C drive |
| W16 | ESP32 GPIO16 | ULN2003A pin 4 (IN4) | Any | K1 drive |
| W17 | ESP32 GPIO17 | ULN2003A pin 5 (IN5) | Any | KSP drive |

---

## 4. K3 Coil Bus (Phase Contactors) — Cable: 1.0mm² flex

The K3 coil bus is fed from +24V via the K1 and KSP NC auxiliary contacts (hardware interlock).

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W18 | +24V rail terminal | K1 AUX NC (com) | Red | Interlock chain start |
| W19 | K1 AUX NC (NO) | KSP AUX NC (com) | Red | Chain link |
| W20 | KSP AUX NC (NO) | K3 coil bus junction | Red | Interlock chain output |
| W21 | K3 coil bus junction | K3A coil terminal A1 | Red | K3A coil +ve |
| W22 | K3 coil bus junction | K3B coil terminal A1 | Red | K3B coil +ve |
| W23 | K3 coil bus junction | K3C coil terminal A1 | Red | K3C coil +ve |
| W24 | K3A coil terminal A2 | ULN2003A pin 16 (OUT1) | Black | K3A coil −ve (switched) |
| W25 | K3B coil terminal A2 | ULN2003A pin 15 (OUT2) | Black | K3B coil −ve (switched) |
| W26 | K3C coil terminal A2 | ULN2003A pin 14 (OUT3) | Black | K3C coil −ve (switched) |

---

## 5. K1/KSP Coil Bus (FORM 1 Contactors) — Cable: 1.0mm² flex

The K1/KSP coil bus is fed from +24V via the K3A, K3B, and K3C NC auxiliary contacts (hardware interlock).

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W27 | +24V rail terminal | K3A AUX NC (com) | Red | Interlock chain start |
| W28 | K3A AUX NC (NO) | K3B AUX NC (com) | Red | Chain link |
| W29 | K3B AUX NC (NO) | K3C AUX NC (com) | Red | Chain link |
| W30 | K3C AUX NC (NO) | K1/KSP coil bus junction | Red | Interlock chain output |
| W31 | K1/KSP coil bus junction | K1 coil terminal A1 | Red | K1 coil +ve |
| W32 | K1/KSP coil bus junction | KSP coil terminal A1 | Red | KSP coil +ve |
| W33 | K1 coil terminal A2 | ULN2003A pin 13 (OUT4) | Black | K1 coil −ve (switched) |
| W34 | KSP coil terminal A2 | ULN2003A pin 12 (OUT5) | Black | KSP coil −ve (switched) |

---

## 6. Feedback Optocouplers (24V Side) — Cable: 0.5mm² flex

Each PC817 optocoupler LED is wired: +24V → 4.7kΩ → LED anode → LED cathode → AUX NO contact → 0V

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W35 | +24V rail | R1 (4.7kΩ) lead 1 | Red | PC817-1 supply |
| W36 | R1 (4.7kΩ) lead 2 | PC817-1 pin 1 (anode) | — | Via resistor |
| W37 | PC817-1 pin 2 (cathode) | K3A AUX NO (com) | — | To aux contact |
| W38 | K3A AUX NO (NO) | 0V rail | Black | Return when closed |
| W39 | +24V rail | R2 (4.7kΩ) lead 1 | Red | PC817-2 supply |
| W40 | R2 (4.7kΩ) lead 2 | PC817-2 pin 1 (anode) | — | Via resistor |
| W41 | PC817-2 pin 2 (cathode) | K3B AUX NO (com) | — | To aux contact |
| W42 | K3B AUX NO (NO) | 0V rail | Black | Return when closed |
| W43 | +24V rail | R3 (4.7kΩ) lead 1 | Red | PC817-3 supply |
| W44 | R3 (4.7kΩ) lead 2 | PC817-3 pin 1 (anode) | — | Via resistor |
| W45 | PC817-3 pin 2 (cathode) | K3C AUX NO (com) | — | To aux contact |
| W46 | K3C AUX NO (NO) | 0V rail | Black | Return when closed |
| W47 | +24V rail | R4 (4.7kΩ) lead 1 | Red | PC817-4 supply |
| W48 | R4 (4.7kΩ) lead 2 | PC817-4 pin 1 (anode) | — | Via resistor |
| W49 | PC817-4 pin 2 (cathode) | K1 AUX NO (com) | — | To aux contact |
| W50 | K1 AUX NO (NO) | 0V rail | Black | Return when closed |
| W51 | +24V rail | R5 (4.7kΩ) lead 1 | Red | PC817-5 supply |
| W52 | R5 (4.7kΩ) lead 2 | PC817-5 pin 1 (anode) | — | Via resistor |
| W53 | PC817-5 pin 2 (cathode) | KSP AUX NO (com) | — | To aux contact |
| W54 | KSP AUX NO (NO) | 0V rail | Black | Return when closed |

---

## 7. Feedback Optocouplers (3.3V Side) — Cable: 0.5mm² flex

Each PC817 phototransistor output: 3.3V → 10kΩ pull-up → collector → ESP32 GPIO, emitter → GND

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W55 | ESP32 3.3V | R6 (10kΩ) lead 1 | — | Pull-up for K3A feedback |
| W56 | R6 lead 2 + PC817-1 pin 4 (collector) | ESP32 GPIO32 | — | K3A feedback (LOW=closed) |
| W57 | PC817-1 pin 3 (emitter) | 0V rail / ESP32 GND | Black | Emitter return |
| W58 | ESP32 3.3V | R7 (10kΩ) lead 1 | — | Pull-up for K3B feedback |
| W59 | R7 lead 2 + PC817-2 pin 4 (collector) | ESP32 GPIO33 | — | K3B feedback |
| W60 | PC817-2 pin 3 (emitter) | 0V rail / ESP32 GND | Black | Emitter return |
| W61 | ESP32 3.3V | R8 (10kΩ) lead 1 | — | Pull-up for K3C feedback |
| W62 | R8 lead 2 + PC817-3 pin 4 (collector) | ESP32 GPIO34 | — | K3C feedback |
| W63 | PC817-3 pin 3 (emitter) | 0V rail / ESP32 GND | Black | Emitter return |
| W64 | ESP32 3.3V | R9 (10kΩ) lead 1 | — | Pull-up for K1 feedback |
| W65 | R9 lead 2 + PC817-4 pin 4 (collector) | ESP32 GPIO36 | — | K1 feedback |
| W66 | PC817-4 pin 3 (emitter) | 0V rail / ESP32 GND | Black | Emitter return |
| W67 | ESP32 3.3V | R10 (10kΩ) lead 1 | — | Pull-up for KSP feedback |
| W68 | R10 lead 2 + PC817-5 pin 4 (collector) | ESP32 GPIO39 | — | KSP feedback |
| W69 | PC817-5 pin 3 (emitter) | 0V rail / ESP32 GND | Black | Emitter return |

---

## 8. E-Stop (Software) — Cable: 0.5mm² flex

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W70 | ESP32 3.3V | R11 (10kΩ) lead 1 | — | Pull-up for E-stop |
| W71 | R11 lead 2 | ESP32 GPIO35 | — | E-stop input (HIGH = released) |
| W72 | ESP32 GPIO35 | NO pushbutton terminal 1 | — | E-stop button |
| W73 | NO pushbutton terminal 2 | 0V rail / ESP32 GND | Black | Button pulls LOW when pressed |

---

## 9. Status LEDs — Cable: 0.5mm² flex

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W74 | ESP32 GPIO18 | R12 (330Ω) lead 1 | — | Green LED series resistor |
| W75 | R12 lead 2 | Green LED anode (+) | — | ~3.9mA (Vf≈2.0V) |
| W76 | Green LED cathode (−) | 0V rail / ESP32 GND | Black | LED return |
| W77 | ESP32 GPIO19 | R13 (100Ω) lead 1 | — | Blue LED series resistor |
| W78 | R13 lead 2 | Blue LED anode (+) | — | ~3.0mA (Vf≈3.0V) |
| W79 | Blue LED cathode (−) | 0V rail / ESP32 GND | Black | LED return |
| W80 | ESP32 GPIO21 | R14 (330Ω) lead 1 | — | Red LED series resistor |
| W81 | R14 lead 2 | Red LED anode (+) | — | ~4.5mA (Vf≈1.8V) |
| W82 | Red LED cathode (−) | 0V rail / ESP32 GND | Black | LED return |

---

## 10. Power Path — Phase Wiring (AGX → Contactors → Loads)

### FORM 3 Path (Individual Phases) — Cable: 2.5mm² min (40A rated)

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W83 | AGX Phase A output | K3A NO input (1) | Red | Phase A, 40A |
| W84 | K3A NO output (2) | Load A phase terminal | Red | Phase A to load |
| W85 | AGX Phase B output | K3B NO input (1) | Brown | Phase B, 40A |
| W86 | K3B NO output (2) | Load B phase terminal | Brown | Phase B to load |
| W87 | AGX Phase C output | K3C NO input (1) | Grey | Phase C, 40A |
| W88 | K3C NO output (2) | Load C phase terminal | Grey | Phase C to load |

### FORM 1 Path (Commoned) — Cable: 16mm² for SP_BUS, 2.5mm² per phase

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W89 | AGX Phase A output | K1 pole A input (1) | Red | Phase A to K1 |
| W90 | AGX Phase B output | K1 pole B input (3) | Brown | Phase B to K1 |
| W91 | AGX Phase C output | K1 pole C input (5) | Grey | Phase C to K1 |
| W92 | K1 pole A output (2) | SP_BUS junction | Red/marked | Commoned output |
| W93 | K1 pole B output (4) | SP_BUS junction | Red/marked | Commoned output |
| W94 | K1 pole C output (6) | SP_BUS junction | Red/marked | Commoned output |
| W95 | SP_BUS junction | KSP NO input (1) | Red | 125A rated, 16mm² |
| W96 | KSP NO output (2) | 1Φ load phase terminal | Red | 125A to load |

### Neutral — Cable: 2.5mm² (FORM 3) / 16mm² (FORM 1 return)

| Wire | From | To | Colour | Notes |
|------|------|----|--------|-------|
| W97 | AGX Neutral output | Neutral bus terminal | Black | Common neutral |
| W98 | Neutral bus terminal | Load A neutral terminal | Black | Load A return |
| W99 | Neutral bus terminal | Load B neutral terminal | Black | Load B return |
| W100 | Neutral bus terminal | Load C neutral terminal | Black | Load C return |
| W101 | Neutral bus terminal | 1Φ load neutral terminal | Black | 1Φ load return (16mm²) |

---

## Summary

| Section | Wire Count | Cable Size |
|---------|-----------|------------|
| Mains input | W1–W6 (6) | 1.0mm² mains rated |
| 24V supply & E-stop | W7–W12 (6) | 1.0mm² |
| ESP32 → ULN2003A | W13–W17 (5) | 0.5mm² |
| K3 coil bus + interlock | W18–W26 (9) | 1.0mm² |
| K1/KSP coil bus + interlock | W27–W34 (8) | 1.0mm² |
| Feedback optos (24V side) | W35–W54 (20) | 0.5mm² |
| Feedback optos (3.3V side) | W55–W69 (15) | 0.5mm² |
| SW E-stop | W70–W73 (4) | 0.5mm² |
| Status LEDs | W74–W82 (9) | 0.5mm² |
| Phase wiring (FORM 3) | W83–W88 (6) | 2.5mm² |
| Phase wiring (FORM 1) | W89–W96 (8) | 2.5mm² / 16mm² |
| Neutral | W97–W101 (5) | 2.5mm² / 16mm² |
| **Total** | **101 wires** | |

---

## Resistor Schedule

| Ref | Value | Function | Circuit |
|-----|-------|----------|---------|
| R1–R5 | 4.7kΩ 0.25W | Opto LED current limit | +24V → R → PC817 LED (I ≈ 4.3mA) |
| R6–R10 | 10kΩ 0.25W | Pull-up to 3.3V | Feedback GPIO pull-up (GPIO34,36,39 have no internal pull-up) |
| R11 | 10kΩ 0.25W | Pull-up to 3.3V | E-stop GPIO35 pull-up |
| R12 | 330Ω 0.25W | Green LED series | GPIO18 → R → LED → 0V (I ≈ 3.9mA) |
| R13 | 100Ω 0.25W | Blue LED series | GPIO19 → R → LED → 0V (I ≈ 3.0mA) |
| R14 | 330Ω 0.25W | Red LED series | GPIO21 → R → LED → 0V (I ≈ 4.5mA) |

---

## LADN11 Auxiliary Contact Block Assignments

Each contactor gets one Schneider LADN11 (1NO + 1NC) auxiliary block:

| Contactor | NO Contact Used For | NC Contact Used For |
|-----------|--------------------|--------------------|
| K3A | Feedback opto PC817-1 (W37–W38) | K1/KSP interlock chain (W27–W28) |
| K3B | Feedback opto PC817-2 (W41–W42) | K1/KSP interlock chain (W28–W29) |
| K3C | Feedback opto PC817-3 (W45–W46) | K1/KSP interlock chain (W29–W30) |
| K1 | Feedback opto PC817-4 (W49–W50) | K3 interlock chain (W18–W19) |
| KSP | Feedback opto PC817-5 (W53–W54) | K3 interlock chain (W19–W20) |

---

## ULN2003A Pin Assignment (DIP-16)

| Pin | Function | Connected To |
|-----|----------|-------------|
| 1 | IN1 | ESP32 GPIO25 (W13) |
| 2 | IN2 | ESP32 GPIO26 (W14) |
| 3 | IN3 | ESP32 GPIO27 (W15) |
| 4 | IN4 | ESP32 GPIO16 (W16) |
| 5 | IN5 | ESP32 GPIO17 (W17) |
| 6 | IN6 | Not connected |
| 7 | IN7 | Not connected |
| 8 | GND | 0V rail (W11) |
| 9 | COM | +24V rail (W12) |
| 10 | OUT7 | Not connected |
| 11 | OUT6 | Not connected |
| 12 | OUT5 | KSP coil A2 (W34) |
| 13 | OUT4 | K1 coil A2 (W33) |
| 14 | OUT3 | K3C coil A2 (W26) |
| 15 | OUT2 | K3B coil A2 (W25) |
| 16 | OUT1 | K3A coil A2 (W24) |

---

## PC817 Pin Assignment (all 5 identical)

| Pin | Function | Connection |
|-----|----------|------------|
| 1 | Anode (+) | From 4.7kΩ resistor (from +24V) |
| 2 | Cathode (−) | To contactor AUX NO contact |
| 3 | Emitter | To 0V / ESP32 GND |
| 4 | Collector | To 10kΩ pull-up (to 3.3V) + ESP32 GPIO |
