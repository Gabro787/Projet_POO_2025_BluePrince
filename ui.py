# ui.py
import math
import pygame
from constants import *

"""
Ce module contient tout l'affichage (UI) :
- Grille, pièces, portes
- Joueur
- HUD
- Indicateur de direction (clignotement ON/OFF)
- Menu de sélection de salle (pulsing sur la carte sélectionnée)
- Écran de fin de partie
"""

# Couleurs associées aux "types/couleurs" de salles
COLORS_BY_ROOM_COLOR = {
    "blue": BLUE,
    "green": GREEN,
    "purple": PURPLE,
    "orange": ORANGE,
    "red": RED,
    "yellow": YELLOW,
    None: GRAY,
}

def draw_grid(surface, manor):
    """
    Dessine la grille et les pièces connues du manoir.
    - Chaque case est une tuile TILE x TILE.
    - Si une Room est présente : fond coloré + portes + label court.
    """
    for r in range(ROWS):
        for c in range(COLS):
            x, y = c * TILE, r * TILE
            rect = pygame.Rect(x, y, TILE, TILE)

            # Trait de grille
            pygame.draw.rect(surface, GRAY, rect, width=1)

            # Pièce si connue
            room = manor.get_room(r, c) if manor else None
            if room:
                # Fond par couleur de salle
                color = COLORS_BY_ROOM_COLOR.get(getattr(room, "color", None), GRAY)
                pygame.draw.rect(surface, color, rect.inflate(-8, -8), border_radius=8)

                # Portes (petits traits sur les bords)
                for d in getattr(room, "doors", []):  # ex: ["N","S","E","W"]
                    _draw_door(surface, rect, d)

                # Nom court au centre
                label = getattr(room, "short", "?")
                text = FONT_SM.render(label, True, BLACK)
                surface.blit(text, text.get_rect(center=rect.center))

def _draw_door(surface, rect, direction):
    """
    Dessine une petite 'barre' sur le bord de la tuile pour représenter une porte.
    direction ∈ {"N","S","E","W"}.
    """
    w = 14  # longueur du trait de porte
    if direction == "N":
        pygame.draw.rect(surface, WHITE, (rect.centerx - w//2, rect.top-1, w, 6))
    if direction == "S":
        pygame.draw.rect(surface, WHITE, (rect.centerx - w//2, rect.bottom-5, w, 6))
    if direction == "W":
        pygame.draw.rect(surface, WHITE, (rect.left-1, rect.centery - w//2, 6, w))
    if direction == "E":
        pygame.draw.rect(surface, WHITE, (rect.right-5, rect.centery - w//2, 6, w))

def draw_player(surface, rc_pos):
    """
    Dessine le joueur sous forme d'un petit disque jaune
    centré dans sa tuile (r, c).
    """
    r, c = rc_pos
    x = c * TILE + TILE // 2
    y = r * TILE + TILE // 2
    pygame.draw.circle(surface, YELLOW, (x, y), 14)

def draw_hud(surface, player_state, message=""):
    """
    Dessine le bandeau HUD sous la grille :
    - Pas restants
    - Gemmes
    - Clés
    - Dés
    - Message d'état (aide / feedback utilisateur)
    """
    hud_rect = pygame.Rect(0, ROWS * TILE, WIDTH, HEIGHT - ROWS * TILE)
    pygame.draw.rect(surface, (32, 34, 44), hud_rect)

    items = [
        ("Pas", player_state.steps),
        ("Gemmes", player_state.gems),
        ("Clés", player_state.keys),
        ("Dés", player_state.dice),
    ]
    x = 16
    for name, val in items:
        txt = FONT_MD.render(f"{name}: {val}", True, WHITE)
        surface.blit(txt, (x, ROWS * TILE + 18))
        x += txt.get_width() + 28

    if message:
        msg = FONT_MD.render(message, True, WHITE)
        surface.blit(msg, (16, ROWS * TILE + 56))

# -------- Effets visuels : blink (direction) & pulsing (cartes) --------

def draw_direction_hint(surface, rc_pos, dir_, visible=True):
    """
    Dessine l'indicateur de direction sur l'arête de la tuile du joueur
    en mode CLIGNOTEMENT ON/OFF.
    - rc_pos : tuple (r, c) position du joueur
    - dir_   : "N","S","E","W" ou None
    - visible: booléen (True = on dessine, False = invisible sur ce frame)
    """
    if not dir_ or not visible:
        return

    r, c = rc_pos
    rect = pygame.Rect(c * TILE, r * TILE, TILE, TILE)
    glow = 6  # épaisseur/halo fixe pour l'indicateur

    # On dessine un "trait" collé au bord correspondant à la direction
    if dir_ == "N":
        pygame.draw.rect(surface, YELLOW, (rect.left + 10, rect.top - 2, rect.width - 20, glow))
    elif dir_ == "S":
        pygame.draw.rect(surface, YELLOW, (rect.left + 10, rect.bottom - glow + 2, rect.width - 20, glow))
    elif dir_ == "W":
        pygame.draw.rect(surface, YELLOW, (rect.left - 2, rect.top + 10, glow, rect.height - 20))
    elif dir_ == "E":
        pygame.draw.rect(surface, YELLOW, (rect.right - glow + 2, rect.top + 10, glow, rect.height - 20))

def _pulse_amount(phase: float) -> float:
    """
    Convertit une phase (0..1) en valeur lissée 0..1..0 via cosinus :
    - phase = 0   -> 0
    - phase = 0.5 -> 1
    - phase = 1   -> 0
    """
    return 0.5 * (1 - math.cos(2 * math.pi * phase))

def _pulse_width(phase: float, w_min: int = 2, w_max: int = 8) -> int:
    """
    Renvoie une épaisseur d'affichage entière qui 'respire' entre w_min et w_max.
    Utilisé pour le cadre des cartes sélectionnées (menu).
    """
    t = _pulse_amount(phase)
    return int(round(w_min + t * (w_max - w_min)))

def draw_pick_screen_pulse(surface, three_rooms, selected_idx, phase: float):
    """
    Affiche l'écran de sélection d'une salle parmi 3 propositions.
    - La carte sélectionnée affiche un cadre 'pulsant' (épaisseur qui varie).
    - Flèches gauche/droite (ou A/E) : changer de sélection.
    - Entrée : valider la salle.
    - Échap : annuler et revenir au jeu.
    """
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    title = FONT_LG.render("Choisis une pièce (← →, Entrée)", True, WHITE)
    tip   = FONT_SM.render("Échap: annuler et revenir", True, WHITE)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 40)))
    surface.blit(tip,   tip.get_rect(center=(WIDTH // 2, 72)))

    # Mise en page des 3 cartes
    gap = 40
    card_w, card_h = 220, 180
    total_w = 3 * card_w + 2 * gap
    start_x = (WIDTH - total_w) // 2
    y = 120

    for i, room in enumerate(three_rooms):
        rect = pygame.Rect(start_x + i * (card_w + gap), y, card_w, card_h)
        color = COLORS_BY_ROOM_COLOR.get(getattr(room, "color", None), GRAY)

        # Corps de la carte
        pygame.draw.rect(surface, color, rect, border_radius=16)

        # Cadre : si carte sélectionnée, on dessine un halo dont l'épaisseur pulse
        if i == selected_idx:
            w = _pulse_width(phase, 3, 10)
            pygame.draw.rect(surface, YELLOW, rect.inflate(8, 8), width=w, border_radius=18)
        else:
            pygame.draw.rect(surface, WHITE, rect, width=1, border_radius=16)

        # Texte informatif sur la carte
        name  = getattr(room, "name", "???")
        cost  = getattr(room, "gem_cost", 0)
        doors = "".join(getattr(room, "doors", [])) or "-"
        t1 = FONT_MD.render(name, True, BLACK)
        t2 = FONT_SM.render(f"Gemmes: {cost}", True, BLACK)
        t3 = FONT_SM.render(f"Portes: {doors}", True, BLACK)
        surface.blit(t1, t1.get_rect(center=(rect.centerx, rect.top + 40)))
        surface.blit(t2, t2.get_rect(center=(rect.centerx, rect.centery)))
        surface.blit(t3, t3.get_rect(center=(rect.centerx, rect.centery + 24)))

def draw_end_screen(surface, win=True):
    """
    Dessine l'écran de fin (victoire/défaite) avec une invite à rejouer.
    """
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    surface.blit(overlay, (0, 0))
    text = "Victoire !" if win else "Défaite…"
    color = GREEN if win else RED
    title = FONT_LG.render(text, True, color)
    press = FONT_MD.render("Entrée pour rejouer", True, WHITE)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 16)))
    surface.blit(press, press.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 26)))
