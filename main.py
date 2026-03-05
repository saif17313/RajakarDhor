# main.py
import pygame
from settings import (
    SCREEN_W, SCREEN_H, FPS, TITLE,
    GRID_SIZE, TILE_SIZE, BOARD_PX,
    UI_PANEL_W, TOP_BAR_H,
    BG, TOP_BAR_BG, PANEL_BG, BOARD_BG,
    GRID_LINE, TILE_A, TILE_B,
    WALL_FILL, WALL_EDGE,
    EXIT_FILL, EXIT_EDGE, EXIT_GLOW
)
from render.ui import draw_ui
from core.grid import Grid, FLOOR, WALL, EXIT


def draw_layout(screen, grid, font_exit):
    # Background
    screen.fill(BG)

    # Top bar
    top_bar_rect = pygame.Rect(0, 0, SCREEN_W, TOP_BAR_H)
    pygame.draw.rect(screen, TOP_BAR_BG, top_bar_rect)

    # Board area
    board_rect = pygame.Rect(0, TOP_BAR_H, BOARD_PX, BOARD_PX)
    pygame.draw.rect(screen, BOARD_BG, board_rect)

    # UI panel
    panel_rect = pygame.Rect(BOARD_PX, 0, UI_PANEL_W, SCREEN_H)
    pygame.draw.rect(screen, PANEL_BG, panel_rect)

    # Divider line
    pygame.draw.line(screen, GRID_LINE, (BOARD_PX, 0), (BOARD_PX, SCREEN_H), 2)

    # --- Draw tiles from grid ---
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            x = c * TILE_SIZE
            y = TOP_BAR_H + r * TILE_SIZE
            rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

            t = grid.get(r, c)

            if t == WALL:
                pygame.draw.rect(screen, WALL_FILL, rect)
                pygame.draw.rect(screen, WALL_EDGE, rect, width=2)

            else:
                # floor (keep your nice checkerboard for walkable tiles)
                base = TILE_A if (r + c) % 2 == 0 else TILE_B
                pygame.draw.rect(screen, base, rect)

                if t == EXIT:
                    # exit overlay
                    pygame.draw.rect(screen, EXIT_FILL, rect, border_radius=10)

                    # glow (cheap but looks great)
                    glow = pygame.Surface(
                        (TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    pygame.draw.rect(
                        glow, EXIT_GLOW, glow.get_rect(), border_radius=10)
                    screen.blit(glow, (x, y))

                    pygame.draw.rect(screen, EXIT_EDGE, rect,
                                     width=3, border_radius=10)

                    # small "E" mark
                    label = font_exit.render("E", True, (10, 10, 12))
                    lx = x + (TILE_SIZE - label.get_width()) // 2
                    ly = y + (TILE_SIZE - label.get_height()) // 2
                    screen.blit(label, (lx, ly))

    # Grid lines (on top for crisp look)
    for i in range(GRID_SIZE + 1):
        x = i * TILE_SIZE
        pygame.draw.line(screen, GRID_LINE, (x, TOP_BAR_H),
                         (x, TOP_BAR_H + BOARD_PX), 1)

        y = TOP_BAR_H + i * TILE_SIZE
        pygame.draw.line(screen, GRID_LINE, (0, y), (BOARD_PX, y), 1)


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    # Create fonts
    font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
    font_body = pygame.font.SysFont("Segoe UI", 18)
    font_small = pygame.font.SysFont("Segoe UI", 14)
    fonts = (font_title, font_body, font_small)

    # --- Create a test maze (you can change this anytime) ---
    ascii_map = [
        "........",
        ".##..#..",
        ".#...#..",
        ".#..##..",
        "...#....",
        "..##..#.",
        "...#....",
        "........",
    ]
    grid = Grid.from_ascii(ascii_map)
    grid.place_random_exits(n=2, seed=7)  # seed makes it consistent each run

    # Create temporary UI state for testing
    state = {
        "current": "Rajakar",
        "turn": 0,
        "max_turns": 60,
        "seen": False,
        "heard": False
    }

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds since last frame

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Test keyboard controls
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    state["current"] = "Guard" if state["current"] == "Rajakar" else "Rajakar"
                elif event.key == pygame.K_v:
                    state["seen"] = not state["seen"]
                elif event.key == pygame.K_h:
                    state["heard"] = not state["heard"]
                elif event.key == pygame.K_n:
                    state["turn"] = min(state["turn"] + 1, state["max_turns"])

        # --- Update ---
        # (nothing yet)

        # --- Draw ---
        draw_layout(screen, grid, font_small)
        draw_ui(screen, fonts, state)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
