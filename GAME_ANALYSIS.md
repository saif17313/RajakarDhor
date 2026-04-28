# RajakarDhor - Game Analysis & Features

## Game Overview

**RajakarDhor** is a turn-based stealth/tactical game where a **Rajakar** (thief/intruder) tries to escape while being hunted by **BirSreshtha** (guard).

---

## Game Features

### 1. **Grid-Based Gameplay**

- 10x10 grid with walkable floors, walls, and exit tiles
- Turn-based system alternating between Rajakar and BirSreshtha
- Maximum 60 turns per match

### 2. **Detection & Sensing System**

- **Straight Sight (BirSreshtha)**: 4 cardinal directions (up/down/left/right), range 3 cells, blocked by walls
- **Orthogonal Range**: Always-on detection in cardinal directions (ignores walls)
- **Power Scan (BirSreshtha)**: Special cooldown ability
  - Available every 4 BirSreshtha turns
  - Radius: 2 cells in all 8 directions (cardinal + diagonal)
  - **Ignores walls** - can see through obstacles
  - Automatically triggers when ready (AI-controlled)
  - Visual effect: Blue highlighted cells on grid showing scan area
  - If Rajakar is within scan radius, instantly reveals position
- **Noise Detection**: Rajakar's actions generate noise that BirSreshtha can hear
  - MOVE: radius 2
  - WAIT: radius 0 (silent)
  - ESCAPE: radius 3

### 3. **Probability Tracking**

- BirSreshtha maintains a probability map of Rajakar's likely position
- Updates based on: motion prediction, sight information, noise evidence, power scan results
- Uses this to hunt Rajakar probabilistically

### 4. **Fog of War**

- BirSreshtha gradually discovers exit locations through vision
- Rajakar doesn't know BirSreshtha's exact location after detection

### 5. **Win Conditions**

- ✓ **Rajakar Wins**: Reaches an EXIT and uses ESCAPE action
- ✓ **BirSreshtha Wins**: Gets adjacent (Manhattan distance = 1) to Rajakar AFTER BirSreshtha's action
- ✓ **Draw**: Game reaches turn limit (60 turns)

---

## Who Can Give Which Moves?

### **RAJAKAR (The Thief)**

| Action     | Description                    | Mechanics                                                                                 |
| ---------- | ------------------------------ | ----------------------------------------------------------------------------------------- |
| **MOVE**   | Move to adjacent walkable cell | 4 directions (up/down/left/right); generates noise (radius 2); can't move through walls   |
| **WAIT**   | Stay in place for 1 turn       | No movement; generates NO noise (radius 0); silent action                                 |
| **ESCAPE** | Escape on EXIT tile            | Only executable when standing on EXIT tile; takes full 1 turn; generates noise (radius 3) |

### **BIRSRESHTHA (The Guard)**

| Action         | Description                           | Mechanics                                                                                                                                                                        |
| -------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MOVE**       | Move to adjacent cell (guided by AI)  | Moves toward highest probability Rajakar location OR toward known Rajakar location if seen; avoids back-and-forth loops                                                          |
| **WAIT**       | Stay in place for 1 turn              | No movement; useful for ambush or when uncertain                                                                                                                                 |
| **POWER SCAN** | Special detection ability (automatic) | Activates every 4 BirSreshtha turns (turns 4, 8, 12, etc.); reveals all cells within 2-cell radius in all 8 directions; ignores walls; instantly reveals Rajakar if within range |

---

## Image Compliance Check

### Current "HOW TO PLAY" Text:

1. ✓ **"Move silently"** - COMPLIANT
   - Correct: Rajakar moves quietly (WAIT is completely silent)
2. ✓ **"Avoid detection"** - COMPLIANT
   - Correct: Must avoid BirSreshtha's sight and noise detection
3. ✓ **"Use cover"** - COMPLIANT
   - Correct: Walls block BirSreshtha's straight sight; use them strategically
4. ⚠ **"Get adjacent to capture"** - PARTIALLY COMPLIANT (AMBIGUOUS)
   - **ISSUE**: Doesn't specify WHO and HOW
   - **Current meaning unclear**: Sounds like Rajakar gets adjacent to something
   - **Actual mechanic**: BirSreshtha needs to get adjacent to Rajakar to CAPTURE
   - **Recommendation**: Change to **"Avoid getting adjacent to the guard"** OR **"Guard captures when adjacent"**
5. ✓ **"Escape through exit tiles"** - COMPLIANT (but incomplete)
   - Correct: Rajakar must reach exits
   - **Enhancement needed**: Should specify the ESCAPE action is required (it takes 1 full turn)

---

## Missing From "HOW TO PLAY" Image

### Critical Mechanics Not Mentioned:

1. **Wall Blocking** - Walls prevent guard's straight sight (important strategy)
2. **Noise Mechanics** - Moving makes noise; waiting is silent (key for stealth)
3. **Turn Limits** - 60 turns total before draw
4. **ESCAPE Action** - Reaching exit isn't enough; must use ESCAPE (takes 1 turn)
5. **Range Limits** - Guard's straight sight has limited range (3 cells)

---

## Recommended Changes to Image

### ✓ UPDATED - Now Includes:

1. ✓ **"Move silently"** - Rajakar should move quietly
2. ✓ **"Avoid detection"** - Core mechanic
3. ✓ **"Use cover"** - Walls block guard's sight
4. ✓ **"Guard captures when adjacent"** - FIXED from ambiguous "Get adjacent to capture"
5. ✓ **"Guard has a power scan every 4 turns"** - NEW: Power Scan ability included
6. ✓ **"Escape through exit tiles"** - Full escape mechanic

### Power Scan Details (Now in "How to Play"):

- **Cooldown**: Activates every 4 BirSreshtha turns
- **Coverage**: 2-cell radius in all 8 directions (cardinal + diagonal)
- **Wall Penetration**: Ignores walls unlike regular sight
- **Threat Level**: HIGH - automatically reveals Rajakar if within range
- **Strategy**: Avoid staying near BirSreshtha when scan timer approaches turn 4, 8, 12, etc.

---

## Summary Table: Move Availability

| Entity          | Move          | Wait       | Escape      | Power Scan        | Notes                                                      |
| --------------- | ------------- | ---------- | ----------- | ----------------- | ---------------------------------------------------------- |
| **Rajakar**     | ✓ (4 dirs)    | ✓ (silent) | ✓ (on EXIT) | ✗                 | Generates noise on MOVE/ESCAPE                             |
| **BirSreshtha** | ✓ (AI-guided) | ✓          | ✗           | ✓ (every 4 turns) | Hunts based on probability/vision; Auto scan ignores walls |
