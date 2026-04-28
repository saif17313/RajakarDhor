# RajakarDhor - Complete Game Guide & Analysis

## Table of Contents
1. [Game Overview](#game-overview)
2. [Game Concept](#game-concept)
3. [Character Roles](#character-roles)
4. [Movement & Actions](#movement--actions)
5. [Game Mechanics](#game-mechanics)
6. [Detection System](#detection-system)
7. [Win Conditions](#win-conditions)
8. [Game Flow](#game-flow)
9. [UI & Information Display](#ui--information-display)
10. [Strategy & Tactics](#strategy--tactics)

---

## Game Overview

**RajakarDhor** is a **turn-based stealth/tactical game** set on a 10x10 grid-based maze. It's a two-player asymmetric game where:
- One player takes the role of **Rajakar** (the thief/intruder trying to escape)
- The other takes **Birsreshtha** (the guard/defender trying to prevent escape)

**Key Statistics:**
- **Grid Size**: 10×10 cells
- **Maximum Turns**: 60 (30 rounds when alternating turns)
- **Tile Size**: 64 pixels (48-64 recommended)
- **Game Speed**: 60 FPS with adjustable simulation speed
- **Playable Mode**: Fully automated AI gameplay (both players controlled by AI)

---

## Game Concept

### Theme: Medieval Indian Tactics
The game name "RajakarDhor" has roots in Indian administrative history:
- **Rajakar**: A historical term referring to tax collectors or administrators
- **Dhor**: Pursuit/capture

### Gameplay Philosophy
- **Asymmetric**: Each player has fundamentally different abilities and objectives
- **Information Warfare**: Players have incomplete information about each other
- **Strategic Depth**: Combines stealth (Rajakar) with hunting (Birsreshtha)
- **Probabilistic**: Uses belief maps and statistical inference for AI decision-making

### Target Audience
- Strategy game enthusiasts
- AI/Game Theory enthusiasts
- Tactical puzzle players

---

## Character Roles

### 1. RAJAKAR (The Intruder/Thief) 🏃‍♂️

#### Objective
**Escape the maze by reaching an EXIT tile and executing an ESCAPE action**

#### Role Description
Rajakar is an infiltrator trying to escape through exit points in the maze. The character must:
- Move silently through the maze
- Avoid detection by Birsreshtha
- Use walls as cover to block sightlines
- Navigate to designated EXIT tiles
- Execute the ESCAPE action to win

#### Capabilities
- **Vision**: Can see in 4 cardinal directions (up/down/left/right) up to 3 cells away
- **Can see through walls**: Does NOT have line-of-sight restrictions
- **Silent movement**: Waiting generates NO noise
- **Escape ability**: Can only use on EXIT tiles

#### Player Type
- Typically controlled by AI (optional: human player mode)
- Strategy: Stealth, evasion, path-finding
- Difficulty: Medium (must balance speed with stealth)

---

### 2. BIRSRESHTHA (The Guard/Defender) 🛡️

#### Objective
**Capture Rajakar by getting adjacent to them AFTER Birsreshtha's action**

#### Role Description
Birsreshtha is the defender protecting the maze, tracking and intercepting the escaped. The character must:
- Locate Rajakar using various detection methods
- Track Rajakar's likely positions using probability inference
- Move toward and intercept Rajakar
- Use the power scan strategically
- Maintain awareness of exit points

#### Capabilities
- **Directional Sight**: Sees in the direction facing (4 cardinal directions), up to 3 cells away, blocked by walls
- **Orthogonal Range**: Always-on detection in cardinal directions ignoring walls
- **Power Scan**: Special ability available every 4 turns
  - 8-directional coverage (orthogonal + diagonal)
  - Radius: 2 cells
  - **Ignores walls** - can penetrate obstacles
  - Instantly reveals Rajakar if within range
- **AI Assistance**: Sophisticated AI that uses both Minimax (when Rajakar seen) and Probability Maps (when hidden)

#### Player Type
- Controlled by AI with advanced decision-making
- Strategy: Hunting, predicting, narrowing down possibilities
- Difficulty: Hard (complex AI with multiple algorithms)

---

## Movement & Actions

### RAJAKAR Actions

| Action | Description | Noise | When Available | Duration | Effect |
|--------|-------------|-------|-----------------|----------|--------|
| **MOVE** | Move to adjacent cell (4 directions) | 2 cells radius | Always (valid floor) | 1 turn | Generates noise, reveals position to those within range |
| **WAIT** | Stay in place, no action | Silent (0) | Always | 1 turn | **No noise generated** - perfect for stealth |
| **ESCAPE** | Execute escape sequence | 3 cells radius | On EXIT tiles only | 1 turn | **Wins the game** if Birsreshtha doesn't capture first |

#### Movement Constraints
- **Can move**: To adjacent walkable floor tiles (4 directions only: up/down/left/right)
- **Cannot move**: Through walls (#), out of bounds, or diagonally
- **Line of Sight**: Not required for movement (can move behind walls)

#### Noise Mechanics
When Rajakar performs an action, noise is generated:
- **MOVE**: Noise reaches up to 2 cells away (Manhattan distance)
- **WAIT**: **No noise** (silent action)
- **ESCAPE**: Noise reaches up to 3 cells away (loudest action)

**Strategic Implication**: If Birsreshtha is within the noise radius, they HEAR the action and update their belief map accordingly.

---

### BIRSRESHTHA Actions

| Action | Description | Trigger | When Available | Effect |
|--------|-------------|---------|-----------------|--------|
| **MOVE** | Move to adjacent cell (AI-guided) | AI decision | Always (valid floor) | Moves toward Rajakar or likely location |
| **WAIT** | Stay in place | AI decision | Always | Hold position, useful for ambush or when uncertain |
| **POWER SCAN** | Special detection ability | Automatic (every 4 turns) | Every 4th Birsreshtha turn | Reveals all cells within 2-cell radius in all 8 directions |

#### Detection Methods (Passive)

1. **Directional Sight** (Always Active)
   - **Coverage**: Direction facing (one of 4 cardinal directions)
   - **Range**: 3 cells maximum
   - **Obstacles**: Blocked by walls (line-of-sight required)
   - **Visibility**: Shows up as light blue tint on grid

2. **Orthogonal Range** (Always Active)
   - **Coverage**: All 4 cardinal directions
   - **Range**: 3 cells maximum
   - **Obstacles**: Ignores walls (penetrates obstacles)
   - **Purpose**: Always-on backup detection

3. **Noise Detection** (Passive)
   - **Triggered By**: Rajakar's MOVE or ESCAPE actions
   - **Range**: Action-dependent (2 for MOVE, 3 for ESCAPE)
   - **Information**: Tells Birsreshtha that Rajakar made an action, but not exact position (only distance)

4. **Power Scan** (Active Ability)
   - **Frequency**: Every 4 Birsreshtha turns (automatic at turns 4, 8, 12, 16, etc.)
   - **Coverage**: 8 directions (cardinal + diagonal)
   - **Range**: 2 cells radius
   - **Wall Penetration**: **Ignores walls completely**
   - **Accuracy**: If Rajakar is within range, instantly reveals position
   - **Visual Feedback**: Blue highlighted cells appear on grid showing scan area
   - **AI Uses**: Updates belief map with this evidence

#### AI Decision-Making

Birsreshtha's moves are determined by sophisticated AI:

**When Rajakar is SEEN** (detected directly):
- Uses **MINIMAX with Alpha-Beta Pruning** algorithm
- Looks 3 moves ahead
- Makes optimal interception move
- Direct pursuit mode

**When Rajakar is HIDDEN** (not currently visible):
- Uses **Probability-Based Belief Map Tracking**
- Maintains probability distribution of possible locations
- Moves toward highest-probability regions
- Incorporates noise, scan results, and motion prediction
- Adaptive hunting mode

---

## Game Mechanics

### Grid System

**Structure:**
- 10×10 grid (100 cells total)
- Three tile types:
  - **FLOOR (.)**: Walkable space (default)
  - **WALL (#)**: Impassable obstacle, blocks line-of-sight
  - **EXIT (E)**: Escape point for Rajakar (appears as green tile)

**Coordinates:**
- (0,0) is top-left corner
- Rows increase downward (0-9)
- Columns increase rightward (0-9)
- Movement uses compass directions: Up (-1,0), Down (+1,0), Left (0,-1), Right (0,+1)

### Spawn System

Rajakar and Birsreshtha are spawned with strict distance constraints:

**Spawn Constraints:**
- Rajakar to Birsreshtha: Minimum 4 cells (Manhattan distance)
- Rajakar to each EXIT: Minimum 4 cells
- Birsreshtha to each EXIT: Minimum 8 cells
- EXIT to EXIT: Minimum 8 cells
- Attempts: Up to 8000 tries to find valid spawn configuration
- Exits: 2 per game

**Rationale**: Ensures fair starting positions - Rajakar has space to move, Birsreshtha isn't positioned to capture immediately.

### Turn System

**Turn Structure:**
1. **Current Player**: One player takes an action
2. **Turn Count**: Increments after action resolves
3. **Alternation**: Switches to other player
4. **Order**: Rajakar starts first
5. **Total Limit**: 60 turns maximum

**Timing:**
- Each turn represents one action (MOVE, WAIT, or special)
- Actions resolve immediately
- No simultaneous turns (fully sequential)
- Players alternate: R → B → R → B → ...

**Turn Counting:**
- Turns = individual actions (60 total)
- Rounds = pairs of actions (30 rounds = 1 Rajakar + 1 Birsreshtha)
- UI displays: "Turn Count: X / 60"

### Detection & Observation

**What each player knows:**

At the START of Rajakar's turn:
- If Birsreshtha is visible in Rajakar's 4-direction sight (range 3, blocked by walls)
- If noise was heard from Birsreshtha (not implemented for Birsreshtha yet)

At the START of Birsreshtha's turn:
- If Rajakar is visible through directional sight (range 3, blocked by walls)
- If Rajakar is within orthogonal range (range 3, ignores walls)
- If noise was heard from Rajakar's last action (range 2 for MOVE, range 3 for ESCAPE)
- Power scan evidence (if active and within range)

**Fog of War:**
- Birsreshtha doesn't know EXIT positions until seeing them directly
- Rajakar doesn't know Birsreshtha's exact position after losing sight
- Both use probability/inference to track hidden opponent

---

## Detection System

### Birsreshtha's Detection Channels

#### 1. Directional Sight (Primary Detection)
- **Active**: Always (in facing direction)
- **Range**: 3 cells in one cardinal direction
- **Line of Sight**: Yes - blocked by walls
- **Directions**: Up, Down, Left, Right (Birsreshtha turns to face)
- **Accuracy**: Perfect - if visible, exact position is known
- **Visuals**: Light blue tint on grid shows sight cone

**Example**: If Birsreshtha faces UP and Rajakar is 2 cells above in direct line with no walls → DETECTED

#### 2. Orthogonal Range (Passive Detection)
- **Active**: Always
- **Range**: 3 cells in cardinal directions
- **Line of Sight**: No - ignores walls
- **Accuracy**: Perfect if within range
- **Purpose**: Backup detection that works through walls

**Example**: If Rajakar is 2 cells to the RIGHT even behind a wall → DETECTED

#### 3. Noise Detection (Hearing)
- **Active**: When Rajakar moves or escapes
- **Trigger**: 
  - MOVE action → 2 cell radius noise
  - ESCAPE action → 3 cell radius noise
  - WAIT action → 0 (no noise)
- **Information**: Birsreshtha hears *that* something happened within range, but exact position unclear
- **Effect**: Updates probability belief map with noise constraint
- **Advantages**: Works through walls, detects WAIT is NOT performed

#### 4. Power Scan (Special Ability)
- **Active**: Every 4 Birsreshtha turns (turns 4, 8, 12, etc.)
- **Range**: 2 cells in all 8 directions (orthogonal + diagonal)
- **Line of Sight**: No - penetrates all walls
- **Coverage**: 24 cells maximum (8 directions × 2 cells + center)
- **Accuracy**: Perfect - instant reveal if Rajakar is within range
- **Visuals**: Bright blue highlighted cells appear briefly
- **Strategic**: Most dangerous detection method (no hiding from scan)

**Power Scan Pattern** (from Birsreshtha at center):
```
  □ □ □
  □ □ □
□ □ B □ □
  □ □ □
  □ □ □
```
All 24 surrounding cells + center in 8 directions, radius 2

### Rajakar's Detection (Simpler)

- **Method**: 4-directional sight only
- **Range**: 3 cells in cardinal directions
- **Line of Sight**: Yes - blocked by walls
- **Detection Target**: Can only see Birsreshtha
- **Purpose**: Know if guard is visible, doesn't affect gameplay (AI-controlled)

---

## Win Conditions

### Rajakar WINS 🏆
**Condition**: Standing on EXIT tile + ESCAPE action executed

**Mechanics**:
1. Move adjacent to or onto an EXIT tile
2. Use ESCAPE action while on EXIT tile
3. If Birsreshtha has NOT moved adjacent to Rajakar yet this turn → **RAJAKAR WINS**
4. Screen displays: "RAJAKAR WINS!"
5. Score: Victory for Rajakar

**Requirements**:
- EXIT tile must be reached (visible on grid as green)
- ESCAPE action must be executed on that exact tile
- Birsreshtha must not be adjacent when Rajakar escapes
- ESCAPE takes exactly 1 full turn

### Birsreshtha WINS 🏆
**Condition**: Adjacent to Rajakar (Manhattan distance = 1) AFTER Birsreshtha's action

**Mechanics**:
1. Birsreshtha performs MOVE action to move adjacent to Rajakar
2. After Birsreshtha's action resolves, check: Is Birsreshtha adjacent to Rajakar?
3. If YES → **BIRSRESHTHA WINS**
4. Screen displays: "BIRSRESHTHA WINS!"
5. Score: Victory for Birsreshtha

**Requirements**:
- Must be adjacent AFTER Birsreshtha moves (not before)
- Adjacency = Manhattan distance of 1 (4 adjacent cells: up/down/left/right)
- Capture doesn't require facing or direct sight
- Diagonal adjacency does NOT count

**Note**: Rajakar cannot be captured WHILE moving. Capture check happens AFTER Birsreshtha's action completes.

### DRAW 🤝
**Condition**: Reach turn limit without either player winning

**Mechanics**:
1. Game progresses through turns
2. At end of turn 60: Check if winner is still `None`
3. If YES → Game is **DRAW**
4. Screen displays: "DRAW!"
5. Score: Draw (no winner)

**Why Draw Happens**:
- Rajakar managed to evade for maximum turns without escaping
- Birsreshtha couldn't intercept in time
- Both players' strategies were defensive

**Duration**: 30 complete rounds (60 individual turns)

---

## Game Flow

### Initialization Phase
1. **Load Game**: Parse maze from ASCII map
2. **Spawn Players**: Generate valid spawn positions for Rajakar and Birsreshtha
3. **Place Exits**: Position 2 EXIT tiles using spawn constraints
4. **Initialize AI**: 
   - Create probability map for Birsreshtha
   - Reset detection clues
   - Set facing direction for Birsreshtha
5. **UI Setup**: Display initial game state

### Game Loop (Repeating)

```
While running AND winner is None:
  
  1. Handle Events (quit, pause, restart)
  2. Check if current player is AI
  3. If AI turn:
     - Delay for visibility (300-350ms)
     - If Rajakar: AI chooses move (fuzzy)
     - If Birsreshtha: AI chooses move (Minimax or Probability)
  4. Process Action:
     - Execute movement/action
     - Update positions
     - Generate noise if applicable
     - Check win conditions:
       * Rajakar on EXIT + ESCAPE → Rajakar Wins
       * Birsreshtha adjacent after move → Birsreshtha Wins
       * Turn 60 reached → Draw
  5. Update Detection:
     - Calculate what each player can see
     - Update belief maps
     - Record noise/sight clues
  6. Switch Turns:
     - Current = other player
     - Increment turn counter
  7. Render:
     - Draw grid and tiles
     - Show players (R=Rajakar, B=Birsreshtha)
     - Show vision cones (gold for R, blue for B)
     - Show power scan highlights (if active)
     - Display UI panel with stats
  8. Update Frame:
     - Display to screen
     - Cap FPS to 60
```

### End Game Phase
1. **Game Over**: Display win message or draw
2. **Options**:
   - Press R to restart simulation
   - Click restart button → Reset game
   - Click menu button → Return to main menu
3. **Statistics**: Show turn count and winner

---

## UI & Information Display

### Main Game Screen Layout

```
┌─────────────────────────────────────────────┐
│        TOP BAR (Game Status)                │
├─────────────────────┬───────────────────────┤
│                     │                       │
│   10×10 GRID        │  RIGHT PANEL (UI)    │
│   • Walls (#)       │  • Round Info        │
│   • Floor (.)       │  • Detection Signals │
│   • Exits (E)       │  • Objective Info    │
│   • Rajakar (R)     │  • Confidence %      │
│   • Birsreshtha (B) │  • Exit Tracking     │
│                     │                       │
└─────────────────────┴───────────────────────┘
```

### Information Displayed

**Right Panel Cards:**

1. **Round Info**
   - Current player: Rajakar or Birsreshtha
   - Turn count: Current / Max (e.g., 12 / 60)
   - Confidence: % probability (for Birsreshtha's belief map)
   - Exits discovered: X/Y (how many Birsreshtha has found)

2. **Detection Signals**
   - For Rajakar's turn: "Contact this turn: [Seen/Not Seen] [Heard/Not Heard]"
   - For Birsreshtha's turn: "Signals this turn: [Seen/Not Seen] [Heard/Not Heard]"

3. **Objective**
   - Rajakar turn: "Reach EXIT and Escape. (Escape takes 1 full turn on EXIT)"
   - Birsreshtha turn: "Get adjacent to capture. (Capture check happens after Birsreshtha move)"

4. **Visual Indicators**
   - Green circle: Positive (detection success)
   - Red circle: Alert (danger zone)
   - Gold tint: Rajakar's vision area
   - Blue tint: Birsreshtha's vision area
   - Bright blue: Power scan area (when active)

### Pause Menu
- **Options**:
  - Resume Game
  - Restart Match
  - Main Menu

### Game Over Screen
- **Message**: "RAJAKAR WINS!" or "BIRSRESHTHA WINS!" or "DRAW!"
- **Buttons**:
  - Restart
  - Main Menu

---

## Strategy & Tactics

### RAJAKAR Strategies

#### Offensive (Escape-Focused)
1. **Speed Route**: Move quickly toward nearest EXIT while avoiding Birsreshtha
2. **Noise Masking**: Wait (silent) when Birsreshtha is far, MOVE only when sure it's safe
3. **Wall Hugging**: Use walls to block Birsreshtha's directional sight
4. **False Trails**: Move in one direction to generate noise, then WAIT
5. **Exit Rushing**: Once path to EXIT is clear, sprint there before power scan

#### Defensive (Evasion-Focused)
1. **Silent Movement**: Alternate MOVE with WAIT to confuse Birsreshtha's tracking
2. **Maze Mastery**: Know wall patterns to maximize blocked sightlines
3. **Temporal Avoidance**: Move when power scan won't activate (turns 1-3, 5-7, etc.)
4. **Corner Camping**: Hide in maze corners where detection is hardest
5. **Misdirection**: Generate noise far from actual EXIT location

#### Mixed Strategy
- **Mid-Game**: Conservative movement, gather information
- **Late-Game**: Aggressive push toward EXIT when turn count is high
- **Crisis**: If detected, either escape or evade depending on distance

### BIRSRESHTHA Strategies

#### Aggressive (Interception-Focused)
1. **Direct Pursuit**: Move directly toward last known position of Rajakar
2. **Choke Points**: Position near EXITs (discovered through vision) to block escape
3. **Scan Timing**: Use power scan strategically at turns 4, 8, 12, etc.
4. **Narrowing**: Eliminate possibilities based on noise range
5. **Ambush**: Wait at likely escape routes

#### Defensive (Prevention-Focused)
1. **Perimeter Control**: Patrol around all known EXITs
2. **Exit Discovery**: Actively search maze to find all EXIT locations first
3. **Containment**: Use walls to restrict Rajakar's movement options
4. **Information Gathering**: Use every detection method to build accurate belief map
5. **Entropy Reduction**: Each turn, eliminate impossible positions

#### Mixed Strategy
- **Early Game**: Explore maze, discover exits, build belief map
- **Mid Game**: Active hunting when Rajakar generates noise
- **Late Game**: Aggressive if Rajakar not found; passive if confident of position

### Tactical Tips

**For Rajakar:**
- WAIT is your friend (no noise)
- Move when Birsreshtha just moved (can't capture yet)
- Plan EXIT route during early game
- Use walls to break line-of-sight
- Don't move on turns 4, 8, 12 (power scan danger)

**For Birsreshtha:**
- Power scan is your superpower (use every 4 turns)
- Track noise sources with belief map
- EXITs are natural chokepoints
- Don't waste moves; use probability to predict
- Orthogonal range (ignores walls) is free detection

**General:**
- Maze layout determines strategy (open = hard for Rajakar, tight = good for hiding)
- Turn count increases pressure on Rajakar (must escape)
- Detection is asymmetric (Birsreshtha has more tools)

---

## Technical Details

### Configuration (settings.py)

| Setting | Value | Purpose |
|---------|-------|---------|
| GRID_SIZE | 10 | 10×10 maze |
| TILE_SIZE | 64 px | Visual size |
| MAX_TURNS | 60 | Game length |
| SIGHT_RANGE | 3 cells | Detection range |
| NOISE_MOVE | 2 cells | Movement noise radius |
| NOISE_WAIT | 0 cells | Silent action |
| NOISE_ESCAPE | 3 cells | Escape noise radius |
| BIRSRESHTHA_POWER_COOLDOWN_TURNS | 4 | Scan frequency |
| BIRSRESHTHA_POWER_SCAN_RADIUS | 2 cells | Scan range |
| BIRSRESHTHA_MINIMAX_DEPTH | 3 plies | Look-ahead depth |

### Performance
- **Frame Rate**: 60 FPS
- **AI Delay**: 300-350ms per move (for visibility)
- **Grid Updates**: Real-time each frame
- **Rendering**: Pygame 2D rendering

---

## Summary

**RajakarDhor** is a sophisticated tactical game combining:
- ✓ Turn-based grid movement
- ✓ Asymmetric gameplay (two different playstyles)
- ✓ Information uncertainty (fog of war)
- ✓ Advanced AI (Minimax + Probability Maps)
- ✓ Strategic depth (multiple win paths)
- ✓ Rich detection mechanics (sight, sound, scan)

The game creates an emergent gameplay experience where Rajakar must use stealth and evasion while Birsreshtha employs hunting and probability inference. The ~30-turn length ensures paced, strategic gameplay where every action matters.
