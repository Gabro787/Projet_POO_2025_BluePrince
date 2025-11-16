# sprites.py
import pygame
from pygame import Surface, Rect


def load_tileset(path: str, tile_src: int, tile_dst: int) -> list[Surface]:
    """
    Version générique (grille sans marges ni espacements).
    Utilisée éventuellement pour d'autres sprites.
    """
    sheet = pygame.image.load(path).convert_alpha()
    sheet_w, sheet_h = sheet.get_size()

    cols = sheet_w // tile_src
    rows = sheet_h // tile_src

    tiles: list[Surface] = []

    for row in range(rows):
        for col in range(cols):
            x = col * tile_src
            y = row * tile_src
            rect = Rect(x, y, tile_src, tile_src)
            sub = sheet.subsurface(rect)
            if tile_dst != tile_src:
                sub = pygame.transform.smoothscale(sub, (tile_dst, tile_dst))
            tiles.append(sub)

    return tiles


def load_tileset_with_margins(
    path: str,
    tile_w: int,
    tile_h: int,
    offset_x: int,
    offset_y: int,
    spacing_x: int,
    spacing_y: int,
    tile_dst: int,
) -> list[Surface]:
    """
    Découpe un tileset avec marge + espacement entre les tuiles.
    """
    sheet = pygame.image.load(path).convert_alpha()
    sheet_w, sheet_h = sheet.get_size()

    tiles: list[Surface] = []

    y = offset_y
    while y + tile_h <= sheet_h:
        x = offset_x
        while x + tile_w <= sheet_w:
            rect = Rect(x, y, tile_w, tile_h)
            sub = sheet.subsurface(rect)
            if tile_dst and tile_dst > 0:
                sub = pygame.transform.smoothscale(sub, (tile_dst, tile_dst))
            tiles.append(sub)
            x += tile_w + spacing_x
        y += tile_h + spacing_y

    return tiles