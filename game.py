# game.py
import pygame, random
from dataclasses import dataclass
from constants import *
from ui import (
    draw_grid, draw_player, draw_hud,
    draw_pick_screen_pulse, draw_end_screen,
    draw_direction_hint
)

"""
Ce module gère la boucle de jeu, les états et les entrées clavier.
Il inclut des 'mocks' de Manor/Room/Player pour pouvoir jouer tout de suite.
- Sélection de PORTE (direction) : CLIGNOTEMENT ON/OFF.
- Menu de sélection de SALLE : PULSING sur la carte sélectionnée.
Quand les modules A (Manor/Room/Doors) et B (Player) seront prêts,
remplacez les mocks par vos vraies classes (en gardant la même interface).
"""

# ---------- Mocks (à remplacer par A/B) ----------

@dataclass
class MockRoom:
    """
    Représente une salle minimale pour les tests UI.
    - name/short : textes d'affichage
    - color      : clé pour COLORS_BY_ROOM_COLOR
    - doors      : liste des directions ["N","S","E","W"]
    - gem_cost   : coût en gemmes pour placer cette salle
    """
    name: str
    short: str
    color: str | None
    doors: list[str]
    gem_cost: int = 0

class MockManor:
    """
    Simule un manoir 9x5 :
    - Une salle d'entrée en bas milieu
    - Une 'antichambre' (objectif) en haut milieu
    - Gestion simple des déplacements dans la grille (sans murs complexes)
    """
    def __init__(self):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        # Entrée en bas milieu
        r, c = ROWS - 1, COLS // 2
        self.grid[r][c] = MockRoom("Entrée", "ENT", "blue", ["N"])
        self.start = (r, c)
        # Antichambre (objectif) en haut milieu
        self.antechamber_rc = (0, COLS // 2)

    def get_room(self, r, c):
        """Retourne la Room à (r,c) ou None si inconnu."""
        return self.grid[r][c]

    def set_room(self, r, c, room):
        """Place une Room dans la grille à (r,c)."""
        self.grid[r][c] = room

    def in_bounds(self, r, c) -> bool:
        """Vrai si (r,c) est dans les limites de la grille."""
        return 0 <= r < ROWS and 0 <= c < COLS

    def valid_move(self, from_rc, dir_):
        """
        Calcule la destination si on se déplace depuis from_rc dans la direction dir_.
        Retourne (nr, nc) si valide, sinon None si sortie de la grille.
        """
        drdc = {"N": (-1, 0), "S": (1, 0), "W": (0, -1), "E": (0, 1)}[dir_]
        nr, nc = from_rc[0] + drdc[0], from_rc[1] + drdc[1]
        if not self.in_bounds(nr, nc):
            return None
        return (nr, nc)

@dataclass
class PlayerState:
    """
    État du joueur minimal :
    - Position (r, c)
    - Ressources (pas, gemmes, clés, dés)
    """
    r: int
    c: int
    steps: int = 70
    gems: int = 2
    keys: int = 0
    dice: int = 0

# ---------- Classe Game ----------

class Game:
    """
    Orchestrateur principal :
    - États de jeu : PLAY | PICK | END
    - Entrées clavier (sélection/validation/annulation)
    - Logique de déplacement, tirage et placement de salle
    - Rendu via ui.py
    - Effets :
        * BLINK pour la direction (porte) pendant PLAY
        * PULSE pour le cadre sélectionné pendant PICK
    """
    def __init__(self, manor, player):
        """Initialise Pygame, l'état du jeu et les valeurs par défaut."""
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Blue Prince 2D (simplifié)")
        self.clock = pygame.time.Clock()
        self.running = True

        # Références vers les données (prêtes à être remplacées par A/B)
        self.manor = manor
        self.player = player

        # États
        self.state = "PLAY"          # PLAY | PICK | END
        self.message = ""

        # Sélection direction (PLAY)
        self.pending_dir = None       # "N","S","E","W" ou None

        # Sélection de pièces (PICK)
        self.pick_rooms = []
        self.pick_idx = 0
        self._pending_dir = None      # direction qui a déclenché l'ouverture
        self._pending_dest = None     # case destination (r,c) où placer la salle

        # Effets visuels : blink (bool visible) & pulse (phase 0..1)
        self._blink_visible = True
        self._pulse_phase = 0.0

        # Fin de partie
        self.win = False

    # ---------- Gestion des effets visuels ----------
    def update_blink(self):
        """
        Met à jour la visibilité du clignotement (ON/OFF) en fonction du temps.
        """
        now = pygame.time.get_ticks()
        self._blink_visible = ((now // BLINK_PERIOD_MS) % 2) == 0

    def update_pulse(self):
        """
        Met à jour la phase du pulsing (0..1) en fonction du temps.
        """
        now = pygame.time.get_ticks()
        self._pulse_phase = (now % PULSE_PERIOD_MS) / PULSE_PERIOD_MS

    # ---------- Gestion des entrées ----------
    def handle_play_input(self, event):
        """
        Gestion des touches durant l'état PLAY :
        - Z/Q/S/D : sélectionner une direction (sans bouger immédiatement)
        - Entrée  : valider la direction sélectionnée et tenter le mouvement
        - Échap/Espace : annuler la sélection en cours
        """
        if event.type != pygame.KEYDOWN:
            return

        # Choisir une direction (ne bouge pas immédiatement)
        if event.key in (KEY_UP, KEY_LEFT, KEY_DOWN, KEY_RIGHT):
            self.pending_dir = {
                KEY_UP: "N", KEY_LEFT: "W", KEY_DOWN: "S", KEY_RIGHT: "E"
            }[event.key]
            self.message = (
                f"Direction sélectionnée: {self.pending_dir}. "
                "Entrée pour valider, Échap/Espace pour annuler."
            )
            return

        # Valider la direction choisie
        if event.key == KEY_CONFIRM:
            if self.pending_dir:
                dir_ = self.pending_dir
                self.pending_dir = None
                self.try_move(dir_)
            else:
                self.message = "Aucune direction sélectionnée."
            return

        # Annuler la sélection
        if event.key == KEY_CANCEL or event.key == KEY_USE:
            self.pending_dir = None
            self.message = "Sélection annulée."
            return

    def handle_pick_input(self, event):
        """
        Gestion des touches durant l'état PICK (sélection de salle) :
        - ← / → (ou A / E) : naviguer parmi les 3 cartes
        - Entrée : valider la carte sélectionnée et placer la salle
        - Échap  : annuler et revenir à PLAY (rien n'est consommé)
        """
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.pick_idx = (self.pick_idx - 1) % len(self.pick_rooms)
        elif event.key in (pygame.K_RIGHT, pygame.K_e):
            self.pick_idx = (self.pick_idx + 1) % len(self.pick_rooms)
        elif event.key == KEY_CONFIRM:
            self.confirm_pick()
        elif event.key == KEY_CANCEL:
            # Quitter le menu sans rien poser
            self.pick_rooms = []
            self.state = "PLAY"
            self.message = "Sélection de salle annulée. Choisis une autre porte."
            # on nettoie les pendings pour éviter des effets indésirables
            self.pending_dir = None
            self._pending_dir = None
            self._pending_dest = None

    def handle_end_input(self, event):
        """
        Gestion des touches durant l'état END :
        - Entrée : relancer une nouvelle partie.
        """
        if event.type == pygame.KEYDOWN and event.key == KEY_CONFIRM:
            # Restart : on repart sur un nouveau manoir/joueur mock
            self.__init__(MockManor(), PlayerState(*self.manor.start))

    # ---------- Logique de jeu ----------
    def try_move(self, dir_):
        """
        Tente de se déplacer dans la direction 'dir_'.
        - Si la destination est hors-grille : message 'Mur.'
        - Si la destination est vide (pas de salle) : on ouvre le menu PICK (tirage de 3 salles)
        - Si la salle existe : on consomme 1 pas, on entre, et on teste la fin.
        """
        if self.player.steps <= 0:
            self.lose("Plus de pas !")
            return

        dest = self.manor.valid_move((self.player.r, self.player.c), dir_)
        if not dest:
            self.message = "Mur."
            return

        nr, nc = dest
        target_room = self.manor.get_room(nr, nc)

        if target_room is None:
            # Ouvrir une porte -> écran tirage 3 pièces
            self.roll_three_rooms(dir_, dest)
            return

        # Déplacement dans une pièce déjà connue
        self.player.steps -= 1
        self.player.r, self.player.c = nr, nc
        self.message = f"Tu avances vers {dir_}."
        self.check_end((nr, nc))

    def roll_three_rooms(self, dir_, dest_rc):
        """
        Tire 3 salles (mock) et passe à l'état PICK.
        - Garantit qu'au moins une salle coûte 0 gemme.
        - Stocke la direction et la destination 'pendantes' pour la pose.
        """
        pool = [
            MockRoom("Coffre",   "VLT", "blue",   [opposite(dir_)],            gem_cost=3),
            MockRoom("Véranda",  "VRN", "green",  [opposite(dir_), "E"],       gem_cost=2),
            MockRoom("Couloir",  "HW",  "orange", [opposite(dir_), "N", "S"],  gem_cost=0),
            MockRoom("Chambre",  "BED", "purple", [opposite(dir_)],            gem_cost=0),
            MockRoom("Cave",     "CLR", "red",    [opposite(dir_)],            gem_cost=1),
            MockRoom("Boutique", "SHP", "yellow", [opposite(dir_), "S"],       gem_cost=0),
        ]
        random.shuffle(pool)
        pick = pool[:3]
        if all(r.gem_cost > 0 for r in pick):
            pick[0].gem_cost = 0

        self.pick_rooms = pick
        self.pick_idx = 0
        self.state = "PICK"
        self._pending_dir = dir_
        self._pending_dest = dest_rc

    def confirm_pick(self):
        """
        Valide la salle sélectionnée :
        - Vérifie le coût en gemmes
        - Pose la salle sur la destination pendante
        - Consomme 1 pas pour 'entrer' dans la salle posée
        - Revient à PLAY et teste la fin
        """
        chosen = self.pick_rooms[self.pick_idx]
        if chosen.gem_cost > self.player.gems:
            self.message = "Pas assez de gemmes."
            return

        # Payer et poser
        self.player.gems -= chosen.gem_cost
        r, c = self._pending_dest
        self.manor.set_room(r, c, chosen)
        self.state = "PLAY"
        self.message = f"Ajouté: {chosen.name}"

        # Entrer dans la nouvelle pièce = 1 pas
        self.player.steps -= 1
        self.player.r, self.player.c = r, c
        self.check_end((r, c))

        # Nettoyage
        self.pick_rooms = []
        self._pending_dir = None
        self._pending_dest = None

    def check_end(self, rc):
        """
        Détermine si la partie est terminée :
        - Victoire : si on atteint l'antichambre.
        - Défaite : si les pas tombent à 0 ou moins.
        """
        if rc == self.manor.antechamber_rc:
            self.win = True
            self.state = "END"
        elif self.player.steps <= 0:
            self.lose("Plus de pas !")

    def lose(self, cause: str):
        """
        Déclare la défaite avec un message explicite,
        puis bascule sur l'écran END.
        """
        self.win = False
        self.message = cause
        self.state = "END"

    # ---------- Boucle principale ----------
    def run(self):
        """
        Boucle de jeu :
        - Lecture des événements
        - Mise à jour des effets visuels (blink & pulse)
        - Rendu de la grille, du joueur, de l'UI et des écrans
        """
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.state == "PLAY":
                    self.handle_play_input(event)
                elif self.state == "PICK":
                    self.handle_pick_input(event)
                elif self.state == "END":
                    self.handle_end_input(event)

            # Met à jour les effets visuels
            self.update_blink()   # pour l'indicateur de direction (porte)
            self.update_pulse()   # pour le cadre du menu de sélection

            # Rendu principal
            self.screen.fill(BG)
            draw_grid(self.screen, self.manor)
            draw_player(self.screen, (self.player.r, self.player.c))

            # Indicateur de direction en mode clignotement (pendant PLAY)
            if self.state == "PLAY":
                draw_direction_hint(
                    self.screen,
                    (self.player.r, self.player.c),
                    self.pending_dir,
                    self._blink_visible
                )

            # HUD
            draw_hud(self.screen, self.player, self.message)

            # Écrans d'état
            if self.state == "PICK":
                draw_pick_screen_pulse(self.screen, self.pick_rooms, self.pick_idx, self._pulse_phase)
            if self.state == "END":
                draw_end_screen(self.screen, win=self.win)

            pygame.display.flip()
            self.clock.tick(FPS)

# ---------- Utilitaires ----------

def opposite(d: str) -> str:
    """Retourne l'opposé d'une direction ('N'↔'S', 'E'↔'W')."""
    return {"N": "S", "S": "N", "E": "W", "W": "E"}[d]

# ---------- Lancement ----------

if __name__ == "__main__":
    random.seed()
    manor = MockManor()
    player = PlayerState(*manor.start)
    Game(manor, player).run()
