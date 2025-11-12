# constants.py
import pygame

"""
Ce module centralise toutes les constantes du jeu :
- Dimensions de la grille et de la fenêtre
- Couleurs et polices
- Paramètres des effets visuels (clignotement et pulsing)
- Mappings des touches (AZERTY)
"""

# -------- Fenêtre / Grille --------
TILE = 96                  # Taille d'une case en pixels
COLS, ROWS = 9, 5          # Grille 9 colonnes x 5 lignes
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE + 120  # Hauteur totale = grille + HUD
FPS = 60                   # Images par seconde

# -------- Couleurs --------
WHITE  = (245, 245, 245)
BLACK  = (15, 15, 15)
GRAY   = (60, 60, 60)
BLUE   = (90, 140, 255)
GREEN  = (80, 170, 120)
RED    = (220, 70, 70)
YELLOW = (230, 200, 80)
PURPLE = (170, 120, 220)
ORANGE = (230, 150, 70)
BG     = (25, 27, 35)      # Couleur de fond

# -------- Polices --------
pygame.font.init()
FONT_SM = pygame.font.SysFont("consolas", 18)
FONT_MD = pygame.font.SysFont("consolas", 22, bold=True)
FONT_LG = pygame.font.SysFont("consolas", 36, bold=True)

# -------- Effets visuels --------
"""
Clignotement (ON/OFF) : utilisé pour l'indicateur de direction (porte).
Pulsing (épaisseur qui 'respire') : utilisé pour le cadre de la carte sélectionnée dans le menu.
"""
BLINK_PERIOD_MS = 300   # Période du clignotement (ON/OFF) en millisecondes
PULSE_PERIOD_MS = 900   # Période du pulsing (inspire/expire) en millisecondes

# -------- Touches (AZERTY) --------
# Déplacements
KEY_UP    = pygame.K_z
KEY_LEFT  = pygame.K_q
KEY_DOWN  = pygame.K_s
KEY_RIGHT = pygame.K_d

# Validation / Annulation / Action
KEY_CONFIRM = pygame.K_RETURN   # Valider (Entrée)
KEY_CANCEL  = pygame.K_ESCAPE   # Annuler / quitter un menu (Échap)
KEY_USE     = pygame.K_SPACE    # Action contextuelle (ici: annuler aussi)

# -------- Images (optionnel) --------
IMG_ROOMS = {}  # À remplir plus tard {room_name: pygame.Surface}
