# main.py
import pygame
from settings import (
    SCREEN_W, SCREEN_H, FPS, TITLE,
    GRID_SIZE, TILE_SIZE, BOARD_PX,
    UI_PANEL_W, TOP_BAR_H,
    BG, TOP_BAR_BG, PANEL_BG, BOARD_BG,
    GRID_LINE, TILE_A, TILE_B
)


def draw_layout(screen):
    # Background
    screen.fill(BG)

    # Top bar
    top_bar_rect = pygame.Rect(0, 0, SCREEN_W, TOP_BAR_H)
    pygame.draw.rect(screen, TOP_BAR_BG, top_bar_rect)

    # Board area (below top bar, left side)
    board_rect = pygame.Rect(0, TOP_BAR_H, BOARD_PX, BOARD_PX)
    pygame.draw.rect(screen, BOARD_BG, board_rect)

    # UI panel (right side)
    panel_rect = pygame.Rect(BOARD_PX, 0, UI_PANEL_W, SCREEN_H)
    pygame.draw.rect(screen, PANEL_BG, panel_rect)

    # Divider line between board and panel
    pygame.draw.line(screen, GRID_LINE, (BOARD_PX, 0), (BOARD_PX, SCREEN_H), 2)

    # Draw checkerboard tiles + grid lines
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            x = c * TILE_SIZE
            y = TOP_BAR_H + r * TILE_SIZE
            tile_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

            # checker pattern
            color = TILE_A if (r + c) % 2 == 0 else TILE_B
            pygame.draw.rect(screen, color, tile_rect)

    # Grid lines (crisp)
    for i in range(GRID_SIZE + 1):
        # vertical
        x = i * TILE_SIZE
        pygame.draw.line(screen, GRID_LINE, (x, TOP_BAR_H),
                         (x, TOP_BAR_H + BOARD_PX), 1)

        # horizontal
        y = TOP_BAR_H + i * TILE_SIZE
        pygame.draw.line(screen, GRID_LINE, (0, y), (BOARD_PX, y), 1)


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds since last frame

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Update ---
        # (nothing yet)

        # --- Draw ---
        draw_layout(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
