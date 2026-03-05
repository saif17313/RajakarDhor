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
