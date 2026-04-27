# main.py
from __future__ import annotations

import os

import pygame
from typing import Optional
import settings as s
import core.rules as rules
import core.ai as ai
from core.grid import Grid, FLOOR, WALL, EXIT
from core.spawn import spawn_match
from render.menu import MainMenu
from render.ui import draw_ui


# Try to load a board/grid background image from common asset locations.
def _load_board_image() -> Optional[pygame.Surface]:
    # Search the project's assets directory recursively for grid.png so any
    # subfolder (e.g. assets/gameplay) will be found.
    base_dir = os.path.dirname(__file__)
    assets_dir = os.path.join(base_dir, "assets")
    if os.path.exists(assets_dir):
        for root, _dirs, files in os.walk(assets_dir):
            if "grid.png" in files:
                p = os.path.join(root, "grid.png")
                try:
                    img = pygame.image.load(p)
                    img = img.convert_alpha()
                    # Trim any symmetric border so the artwork maps cleanly to
                    # the 10x10 gameplay grid (e.g. 1254px -> 1250px).
                    crop_w = img.get_width() - (img.get_width() % s.GRID_SIZE)
                    crop_h = img.get_height() - (img.get_height() % s.GRID_SIZE)
                    if crop_w > 0 and crop_h > 0 and (crop_w != img.get_width() or crop_h != img.get_height()):
                        crop_x = (img.get_width() - crop_w) // 2
                        crop_y = (img.get_height() - crop_h) // 2
                        img = img.subsurface((crop_x, crop_y, crop_w, crop_h)).copy()
                    try:
                        print(f"[board] loaded grid image: {p} size={img.get_size()}")
                    except Exception:
                        print(f"[board] loaded grid image: {p}")
                    return img
                except pygame.error:
                    continue

    # Fallback to a few common relative locations (keeps backward-compatibility)
    candidates = [
        os.path.join(base_dir, "assets", "menu", "grid.png"),
        os.path.join(base_dir, "assets", "grid.png"),
        os.path.join(base_dir, "assets", "tiles", "grid.png"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                img = pygame.image.load(p)
                return img.convert_alpha()
            except pygame.error:
                continue
    return None


BOARD_BG_IMAGE = None


MENU = "MENU"
HOW_TO_PLAY = "HOW_TO_PLAY"
GAME = "GAME"
PAUSED = "PAUSED"
GAME_OVER = "GAME_OVER"


def setup_background_music():
    try:
        pygame.mixer.init()
    except pygame.error:
        return

    if not os.path.exists(s.BGM_FILE):
        return

    try:
        pygame.mixer.music.load(s.BGM_FILE)
        pygame.mixer.music.set_volume(s.BGM_VOLUME)
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass


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
        pygame.draw.line(screen, (10, 10, 12), (cx, cy),
                         (arrow_end_x, arrow_end_y), 3)
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


def draw_layout(screen, grid, font_exit, raj_pos, birsreshtha_pos, birsreshtha_facing, scan_cells=None):
    # Background
    screen.fill(s.BG)

    # Top bar
    top_bar_rect = pygame.Rect(0, 0, s.SCREEN_W, s.TOP_BAR_H)
    pygame.draw.rect(screen, s.TOP_BAR_BG, top_bar_rect)

    # Board area
    board_rect = pygame.Rect(0, s.TOP_BAR_H, s.BOARD_PX, s.BOARD_PX)
    # If a board background image is available, scale & blit it; otherwise fill.
    global BOARD_BG_IMAGE
    if BOARD_BG_IMAGE is None:
        BOARD_BG_IMAGE = _load_board_image()
    if BOARD_BG_IMAGE is not None:
        try:
            scaled = pygame.transform.smoothscale(BOARD_BG_IMAGE, (s.BOARD_PX, s.BOARD_PX))
            screen.blit(scaled, board_rect.topleft)
        except Exception:
            pygame.draw.rect(screen, s.BOARD_BG, board_rect)
    else:
        pygame.draw.rect(screen, s.BOARD_BG, board_rect)

    # UI panel
    panel_rect = pygame.Rect(s.BOARD_PX, 0, s.UI_PANEL_W, s.SCREEN_H)
    pygame.draw.rect(screen, s.PANEL_BG, panel_rect)

    # Divider line
    pygame.draw.line(screen, s.GRID_LINE, (s.BOARD_PX, 0),
                     (s.BOARD_PX, s.SCREEN_H), 2)

    # --- Draw tiles from grid ---
    use_board_image = BOARD_BG_IMAGE is not None
    for r in range(s.GRID_SIZE):
        for c in range(s.GRID_SIZE):
            x = c * s.TILE_SIZE
            y = s.TOP_BAR_H + r * s.TILE_SIZE
            rect = pygame.Rect(x, y, s.TILE_SIZE, s.TILE_SIZE)

            t = grid.get(r, c)

            if t == WALL:
                # The grid image already shows wall/obstacle tiles visually,
                # so keep the collision logic but don't paint an extra black
                # wall over the board.
                if not use_board_image:
                    pygame.draw.rect(screen, s.WALL_FILL, rect)
                    pygame.draw.rect(screen, s.WALL_EDGE, rect, width=2)

            else:
                # floor: if we have a background image, skip drawing the
                # checkerboard so the image remains visible. Otherwise draw
                # the checkerboard floor as before.
                if not use_board_image:
                    base = s.TILE_A if (r + c) % 2 == 0 else s.TILE_B
                    pygame.draw.rect(screen, base, rect)

                if t == EXIT:
                    # exit overlay
                    pygame.draw.rect(screen, s.EXIT_FILL,
                                     rect, border_radius=10)

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

    # BirSreshtha power scan overlay (transparent blue cells)
    if scan_cells:
        for r, c in scan_cells:
            x = c * s.TILE_SIZE
            y = s.TOP_BAR_H + r * s.TILE_SIZE
            overlay = pygame.Surface(
                (s.TILE_SIZE, s.TILE_SIZE), pygame.SRCALPHA)
            overlay.fill((70, 170, 255, 80))
            screen.blit(overlay, (x, y))

    # BirSreshtha vision cone (show what BirSreshtha can see)
    if birsreshtha_facing != (0, 0):
        gr, gc = birsreshtha_pos
        dr, dc = birsreshtha_facing
        for step in range(1, s.SIGHT_RANGE + 1):
            vr, vc = gr + dr * step, gc + dc * step
            if not grid.in_bounds(vr, vc):
                break
            if grid.get(vr, vc) == WALL:
                break
            x = vc * s.TILE_SIZE
            y = s.TOP_BAR_H + vr * s.TILE_SIZE
            overlay = pygame.Surface(
                (s.TILE_SIZE, s.TILE_SIZE), pygame.SRCALPHA)
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
            overlay = pygame.Surface(
                (s.TILE_SIZE, s.TILE_SIZE), pygame.SRCALPHA)
            # Light gold tint for Rajakar vision
            overlay.fill((240, 190, 70, 30))
            screen.blit(overlay, (x, y))

    # Grid lines: the board image already has its own grid, so avoid drawing
    # a second set of lines that can make the board look offset.
    if not use_board_image:
        for i in range(s.GRID_SIZE + 1):
            x = i * s.TILE_SIZE
            pygame.draw.line(screen, s.GRID_LINE, (x, s.TOP_BAR_H),
                             (x, s.TOP_BAR_H + s.BOARD_PX), 1)

            y = s.TOP_BAR_H + i * s.TILE_SIZE
            pygame.draw.line(screen, s.GRID_LINE, (0, y), (s.BOARD_PX, y), 1)

    # --- Draw players on top of tiles ---
    rr, rc = raj_pos
    gr, gc = birsreshtha_pos

    draw_player(screen, rr, rc, s.RAJAKAR_FILL, s.RAJAKAR_EDGE, "R", font_exit)
    draw_player(screen, gr, gc, s.BIRSRESHTHA_FILL,
                s.BIRSRESHTHA_EDGE, "B", font_exit, facing=birsreshtha_facing)


def draw_game_button(screen, rect, text, font, primary=False):
    mouse_pos = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mouse_pos)
    if primary:
        fill = (68, 78, 35) if not hovered else (92, 106, 48)
        border = (181, 159, 75) if not hovered else (236, 213, 116)
        text_color = (241, 235, 211)
    else:
        fill = (21, 20, 17) if not hovered else (38, 34, 27)
        border = (101, 82, 56) if not hovered else (178, 145, 82)
        text_color = (211, 195, 163)

    shadow = pygame.Surface((rect.w + 12, rect.h + 12), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 150), shadow.get_rect(), border_radius=7)
    screen.blit(shadow, (rect.x + 4, rect.y + 6))
    pygame.draw.rect(screen, fill, rect, border_radius=7)
    pygame.draw.rect(screen, border, rect, width=2, border_radius=7)

    label = font.render(text, True, text_color)
    screen.blit(label, label.get_rect(center=rect.center))


def draw_pause_button(screen, rect, font):
    draw_game_button(screen, rect, "Pause", font, primary=False)


def draw_center_overlay(screen, title, buttons, font_title, font_body):
    overlay = pygame.Surface((s.SCREEN_W, s.SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(0, 0, 360, 300)
    panel.center = (s.BOARD_PX // 2, s.SCREEN_H // 2)
    pygame.draw.rect(screen, (24, 24, 31), panel, border_radius=10)
    pygame.draw.rect(screen, (92, 82, 58), panel, width=2, border_radius=10)

    title_img = font_title.render(title, True, (245, 245, 255))
    screen.blit(title_img, title_img.get_rect(center=(panel.centerx, panel.y + 54)))

    for text, rect, primary in buttons:
        draw_game_button(screen, rect, text, font_body, primary=primary)


def main():
    pygame.init()
    setup_background_music()
    pygame.display.set_caption(s.TITLE)

    screen = pygame.display.set_mode((s.SCREEN_W, s.SCREEN_H))
    clock = pygame.time.Clock()

    # Create fonts
    font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
    font_body = pygame.font.SysFont("Segoe UI", 18)
    font_small = pygame.font.SysFont("Segoe UI", 14)
    fonts = (font_title, font_body, font_small)
    font_button = pygame.font.SysFont("Segoe UI", 20, bold=True)
    font_overlay_title = pygame.font.SysFont("Segoe UI", 42, bold=True)

    menu = MainMenu(s.SCREEN_W, s.SCREEN_H)
    screen_state = MENU
    simulation_speed = menu.speed_multiplier
    pause_button_rect = pygame.Rect(s.SCREEN_W - 128, 12, 104, 36)
    overlay_button_w = 220
    overlay_button_h = 48
    overlay_button_x = s.BOARD_PX // 2 - overlay_button_w // 2
    overlay_start_y = s.SCREEN_H // 2 - 52
    pause_menu_buttons = {
        "resume": pygame.Rect(overlay_button_x, overlay_start_y, overlay_button_w, overlay_button_h),
        "restart": pygame.Rect(overlay_button_x, overlay_start_y + 64, overlay_button_w, overlay_button_h),
        "menu": pygame.Rect(overlay_button_x, overlay_start_y + 128, overlay_button_w, overlay_button_h),
    }
    game_over_buttons = {
        "restart": pygame.Rect(overlay_button_x, overlay_start_y + 32, overlay_button_w, overlay_button_h),
        "menu": pygame.Rect(overlay_button_x, overlay_start_y + 96, overlay_button_w, overlay_button_h),
    }

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

    # Game state variables
    grid = Grid.from_ascii(ascii_map)
    rajakar_pos = (0, 0)
    birsreshtha_pos = (0, 0)
    exits = []
    current = "Rajakar"   # Rajakar starts
    turn_count = 0
    birsreshtha_turns_taken = 0
    winner = None         # "Rajakar" / "BirSreshtha" / "Draw" / None
    rajakar_visit_counts = {}
    scan_fx_cells = []
    scan_fx_until_ms = 0
    birsreshtha_prob_map = {}
    last_birsreshtha_pos = None
    birsreshtha_known_exits = []  # Fog-of-war: BirSreshtha discovers exits through vision
    birsreshtha_facing = (1, 0)

    # What each player knows about the opponent on THEIR upcoming turn:
    clues = {
        "Rajakar": {"seen": False, "heard": False},
        "BirSreshtha": {"seen": False, "heard": False},
    }

    # UI state (updated every frame)
    state = {
        "current": current,
        "turn": turn_count,
        "max_turns": s.MAX_TURNS,
        "seen": clues[current]["seen"],
        "heard": clues[current]["heard"],
        "birsreshtha_peak": 0.0,
    }

    def actual_ai_delay_ms() -> int:
        return max(60, int(s.AI_TURN_DELAY_MS / simulation_speed))

    def reset_game(seed=None):
        nonlocal grid, rajakar_pos, birsreshtha_pos, exits
        nonlocal current, turn_count, birsreshtha_turns_taken, winner
        nonlocal rajakar_visit_counts, scan_fx_cells, scan_fx_until_ms
        nonlocal birsreshtha_prob_map, last_birsreshtha_pos
        nonlocal birsreshtha_known_exits, birsreshtha_facing, clues

        grid = Grid.from_ascii(ascii_map)

        # Spawn players + exits using smart spawn system.
        spawn = spawn_match(grid, seed=seed, exits_n=2)
        rajakar_pos = spawn["rajakar"]
        birsreshtha_pos = spawn["birsreshtha"]
        exits = spawn["exits"]

        # Clear any old exits and set the new ones.
        for (r, c) in grid.all_cells_of_type(EXIT):
            grid.set(r, c, FLOOR)
        for (r, c) in exits:
            grid.set(r, c, EXIT)

        current = "Rajakar"
        turn_count = 0
        birsreshtha_turns_taken = 0
        winner = None
        rajakar_visit_counts = {rajakar_pos: 1}
        scan_fx_cells = []
        scan_fx_until_ms = 0
        birsreshtha_prob_map = ai.init_birsreshtha_probability_map(
            grid, birsreshtha_pos)
        last_birsreshtha_pos = None
        birsreshtha_known_exits = []
        birsreshtha_facing = (1, 0)
        clues = {"Rajakar": {"seen": False, "heard": False},
                 "BirSreshtha": {"seen": False, "heard": False}}

        state["current"] = current
        state["turn"] = turn_count
        state["max_turns"] = s.MAX_TURNS
        state["seen"] = clues[current]["seen"]
        state["heard"] = clues[current]["heard"]
        state["birsreshtha_peak"] = max(
            birsreshtha_prob_map.values()) if birsreshtha_prob_map else 0.0
        state["birsreshtha_exits_known"] = len(birsreshtha_known_exits)
        state["exits_total"] = len(exits)

    reset_game(seed=7)

    def restart_match():
        nonlocal screen_state, last_ai_tick
        reset_game()
        screen_state = GAME
        last_ai_tick = pygame.time.get_ticks()

    def end_turn(action_name: str):
        nonlocal current, turn_count, winner, screen_state
        nonlocal rajakar_pos, birsreshtha_pos, clues, birsreshtha_turns_taken, rajakar_visit_counts
        nonlocal scan_fx_cells, scan_fx_until_ms, birsreshtha_prob_map, birsreshtha_known_exits, birsreshtha_facing

        # 1) Check win conditions tied to the actor
        if current == "Rajakar":
            rajakar_visit_counts[rajakar_pos] = rajakar_visit_counts.get(
                rajakar_pos, 0) + 1
            # Immediate capture: adjacency to BirSreshtha ends the game instantly.
            if rules.manhattan(birsreshtha_pos, rajakar_pos) == 1:
                winner = "BirSreshtha"
            # Rajakar wins if standing on EXIT and used ESCAPE action.
            elif action_name == "ESCAPE" and grid.get(*rajakar_pos) == EXIT:
                winner = "Rajakar"
        else:
            birsreshtha_turns_taken += 1
            # BirSreshtha wins if adjacent to Rajakar after BirSreshtha action.
            if rules.manhattan(birsreshtha_pos, rajakar_pos) == 1:
                winner = "BirSreshtha"

        # 2) Increment turn count and draw rule
        turn_count += 1
        if winner is None and turn_count >= s.MAX_TURNS:
            winner = "Draw"

        # 3) If game ended, don't switch turns
        if winner is not None:
            screen_state = GAME_OVER
            return

        # 4) Discover exits through BirSreshtha's vision (fog-of-war)
        if current == "BirSreshtha":
            for exit_pos in exits:
                if exit_pos not in birsreshtha_known_exits:
                    # BirSreshtha discovers exit if it can see it (directional) or is standing on it
                    if birsreshtha_pos == exit_pos or rules.in_directional_sight(grid, birsreshtha_pos, exit_pos, birsreshtha_facing, s.SIGHT_RANGE):
                        birsreshtha_known_exits.append(exit_pos)

        # 5) Update clues for the NEXT player (the one who will move now)
        if current == "Rajakar":
            # BirSreshtha is next: what can BirSreshtha sense about Rajakar?
            seen = rules.in_directional_sight(
                grid, birsreshtha_pos, rajakar_pos, birsreshtha_facing, s.SIGHT_RANGE)
            next_birsreshtha_turn_number = birsreshtha_turns_taken + 1
            power_ready = (
                s.BIRSRESHTHA_POWER_COOLDOWN_TURNS > 0
                and next_birsreshtha_turn_number >= s.BIRSRESHTHA_POWER_COOLDOWN_TURNS
                and next_birsreshtha_turn_number % s.BIRSRESHTHA_POWER_COOLDOWN_TURNS == 0
            )
            if power_ready and rules.in_power_scan(birsreshtha_pos, rajakar_pos, s.BIRSRESHTHA_POWER_SCAN_RADIUS):
                seen = True
            if power_ready:
                scan_fx_cells = rules.power_scan_cells(
                    grid, birsreshtha_pos, s.BIRSRESHTHA_POWER_SCAN_RADIUS)
                scan_fx_until_ms = pygame.time.get_ticks() + max(450, actual_ai_delay_ms())
            heard = rules.heard_noise(birsreshtha_pos, rajakar_pos,
                                      action_noise_radius(action_name))
            clues["BirSreshtha"] = {"seen": seen, "heard": heard}
            birsreshtha_prob_map = ai.update_birsreshtha_probability_map(
                grid,
                birsreshtha_prob_map,
                birsreshtha_pos,
                heard=heard,
                noise_radius=action_noise_radius(action_name),
                seen=seen,
                seen_pos=rajakar_pos if seen else None,
                power_used=power_ready,
                sight_range=s.SIGHT_RANGE,
                scan_radius=s.BIRSRESHTHA_POWER_SCAN_RADIUS,
            )
            current = "BirSreshtha"
        else:
            # Rajakar is next: what can Rajakar sense about BirSreshtha?
            # Rajakar can only see BirSreshtha in plain sight (4 directions) with line-of-sight
            seen = rules.in_straight_sight(
                grid, rajakar_pos, birsreshtha_pos, s.SIGHT_RANGE)
            heard = rules.heard_noise(rajakar_pos, birsreshtha_pos,
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

            if screen_state == MENU:
                simulation_speed = menu.speed_multiplier
                action = menu.handle_menu_event(event)
                if action == "start":
                    simulation_speed = menu.speed_multiplier
                    restart_match()
                elif action == "how":
                    screen_state = HOW_TO_PLAY
                elif action == "exit":
                    running = False
                continue

            if screen_state == HOW_TO_PLAY:
                action = menu.handle_how_to_play_event(event)
                if action == "back":
                    screen_state = MENU
                continue

            if screen_state == GAME_OVER:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    restart_match()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if game_over_buttons["restart"].collidepoint(event.pos):
                        restart_match()
                    elif game_over_buttons["menu"].collidepoint(event.pos):
                        screen_state = MENU
                continue

            if screen_state == PAUSED:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        screen_state = GAME
                        last_ai_tick = pygame.time.get_ticks()
                    elif event.key == pygame.K_r:
                        restart_match()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if pause_menu_buttons["resume"].collidepoint(event.pos):
                        screen_state = GAME
                        last_ai_tick = pygame.time.get_ticks()
                    elif pause_menu_buttons["restart"].collidepoint(event.pos):
                        restart_match()
                    elif pause_menu_buttons["menu"].collidepoint(event.pos):
                        screen_state = MENU
                continue

            if screen_state != GAME:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pause_button_rect.collidepoint(event.pos):
                    screen_state = PAUSED
                    continue

            if event.type == pygame.KEYDOWN:
                # --- Restart (full respawn) ---
                if event.key == pygame.K_r:
                    restart_match()
                    continue

                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    screen_state = PAUSED
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
                        new_pos, ok = try_move(grid, birsreshtha_pos, dr, dc)
                        if ok:
                            last_birsreshtha_pos = birsreshtha_pos
                            birsreshtha_pos = new_pos
                            # Update facing direction
                            birsreshtha_facing = (dr, dc)
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

        if not running:
            break

        if screen_state == MENU:
            simulation_speed = menu.speed_multiplier
            menu.draw_menu(screen)
            pygame.display.flip()
            continue

        if screen_state == HOW_TO_PLAY:
            menu.draw_how_to_play(screen)
            pygame.display.flip()
            continue

        # --- AI turn ---
        if screen_state == GAME and winner is None and s.AUTO_PLAY_AI:
            now = pygame.time.get_ticks()
            if now - last_ai_tick >= actual_ai_delay_ms():
                if current == "BirSreshtha":
                    if clues["BirSreshtha"]["seen"]:
                        action_name, next_birsreshtha = ai.choose_birsreshtha_minimax_action(
                            grid,
                            birsreshtha_pos,
                            rajakar_pos,
                            turn_count,
                            s.MAX_TURNS,
                            s.SIGHT_RANGE,
                            birsreshtha_known_exits,
                            depth=s.BIRSRESHTHA_MINIMAX_DEPTH,
                        )
                    else:
                        action_name, next_birsreshtha = ai.choose_birsreshtha_probability_action(
                            grid,
                            birsreshtha_pos,
                            birsreshtha_prob_map,
                            last_birsreshtha_pos=last_birsreshtha_pos,
                        )
                    if action_name == "MOVE":
                        last_birsreshtha_pos = birsreshtha_pos
                        dr = next_birsreshtha[0] - birsreshtha_pos[0]
                        dc = next_birsreshtha[1] - birsreshtha_pos[1]
                        # Update facing direction
                        birsreshtha_facing = (dr, dc)
                        birsreshtha_pos = next_birsreshtha
                else:
                    raj_target = birsreshtha_pos if clues["Rajakar"]["seen"] else None
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
        state["birsreshtha_peak"] = max(
            birsreshtha_prob_map.values()) if birsreshtha_prob_map else 0.0
        state["birsreshtha_exits_known"] = len(birsreshtha_known_exits)
        state["exits_total"] = len(exits)

        # --- Draw ---
        active_scan_cells = scan_fx_cells if pygame.time.get_ticks() < scan_fx_until_ms else None
        draw_layout(screen, grid, font_small, rajakar_pos,
                    birsreshtha_pos, birsreshtha_facing, active_scan_cells)
        draw_ui(screen, fonts, state)

        if screen_state == GAME and winner is None:
            draw_pause_button(screen, pause_button_rect, font_button)

        if screen_state == PAUSED:
            draw_center_overlay(
                screen,
                "Paused",
                [
                    ("Resume", pause_menu_buttons["resume"], True),
                    ("Restart", pause_menu_buttons["restart"], False),
                    ("Main Menu", pause_menu_buttons["menu"], False),
                ],
                font_overlay_title,
                font_button,
            )

        if winner is not None:
            msg = f"{winner} WINS!" if winner in (
                "Rajakar", "BirSreshtha") else "DRAW!"
            draw_center_overlay(
                screen,
                msg,
                [
                    ("Restart", game_over_buttons["restart"], True),
                    ("Main Menu", game_over_buttons["menu"], False),
                ],
                font_overlay_title,
                font_button,
            )

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
