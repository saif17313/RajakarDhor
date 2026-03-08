# main.py
import pygame
import settings as s
import core.rules as rules
import core.ai as ai
from core.grid import Grid, FLOOR, WALL, EXIT
from core.spawn import spawn_match
from render.ui import draw_ui


def try_move(grid, pos, dr, dc):
    r, c = pos
    nr, nc = r + dr, c + dc
    if grid.is_walkable(nr, nc):
        return (nr, nc), True
    return pos, False


def action_noise_radius(action_name: str) -> int:
    if action_name == "MOVE":
        return s.NOISE_MOVE
    if action_name == "WAIT":
        return s.NOISE_WAIT
    if action_name == "ESCAPE":
        return s.NOISE_ESCAPE
    return 0


def draw_player(screen, r, c, fill, edge, label, font_small, facing=None):
    # tile center
    cx = c * s.TILE_SIZE + s.TILE_SIZE // 2
    cy = s.TOP_BAR_H + r * s.TILE_SIZE + s.TILE_SIZE // 2

    radius = int(s.TILE_SIZE * 0.30)

    # shadow (RGBA)
    shadow = pygame.Surface((s.TILE_SIZE, s.TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(
        shadow, s.PLAYER_SHADOW,
        (s.TILE_SIZE // 2, s.TILE_SIZE // 2 + 10),
        radius + 6
    )
    screen.blit(shadow, (c * s.TILE_SIZE, s.TOP_BAR_H + r * s.TILE_SIZE))

    # glow ring
    glow = pygame.Surface((s.TILE_SIZE, s.TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(glow, s.PLAYER_GLOW, (s.TILE_SIZE //
                       2, s.TILE_SIZE // 2), radius + 10)
    screen.blit(glow, (c * s.TILE_SIZE, s.TOP_BAR_H + r * s.TILE_SIZE))

    # body
    pygame.draw.circle(screen, fill, (cx, cy), radius)
    pygame.draw.circle(screen, edge, (cx, cy), radius, width=3)

    # Direction indicator (arrow) for facing direction
    if facing is not None:
        dr, dc = facing
        arrow_len = int(radius * 0.6)
        arrow_end_x = cx + dc * arrow_len
        arrow_end_y = cy + dr * arrow_len
        # Draw arrow line
        pygame.draw.line(screen, (10, 10, 12), (cx, cy), (arrow_end_x, arrow_end_y), 3)
        # Draw arrow head (small triangle)
        head_size = 5
        if dr != 0:  # Vertical
            points = [
                (arrow_end_x, arrow_end_y),
                (arrow_end_x - head_size, arrow_end_y - dr * head_size),
                (arrow_end_x + head_size, arrow_end_y - dr * head_size)
            ]
        else:  # Horizontal
            points = [
                (arrow_end_x, arrow_end_y),
                (arrow_end_x - dc * head_size, arrow_end_y - head_size),
                (arrow_end_x - dc * head_size, arrow_end_y + head_size)
            ]
        pygame.draw.polygon(screen, (10, 10, 12), points)

    # label (R / G)
    txt = font_small.render(label, True, (10, 10, 12))
    screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))


def draw_layout(screen, grid, font_exit, raj_pos, guard_pos, guard_facing, scan_cells=None):
    # Background
    screen.fill(s.BG)

    # Top bar
    top_bar_rect = pygame.Rect(0, 0, s.SCREEN_W, s.TOP_BAR_H)
    pygame.draw.rect(screen, s.TOP_BAR_BG, top_bar_rect)

    # Board area
    board_rect = pygame.Rect(0, s.TOP_BAR_H, s.BOARD_PX, s.BOARD_PX)
    pygame.draw.rect(screen, s.BOARD_BG, board_rect)

    # UI panel
    panel_rect = pygame.Rect(s.BOARD_PX, 0, s.UI_PANEL_W, s.SCREEN_H)
    pygame.draw.rect(screen, s.PANEL_BG, panel_rect)

    # Divider line
    pygame.draw.line(screen, s.GRID_LINE, (s.BOARD_PX, 0), (s.BOARD_PX, s.SCREEN_H), 2)

    # --- Draw tiles from grid ---
    for r in range(s.GRID_SIZE):
        for c in range(s.GRID_SIZE):
            x = c * s.TILE_SIZE
            y = s.TOP_BAR_H + r * s.TILE_SIZE
            rect = pygame.Rect(x, y, s.TILE_SIZE, s.TILE_SIZE)

            t = grid.get(r, c)

            if t == WALL:
                pygame.draw.rect(screen, s.WALL_FILL, rect)
                pygame.draw.rect(screen, s.WALL_EDGE, rect, width=2)

            else:
                # floor (keep your nice checkerboard for walkable tiles)
                base = s.TILE_A if (r + c) % 2 == 0 else s.TILE_B
                pygame.draw.rect(screen, base, rect)

                if t == EXIT:
                    # exit overlay
                    pygame.draw.rect(screen, s.EXIT_FILL, rect, border_radius=10)

                    # glow (cheap but looks great)
                    glow = pygame.Surface(
                        (s.TILE_SIZE, s.TILE_SIZE), pygame.SRCALPHA)
                    pygame.draw.rect(
                        glow, s.EXIT_GLOW, glow.get_rect(), border_radius=10)
                    screen.blit(glow, (x, y))

                    pygame.draw.rect(screen, s.EXIT_EDGE, rect,
                                     width=3, border_radius=10)

                    # small "E" mark
                    label = font_exit.render("E", True, (10, 10, 12))
                    lx = x + (s.TILE_SIZE - label.get_width()) // 2
                    ly = y + (s.TILE_SIZE - label.get_height()) // 2
                    screen.blit(label, (lx, ly))

    # Guard power scan overlay (transparent blue cells)
    if scan_cells:
        for r, c in scan_cells:
            x = c * s.TILE_SIZE
            y = s.TOP_BAR_H + r * s.TILE_SIZE
            overlay = pygame.Surface((s.TILE_SIZE, s.TILE_SIZE), pygame.SRCALPHA)
            overlay.fill((70, 170, 255, 80))
            screen.blit(overlay, (x, y))
    
    # Guard vision cone (show what Guard can see)
    if guard_facing != (0, 0):
        gr, gc = guard_pos
        dr, dc = guard_facing
        for step in range(1, s.SIGHT_RANGE + 1):
            vr, vc = gr + dr * step, gc + dc * step
            if not grid.in_bounds(vr, vc):
                break
            if grid.get(vr, vc) == WALL:
                break
            x = vc * s.TILE_SIZE
            y = s.TOP_BAR_H + vr * s.TILE_SIZE
            overlay = pygame.Surface((s.TILE_SIZE, s.TILE_SIZE), pygame.SRCALPHA)
            overlay.fill((90, 180, 255, 40))  # Light blue tint for vision
            screen.blit(overlay, (x, y))
    
    # Rajakar vision (4 directions: up, down, left, right)
    rr, rc = raj_pos
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # up, down, left, right
        for step in range(1, s.SIGHT_RANGE + 1):
            vr, vc = rr + dr * step, rc + dc * step
            if not grid.in_bounds(vr, vc):
                break
            if grid.get(vr, vc) == WALL:
                break
            x = vc * s.TILE_SIZE
            y = s.TOP_BAR_H + vr * s.TILE_SIZE
            overlay = pygame.Surface((s.TILE_SIZE, s.TILE_SIZE), pygame.SRCALPHA)
            overlay.fill((240, 190, 70, 30))  # Light gold tint for Rajakar vision
            screen.blit(overlay, (x, y))

    # Grid lines (on top for crisp look)
    for i in range(s.GRID_SIZE + 1):
        x = i * s.TILE_SIZE
        pygame.draw.line(screen, s.GRID_LINE, (x, s.TOP_BAR_H),
                         (x, s.TOP_BAR_H + s.BOARD_PX), 1)

        y = s.TOP_BAR_H + i * s.TILE_SIZE
        pygame.draw.line(screen, s.GRID_LINE, (0, y), (s.BOARD_PX, y), 1)

    # --- Draw players on top of tiles ---
    rr, rc = raj_pos
    gr, gc = guard_pos

    draw_player(screen, rr, rc, s.RAJAKAR_FILL, s.RAJAKAR_EDGE, "R", font_exit)
    draw_player(screen, gr, gc, s.GUARD_FILL, s.GUARD_EDGE, "G", font_exit, facing=guard_facing)


def main():
    pygame.init()
    pygame.display.set_caption(s.TITLE)

    screen = pygame.display.set_mode((s.SCREEN_W, s.SCREEN_H))
    clock = pygame.time.Clock()

    # Create fonts
    font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
    font_body = pygame.font.SysFont("Segoe UI", 18)
    font_small = pygame.font.SysFont("Segoe UI", 14)
    fonts = (font_title, font_body, font_small)

    # --- Create a test maze (you can change this anytime) ---
    ascii_map = [
        "..........",
        ".##..#....",
        ".#...#....",
        ".#..##....",
        "..........",
        "..##..#...",
        "...#......",
        "..........",
        "..#...##..",
        "..........",
    ]
    grid = Grid.from_ascii(ascii_map)

    # Spawn players + exits using smart spawn system
    spawn = spawn_match(grid, seed=7, exits_n=2)
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
    guard_turns_taken = 0
    winner = None         # "Rajakar" / "Guard" / "Draw" / None
    rajakar_visit_counts = {rajakar_pos: 1}
    scan_fx_cells = []
    scan_fx_until_ms = 0
    guard_prob_map = ai.init_guard_probability_map(grid, guard_pos)
    last_guard_pos = None
    guard_known_exits = []  # Fog-of-war: Guard discovers exits through vision
    guard_facing = (1, 0)  # Direction Guard is facing (dr, dc), starts facing down

    # What each player knows about the opponent on THEIR upcoming turn:
    clues = {
        "Rajakar": {"seen": False, "heard": False},
        "Guard":   {"seen": False, "heard": False},
    }

    # UI state (updated every frame)
    state = {
        "current": current,
        "turn": turn_count,
        "max_turns": s.MAX_TURNS,
        "seen": clues[current]["seen"],
        "heard": clues[current]["heard"],
        "guard_peak": max(guard_prob_map.values()) if guard_prob_map else 0.0,
    }

    def end_turn(action_name: str):
        nonlocal current, turn_count, winner
        nonlocal rajakar_pos, guard_pos, clues, guard_turns_taken, rajakar_visit_counts
        nonlocal scan_fx_cells, scan_fx_until_ms, guard_prob_map, guard_known_exits, guard_facing

        # 1) Check win conditions tied to the actor
        if current == "Rajakar":
            rajakar_visit_counts[rajakar_pos] = rajakar_visit_counts.get(rajakar_pos, 0) + 1
            # Immediate capture: adjacency to Guard ends the game instantly.
            if rules.manhattan(guard_pos, rajakar_pos) == 1:
                winner = "Guard"
            # Rajakar wins if standing on EXIT and used ESCAPE action.
            elif action_name == "ESCAPE" and grid.get(*rajakar_pos) == EXIT:
                winner = "Rajakar"
        else:
            guard_turns_taken += 1
            # Guard wins if adjacent to Rajakar after Guard action.
            if rules.manhattan(guard_pos, rajakar_pos) == 1:
                winner = "Guard"

        # 2) Increment turn count and draw rule
        turn_count += 1
        if winner is None and turn_count >= s.MAX_TURNS:
            winner = "Draw"

        # 3) If game ended, don't switch turns
        if winner is not None:
            return

        # 4) Discover exits through Guard's vision (fog-of-war)
        if current == "Guard":
            for exit_pos in exits:
                if exit_pos not in guard_known_exits:
                    # Guard discovers exit if it can see it (directional) or is standing on it
                    if guard_pos == exit_pos or rules.in_directional_sight(grid, guard_pos, exit_pos, guard_facing, s.SIGHT_RANGE):
                        guard_known_exits.append(exit_pos)

        # 5) Update clues for the NEXT player (the one who will move now)
        if current == "Rajakar":
            # Guard is next: what can Guard sense about Rajakar?
            seen = rules.in_directional_sight(grid, guard_pos, rajakar_pos, guard_facing, s.SIGHT_RANGE)
            next_guard_turn_number = guard_turns_taken + 1
            power_ready = (
                s.GUARD_POWER_COOLDOWN_TURNS > 0
                and next_guard_turn_number >= s.GUARD_POWER_COOLDOWN_TURNS
                and next_guard_turn_number % s.GUARD_POWER_COOLDOWN_TURNS == 0
            )
            if power_ready and rules.in_power_scan(guard_pos, rajakar_pos, s.GUARD_POWER_SCAN_RADIUS):
                seen = True
            if power_ready:
                scan_fx_cells = rules.power_scan_cells(grid, guard_pos, s.GUARD_POWER_SCAN_RADIUS)
                scan_fx_until_ms = pygame.time.get_ticks() + max(450, s.AI_TURN_DELAY_MS)
            heard = rules.heard_noise(guard_pos, rajakar_pos,
                                action_noise_radius(action_name))
            clues["Guard"] = {"seen": seen, "heard": heard}
            guard_prob_map = ai.update_guard_probability_map(
                grid,
                guard_prob_map,
                guard_pos,
                heard=heard,
                noise_radius=action_noise_radius(action_name),
                seen=seen,
                seen_pos=rajakar_pos if seen else None,
                power_used=power_ready,
                sight_range=s.SIGHT_RANGE,
                scan_radius=s.GUARD_POWER_SCAN_RADIUS,
            )
            current = "Guard"
        else:
            # Rajakar is next: what can Rajakar sense about Guard?
            # Rajakar can only see Guard in plain sight (4 directions) with line-of-sight
            seen = rules.in_straight_sight(grid, rajakar_pos, guard_pos, s.SIGHT_RANGE)
            heard = rules.heard_noise(rajakar_pos, guard_pos,
                                action_noise_radius(action_name))
            clues["Rajakar"] = {"seen": seen, "heard": heard}
            current = "Rajakar"

    running = True
    last_ai_tick = pygame.time.get_ticks()

    while running:
        dt = clock.tick(s.FPS) / 1000.0  # seconds since last frame

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # --- Restart (full respawn) ---
                if event.key == pygame.K_r:
                    spawn = spawn_match(grid, exits_n=2)  # random new match
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
                    guard_turns_taken = 0
                    winner = None
                    rajakar_visit_counts = {rajakar_pos: 1}
                    scan_fx_cells = []
                    scan_fx_until_ms = 0
                    guard_prob_map = ai.init_guard_probability_map(grid, guard_pos)
                    last_guard_pos = None
                    guard_known_exits = []
                    guard_facing = (1, 0)
                    clues = {"Rajakar": {"seen": False, "heard": False},
                             "Guard": {"seen": False, "heard": False}}
                    continue

                # If game ended, ignore other inputs
                if winner is not None:
                    continue

                # In AI autoplay mode, keep controls only for restart.
                if s.AUTO_PLAY_AI:
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
                            last_guard_pos = guard_pos
                            guard_pos = new_pos
                            guard_facing = (dr, dc)  # Update facing direction
                            acted = True
                            action_name = "MOVE"

                # --- Wait ---
                elif event.key == pygame.K_SPACE:
                    if current == "Rajakar":
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

        # --- AI turn ---
        if winner is None and s.AUTO_PLAY_AI:
            now = pygame.time.get_ticks()
            if now - last_ai_tick >= s.AI_TURN_DELAY_MS:
                if current == "Guard":
                    if clues["Guard"]["seen"]:
                        action_name, next_guard = ai.choose_guard_minimax_action(
                            grid,
                            guard_pos,
                            rajakar_pos,
                            turn_count,
                            s.MAX_TURNS,
                            s.SIGHT_RANGE,
                            guard_known_exits,
                            depth=3,
                        )
                    else:
                        action_name, next_guard = ai.choose_guard_probability_action(
                            grid,
                            guard_pos,
                            guard_prob_map,
                            last_guard_pos=last_guard_pos,
                        )
                    if action_name == "MOVE":
                        last_guard_pos = guard_pos
                        dr = next_guard[0] - guard_pos[0]
                        dc = next_guard[1] - guard_pos[1]
                        guard_facing = (dr, dc)  # Update facing direction
                        guard_pos = next_guard
                else:
                    raj_target = guard_pos if clues["Rajakar"]["seen"] else None
                    action_name, next_raj = ai.choose_rajakar_fuzzy_action(
                        grid,
                        rajakar_pos,
                        raj_target,
                        clues["Rajakar"],
                        rajakar_visit_counts,
                    )
                    if action_name == "MOVE":
                        rajakar_pos = next_raj

                end_turn(action_name)
                last_ai_tick = now

        # --- Update ---
        # Update UI state to match game state
        state["current"] = current
        state["turn"] = turn_count
        state["max_turns"] = s.MAX_TURNS
        state["seen"] = clues[current]["seen"]
        state["heard"] = clues[current]["heard"]
        state["guard_peak"] = max(guard_prob_map.values()) if guard_prob_map else 0.0
        state["guard_exits_known"] = len(guard_known_exits)
        state["exits_total"] = len(exits)

        # --- Draw ---
        active_scan_cells = scan_fx_cells if pygame.time.get_ticks() < scan_fx_until_ms else None
        draw_layout(screen, grid, font_small, rajakar_pos, guard_pos, guard_facing, active_scan_cells)
        draw_ui(screen, fonts, state)

        # Winner overlay
        if winner is not None:
            overlay = pygame.Surface((s.SCREEN_W, s.SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            msg = f"{winner} WINS!" if winner in (
                "Rajakar", "Guard") else "DRAW!"
            big = pygame.font.SysFont("Segoe UI", 44, bold=True).render(
                msg, True, (245, 245, 255))
            small = pygame.font.SysFont("Segoe UI", 18).render(
                "Press R to restart", True, (200, 200, 215))

            screen.blit(
                big, (s.BOARD_PX // 2 - big.get_width() // 2, s.SCREEN_H // 2 - 60))
            screen.blit(
                small, (s.BOARD_PX // 2 - small.get_width() // 2, s.SCREEN_H // 2 + 6))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
