# main.py
import pygame
from settings import (
    SCREEN_W, SCREEN_H, FPS, TITLE,
    GRID_SIZE, TILE_SIZE, BOARD_PX,
    UI_PANEL_W, TOP_BAR_H,
    BG, TOP_BAR_BG, PANEL_BG, BOARD_BG,
    GRID_LINE, TILE_A, TILE_B,
    WALL_FILL, WALL_EDGE,
    EXIT_FILL, EXIT_EDGE, EXIT_GLOW,
    RAJAKAR_FILL, RAJAKAR_EDGE,
    GUARD_FILL, GUARD_EDGE,
    PLAYER_SHADOW, PLAYER_GLOW,
    SIGHT_RANGE, NOISE_MOVE, NOISE_WAIT, NOISE_ESCAPE, MAX_TURNS
)
from render.ui import draw_ui
from core.grid import Grid, FLOOR, WALL, EXIT
from core.spawn import spawn_match
from core.rules import manhattan, in_straight_sight, heard_noise


def try_move(grid, pos, dr, dc):
    r, c = pos
    nr, nc = r + dr, c + dc
    if grid.is_walkable(nr, nc):
        return (nr, nc), True
    return pos, False


def action_noise_radius(action_name: str) -> int:
    if action_name == "MOVE":
        return NOISE_MOVE
    if action_name == "WAIT":
        return NOISE_WAIT
    if action_name == "ESCAPE":
        return NOISE_ESCAPE
    return 0


def draw_player(screen, r, c, fill, edge, label, font_small):
    # tile center
    cx = c * TILE_SIZE + TILE_SIZE // 2
    cy = TOP_BAR_H + r * TILE_SIZE + TILE_SIZE // 2

    radius = int(TILE_SIZE * 0.30)

    # shadow (RGBA)
    shadow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(
        shadow, PLAYER_SHADOW,
        (TILE_SIZE // 2, TILE_SIZE // 2 + 10),
        radius + 6
    )
    screen.blit(shadow, (c * TILE_SIZE, TOP_BAR_H + r * TILE_SIZE))

    # glow ring
    glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(glow, PLAYER_GLOW, (TILE_SIZE //
                       2, TILE_SIZE // 2), radius + 10)
    screen.blit(glow, (c * TILE_SIZE, TOP_BAR_H + r * TILE_SIZE))

    # body
    pygame.draw.circle(screen, fill, (cx, cy), radius)
    pygame.draw.circle(screen, edge, (cx, cy), radius, width=3)

    # label (R / G)
    txt = font_small.render(label, True, (10, 10, 12))
    screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))


def draw_layout(screen, grid, font_exit, raj_pos, guard_pos):
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

    # --- Draw players on top of tiles ---
    rr, rc = raj_pos
    gr, gc = guard_pos

    draw_player(screen, rr, rc, RAJAKAR_FILL, RAJAKAR_EDGE, "R", font_exit)
    draw_player(screen, gr, gc, GUARD_FILL, GUARD_EDGE, "G", font_exit)


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

    # Spawn players + exits using smart spawn system
    spawn = spawn_match(grid, seed=7)
    rajakar_pos = spawn["rajakar"]
    guard_pos = spawn["guard"]
    exits = spawn["exits"]

    # Clear any old exits and set the new ones
    for (r, c) in grid.all_cells_of_type(EXIT):
        grid.set(r, c, FLOOR)
    for (r, c) in exits:
        grid.set(r, c, EXIT)

    # Game state variables
    current = "Rajakar"   # Rajakar starts
    turn_count = 0
    winner = None         # "Rajakar" / "Guard" / "Draw" / None

    # What each player knows about the opponent on THEIR upcoming turn:
    clues = {
        "Rajakar": {"seen": False, "heard": False},
        "Guard":   {"seen": False, "heard": False},
    }

    # UI state (updated every frame)
    state = {
        "current": current,
        "turn": turn_count,
        "max_turns": MAX_TURNS,
        "seen": clues[current]["seen"],
        "heard": clues[current]["heard"],
    }

    def end_turn(action_name: str):
        nonlocal current, turn_count, winner
        nonlocal rajakar_pos, guard_pos, clues

        # 1) Check win conditions tied to the actor
        if current == "Rajakar":
            # Rajakar wins if standing on EXIT and used ESCAPE action
            if action_name == "ESCAPE" and grid.get(*rajakar_pos) == EXIT:
                winner = "Rajakar"
        else:
            # Guard wins if on the SAME tile as Rajakar (captured)
            if guard_pos == rajakar_pos:
                winner = "Guard"

        # 2) Increment turn count and draw rule
        turn_count += 1
        if winner is None and turn_count >= MAX_TURNS:
            winner = "Draw"

        # 3) If game ended, don't switch turns
        if winner is not None:
            return

        # 4) Update clues for the NEXT player (the one who will move now)
        if current == "Rajakar":
            # Guard is next: what can Guard sense about Rajakar?
            seen = in_straight_sight(grid, guard_pos, rajakar_pos, SIGHT_RANGE)
            heard = heard_noise(guard_pos, rajakar_pos,
                                action_noise_radius(action_name))
            clues["Guard"] = {"seen": seen, "heard": heard}
            current = "Guard"
        else:
            # Rajakar is next: what can Rajakar sense about Guard?
            seen = in_straight_sight(grid, rajakar_pos, guard_pos, SIGHT_RANGE)
            heard = heard_noise(rajakar_pos, guard_pos,
                                action_noise_radius(action_name))
            clues["Rajakar"] = {"seen": seen, "heard": heard}
            current = "Rajakar"

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds since last frame

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # --- Restart (full respawn) ---
                if event.key == pygame.K_r:
                    spawn = spawn_match(grid)  # random new match
                    rajakar_pos = spawn["rajakar"]
                    guard_pos = spawn["guard"]
                    exits = spawn["exits"]

                    # reset exits on grid
                    for (r, c) in grid.all_cells_of_type(EXIT):
                        grid.set(r, c, FLOOR)
                    for (r, c) in exits:
                        grid.set(r, c, EXIT)

                    current = "Rajakar"
                    turn_count = 0
                    winner = None
                    clues = {"Rajakar": {"seen": False, "heard": False},
                             "Guard": {"seen": False, "heard": False}}
                    continue

                # If game ended, ignore other inputs
                if winner is not None:
                    continue

                acted = False
                action_name = None

                # --- Movement keys (Arrow or WASD) ---
                move_map = {
                    pygame.K_UP: (-1, 0),
                    pygame.K_DOWN: (1, 0),
                    pygame.K_LEFT: (0, -1),
                    pygame.K_RIGHT: (0, 1),

                    pygame.K_w: (-1, 0),
                    pygame.K_s: (1, 0),
                    pygame.K_a: (0, -1),
                    pygame.K_d: (0, 1),
                }

                if event.key in move_map:
                    dr, dc = move_map[event.key]
                    if current == "Rajakar":
                        new_pos, ok = try_move(grid, rajakar_pos, dr, dc)
                        if ok:
                            rajakar_pos = new_pos
                            acted = True
                            action_name = "MOVE"
                    else:
                        new_pos, ok = try_move(grid, guard_pos, dr, dc)
                        if ok:
                            guard_pos = new_pos
                            acted = True
                            action_name = "MOVE"

                # --- Wait ---
                elif event.key == pygame.K_SPACE:
                    acted = True
                    action_name = "WAIT"

                # --- Escape (Rajakar only) ---
                elif event.key == pygame.K_e:
                    if current == "Rajakar" and grid.get(*rajakar_pos) == EXIT:
                        acted = True
                        action_name = "ESCAPE"

                # If an action happened, end turn
                if acted and action_name is not None:
                    end_turn(action_name)

        # --- Update ---
        # Update UI state to match game state
        state["current"] = current
        state["turn"] = turn_count
        state["max_turns"] = MAX_TURNS
        state["seen"] = clues[current]["seen"]
        state["heard"] = clues[current]["heard"]

        # --- Draw ---
        draw_layout(screen, grid, font_small, rajakar_pos, guard_pos)
        draw_ui(screen, fonts, state)

        # Winner overlay
        if winner is not None:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            msg = f"{winner} WINS!" if winner in (
                "Rajakar", "Guard") else "DRAW!"
            big = pygame.font.SysFont("Segoe UI", 44, bold=True).render(
                msg, True, (245, 245, 255))
            small = pygame.font.SysFont("Segoe UI", 18).render(
                "Press R to restart", True, (200, 200, 215))

            screen.blit(
                big, (BOARD_PX // 2 - big.get_width() // 2, SCREEN_H // 2 - 60))
            screen.blit(
                small, (BOARD_PX // 2 - small.get_width() // 2, SCREEN_H // 2 + 6))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
