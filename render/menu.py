from __future__ import annotations

import os
from typing import Dict, Optional, Tuple

import pygame


Color = Tuple[int, int, int]


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def load_image(path: str, alpha: bool = True) -> Optional[pygame.Surface]:
    """Safe PNG loader. Missing or invalid files use code fallbacks."""
    if not os.path.exists(path):
        return None
    try:
        image = pygame.image.load(path)
        return image.convert_alpha() if alpha else image.convert()
    except pygame.error:
        return None


def load_first_image(paths: Tuple[str, ...], alpha: bool = True) -> Optional[pygame.Surface]:
    for path in paths:
        image = load_image(path, alpha)
        if image is not None:
            return image
    return None


def load_font(path: str, size: int, fallback_name: str = "Segoe UI", bold: bool = False) -> pygame.font.Font:
    if os.path.exists(path):
        try:
            return pygame.font.Font(path, size)
        except pygame.error:
            pass
    return pygame.font.SysFont(fallback_name, size, bold=bold)


def draw_text_with_shadow(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    pos: Tuple[int, int],
    color: Color,
    shadow: Color = (0, 0, 0),
    center: bool = False,
    offset: Tuple[int, int] = (3, 4),
) -> pygame.Rect:
    shadow_img = font.render(text, True, shadow)
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(shadow_img, rect.move(offset))
    surface.blit(img, rect)
    return rect


def scale_cover(image: pygame.Surface, size: Tuple[int, int]) -> pygame.Surface:
    iw, ih = image.get_size()
    tw, th = size
    scale = max(tw / iw, th / ih)
    scaled = pygame.transform.smoothscale(image, (int(iw * scale), int(ih * scale)))
    crop = pygame.Rect(0, 0, tw, th)
    crop.center = scaled.get_rect().center
    return scaled.subsurface(crop).copy()


def blit_fit(surface: pygame.Surface, image: pygame.Surface, rect: pygame.Rect) -> pygame.Rect:
    iw, ih = image.get_size()
    scale = min(rect.w / iw, rect.h / ih)
    size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
    scaled = pygame.transform.smoothscale(image, size)
    out_rect = scaled.get_rect(center=rect.center)
    surface.blit(scaled, out_rect)
    return out_rect


def tint_image(image: pygame.Surface, color: Color) -> pygame.Surface:
    tinted = image.copy()
    mask = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    mask.fill((*color, 255))
    tinted.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


class Button:
    def __init__(self, rect: pygame.Rect, text: str, icon: Optional[pygame.Surface], primary: bool = False):
        self.rect = rect
        self.text = text
        self.icon = icon
        self.primary = primary
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hovered = self.rect.collidepoint(event.pos)
            return self.hovered
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if self.primary:
            fill = (68, 78, 35) if not self.hovered else (92, 106, 48)
            border = (181, 159, 75) if not self.hovered else (236, 213, 116)
            text_color = (241, 235, 211)
        else:
            fill = (21, 20, 17) if not self.hovered else (38, 34, 27)
            border = (101, 82, 56) if not self.hovered else (178, 145, 82)
            text_color = (211, 195, 163)

        shadow = pygame.Surface((self.rect.w + 14, self.rect.h + 14), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 155), shadow.get_rect(), border_radius=7)
        surface.blit(shadow, (self.rect.x + 5, self.rect.y + 7))

        pygame.draw.rect(surface, fill, self.rect, border_radius=7)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=7)
        pygame.draw.rect(surface, (255, 246, 198, 16), self.rect.inflate(-6, -6), width=1, border_radius=5)

        if self.hovered:
            glow = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (235, 204, 105, 42), glow.get_rect(), border_radius=7)
            surface.blit(glow, self.rect.topleft)

        if self.icon is not None:
            icon_size = int(self.rect.h * (0.58 if self.primary else 0.52))
            icon = pygame.transform.smoothscale(self.icon, (icon_size, icon_size))
            icon = tint_image(icon, text_color)
            icon_rect = icon.get_rect(center=(self.rect.x + int(self.rect.w * 0.22), self.rect.centery))
            surface.blit(icon, icon_rect)
        else:
            self._draw_fallback_icon(surface, text_color)

        label = font.render(self.text, True, text_color)
        label_rect = label.get_rect(center=(self.rect.centerx + int(self.rect.w * 0.07), self.rect.centery))
        surface.blit(label, label_rect)

    def _draw_fallback_icon(self, surface: pygame.Surface, color: Color) -> None:
        x = self.rect.x + int(self.rect.w * 0.22)
        y = self.rect.centery
        if self.text == "START":
            pygame.draw.circle(surface, color, (x, y), 17, width=3)
            pygame.draw.circle(surface, color, (x, y), 5)
        elif self.text == "HOW TO PLAY":
            pygame.draw.rect(surface, color, (x - 18, y - 13, 15, 26), width=3)
            pygame.draw.rect(surface, color, (x + 3, y - 13, 15, 26), width=3)
        else:
            pygame.draw.rect(surface, color, (x - 15, y - 18, 24, 36), width=3)
            pygame.draw.polygon(surface, color, [(x + 21, y), (x + 8, y - 9), (x + 8, y + 9)])


class Slider:
    def __init__(self, track_rect: pygame.Rect, clock_icon: Optional[pygame.Surface], value: float = 0.5):
        self.rect = track_rect
        self.clock_icon = clock_icon
        self.value = clamp(value, 0.0, 1.0)
        self.dragging = False

    @property
    def speed_multiplier(self) -> float:
        if self.value <= 0.5:
            return 0.5 + self.value
        return 1.0 + (self.value - 0.5) * 4.0

    def speed_label(self) -> str:
        speed = self.speed_multiplier
        if speed < 0.85:
            return "Slow"
        if speed < 1.35:
            return "Normal"
        if speed < 2.25:
            return "Fast"
        return "Very Fast"

    def _set_from_mouse(self, x: int) -> None:
        self.value = clamp((x - self.rect.x) / max(1, self.rect.w), 0.0, 1.0)

    def handle_event(self, event: pygame.event.Event) -> bool:
        knob_x = self.rect.x + int(self.rect.w * self.value)
        knob = pygame.Rect(0, 0, 42, 42)
        knob.center = (knob_x, self.rect.centery)
        hit = self.rect.inflate(34, 52)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if knob.collidepoint(event.pos) or hit.collidepoint(event.pos):
                self.dragging = True
                self._set_from_mouse(event.pos[0])
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_dragging = self.dragging
            self.dragging = False
            return was_dragging
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_mouse(event.pos[0])
            return True
        return False

    def draw(self, surface: pygame.Surface, fonts: Dict[str, pygame.font.Font]) -> None:
        panel = pygame.Rect(self.rect.x - 14, self.rect.y - 50, self.rect.w + 28, 88)

        box = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(box, (17, 16, 13, 196), box.get_rect(), border_radius=7)
        pygame.draw.rect(box, (125, 101, 66, 210), box.get_rect(), width=2, border_radius=7)
        surface.blit(box, panel.topleft)

        label_y = panel.y + 12
        label_color = (211, 184, 129)
        if self.clock_icon is not None:
            icon = pygame.transform.smoothscale(self.clock_icon, (28, 28))
            icon = tint_image(icon, label_color)
            surface.blit(icon, icon.get_rect(center=(panel.x + 18, label_y + 12)))
        else:
            pygame.draw.circle(surface, label_color, (panel.x + 18, label_y + 12), 12, width=3)
        draw_text_with_shadow(surface, fonts["small_bold"], "SIMULATION SPEED", (panel.x + 46, label_y), label_color, (0, 0, 0), offset=(2, 2))

        pygame.draw.rect(surface, (13, 14, 11), self.rect, border_radius=999)
        pygame.draw.rect(surface, (105, 91, 60), self.rect, width=2, border_radius=999)

        fill_rect = self.rect.copy()
        fill_rect.w = max(8, int(self.rect.w * self.value))
        pygame.draw.rect(surface, (105, 127, 57), fill_rect, border_radius=999)

        knob_x = self.rect.x + int(self.rect.w * self.value)
        pygame.draw.circle(surface, (25, 29, 18), (knob_x, self.rect.centery), 18)
        pygame.draw.circle(surface, (234, 226, 195), (knob_x, self.rect.centery), 18, width=3)

        text_y = self.rect.bottom + 18
        muted = (202, 178, 132)
        draw_text_with_shadow(surface, fonts["small"], "Slow", (panel.x + 14, text_y), muted, offset=(1, 1))
        current = f"Current: {self.speed_label()} ({self.speed_multiplier:.1f}x)"
        draw_text_with_shadow(surface, fonts["small"], current, (panel.centerx, text_y), (223, 207, 169), center=True, offset=(1, 1))
        fast = fonts["small"].render("Fast", True, muted)
        shadow = fonts["small"].render("Fast", True, (0, 0, 0))
        pos = (panel.right - fast.get_width() - 14, text_y)
        surface.blit(shadow, (pos[0] + 1, pos[1] + 1))
        surface.blit(fast, pos)


class MainMenu:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.assets = self._load_assets()
        self.fonts = self._build_fonts()
        self.buttons = self._build_buttons()
        self.slider = Slider(self._slider_rect(), self.assets["clock"], value=0.5)
        self.back_button = Button(pygame.Rect(48, height - 94, 180, 56), "BACK", None, False)

    @property
    def speed_multiplier(self) -> float:
        return self.slider.speed_multiplier

    def _load_assets(self) -> Dict[str, Optional[pygame.Surface]]:
        return {
            "background": load_first_image((
                os.path.join("assets", "menu", "menu_background.png"),
                os.path.join("assets", "menu", "menu_backgorund.png"),
            )),
            "bir_card": load_image(os.path.join("assets", "menu", "bir_sreshtha_card.png")),
            "raj_card": load_image(os.path.join("assets", "menu", "rajakar_card.png")),
            "star": load_image(os.path.join("assets", "icons", "star.png")),
            "book": load_image(os.path.join("assets", "icons", "book.png")),
            "exit": load_image(os.path.join("assets", "icons", "exit.png")),
            "clock": load_image(os.path.join("assets", "icons", "clock.png")),
            "settings": load_image(os.path.join("assets", "icons", "settings.png")),
        }

    def _build_fonts(self) -> Dict[str, pygame.font.Font]:
        title_path = os.path.join("assets", "fonts", "title.ttf")
        ui_path = os.path.join("assets", "fonts", "ui.ttf")
        return {
            "title": load_font(title_path, max(64, int(self.height * 0.108)), "Georgia", True),
            "subtitle": load_font(ui_path, max(20, int(self.height * 0.032)), "Segoe UI", True),
            "mission": load_font(ui_path, max(17, int(self.height * 0.026)), "Segoe UI"),
            "button": load_font(ui_path, max(31, int(self.height * 0.055)), "Segoe UI", True),
            "button_small": load_font(ui_path, max(22, int(self.height * 0.038)), "Segoe UI", True),
            "body": load_font(ui_path, max(18, int(self.height * 0.028)), "Segoe UI"),
            "small": load_font(ui_path, max(14, int(self.height * 0.022)), "Segoe UI"),
            "small_bold": load_font(ui_path, max(16, int(self.height * 0.025)), "Segoe UI", True),
        }

    def _button_layout(self) -> Tuple[int, int, int, int]:
        button_x = int(self.width * 0.08)
        button_w = int(self.width * 0.40)
        button_h = max(48, int(self.height * 0.072))
        start_y = int(self.height * 0.49)
        return button_x, start_y, button_w, button_h

    def _build_buttons(self) -> Dict[str, Button]:
        x, y, w, h = self._button_layout()
        return {
            "start": Button(pygame.Rect(x, y, w, h), "START", self.assets["star"], True),
            "how": Button(pygame.Rect(x, y + h + 18, w, h), "HOW TO PLAY", self.assets["book"], False),
            "exit": Button(pygame.Rect(x, y + (h + 18) * 2, w, h), "EXIT", self.assets["exit"], False),
        }

    def _slider_rect(self) -> pygame.Rect:
        x, y, w, h = self._button_layout()
        exit_bottom = y + (h + 18) * 2 + h
        track_y = exit_bottom + 60
        return pygame.Rect(x + 14, track_y, w - 28, max(12, int(self.height * 0.014)))

    def handle_menu_event(self, event: pygame.event.Event) -> Optional[str]:
        if self.slider.handle_event(event):
            return None
        if self.buttons["start"].handle_event(event):
            return "start"
        if self.buttons["how"].handle_event(event):
            return "how"
        if self.buttons["exit"].handle_event(event):
            return "exit"
        return None

    def handle_how_to_play_event(self, event: pygame.event.Event) -> Optional[str]:
        if self.back_button.handle_event(event):
            return "back"
        return None

    def draw_menu(self, surface: pygame.Surface) -> None:
        self._draw_background(surface)
        self._draw_title_block(surface)
        for key in ("start", "how", "exit"):
            font = self.fonts["button"] if key == "start" else self.fonts["button_small"]
            self.buttons[key].draw(surface, font)
        self.slider.draw(surface, self.fonts)
        self._draw_character_cards(surface)
        self._draw_footer(surface)

    def draw_how_to_play(self, surface: pygame.Surface) -> None:
        self._draw_background(surface)
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(int(self.width * 0.20), int(self.height * 0.15), int(self.width * 0.60), int(self.height * 0.64))
        panel_surf = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (28, 26, 20, 230), panel_surf.get_rect(), border_radius=10)
        pygame.draw.rect(panel_surf, (157, 124, 67, 230), panel_surf.get_rect(), width=2, border_radius=10)
        surface.blit(panel_surf, panel.topleft)

        draw_text_with_shadow(surface, self.fonts["subtitle"], "HOW TO PLAY", (panel.centerx, panel.y + 48), (239, 226, 190), center=True)
        lines = [
            "Move silently.",
            "Avoid detection.",
            "Use cover.",
            "Get adjacent to capture.",
            "Escape through exit tiles.",
        ]
        y = panel.y + 120
        for line in lines:
            pygame.draw.circle(surface, (151, 55, 42), (panel.x + 50, y + 12), 5)
            draw_text_with_shadow(surface, self.fonts["body"], line, (panel.x + 82, y), (218, 203, 166), offset=(2, 2))
            y += 52

        note = "Press R during a finished match to restart the simulation."
        draw_text_with_shadow(surface, self.fonts["small"], note, (panel.centerx, panel.bottom - 66), (160, 145, 112), center=True, offset=(1, 1))
        self.back_button.draw(surface, self.fonts["button_small"])

    def _draw_background(self, surface: pygame.Surface) -> None:
        background = self.assets["background"]
        if background is not None:
            surface.blit(scale_cover(background, (self.width, self.height)), (0, 0))
        else:
            self._draw_fallback_background(surface)

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 54))
        surface.blit(overlay, (0, 0))

        vignette = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        edge = max(80, int(self.width * 0.14))
        for i in range(edge):
            alpha = int(115 * (1 - i / edge))
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (i, 0, 1, self.height))
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (self.width - i - 1, 0, 1, self.height))
        surface.blit(vignette, (0, 0))

    def _draw_fallback_background(self, surface: pygame.Surface) -> None:
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            col = (
                int(52 - t * 34),
                int(44 - t * 30),
                int(30 - t * 22),
            )
            pygame.draw.line(surface, col, (0, y), (self.width, y))
        pygame.draw.circle(surface, (116, 78, 43), (int(self.width * 0.47), int(self.height * 0.22)), 80)
        pygame.draw.rect(surface, (32, 22, 16), (0, int(self.height * 0.56), self.width, self.height))

    def _draw_title_block(self, surface: pygame.Surface) -> None:
        x = int(self.width * 0.08)
        y = int(self.height * 0.25)
        title = "RajakarDhor"
        title_rect = draw_text_with_shadow(surface, self.fonts["title"], title, (x, y), (226, 215, 181), (10, 8, 4), offset=(5, 7))

        sub_y = title_rect.bottom + 16
        red = (151, 55, 42)
        pygame.draw.circle(surface, red, (x + 18, sub_y + 15), 8)
        pygame.draw.circle(surface, red, (x + min(int(self.width * 0.41), 470), sub_y + 15), 8)
        draw_text_with_shadow(surface, self.fonts["subtitle"], "TURN-BASED STEALTH PURSUIT", (x + 48, sub_y), (186, 158, 101), (0, 0, 0), offset=(2, 3))

        mission_y = sub_y + max(34, int(self.height * 0.044))
        draw_text_with_shadow(surface, self.fonts["mission"], "Eliminate the Rajakar without being detected.", (x + 48, mission_y), (205, 178, 125), (0, 0, 0), offset=(2, 3))

    def _draw_character_cards(self, surface: pygame.Surface) -> None:
        gap = 25
        card_w = int(self.width * 0.20)
        card_h = int(self.height * 0.45)
        max_total = self.width - int(self.width * 0.53) - int(self.width * 0.04)
        if card_w * 2 + gap > max_total:
            card_w = int((max_total - gap) / 2)
        card_h = min(card_h, int(card_w * 1.55))
        x = int(self.width * 0.53)
        y = int(self.height * 0.31)

        self._draw_card_image(surface, self.assets["bir_card"], pygame.Rect(x, y, card_w, card_h), (52, 78, 38), (142, 161, 68), "BIR SRESHTHA")
        self._draw_card_image(surface, self.assets["raj_card"], pygame.Rect(x + card_w + gap, y, card_w, card_h), (71, 32, 22), (157, 68, 44), "RAJAKAR")

    def _draw_card_image(
        self,
        surface: pygame.Surface,
        image: Optional[pygame.Surface],
        rect: pygame.Rect,
        fill: Color,
        border: Color,
        fallback_title: str,
    ) -> None:
        shadow = pygame.Surface((rect.w + 14, rect.h + 14), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 145), shadow.get_rect(), border_radius=8)
        surface.blit(shadow, (rect.x + 6, rect.y + 8))

        if image is not None:
            fitted = blit_fit(surface, image, rect)
            pygame.draw.rect(surface, border, fitted, width=2, border_radius=5)
            return

        pygame.draw.rect(surface, fill, rect, border_radius=7)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=7)
        draw_text_with_shadow(surface, self.fonts["small_bold"], fallback_title, (rect.centerx, rect.y + 36), border, center=True)

    def _draw_footer(self, surface: pygame.Surface) -> None:
        icon = self.assets["settings"]
        color = (164, 146, 100)
        x = int(self.width * 0.02)
        y = min(
            max(int(self.height * 0.88), self.slider.rect.bottom + 24),
            self.height - 74,
        )
        if icon is not None:
            size = max(28, int(self.height * 0.045))
            image = tint_image(pygame.transform.smoothscale(icon, (size, size)), color)
            surface.blit(image, image.get_rect(center=(x + size // 2, y + size // 2)))
            text_x = x + size + 18
        else:
            pygame.draw.circle(surface, color, (x + 20, y + 20), 15, width=5)
            text_x = x + 58
        draw_text_with_shadow(surface, self.fonts["small_bold"], "SETTINGS", (text_x, y + 9), color, offset=(1, 1))

        footer = "© 2024 RajakarDhor Team. All rights reserved."
        draw_text_with_shadow(surface, self.fonts["small"], footer, (int(self.width * 0.02), self.height - 36), (123, 106, 75), offset=(1, 1))
        version = self.fonts["small"].render("v1.0.0", True, (129, 112, 77))
        shadow = self.fonts["small"].render("v1.0.0", True, (0, 0, 0))
        vx = self.width - version.get_width() - int(self.width * 0.03)
        vy = self.height - 36
        surface.blit(shadow, (vx + 1, vy + 1))
        surface.blit(version, (vx, vy))
