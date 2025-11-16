# ui.py
import math
import pygame
from room import RoomType
from items import Food  # pour compter la nourriture dans l'inventaire
from constants import *
from door import DoorLockLevel


"""
Ce module contient tout l'affichage (UI) :
- Grille, pièces, portes
- Joueur
- HUD
- Indicateur de direction (clignotement ON/OFF)
- Menu de sélection de salle (pulsing sur la carte sélectionnée)
- Fenêtre de boutique
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

# Texte de bonus / effet pour certaines salles
ROOM_BONUS_TEXT = {
    "BED": "Entrée: repos (+2 pas).",
    "GBD": "Entrée: détecteur trouvé.",
    "SUI": "Entrée: gros repos (+10 pas).",
    "VLT": "Entrée: or + gemmes.",
    "TRS": "Entrée: or + clé + gemme.",
    "VRN": "Entrée: pelle trouvée ici.",
    "CEL": "Entrée: kit de crochetage.",
    "MCH": "Entrée: or / chance patte de lapin.",
    "TRP": "Entrée: gros pièges (perte de pas).",
    "CHN": "Entrée: petits pièges.",
}


def _draw_wrapped_text(surface, text, x, y, font, color, max_width) -> int:
    """
    Dessine du texte avec retour à la ligne automatique.
    Retourne la nouvelle valeur de y après dessin.
    """
    if not text:
        return y

    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}" if line else word
        w, h = font.size(test_line)
        if w <= max_width:
            line = test_line
        else:
            # Dessiner la ligne actuelle
            surf = font.render(line, True, color)
            surface.blit(surf, (x, y))
            y += h + 2
            line = word

    if line:
        surf = font.render(line, True, color)
        surface.blit(surf, (x, y))
        y += surf.get_height()

    return y


def draw_grid(surface, manor):
    """
    Dessine la grille et les pièces connues du manoir.
    - Chaque case est une tuile TILE x TILE.
    - Si une Room est présente :
        * si room.image est défini -> on blitte le sprite de salle
        * sinon -> fond coloré
      puis on dessine les portes et le label court.
    """
    for r in range(ROWS):
        for c in range(COLS):
            x, y = c * TILE, r * TILE
            rect = pygame.Rect(x, y, TILE, TILE)

            # Trait de grille
            pygame.draw.rect(surface, GRAY, rect, width=1)

            room = manor.get_room(r, c) if manor else None

            # --- Dessin de la salle ---
            if room:
                img = getattr(room, "image", None)
                if img is not None:
                    img_rect = img.get_rect(topleft=rect.topleft)
                    surface.blit(img, img_rect)
                else:
                    color = COLORS_BY_ROOM_COLOR.get(getattr(room, "color", None), GRAY)
                    pygame.draw.rect(surface, color, rect.inflate(-8, -8), border_radius=8)

            # --- Portes + label (par-dessus) ---
            if room:
                for d in getattr(room, "doors", []):
                    lock_level = None
                    if manor and hasattr(manor, "get_door"):
                        door = manor.get_door((r, c), d)
                        if door is not None and not door.is_open:
                            lock_level = door.lock_level

                    _draw_door(surface, rect, d, lock_level)

                label = getattr(room, "short", "?")
                text = FONT_SM.render(label, True, BLACK)
                surface.blit(text, text.get_rect(center=rect.center))


def _draw_door(surface, rect, direction, lock_level: DoorLockLevel | None = None):
    """
    Dessine une petite 'barre' sur le bord de la tuile pour représenter une porte.
    """
    if lock_level is None or lock_level == DoorLockLevel.UNLOCKED:
        color = WHITE
        thickness = 4
    elif lock_level == DoorLockLevel.LOCKED:
        color = YELLOW
        thickness = 6
    else:  # DoorLockLevel.DOUBLE_LOCKED
        color = RED
        thickness = 8

    w = 14  # longueur du trait de porte

    if direction == "N":
        pygame.draw.rect(
            surface,
            color,
            (rect.centerx - w // 2, rect.top - 1, w, thickness),
        )
    if direction == "S":
        pygame.draw.rect(
            surface,
            color,
            (rect.centerx - w // 2, rect.bottom - thickness + 1, w, thickness),
        )
    if direction == "W":
        pygame.draw.rect(
            surface,
            color,
            (rect.left - 1, rect.centery - w // 2, thickness, w),
        )
    if direction == "E":
        pygame.draw.rect(
            surface,
            color,
            (rect.right - thickness + 1, rect.centery - w // 2, thickness, w),
        )


def draw_player(surface, rc_pos):
    """Dessine le joueur sous forme d'un petit disque jaune centré dans sa tuile."""
    r, c = rc_pos
    x = c * TILE + TILE // 2
    y = r * TILE + TILE // 2
    pygame.draw.circle(surface, YELLOW, (x, y), 14)


def draw_hud(surface, player_state, message="", icons=None, room=None, hint: str = ""):
    """
    Dessine le HUD dans une colonne à droite de la grille :
    - Ressources
    - Inventaire
    - Infos salle actuelle (type + bonus)
    - Message
    - Hint (contrôle contexte)
    """
    hud_rect = pygame.Rect(COLS * TILE, 0, WIDTH - COLS * TILE, HEIGHT)
    pygame.draw.rect(surface, (32, 34, 44), hud_rect)

    x = COLS * TILE + 16
    y = 20

    # -------- Ressources de base --------
    steps = getattr(player_state, "steps", 0)
    gems  = getattr(player_state, "gems", 0)
    gold  = getattr(player_state, "gold", 0)
    keys  = getattr(player_state, "keys", 0)
    dice  = getattr(player_state, "dice", 0)

    resources = [
        ("steps", "Pas",    steps),
        ("gems",  "Gemmes", gems),
        ("gold",  "Or",     gold),
        ("keys",  "Clés",   keys),
        ("dice",  "Dés",    dice),
    ]

    for key, label, val in resources:
        icon = icons.get(key) if icons else None
        txt = FONT_MD.render(f"{label}: {val}", True, WHITE)

        if icon:
            icon_rect = icon.get_rect(topleft=(x, y))
            surface.blit(icon, icon_rect)
            text_x = icon_rect.right + 8

            text_rect = txt.get_rect()
            text_rect.topleft = (
                text_x,
                y + (icon_rect.height - text_rect.height) // 2
            )
            surface.blit(txt, text_rect)

            line_height = max(icon_rect.height, text_rect.height)
        else:
            text_rect = txt.get_rect(topleft=(x, y))
            surface.blit(txt, text_rect)
            line_height = text_rect.height

        y += line_height + 8

    # -------- Inventaire détaillé --------
    inv = getattr(player_state, "inventory", None)

    if inv is not None:
        y += 10
        title_inv = FONT_MD.render("Inventaire :", True, WHITE)
        surface.blit(title_inv, (x, y))
        y += title_inv.get_height() + 4

        # Nourriture : compter les Food
        food_count = sum(1 for it in inv.items if isinstance(it, Food))

        icon_food = icons.get("food") if icons else None
        txt_food = FONT_SM.render(f"Nourriture: {food_count}", True, WHITE)

        if icon_food:
            icon_rect = icon_food.get_rect(topleft=(x, y))
            surface.blit(icon_food, icon_rect)
            text_x = icon_rect.right + 8

            text_rect = txt_food.get_rect()
            text_rect.topleft = (
                text_x,
                y + (icon_rect.height - text_rect.height) // 2
            )
            surface.blit(txt_food, text_rect)

            line_height = max(icon_rect.height, text_rect.height)
        else:
            text_rect = txt_food.get_rect(topleft=(x, y))
            surface.blit(txt_food, text_rect)
            line_height = text_rect.height

        y += line_height + 6

        # Objets permanents AVEC description courte
        perm_labels = []
        perm_icons = []

        if inv.has_shovel():
            perm_labels.append("Pelle (creuser jardins)")
            perm_icons.append("perm_shovel")
        if inv.has_hammer():
            perm_labels.append("Marteau (-dégâts pièges)")
            perm_icons.append("perm_hammer")
        if inv.has_lockpick():
            perm_labels.append("Kit crochetage (portes/coffres)")
            perm_icons.append("perm_lockpick")
        if inv.has_detector():
            perm_labels.append("Détecteur (loot+)")
            perm_icons.append("perm_detector")
        if inv.has_rabbit_foot():
            perm_labels.append("Patte de lapin (chance+)")
            perm_icons.append("perm_rabbit")

        if perm_labels:
            for label, icon_key in zip(perm_labels, perm_icons):
                icon_perm = icons.get(icon_key) if icons else None
                txt_perm = FONT_SM.render(label, True, WHITE)

                if icon_perm:
                    icon_rect = icon_perm.get_rect(topleft=(x, y))
                    surface.blit(icon_perm, icon_rect)
                    text_x = icon_rect.right + 8

                    text_rect = txt_perm.get_rect()
                    text_rect.topleft = (
                        text_x,
                        y + (icon_rect.height - text_rect.height) // 2
                    )
                    surface.blit(txt_perm, text_rect)

                    line_height = max(icon_rect.height, text_rect.height)
                else:
                    text_rect = txt_perm.get_rect(topleft=(x, y))
                    surface.blit(txt_perm, text_rect)
                    line_height = text_rect.height

                y += line_height + 4
        else:
            txt_perm = FONT_SM.render("Objets perm.: aucun", True, WHITE)
            surface.blit(txt_perm, (x, y))
            y += txt_perm.get_height() + 4

    # -------- Infos sur la salle actuelle --------
    if room is not None:
        y += 10
        title_room = FONT_MD.render("Salle actuelle :", True, WHITE)
        surface.blit(title_room, (x, y))
        y += title_room.get_height() + 4

        room_name = getattr(room, "name", "Inconnue")
        room_short = getattr(room, "short", "??")
        txt_room = FONT_SM.render(f"{room_name} ({room_short})", True, WHITE)
        surface.blit(txt_room, (x, y))
        y += txt_room.get_height() + 4

        room_type = getattr(room, "room_type", None)

        if room_type == RoomType.FOOD:
            loot_text = "Peut contenir : nourriture (pas +)."
        elif room_type == RoomType.TREASURE:
            loot_text = "Peut contenir : gemmes, or, clés, dés."
        elif room_type == RoomType.TRAP:
            loot_text = "Salle dangereuse : pièges / malus."
        else:
            loot_text = "Peut contenir : objets variés."

        txt_loot = FONT_SM.render(loot_text, True, WHITE)
        surface.blit(txt_loot, (x, y))
        y += txt_loot.get_height() + 4

        # Bonus / effet spécifique de cette salle
        bonus_txt = ROOM_BONUS_TEXT.get(room_short)
        if bonus_txt:
            bonus_surf = FONT_SM.render(f"Effet: {bonus_txt}", True, YELLOW)
            surface.blit(bonus_surf, (x, y))
            y += bonus_surf.get_height() + 4

    # -------- Message d'état + hint --------
    max_w = hud_rect.width - 32

    if message:
        y += 10
        y = _draw_wrapped_text(surface, message, x, y, FONT_SM, WHITE, max_w)

    if hint:
        y += 4
        y = _draw_wrapped_text(surface, hint, x, y, FONT_SM, YELLOW, max_w)


# -------- Effets visuels : blink (direction) & pulsing (cartes) --------

def draw_direction_hint(surface, rc_pos, dir_, visible=True):
    """
    Dessine l'indicateur de direction sur l'arête de la tuile du joueur
    en mode CLIGNOTEMENT ON/OFF.
    """
    if not dir_ or not visible:
        return

    r, c = rc_pos
    rect = pygame.Rect(c * TILE, r * TILE, TILE, TILE)
    glow = 6

    if dir_ == "N":
        pygame.draw.rect(surface, YELLOW, (rect.left + 10, rect.top - 2, rect.width - 20, glow))
    elif dir_ == "S":
        pygame.draw.rect(surface, YELLOW, (rect.left + 10, rect.bottom - glow + 2, rect.width - 20, glow))
    elif dir_ == "W":
        pygame.draw.rect(surface, YELLOW, (rect.left - 2, rect.top + 10, glow, rect.height - 20))
    elif dir_ == "E":
        pygame.draw.rect(surface, YELLOW, (rect.right - glow + 2, rect.top + 10, glow, rect.height - 20))


def _pulse_amount(phase: float) -> float:
    return 0.5 * (1 - math.cos(2 * math.pi * phase))


def _pulse_width(phase: float, w_min: int = 2, w_max: int = 8) -> int:
    t = _pulse_amount(phase)
    return int(round(w_min + t * (w_max - w_min)))


def draw_pick_screen_pulse(surface, three_rooms, selected_idx, phase: float):
    """
    Affiche l'écran de sélection d'une salle parmi 3 propositions.
    """
    grid_width = COLS * TILE
    grid_height = ROWS * TILE

    overlay = pygame.Surface((grid_width, grid_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    title = FONT_LG.render("Choisis une pièce", True, WHITE)
    tip   = FONT_SM.render("← → ou A/E pour changer — Entrée pour valider — Échap pour annuler", True, WHITE)

    title_rect = title.get_rect(center=(grid_width // 2, 40))
    tip_rect   = tip.get_rect(center=(grid_width // 2, 70))

    surface.blit(title, title_rect)
    surface.blit(tip, tip_rect)

    card_w, card_h = 90, 150
    gap = 12

    total_w = 3 * card_w + 2 * gap
    start_x = (grid_width - total_w) // 2
    y = 110

    for i, room in enumerate(three_rooms):
        x = start_x + i * (card_w + gap)
        rect = pygame.Rect(x, y, card_w, card_h)

        color = COLORS_BY_ROOM_COLOR.get(getattr(room, "color", None), GRAY)
        pygame.draw.rect(surface, color, rect, border_radius=10)

        if i == selected_idx:
            w = _pulse_width(phase, 3, 8)
            pygame.draw.rect(surface, YELLOW, rect.inflate(8, 8), width=w, border_radius=12)
        else:
            pygame.draw.rect(surface, WHITE, rect, width=1, border_radius=10)

        idx_label = FONT_SM.render(str(i + 1), True, BLACK)
        surface.blit(idx_label, (rect.left + 6, rect.top + 4))

        name  = getattr(room, "name", "???")
        cost  = getattr(room, "gem_cost", 0)
        doors = "".join(getattr(room, "doors", [])) or "-"

        short_name = name if len(name) <= 12 else name[:11] + "…"
        t_name = FONT_MD.render(short_name, True, BLACK)
        surface.blit(t_name, t_name.get_rect(center=(rect.centerx, rect.top + 30)))

        _draw_card_cost(surface, rect, cost)

        t_doors = FONT_SM.render(f"Portes: {doors}", True, BLACK)
        surface.blit(t_doors, t_doors.get_rect(center=(rect.centerx, rect.centery + 30)))


def _draw_card_cost(surface, rect: pygame.Rect, cost: int):
    if cost < 0:
        cost = 0

    badge_w, badge_h = 34, 20
    bx = rect.centerx - badge_w // 2
    by = rect.bottom - badge_h - 8

    badge_color = GREEN if cost == 0 else YELLOW
    pygame.draw.rect(surface, badge_color, (bx, by, badge_w, badge_h), border_radius=8)

    txt = FONT_SM.render(str(cost), True, BLACK)
    txt_rect = txt.get_rect(center=(bx + badge_w // 2, by + badge_h // 2))
    surface.blit(txt, txt_rect)


def draw_shop_window(surface, inventory, shop_message: str = ""):
    """
    Affiche une petite fenêtre centrée pour la Boutique (SHP).
    - Affiche l'or actuel.
    - Si le joueur n'a pas d'or, un message clair s'affiche.
    - Affiche aussi le dernier message de la boutique (erreur achat, etc.).
    """
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    win_w, win_h = 380, 280
    rect = pygame.Rect(0, 0, win_w, win_h)
    rect.center = (COLS * TILE // 2, ROWS * TILE // 2)

    pygame.draw.rect(surface, (40, 42, 52), rect, border_radius=16)
    pygame.draw.rect(surface, WHITE, rect, width=2, border_radius=16)

    title = FONT_LG.render("Boutique", True, YELLOW)
    surface.blit(title, title.get_rect(center=(rect.centerx, rect.top + 32)))

    lines = [
        f"Or actuel : {inventory.gold}",
        "",
        "1 - Clé (5 or)",
        "2 - Nourriture (+4 pas) (3 or)",
        "3 - Dé (8 or)",
        "4 - Patte de lapin (12 or)",
        "",
        "Échap : quitter la boutique",
    ]

    y = rect.top + 72
    for line in lines:
        txt = FONT_SM.render(line, True, WHITE)
        surface.blit(txt, (rect.left + 24, y))
        y += txt.get_height() + 4

    # Si le joueur n'a aucune pièce d'or, on l'affiche clairement
    if inventory.gold == 0:
        warn = FONT_SM.render("Tu n'as aucune pièce d'or.", True, RED)
        surface.blit(warn, (rect.left + 24, y))
        y += warn.get_height() + 4

    # Message spécifique de la boutique (ex: pas assez d'or, achat réussi)
    if shop_message:
        y += 4
        msg = FONT_SM.render(shop_message, True, YELLOW)
        surface.blit(msg, (rect.left + 24, y))

def draw_end_screen(surface, win=True):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    surface.blit(overlay, (0, 0))
    text = "Victoire !" if win else "Défaite…"
    color = GREEN if win else RED
    title = FONT_LG.render(text, True, color)
    press = FONT_MD.render("Entrée pour rejouer", True, WHITE)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 16)))
    surface.blit(press, press.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 26)))