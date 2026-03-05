# render/renderer.py
import pygame


def draw_rect(surface, rect, color, radius=0, width=0):
    """Draw rounded rect if radius > 0, else normal rect."""
    if radius > 0:
        pygame.draw.rect(surface, color, rect,
                         width=width, border_radius=radius)
    else:
        pygame.draw.rect(surface, color, rect, width=width)
