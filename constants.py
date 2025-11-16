# constants.py
import pygame
import os

# -------- Dossiers / chemins --------
ASSETS_DIR = "assets"

# Image 4x4 des icônes HUD
ITEMS_TILESET_PATH = os.path.join(ASSETS_DIR, "HUD.png")

# Image des salles 
ROOMS_TILESET_PATH = os.path.join(ASSETS_DIR, "Sallee.png")

"""
Constantes du jeu :
- Grille 5 x 9
- HUD à droite
- Taille réduite pour que la fenêtre tienne sur l'écran
"""

# -------- Fenêtre / Grille --------
TILE = 85                # Taille d'une case en pixels

# Orientation : 5 colonnes (horizontal) x 9 lignes (vertical)
COLS, ROWS = 5, 9          # Grille 5 x 9

# Largeur réservée au HUD sur la droite
HUD_WIDTH = 500

# Taille de la fenêtre :
WIDTH  = COLS * TILE + HUD_WIDTH
HEIGHT = ROWS * TILE

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
BG     = (25, 27, 35)

# -------- Polices --------
pygame.font.init()
FONT_SM = pygame.font.SysFont("consolas", 14)
FONT_MD = pygame.font.SysFont("consolas", 18, bold=True)
FONT_LG = pygame.font.SysFont("consolas", 28, bold=True)

# -------- Effets visuels --------
BLINK_PERIOD_MS = 300   # Clignotement ON/OFF (ms)
PULSE_PERIOD_MS = 900   # Pulsing (ms)

# -------- Touches (AZERTY) --------
KEY_UP    = pygame.K_z
KEY_LEFT  = pygame.K_q
KEY_DOWN  = pygame.K_s
KEY_RIGHT = pygame.K_d

KEY_CONFIRM = pygame.K_RETURN   # Valider (Entrée)
KEY_CANCEL  = pygame.K_ESCAPE   # Annuler / quitter un menu (Échap)
KEY_USE     = pygame.K_SPACE    # Action contextuelle

# -------- Images Futur options (pour le prochain patch si y'a le temps) --------
IMG_ROOMS = {}  