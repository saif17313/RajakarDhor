# settings.py

GRID_SIZE = 8          # 8x8
TILE_SIZE = 64         # 48 or 64 recommended

BOARD_PX = GRID_SIZE * TILE_SIZE

UI_PANEL_W = 360       # right-side panel width
TOP_BAR_H = 60

SCREEN_W = BOARD_PX + UI_PANEL_W
SCREEN_H = TOP_BAR_H + BOARD_PX

FPS = 60
TITLE = "RajakarDhor"

# --- Colors (simple dark tactical theme) ---
BG = (14, 14, 18)

TOP_BAR_BG = (22, 22, 28)
PANEL_BG = (20, 20, 26)

BOARD_BG = (16, 16, 20)
GRID_LINE = (40, 40, 52)

TILE_A = (24, 24, 32)  # checkerboard light
TILE_B = (20, 20, 28)  # checkerboard dark

# --- UI text + card colors ---
TEXT = (235, 235, 245)
MUTED = (165, 165, 180)

CARD_BG = (26, 26, 34)
CARD_EDGE = (50, 50, 70)

GOOD = (90, 200, 140)   # seen/heard positive indicator
BAD = (220, 90, 90)    # alerts / danger

# --- Tile colors ---
WALL_FILL = (12, 12, 18)
WALL_EDGE = (60, 60, 85)

EXIT_FILL = (28, 110, 70)
EXIT_EDGE = (80, 220, 150)
EXIT_GLOW = (80, 220, 150, 90)  # RGBA for glow
