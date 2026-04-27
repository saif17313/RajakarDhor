import os
from typing import Optional

import pygame
from settings import (
    SCREEN_W, SCREEN_H, BOARD_PX, UI_PANEL_W, TOP_BAR_H,
    TEXT, MUTED, CARD_BG, CARD_EDGE, GOOD, BAD
)

SIDEBAR_ASSET_SIZE = (795, 1979)
SIDEBAR_IMAGE: Optional[pygame.Surface] = None
SIDEBAR_MISSING = False


def _load_sidebar_image() -> Optional[pygame.Surface]:
    global SIDEBAR_IMAGE, SIDEBAR_MISSING
    if SIDEBAR_IMAGE is not None:
        return SIDEBAR_IMAGE
    if SIDEBAR_MISSING:
        return None

    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "assets", "gameplay", "side_bar.png")
    if not os.path.exists(path):
        SIDEBAR_MISSING = True
        return None

    try:
        SIDEBAR_IMAGE = pygame.image.load(path).convert_alpha()
        return SIDEBAR_IMAGE
    except pygame.error:
        SIDEBAR_MISSING = True
        return None


def _draw_card(surface, rect, radius=14):
    """Card with subtle shadow + border (cheap but looks premium)."""
    # Shadow (alpha)
    shadow = pygame.Surface((rect.w + 10, rect.h + 10), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80),
                     shadow.get_rect(), border_radius=radius)
    surface.blit(shadow, (rect.x + 5, rect.y + 6))

    # Card body
    pygame.draw.rect(surface, CARD_BG, rect, border_radius=radius)
    pygame.draw.rect(surface, CARD_EDGE, rect, width=2, border_radius=radius)


def _draw_text(surface, font, text, x, y, color=TEXT):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))
    return img.get_rect(topleft=(x, y))


def _draw_text_shadow(surface, font, text, x, y, color=TEXT):
    shadow = font.render(text, True, (0, 0, 0))
    img = font.render(text, True, color)
    surface.blit(shadow, (x + 2, y + 2))
    surface.blit(img, (x, y))
    return img.get_rect(topleft=(x, y))


def _draw_pill(surface, font_small, label, value, x, y, ok=True):
    """Small status pill like: Eye: Seen / Not Seen"""
    pad_x, pad_y = 10, 6
    bg = GOOD if ok else BAD

    label_surf = font_small.render(label, True, (15, 15, 18))
    value_surf = font_small.render(value, True, (15, 15, 18))

    w = label_surf.get_width() + value_surf.get_width() + pad_x * 3
    h = max(label_surf.get_height(), value_surf.get_height()) + pad_y * 2

    pill_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, bg, pill_rect, border_radius=999)

    surface.blit(label_surf, (x + pad_x, y + pad_y))
    surface.blit(value_surf, (x + pad_x * 2 +
                 label_surf.get_width(), y + pad_y))


def _draw_top_bar_text(screen, font_title, font_body, state):
    _draw_text(screen, font_title, "RajakarDhor", 18, 16, TEXT)

    right_text = f"Turn: {state['turn']}/{state['max_turns']}  |  Now: {state['current']}"
    img = font_body.render(right_text, True, MUTED)
    screen.blit(img, (BOARD_PX - img.get_width() - 16, 20))


def _sidebar_pos(panel_x, x, y):
    src_w, src_h = SIDEBAR_ASSET_SIZE
    return (
        panel_x + int(x / src_w * UI_PANEL_W),
        int(y / src_h * SCREEN_H),
    )


def _draw_sidebar_ui(screen, fonts, state, sidebar):
    font_title, font_body, font_small = fonts
    panel_rect = pygame.Rect(BOARD_PX, 0, UI_PANEL_W, SCREEN_H)
    fitted = pygame.transform.smoothscale(sidebar, panel_rect.size)
    screen.blit(fitted, panel_rect.topleft)

    ink = (232, 211, 159)
    muted = (186, 158, 105)
    strong = (246, 231, 184)
    pill_text = (238, 226, 190)

    peak = int(round(float(state.get("birsreshtha_peak", 0.0)) * 100))
    exits_known = state.get("birsreshtha_exits_known", 0)
    exits_total = state.get("exits_total", 0)
    seen = state["seen"]
    heard = state["heard"]
    is_rajakar_turn = state["current"] == "Rajakar"

    x, y = _sidebar_pos(BOARD_PX, 72, 225)
    _draw_text_shadow(screen, font_body, f"Current: {state['current']}", x, y, ink)
    x, y = _sidebar_pos(BOARD_PX, 72, 306)
    _draw_text_shadow(
        screen, font_body, f"Turn Count: {state['turn']} / {state['max_turns']}", x, y, ink)
    x, y = _sidebar_pos(BOARD_PX, 72, 385)
    _draw_text_shadow(
        screen, font_small, f"Confidence: {peak}%   Exits: {exits_known}/{exits_total}", x, y, muted)

    x, y = _sidebar_pos(BOARD_PX, 72, 918)
    signal_title = "Contact this turn:" if is_rajakar_turn else "Signals this turn:"
    _draw_text_shadow(screen, font_body, signal_title, x, y, ink)

    vision_label = "CONTACT" if is_rajakar_turn else "VISION"
    vision_value = "ADJACENT" if (is_rajakar_turn and seen) else (
        "NONE" if is_rajakar_turn else ("LOCKED" if seen else "NO LOCK"))
    x, y = _sidebar_pos(BOARD_PX, 170, 986)
    _draw_text_shadow(screen, font_small,
                      f"{vision_label}: {vision_value}", x, y, pill_text)

    x, y = _sidebar_pos(BOARD_PX, 170, 1114)
    _draw_text_shadow(screen, font_small,
                      f"SOUND: {'HEARD' if heard else 'SILENT'}", x, y, pill_text)

    x, y = _sidebar_pos(BOARD_PX, 72, 1460)
    if state["current"] == "Rajakar":
        _draw_text_shadow(screen, font_body, "Reach EXIT and Escape.", x, y, strong)
        x, y = _sidebar_pos(BOARD_PX, 72, 1534)
        _draw_text_shadow(screen, font_small, "Escape takes 1 full turn on EXIT.", x, y, muted)
    else:
        _draw_text_shadow(screen, font_body, "Get adjacent to capture.", x, y, strong)
        x, y = _sidebar_pos(BOARD_PX, 72, 1534)
        _draw_text_shadow(screen, font_small, "Capture after BirSreshtha move.", x, y, muted)


def _draw_fallback_ui(screen, fonts, state):
    font_title, font_body, font_small = fonts

    # --- Right panel content ---
    panel_x = BOARD_PX
    y = 90  # start a bit below top bar inside panel

    # Card 1: Turn info
    card1 = pygame.Rect(panel_x + 18, y, UI_PANEL_W - 36, 140)
    _draw_card(screen, card1)
    _draw_text(screen, font_title, "Round Info", card1.x + 16, card1.y + 14)

    _draw_text(screen, font_body,
               f"Current: {state['current']}", card1.x + 16, card1.y + 58)
    _draw_text(screen, font_body,
               f"Turn Count: {state['turn']} / {state['max_turns']}", card1.x + 16, card1.y + 88)
    peak = int(round(float(state.get("birsreshtha_peak", 0.0)) * 100))
    exits_known = state.get("birsreshtha_exits_known", 0)
    exits_total = state.get("exits_total", 0)
    _draw_text(screen, font_small,
               f"BirSreshtha Confidence: {peak}% | Exits: {exits_known}/{exits_total}", card1.x + 16, card1.y + 114, MUTED)

    y += 160

    # Card 2: Detection / Clues
    card2 = pygame.Rect(panel_x + 18, y, UI_PANEL_W - 36, 190)
    _draw_card(screen, card2)
    _draw_text(screen, font_title, "Detection", card2.x + 16, card2.y + 14)

    seen = state["seen"]
    heard = state["heard"]
    is_rajakar_turn = state["current"] == "Rajakar"

    signal_title = "Contact this turn:" if is_rajakar_turn else "Signals this turn:"
    _draw_text(screen, font_body, signal_title,
               card2.x + 16, card2.y + 58, MUTED)

    _draw_pill(
        screen, font_small,
        "CONTACT:" if is_rajakar_turn else "VISION:",
        "ADJACENT" if (is_rajakar_turn and seen) else (
            "NONE" if is_rajakar_turn else ("LOCKED" if seen else "NO LOCK")),
        card2.x + 16, card2.y + 92,
        ok=seen
    )
    _draw_pill(
        screen, font_small,
        "SOUND:", "HEARD" if heard else "SILENT",
        card2.x + 16, card2.y + 128,
        ok=heard
    )

    if is_rajakar_turn:
        _draw_text(screen, font_small, "Rajakar gets exact BirSreshtha position only when adjacent.",
                   card2.x + 16, card2.y + 164, MUTED)
    else:
        _draw_text(screen, font_small, "BirSreshtha captures if adjacent after BirSreshtha move.",
                   card2.x + 16, card2.y + 164, MUTED)

    y += 210

    # Card 3: Objective (simple)
    card3 = pygame.Rect(panel_x + 18, y, UI_PANEL_W - 36, 150)
    _draw_card(screen, card3)
    _draw_text(screen, font_title, "Objective", card3.x + 16, card3.y + 14)

    if state["current"] == "Rajakar":
        _draw_text(screen, font_body, "Reach EXIT and Escape.",
                   card3.x + 16, card3.y + 58)
        _draw_text(screen, font_small, "Escape takes 1 full turn on EXIT.",
                   card3.x + 16, card3.y + 92, MUTED)
    else:
        _draw_text(screen, font_body, "Get adjacent to capture.",
                   card3.x + 16, card3.y + 58)
        _draw_text(screen, font_small, "Capture check happens after BirSreshtha move.",
                   card3.x + 16, card3.y + 92, MUTED)


def draw_ui(screen, fonts, state):
    """
    state example:
    {
            "current": "Rajakar" or "BirSreshtha",
      "turn": 12,
      "max_turns": 60,
      "seen": False,
      "heard": True
    }
    """
    font_title, font_body, font_small = fonts

    # --- Top bar text ---
    _draw_top_bar_text(screen, font_title, font_body, state)

    sidebar = _load_sidebar_image()
    if sidebar is not None:
        _draw_sidebar_ui(screen, fonts, state, sidebar)
    else:
        _draw_fallback_ui(screen, fonts, state)
