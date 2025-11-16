# game.py
import pygame, random
from typing import Dict, Tuple, List, Set

from sprites import load_tileset  # pas utilisé directement mais OK
from constants import ITEMS_TILESET_PATH
from constants import *
from manoir import Manor
from room import Room, RoomType
from room_data import ALL_ROOMS, clone_room   # adapte le nom si ton fichier s'appelle rooms_data.py
from door import DoorLockLevel
from player import Player
from random_manager import RandomManager
from constants import ROOMS_TILESET_PATH

from items import (
    Food, Gem, Key, Die,
    Shovel, Hammer, LockpickKit,
    MetalDetector, RabbitFoot,
)

"""
Ce module gère :
- la boucle de jeu principale,
- les états (PLAY, PICK, END),
- les entrées clavier (ZQSD, Entrée, Échap, T, E),
- la logique de déplacement et de placement de salles,
- l'affichage via ui.py,
- la connexion avec le joueur (Player + Inventory) et RandomManager.

Fonctionnalités :
- Sélection de PORTE (direction) : clignotement ON/OFF (blink).
- Menu de sélection de SALLE : pulsing sur la carte sélectionnée.
- Pioche FINIE de salles, avec salles spéciales uniques.
- Fouille de salle (T) limitée à une fois par case.
- Interactions contextuelles (E) : creuser avec la pelle, marteau à l'entrée, etc.
"""

from ui import (
    draw_grid, draw_player, draw_hud,
    draw_pick_screen_pulse, draw_end_screen,
    draw_direction_hint
)

# ---------- Classe Game ----------

class Game:
    """
    Orchestrateur principal du jeu.
    """

    def __init__(self, manor: Manor, player: Player):
        """Initialise Pygame, l'état du jeu et les valeurs par défaut."""
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Blue Prince 2D (simplifié)")
        self.clock = pygame.time.Clock()
        self.running = True

        # Charger les icônes d'items (tileset 32x32 → affichage 32x32 dans le HUD)
        self.item_icons = self._load_item_icons()

        # Tileset graphique des salles
        self.room_tiles = self._load_room_tiles()

        # Références vers les données
        self.manor = manor
        self.player = player
        self.rng = RandomManager(self.player)

        # ---------- Pioche FINIE de salles (par type) ----------
        # Templates accessibles par nom
        self.room_templates: Dict[str, Room] = {tpl.name: tpl for tpl in ALL_ROOMS}

        # Salles qui doivent être uniques dans la pioche
        # (par ex. Veranda = pelle, Suite royale = détecteur)
        UNIQUE_ROOM_NAMES = {"Veranda", "Suite royale"}

        # Stock : nombre de copies restantes par nom de salle
        self.room_stock: Dict[str, int] = {}
        for tpl in ALL_ROOMS:
            if tpl.name in UNIQUE_ROOM_NAMES:
                self.room_stock[tpl.name] = 1      # unique
            else:
                self.room_stock[tpl.name] = 3      # 3 copies par défaut (ajuste si tu veux)

        # Associer les sprites aux salles
        self.init_room_images()

        # États
        self.state = "PLAY"          # PLAY | PICK | END
        self.message = ""

        # Sélection direction (PLAY)
        self.pending_dir: str | None = None  # "N","S","E","W" ou None

        # Sélection de pièces (PICK)
        self.pick_rooms: List[Room] = []
        self.pick_idx = 0
        self._pending_dir: str | None = None     # direction qui a déclenché l'ouverture
        self._pending_dest: Tuple[int, int] | None = None    # case destination (r,c)
        self._pending_key: Tuple[int, int, str] | None = None

        # Mémorisation des offres par porte :
        # { (src_r, src_c, dir_) : {"rooms": [Room,...], "dest": (r,c)} }
        self.door_offers: dict[tuple[int, int, str], dict] = {}

        # Effets visuels : blink (bool visible) & pulse (phase 0..1)
        self._blink_visible = True
        self._pulse_phase = 0.0

        # Fin de partie
        self.win = False

        # Salles déjà fouillées (pour limiter T à 1 fois par case)
        self.searched_rooms: Set[Tuple[int, int]] = set()

        # Cases déjà creusées (pour E + pelle, entrée, etc.)
        self.dug_rooms: Set[Tuple[int, int]] = set()


    def use_first_food(self):
        """
        Cherche la première nourriture (Food) dans l'inventaire du joueur
        et l'utilise. Si aucune nourriture n'est disponible, affiche un message.
        Touche associée : F (en mode PLAY).
        """
        inv = self.player.inventory

        from items import Food  # import local pour éviter les imports circulaires

        # On cherche la première Food dans la liste des items
        idx_food = None
        for i, item in enumerate(inv.items):
            if isinstance(item, Food):
                idx_food = i
                break

        if idx_food is None:
            self.message = "Tu n'as pas de nourriture dans ton inventaire."
            return

        # On récupère l'objet pour le message AVANT de l'utiliser (il sera supprimé si consommé)
        food_item = inv.items[idx_food]
        name = food_item.name
        steps = food_item.steps_restored

        inv.use_item(idx_food, self.player)
        self.message = f"Tu manges {name} (+{steps} pas)."
    # ---------- Chargement des assets ----------

    def _load_item_icons(self) -> dict:
        """
        Charge le tileset des items HUD.png (4x4 icônes)
        et prépare un dictionnaire d'icônes utilisables dans le HUD.
        Chaque icône est redimensionnée en 32x32.
        """
        try:
            sheet = pygame.image.load(ITEMS_TILESET_PATH).convert_alpha()
        except Exception as e:
            print("Erreur chargement tileset items:", e)
            return {}

        sheet_w, sheet_h = sheet.get_size()

        # On sait que c'est une grille 4x4
        cols = 4
        rows = 4
        tile_src_w = sheet_w // cols
        tile_src_h = sheet_h // rows

        # Taille d'affichage dans le HUD
        dst_size = 32

        tiles = []
        for row in range(rows):
            for col in range(cols):
                x = col * tile_src_w
                y = row * tile_src_h
                rect = pygame.Rect(x, y, tile_src_w, tile_src_h)
                sub = sheet.subsurface(rect)
                sub = pygame.transform.smoothscale(sub, (dst_size, dst_size))
                tiles.append(sub)

        print("DEBUG: tileset HUD chargé, nb de tuiles =", len(tiles))  # devrait être 16

        def safe(idx):
            return tiles[idx] if 0 <= idx < len(tiles) else None

        icons = {}

        # Mapping en fonction de ta grille HUD.png
        icons["gems"]          = safe(0)   # diamant
        icons["gold"]          = safe(1)   # pièce d'or
        icons["dice"]          = safe(2)   # dé
        icons["steps"]         = safe(12)  # cœur bouclier = "vie/pas"

        icons["food"]          = safe(4)   # pomme (nourriture principale)

        icons["keys"]          = safe(13)  # clé
        icons["perm_shovel"]   = safe(8)   # pelle
        icons["perm_hammer"]   = safe(9)   # marteau
        icons["perm_lockpick"] = safe(10)  # sac/kit
        icons["perm_detector"] = safe(11)  # détecteur
        icons["perm_rabbit"]   = safe(15)  # patte de lapin

        return icons

    def _load_room_tiles(self) -> list:
        """
        Charge le tileset des salles (Salle.png) et le découpe en 20 sous-images.
        L'image actuelle est une grille 4 colonnes x 5 lignes.

        On découpe chaque cellule, on enlève un petit bord pour éviter les traits,
        puis on redimensionne en TILE x TILE.
        """
        tiles = []
        try:
            sheet = pygame.image.load(ROOMS_TILESET_PATH).convert_alpha()
        except Exception as e:
            print("Erreur chargement tileset salles:", e)
            return tiles

        sheet_w, sheet_h = sheet.get_size()
        cols, rows = 4, 5      # 4 colonnes, 5 lignes
        cell_w = sheet_w // cols
        cell_h = sheet_h // rows

        # On enlève un petit bord dans chaque case pour ne pas prendre les lignes de séparation
        margin_x = 4
        margin_y = 4
        inner_w = cell_w - 2 * margin_x
        inner_h = cell_h - 2 * margin_y

        for row in range(rows):
            for col in range(cols):
                x = col * cell_w + margin_x
                y = row * cell_h + margin_y
                rect = pygame.Rect(x, y, inner_w, inner_h)
                sub = sheet.subsurface(rect)
                sub = pygame.transform.smoothscale(sub, (TILE, TILE))
                tiles.append(sub)

        print("DEBUG: tileset salles chargé, nb =", len(tiles))
        return tiles

    def init_room_images(self):
        """
        Associe à chaque Room une image en fonction de son tile_index.
        - Pour les templates de room_data.ALL_ROOMS
        - Pour les salles déjà présentes dans la grille du manoir
        """
        if not self.room_tiles:
            return

        from room_data import ALL_ROOMS  # adapte si besoin

        # Templates
        for tpl in ALL_ROOMS:
            idx = getattr(tpl, "tile_index", -1)
            if 0 <= idx < len(self.room_tiles):
                tpl.image = self.room_tiles[idx]

        # Salles déjà placées dans la grille (Entrée, Antechambre)
        for r in range(self.manor.rows):
            for c in range(self.manor.cols):
                room = self.manor.get_room(r, c)
                if room is None:
                    continue
                idx = getattr(room, "tile_index", -1)
                if 0 <= idx < len(self.room_tiles):
                    room.image = self.room_tiles[idx]
                
    def is_player_blocked(self) -> bool:
        """
        Retourne True si le joueur ne peut plus progresser :
        - Aucun déplacement possible vers une salle déjà posée
        - Et aucune extension possible (case vide atteignable) parce qu'il
          ne reste plus de salles dans la pioche.
        """

        # Si déjà plus de pas, on considère que c'est une situation de défaite,
        # mais check_end s'en charge directement.
        if self.player.steps <= 0:
            return True

        from_rc = (self.player.r, self.player.c)

        # On regarde les 4 directions possibles
        for dir_ in ("N", "S", "E", "W"):
            dest = self.manor.valid_move(from_rc, dir_)
            if not dest:
                continue

            nr, nc = dest
            room = self.manor.get_room(nr, nc)

            if room is not None:
                # Il y a déjà une salle : on pourra au moins s'y déplacer
                return False

            # Case vide : on peut potentiellement poser une salle ici
            # seulement s'il reste des salles dans la pioche.
            if hasattr(self, "room_deck") and len(self.room_deck) > 0:
                return False

        # Si on arrive ici : aucune salle voisine et aucune extension possible
        return True

    # ---------- Gestion des effets visuels ----------

    def update_blink(self):
        """Met à jour la visibilité du clignotement ON/OFF pour l'indicateur de direction."""
        now = pygame.time.get_ticks()
        self._blink_visible = ((now // BLINK_PERIOD_MS) % 2) == 0

    def update_pulse(self):
        """Met à jour la phase du pulsing (0..1) pour le cadre de sélection de salle."""
        now = pygame.time.get_ticks()
        self._pulse_phase = (now % PULSE_PERIOD_MS) / PULSE_PERIOD_MS

    # ---------- Gestion des entrées ----------

    def handle_play_input(self, event: pygame.event.Event):
        """
        Gestion des touches durant l'état PLAY :
        - Z/Q/S/D : sélectionner une direction (sans bouger immédiatement)
        - Entrée  : valider la direction sélectionnée et tenter le mouvement
        - Échap/Espace : annuler la sélection en cours
        - T : fouiller la salle actuelle (une seule fois par case)
        - E : interaction contextuelle (pelle dans jardin / entrée, etc.)
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
        # Valider la direction choisie
        elif event.key == KEY_CONFIRM:
            if self.pending_dir:
                dir_ = self.pending_dir
                self.pending_dir = None
                self.try_move(dir_)
            else:
                self.message = "Aucune direction sélectionnée."

        # Annuler la sélection
        elif event.key == KEY_CANCEL or event.key == KEY_USE:
            self.pending_dir = None
            self.message = "Sélection annulée."

        # Fouille de la salle (une seule fois par case)
        elif event.key == pygame.K_t:
            self.search_current_room()
        
        #manger
        elif event.key == pygame.K_f:
             self.use_first_food()

        # Interaction contextuelle (pelle, marteau, etc.)
        elif event.key == pygame.K_e:
            self.interact_current_room()
 
    def handle_pick_input(self, event):
        """
        Gestion des touches durant l'état PICK (sélection de salle) :
        - ← / → (ou A / E) : naviguer parmi les 3 cartes
        - Entrée : valider la carte sélectionnée et placer la salle
        - Échap  : annuler et revenir à PLAY (rien n'est consommé)
        - R      : relancer le tirage de 3 salles pour cette porte (consomme 1 dé)
        """
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_LEFT, pygame.K_a):
            if self.pick_rooms:
                self.pick_idx = (self.pick_idx - 1) % len(self.pick_rooms)

        elif event.key in (pygame.K_RIGHT, pygame.K_e):
            if self.pick_rooms:
                self.pick_idx = (self.pick_idx + 1) % len(self.pick_rooms)

        elif event.key == KEY_CONFIRM:
            if self.pick_rooms:
                self.confirm_pick()

        elif event.key == KEY_CANCEL:
            # Quitter le menu sans rien poser
            self.pick_rooms = []
            self.state = "PLAY"
            self.message = "Sélection de salle annulée. Choisis une autre porte."
            # On nettoie l'état temporaire, mais on garde door_offers pour retrouver l'offre
            self.pending_dir = None
            self._pending_dir = None
            self._pending_dest = None
            self._pending_key = None

        elif event.key == pygame.K_r:
            # Reroll : relancer le tirage de salles pour cette porte si on a un dé
            inv = self.player.inventory
            if not inv.can_reroll_rooms():
                self.message = "Pas de dé pour relancer le tirage."
                return

            if self._pending_dir is None or self._pending_dest is None or self._pending_key is None:
                # Sécurité : on ne devrait pas arriver ici, mais on évite un crash
                self.message = "Impossible de relancer ici."
                return

            if not inv.spend_die():
                self.message = "Pas de dé pour relancer le tirage."
                return

            # On relance un tirage de salles pour la même porte
            self.message = "Tu relances le tirage (1 dé consommé)."
            self.roll_three_rooms(self._pending_dir, self._pending_dest, self._pending_key)

    def handle_end_input(self, event: pygame.event.Event):
        """
        Gestion des touches durant l'état END :
        - Entrée : relancer une nouvelle partie.
        """
        if event.type == pygame.KEYDOWN and event.key == KEY_CONFIRM:
            # Restart : nouveau manoir + nouveau joueur
            new_manor = Manor()
            new_player = Player(*new_manor.start)
            self.__init__(new_manor, new_player)

    # ---------- Logique de jeu : déplacement ----------

    def try_move(self, dir_: str):
        """
        Tente de se déplacer dans la direction 'dir_'.

        Étapes :
        1) Vérifier qu'il reste des pas.
        2) Demander au manoir si un déplacement géométrique est possible (valid_move).
           -> prend en compte les portes dessinées sur les salles (room.doors).
        3) Gérer la porte verrouillée éventuelle (Door + inventaire).
        4) Si la case cible est vide : ouvrir le menu PICK (tirage de salles).
        5) Sinon : consommer 1 pas, se déplacer, tester la fin.
        """
        # 1) Pas restants
        if self.player.steps <= 0:
            self.lose("Plus de pas !")
            return

        src_rc = (self.player.r, self.player.c)

        # 2) Vérification géométrique via le manoir (porte + limites)
        dest = self.manor.valid_move(src_rc, dir_)
        if not dest:
            self.message = "Mur."
            return

        # 3) Porte verrouillée éventuelle (Door)
        door = self.manor.ensure_door(src_rc, dir_)
        if door is not None and not door.is_open:
            # On tente d'ouvrir la porte avec l'inventaire du joueur
            if not door.open(self.player.inventory):
                # Ouverture impossible : on affiche un message selon le niveau
                if door.lock_level == DoorLockLevel.LOCKED:
                    self.message = "Porte verrouillée. Il te faut une clé ou un kit."
                elif door.lock_level == DoorLockLevel.DOUBLE_LOCKED:
                    self.message = "Porte à double tour. Il te faut une clé."
                else:
                    self.message = "Impossible d'ouvrir cette porte."
                return
            else:
                # Succès de l'ouverture (clé consommée si nécessaire)
                self.message = "Tu ouvres la porte."

        # 4) On peut maintenant gérer la case cible
        nr, nc = dest
        target_room = self.manor.get_room(nr, nc)

        if target_room is None:
            # Case vide : ouverture de porte vers une zone inexplorée -> menu PICK
            door_key = (src_rc[0], src_rc[1], dir_)

            # Si une offre existe déjà pour cette porte, on la réutilise.
            if door_key in self.door_offers:
                offer = self.door_offers[door_key]
                self.pick_rooms = offer["rooms"]
                self.pick_idx = 0
                self.state = "PICK"
                self._pending_dir = dir_
                self._pending_dest = offer["dest"]
                self._pending_key = door_key
                self.message = "Choisis une pièce pour cette porte."
                return

            # Sinon, tirage d'un nouveau trio de salles.
            self.roll_three_rooms(dir_, dest, door_key)
            return

        # 5) Déplacement dans une pièce déjà connue
        self.player.steps -= 1
        self.player.r, self.player.c = nr, nc
        self.message = f"Tu avances vers {dir_}."
        self.check_end((nr, nc))

    # ---------- Pioche FINIE de salles ----------

    def roll_three_rooms(self, dir_: str, dest_rc: tuple[int, int], door_key: tuple[int, int, str]):
        """
        Tire jusqu'à 3 salles compatibles avec dest_rc / dir_, à partir d'une
        pioche FINIE :
        - self.room_templates : modèles de salles
        - self.room_stock     : nombre de copies restantes par nom

        On ne consomme la pioche que LORSQU'ON POSE vraiment une salle
        (dans confirm_pick), pas au moment de l'offre.
        """
        # 1) On part des templates qui ont encore du stock > 0
        available_templates = [
            tpl for tpl in self.room_templates.values()
            if self.room_stock.get(tpl.name, 0) > 0
        ]

        # 2) On garde seulement celles qui peuvent être placées à cet endroit
        candidates: list[Room] = []
        for tpl in available_templates:
            ghost = clone_room(tpl)
            if self.manor.can_place_room(ghost, dest_rc, dir_):
                candidates.append(tpl)

        if not candidates:
            self.message = "Aucune salle ne peut être placée ici (pioche épuisée)."
            return

        # 3) On mélange les candidats et on en prend jusqu'à 3
        random.shuffle(candidates)
        pick_templates = candidates[:3]

        # 4) Les salles proposées sont des COPIES indépendantes
        pick_rooms = [clone_room(tpl) for tpl in pick_templates]

        # 5) On force au moins une salle à 0 gemme pour ne pas bloquer le joueur
        if pick_rooms and all(room.gem_cost > 0 for room in pick_rooms):
            pick_rooms[0].gem_cost = 0

        # 6) On mémorise cette offre pour cette porte
        self.door_offers[door_key] = {
            "rooms": pick_rooms,
            "dest": dest_rc,
        }

        # 7) On entre en mode PICK avec ces salles
        self.pick_rooms = pick_rooms
        self.pick_idx = 0
        self.state = "PICK"
        self._pending_dir = dir_
        self._pending_dest = dest_rc
        self._pending_key = door_key
        self.message = "Choisis une pièce pour cette porte."

    def confirm_pick(self):
        """
        Valide la salle sélectionnée :
        - Vérifie le coût en gemmes
        - Pose la salle sur la destination pendante
        - Consomme 1 pas pour 'entrer' dans la salle posée
        - Retire UNE copie de ce type de salle de la pioche
        - Revient à PLAY et teste la fin
        - Nettoie l'offre associée à cette porte (door_offers)
        """
        chosen = self.pick_rooms[self.pick_idx]
        if chosen.gem_cost > self.player.gems:
            self.message = "Pas assez de gemmes."
            return

        # Payer
        self.player.gems -= chosen.gem_cost

        # Poser la salle
        r, c = self._pending_dest
        self.manor.set_room(r, c, chosen)

        # Consommer UNE copie de ce type dans la pioche
        name = getattr(chosen, "name", None)
        if name is not None and name in self.room_stock:
            if self.room_stock[name] > 0:
                self.room_stock[name] -= 1

        self.state = "PLAY"
        self.message = f"Ajouté: {chosen.name}"

        # Entrer dans la nouvelle pièce = 1 pas
        self.player.steps -= 1
        self.player.r, self.player.c = r, c
        self.check_end((r, c))

        # Nettoyage de l'offre liée à cette porte
        if self._pending_key is not None:
            self.door_offers.pop(self._pending_key, None)

        # Nettoyage de l'état temporaire
        self.pick_rooms = []
        self._pending_dir = None
        self._pending_dest = None
        self._pending_key = None

    # ---------- Fin de partie ----------

    def check_end(self, rc: tuple[int, int]):
        """
        Détermine si la partie est terminée :

        - Victoire : si on atteint l'antichambre.
        - Défaite : 
            * si les pas tombent à 0 ou moins,
            * ou si le manoir est bloqué (plus aucune salle accessible
              ou posable, et pioche éventuellement vide).
        """
        # 1) Victoire : on est arrivé à l'antichambre
        if rc == self.manor.antechamber_rc:
            self.win = True
            self.state = "END"
            self.message = "Tu atteins l'antichambre : victoire !"
            return

        # 2) Défaite : plus de pas
        if self.player.steps <= 0:
            self.lose("Plus de pas !")
            return

        # 3) Défaite : manoir bloqué (plus aucun chemin possible)
        if self.is_player_blocked():
            if hasattr(self, "room_deck") and len(self.room_deck) == 0:
                self.lose("Le manoir est bloqué et il n'y a plus de salles dans la pioche.")
            else:
                self.lose("Le manoir est bloqué : plus aucun chemin possible.")

    def lose(self, cause: str):
        """Déclare la défaite avec un message explicite, puis passe à END."""
        self.win = False
        self.message = cause
        self.state = "END"

    # ---------- Fouille & interactions de salles ----------
    def search_current_room(self):
        """
        Fouille la salle actuelle (touche T).
        - Limité à une fois par case.
        - Effets spéciaux selon le type / nom de la salle.
        """
        r, c = self.player.r, self.player.c
        room = self.manor.get_room(r, c)

        if room is None:
            self.message = "Rien à fouiller ici."
            return

        if (r, c) in self.searched_rooms:
            self.message = "Cette salle a déjà été fouillée."
            return

        self.searched_rooms.add((r, c))
        inv = self.player.inventory

        # ---- Effets spéciaux ----

        # Jardin → nourriture ou patte de lapin
        if room.name == "Jardin intérieur":
            if not inv.has_rabbit_foot() and random.random() < 0.3:
                inv.add_item(RabbitFoot())
                self.message = "Tu trouves une patte de lapin porte-bonheur."
            else:
                inv.add_item(Food("Fruits frais", 5))
                self.message = "Tu trouves de la nourriture fraîche (+5 pas)."
            return

        # Salle des coffres → loot massif
        if room.name == "Salle des coffres":
            inv.add_gems(2)
            inv.add_gold(5)
            inv.add_keys(1)
            self.message = "Tu ouvres un coffre rempli : +2 gemmes, +5 or, +1 clé."
            return

        # Suite royale → détecteur ou repos
        if room.name == "Suite royale":
            if not inv.has_detector():
                inv.add_item(MetalDetector())
                self.message = "Tu trouves un détecteur de métaux !"
            else:
                self.player.steps += 5
                self.message = "Tu te reposes dans le lit royal (+5 pas)."
            return

        # Chambre d’ami → détecteur unique
        if room.name == "Chambre d'ami":
            if not inv.has_detector():
                inv.add_item(MetalDetector())
                self.message = "Tu trouves un détecteur de métaux sous un oreiller !"
            else:
                inv.add_item(Food("Encas", 3))
                self.message = "Tu trouves un encas (+3 pas)."
            return

        # Cellule → lockpick unique
        if room.name == "Cellule":
            if not inv.has_lockpick():
                inv.add_item(LockpickKit())
                self.message = "Tu trouves un kit de crochetage caché."
            else:
                inv.add_keys(1)
                self.message = "Tu récupères une petite clé."
            return

        # Marchand ambulant → patte de lapin possible
        if room.name == "Marchand ambulant":
            if not inv.has_rabbit_foot():
                inv.add_item(RabbitFoot())
                self.message = "Le marchand te donne une patte de lapin."
            else:
                inv.add_gold(1)
                self.message = "Il te donne une pièce d'or."
            return

        # Salle piégée
        if room.room_type == RoomType.TRAP:
            self.player.steps = max(0, self.player.steps - 3)
            self.message = "Un piège se déclenche ! (-3 pas)"
            return

        # ---- Fouille par défaut : item consommable ----
        item = self.rng.draw_consumable()
        inv = self.player.inventory

        if isinstance(item, Food):
            inv.add_item(item)
            self.message = f"Tu trouves de la nourriture : {item.name}"
        elif isinstance(item, Gem):
            inv.add_gems(1)
            self.message = "Tu trouves une gemme."
        elif isinstance(item, Key):
            inv.add_keys(1)
            self.message = "Tu trouves une clé."
        elif isinstance(item, Die):
            inv.add_dice(1)
            self.message = "Tu trouves un dé."
        else:
            inv.add_item(item)
            self.message = f"Tu trouves un objet : {item.name}"

    def interact_current_room(self):
        """
        Interaction contextuelle (touche E) :
        - Jardin + pelle : creuser pour un objet aléatoire (une fois par case).
        - Entrée + pelle : creuser pour un marteau (unique).
        - Sinon : message 'Rien de spécial'.
        """
        r, c = self.player.r, self.player.c
        room = self.manor.get_room(r, c)

        if room is None:
            self.message = "Rien de spécial ici."
            return

        inv = self.player.inventory

        # Entrée : marteau caché si on a une pelle
        if room.room_type == RoomType.ENTRANCE:
            if not inv.has_shovel():
                self.message = "Le sol semble meuble, une pelle serait utile (E)."
                return

            if (r, c) in self.dug_rooms:
                if inv.has_hammer():
                    self.message = "Tu as déjà trouvé le marteau ici."
                else:
                    self.message = "Tu as déjà creusé ici."
                return

            # On creuse
            self.dug_rooms.add((r, c))
            if not inv.has_hammer():
                inv.add_item(Hammer())
                self.message = "Tu déterres un vieux marteau !"
            else:
                self.message = "Tu ne trouves plus rien d'utile."

            return

        # Jardin : creuser avec pelle
        if room.name == "Jardin intérieur":
            if not inv.has_shovel():
                self.message = "Tu pourrais creuser ici avec une pelle (E)."
                return

            if (r, c) in self.dug_rooms:
                self.message = "Tu as déjà creusé dans ce jardin."
                return

            self.dug_rooms.add((r, c))
            # Petit loot aléatoire
            roll = random.random()
            if roll < 0.4:
                inv.add_gems(1)
                self.message = "Tu déterres une gemme."
            elif roll < 0.7:
                inv.add_item(Food("Conserves enterrées", steps_restored=4))
                self.message = "Tu trouves des conserves (+4 pas)."
            else:
                inv.add_dice(1)
                self.message = "Tu déterres un vieux dé."
            return

        # Veranda : endroit logique où on peut obtenir la pelle en fouille (géré dans search)
        if room.name == "Veranda":
            if not inv.has_shovel():
                self.message = "Une pelle traîne probablement ici... fouille la salle (T)."
            else:
                self.message = "Rien de plus à faire ici."
            return

        # Boutique / Marchand : pour l'instant, pas d'UI de shop avancée → simple message.
        if room.name in ("Boutique", "Marchand ambulant"):
            if self.player.gold <= 0:
                self.message = "Tu n'as pas d'or pour acheter quelque chose."
            else:
                self.message = "Ici, tu pourras plus tard acheter des objets (WIP)."
            return

        # Par défaut
        self.message = "Rien de spécial à faire ici."

    # ---------- Intégration RandomManager : tirage de test (optionnel) ----------

    def test_draw_consumable(self):
        """
        Ancienne méthode de test (non utilisée directement par les touches
        maintenant que T fouille la salle).
        On la garde pour debug éventuel.
        """
        item = self.rng.draw_consumable()
        inv = self.player.inventory

        if isinstance(item, Food):
            inv.add_item(item)
            self.message = f"[TEST] Nourriture : {item.name}."
        elif isinstance(item, Gem):
            inv.add_gems(1)
            self.message = "[TEST] +1 gemme."
        elif isinstance(item, Key):
            inv.add_keys(1)
            self.message = "[TEST] +1 clé."
        elif isinstance(item, Die):
            inv.add_dice(1)
            self.message = "[TEST] +1 dé."
        else:
            inv.add_item(item)
            self.message = f"[TEST] Objet : {item.name}."

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
            self.update_blink()
            self.update_pulse()

            # Rendu principal
            self.screen.fill(BG)
            draw_grid(self.screen, self.manor)
            draw_player(self.screen, (self.player.r, self.player.c))

            # Salle actuelle (pour le HUD)
            current_room = self.manor.get_room(self.player.r, self.player.c)

            # Indicateur de direction en mode clignotement (pendant PLAY)
            if self.state == "PLAY":
                draw_direction_hint(
                    self.screen,
                    (self.player.r, self.player.c),
                    self.pending_dir,
                    self._blink_visible
                )

            # HUD (on passe aussi la salle actuelle)
            draw_hud(self.screen, self.player, self.message, self.item_icons, current_room)

            # Écrans d'état
            if self.state == "PICK":
                draw_pick_screen_pulse(
                    self.screen,
                    self.pick_rooms,
                    self.pick_idx,
                    self._pulse_phase
                )
            if self.state == "END":
                draw_end_screen(self.screen, win=self.win)

            pygame.display.flip()
            self.clock.tick(FPS)


# ---------- Lancement ----------

if __name__ == "__main__":
    random.seed()
    manoir = Manor()
    player = Player(*manoir.start)
    Game(manoir, player).run()