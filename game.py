# game.py
import pygame, random
from typing import Dict, Tuple, List, Set

from sprites import load_tileset  
from constants import ITEMS_TILESET_PATH, ROOMS_TILESET_PATH
from constants import *
from manoir import Manor
from room import Room, RoomType
from room_data import ALL_ROOMS, clone_room
from door import DoorLockLevel
from player import Player
from random_manager import RandomManager

from items import (
    Food, Gem, Key, Die,
    Shovel, Hammer, LockpickKit,
    MetalDetector, RabbitFoot,
)

from ui import (
    draw_grid, draw_player, draw_hud,
    draw_pick_screen_pulse, draw_end_screen,
    draw_direction_hint, draw_shop_window,
)


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
        self.room_templates: Dict[str, Room] = {tpl.name: tpl for tpl in ALL_ROOMS}

        UNIQUE_ROOM_NAMES = {"Veranda", "Suite royale"}
        self.room_stock: Dict[str, int] = {}
        for tpl in ALL_ROOMS:
            if tpl.name in UNIQUE_ROOM_NAMES:
                self.room_stock[tpl.name] = 1      # unique
            else:
                self.room_stock[tpl.name] = 3      # copies par défaut

        # Associer les sprites aux salles
        self.init_room_images()

        # États : PLAY | PICK | SHOP | END
        self.state = "PLAY"
        self.message = ""
        self.shop_message = ""  # messages spécifiques à la boutique

        # Sélection direction (PLAY)
        self.pending_dir: str | None = None  # "N","S","E","W" ou None

        # Sélection de pièces (PICK)
        self.pick_rooms: List[Room] = []
        self.pick_idx = 0
        self._pending_dir: str | None = None
        self._pending_dest: Tuple[int, int] | None = None
        self._pending_key: Tuple[int, int, str] | None = None

        # Mémorisation des offres par porte :
        self.door_offers: dict[tuple[int, int, str], dict] = {}

        # Effets visuels
        self._blink_visible = True
        self._pulse_phase = 0.0

        # Fin de partie
        self.win = False

        # Salles déjà fouillées (T)
        self.searched_rooms: Set[Tuple[int, int]] = set()

        # interagir (E)
        self.dug_rooms: Set[Tuple[int, int]] = set()

        # Effet d'entrée sur la salle de départ
        start_room = self.manor.get_room(self.player.r, self.player.c)
        if start_room is not None:
            self.apply_room_entry_effect(start_room)

    # ---------- Chargement des assets ----------

    def _load_item_icons(self) -> dict:
        try:
            sheet = pygame.image.load(ITEMS_TILESET_PATH).convert_alpha()
        except Exception as e:
            print("Erreur chargement tileset items:", e)
            return {}

        sheet_w, sheet_h = sheet.get_size()
        cols = 4
        rows = 4
        tile_src_w = sheet_w // cols
        tile_src_h = sheet_h // rows
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

        print("DEBUG: tileset HUD chargé, nb de tuiles =", len(tiles))

        def safe(idx):
            return tiles[idx] if 0 <= idx < len(tiles) else None

        icons = {}
        icons["gems"]          = safe(0)
        icons["gold"]          = safe(1)
        icons["dice"]          = safe(2)
        icons["steps"]         = safe(12)

        icons["food"]          = safe(4)

        icons["keys"]          = safe(13)
        icons["perm_shovel"]   = safe(8)
        icons["perm_hammer"]   = safe(9)
        icons["perm_lockpick"] = safe(10)
        icons["perm_detector"] = safe(11)
        icons["perm_rabbit"]   = safe(15)

        return icons

    def _load_room_tiles(self) -> list:
        tiles = []
        try:
            sheet = pygame.image.load(ROOMS_TILESET_PATH).convert_alpha()
        except Exception as e:
            print("Erreur chargement tileset salles:", e)
            return tiles

        sheet_w, sheet_h = sheet.get_size()
        cols, rows = 4, 5
        cell_w = sheet_w // cols
        cell_h = sheet_h // rows

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
        if not self.room_tiles:
            return

        from room_data import ALL_ROOMS

        for tpl in ALL_ROOMS:
            idx = getattr(tpl, "tile_index", -1)
            if 0 <= idx < len(self.room_tiles):
                tpl.image = self.room_tiles[idx]

        for r in range(self.manor.rows):
            for c in range(self.manor.cols):
                room = self.manor.get_room(r, c)
                if room is None:
                    continue
                idx = getattr(room, "tile_index", -1)
                if 0 <= idx < len(self.room_tiles):
                    room.image = self.room_tiles[idx]

    # ---------- Gestion des effets d'entrée de salle ----------

    def apply_room_entry_effect(self, room: Room) -> str | None:
        """
        Applique l'effet 'à l'entrée' d'une salle, une seule fois (room.visited).
        Retourne un petit texte à ajouter au message.
        """
        if room.visited:
            return None

        room.visited = True
        inv = self.player.inventory
        msg = None

        if room.short == "BED":
            self.player.steps += 2
            msg = "Tu te reposes un peu dans cette chambre (+2 pas)."

        elif room.short == "SUI":
            self.player.steps += 10
            msg = "Tu te reposes longuement dans la suite royale (+10 pas)."

        elif room.short == "VLT":
            inv.add_gold(2)
            inv.add_gems(1)
            msg = "Tu trouves quelques trésors dès l'entrée (+2 or, +1 gemme)."

        elif room.short == "TRS":
            inv.add_gold(2)
            inv.add_keys(1)
            inv.add_gems(1)
            msg = "Le sac déborde : +2 or, +1 clé, +1 gemme."

        elif room.short == "VRN":
            if not inv.has_shovel():
                inv.add_item(Shovel())
                msg = "Une pelle traîne ici : tu la prends."

        elif room.short == "TRP":
            dmg = 5
            if inv.has_hammer():
                dmg = 2
            self.player.steps = max(0, self.player.steps - dmg)
            msg = f"Un piège violent se déclenche (-{dmg} pas)."

        elif room.short == "CHN":
            dmg = 3
            if inv.has_hammer():
                dmg = 1
            self.player.steps = max(0, self.player.steps - dmg)
            msg = f"Des chaînes te ralentissent (-{dmg} pas)."

        return msg

    # ---------- Détection de blocage ----------

    def is_player_blocked(self) -> bool:
        """
        Retourne True si le joueur ne peut plus PROGRESSER :
        - Aucune nouvelle salle ne peut être posée autour de TOUTES les salles accessibles
          (en tenant compte de la pioche et des verrous de portes).
        On considère qu'on peut encore jouer tant qu'il existe AU MOINS :
          * soit une case vide atteignable via une porte ouvrable,
            sur laquelle on peut poser au moins une salle restante dans la pioche,
          * soit l'antichambre atteignable (gérée ailleurs pour la victoire).
        Le fait de pouvoir juste tourner en rond dans les mêmes salles ne suffit PAS :
        si aucune extension n'est possible, on est bloqué.
        """

        # Si déjà plus de pas, on est de toute façon en défaite (check_end le gère aussi).
        if self.player.steps <= 0:
            return True

        inv = self.player.inventory
        start_rc = (self.player.r, self.player.c)

        # On explore toutes les salles JOIGNABLES avec l'inventaire actuel
        visited: set[tuple[int, int]] = set()
        to_visit: list[tuple[int, int]] = [start_rc]

        while to_visit:
            r, c = to_visit.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))

            room_here = self.manor.get_room(r, c)
            if room_here is None:
                continue

            # Pour chaque direction depuis cette salle accessible
            for dir_ in ("N", "S", "E", "W"):
                dest = self.manor.valid_move((r, c), dir_)
                if not dest:
                    # Pas de porte (ou sortie du manoir)
                    continue

                nr, nc = dest

                # Porte correspondante
                door = self.manor.ensure_door((r, c), dir_)
                if door is not None and not (door.is_open or door.can_open(inv)):
                    # Porte présente mais impossible à ouvrir avec l'inventaire actuel
                    continue

                dest_room = self.manor.get_room(nr, nc)

                # ---- Cas 1 : case vide derrière une porte ouvrable -> peut-on poser une salle ? ----
                if dest_room is None:
                    # On teste toutes les salles encore présentes dans la pioche (room_stock > 0)
                    for tpl in self.room_templates.values():
                        if self.room_stock.get(tpl.name, 0) <= 0:
                            continue
                        ghost = clone_room(tpl)
                        if self.manor.can_place_room(ghost, (nr, nc), dir_):
                            # On a trouvé AU MOINS UNE extension possible -> le joueur n'est pas bloqué
                            return False
                    # Si aucune salle ne peut être posée ici, on continue à chercher ailleurs
                    continue

                # ---- Cas 2 : salle existante atteignable -> on l'ajoute au BFS ----
                if (nr, nc) not in visited:
                    to_visit.append((nr, nc))

        # Si on a exploré toute la zone atteignable sans trouver d'extension possible,
        # alors le joueur est réellement bloqué.
        return True


    # ---------- Gestion des effets visuels ----------

    def update_blink(self):
        now = pygame.time.get_ticks()
        self._blink_visible = ((now // BLINK_PERIOD_MS) % 2) == 0

    def update_pulse(self):
        now = pygame.time.get_ticks()
        self._pulse_phase = (now % PULSE_PERIOD_MS) / PULSE_PERIOD_MS

    # ---------- Gestion des entrées ----------

    def handle_play_input(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (KEY_UP, KEY_LEFT, KEY_DOWN, KEY_RIGHT):
            self.pending_dir = {
                KEY_UP: "N", KEY_LEFT: "W", KEY_DOWN: "S", KEY_RIGHT: "E"
            }[event.key]
            self.message = (
                f"Direction sélectionnée: {self.pending_dir}. "
                "Entrée pour valider, Échap/Espace pour annuler."
            )

        elif event.key == KEY_CONFIRM:
            if self.pending_dir:
                dir_ = self.pending_dir
                self.pending_dir = None
                self.try_move(dir_)
            else:
                self.message = "Aucune direction sélectionnée."

        elif event.key == KEY_CANCEL or event.key == KEY_USE:
            self.pending_dir = None
            self.message = "Sélection annulée."

        elif event.key == pygame.K_t:
            self.search_current_room()

        elif event.key == pygame.K_f:
            self.use_first_food()

        elif event.key == pygame.K_e:
            self.interact_current_room()

    def handle_pick_input(self, event):
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
            self.pick_rooms = []
            self.state = "PLAY"
            self.message = "Sélection de salle annulée. Choisis une autre porte."
            self.pending_dir = None
            self._pending_dir = None
            self._pending_dest = None
            self._pending_key = None

        elif event.key == pygame.K_r:
            inv = self.player.inventory
            if not inv.can_reroll_rooms():
                self.message = "Pas de dé pour relancer le tirage."
                return

            if self._pending_dir is None or self._pending_dest is None or self._pending_key is None:
                self.message = "Impossible de relancer ici."
                return

            if not inv.spend_die():
                self.message = "Pas de dé pour relancer le tirage."
                return

            self.message = "Tu relances le tirage (1 dé consommé)."
            self.roll_three_rooms(self._pending_dir, self._pending_dest, self._pending_key)

    def handle_shop_input(self, event: pygame.event.Event):
        """
        Gestion des touches dans la boutique :
        - 1 : Clé (5 or)
        - 2 : Nourriture (+4 pas) (3 or)
        - 3 : Dé (8 or)
        - 4 : Patte de lapin (12 or)
        - Échap : quitter la boutique
        """
        if event.type != pygame.KEYDOWN:
            return

        inv = self.player.inventory

        if event.key == KEY_CANCEL:
            self.state = "PLAY"
            self.shop_message = ""
            self.message = "Tu quittes la boutique."
            return

        # Achat n°1 : Clé
        if event.key == pygame.K_1:
            cost = 5
            if inv.gold >= cost:
                inv.gold -= cost
                inv.add_keys(1)
                self.shop_message = "Tu achètes une clé (-5 or)."
            else:
                self.shop_message = "Pas assez d'or pour la clé."
            return

        # Achat n°2 : nourriture (+4 pas)
        if event.key == pygame.K_2:
            cost = 3
            if inv.gold >= cost:
                inv.gold -= cost
                inv.add_item(Food("Ration de voyage", 4))
                self.shop_message = "Tu achètes une ration (+4 pas)."
            else:
                self.shop_message = "Pas assez d'or pour la nourriture."
            return

        # Achat n°3 : dé
        if event.key == pygame.K_3:
            cost = 8
            if inv.gold >= cost:
                inv.gold -= cost
                inv.add_dice(1)
                self.shop_message = "Tu achètes un dé (-8 or)."
            else:
                self.shop_message = "Pas assez d'or pour le dé."
            return

        # Achat n°4 : patte de lapin
        if event.key == pygame.K_4:
            cost = 12
            if inv.gold >= cost:
                inv.gold -= cost
                if not inv.has_rabbit_foot():
                    inv.add_item(RabbitFoot())
                    self.shop_message = "Tu achètes une patte de lapin (-12 or)."
                else:
                    self.shop_message = "Tu as déjà une patte de lapin."
            else:
                self.shop_message = "Pas assez d'or pour la patte de lapin."

    def handle_end_input(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == KEY_CONFIRM:
            new_manor = Manor()
            new_player = Player(*new_manor.start)
            self.__init__(new_manor, new_player)

    # ---------- Gestion de la nourriture ----------

    def use_first_food(self):
        inv = self.player.inventory
        from items import Food

        idx_food = None
        for i, item in enumerate(inv.items):
            if isinstance(item, Food):
                idx_food = i
                break

        if idx_food is None:
            self.message = "Tu n'as pas de nourriture dans ton inventaire."
            return

        food_item = inv.items[idx_food]
        name = food_item.name
        steps = food_item.steps_restored

        inv.use_item(idx_food, self.player)
        self.message = f"Tu manges {name} (+{steps} pas)."

    # ---------- Logique de jeu : déplacement ----------

    def try_move(self, dir_: str):
        if self.player.steps <= 0:
            self.lose("Plus de pas !")
            return

        src_rc = (self.player.r, self.player.c)

        dest = self.manor.valid_move(src_rc, dir_)
        if not dest:
            self.message = "Mur."
            # Si après ce mur il n'existe vraiment aucun autre chemin, on perd.
            if self.is_player_blocked():
                self.lose("Le manoir est bloqué : plus aucun chemin possible.")
            return

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

                #  on teste si VRAIMENT toutes les directions sont mortes
                if self.is_player_blocked():
                    self.lose("Tu ne peux ouvrir aucune porte : le manoir est bloqué.")
                return
            else:
                # Succès de l'ouverture (clé consommée si nécessaire)
                self.message = "Tu ouvres la porte."

        nr, nc = dest
        target_room = self.manor.get_room(nr, nc)

        if target_room is None:
            door_key = (src_rc[0], src_rc[1], dir_)

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

            self.roll_three_rooms(dir_, dest, door_key)
            if not self.pick_rooms and self.is_player_blocked():
                self.lose("Le manoir est bloqué : plus aucune pièce ne peut être posée.")
            return

        # Déplacement dans une pièce déjà connue
        self.player.steps -= 1
        self.player.r, self.player.c = nr, nc

        entry_msg = self.apply_room_entry_effect(target_room)
        if entry_msg:
            self.message = f"Tu avances vers {dir_}. {entry_msg}"
        else:
            self.message = f"Tu avances vers {dir_}."

        self.check_end((nr, nc))

    # ---------- Pioche FINIE de salles ----------

    def roll_three_rooms(self, dir_: str, dest_rc: tuple[int, int], door_key: tuple[int, int, str]):
        available_templates = [
            tpl for tpl in self.room_templates.values()
            if self.room_stock.get(tpl.name, 0) > 0
        ]

        candidates: list[Room] = []
        for tpl in available_templates:
            ghost = clone_room(tpl)
            if self.manor.can_place_room(ghost, dest_rc, dir_):
                candidates.append(tpl)

        if not candidates:
            self.message = "Aucune salle ne peut être placée ici (pioche épuisée ou incompatible)."
            self.pick_rooms = []
            return

        random.shuffle(candidates)
        pick_templates = candidates[:3]
        pick_rooms = [clone_room(tpl) for tpl in pick_templates]

        if pick_rooms and all(room.gem_cost > 0 for room in pick_rooms):
            pick_rooms[0].gem_cost = 0

        self.door_offers[door_key] = {
            "rooms": pick_rooms,
            "dest": dest_rc,
        }

        self.pick_rooms = pick_rooms
        self.pick_idx = 0
        self.state = "PICK"
        self._pending_dir = dir_
        self._pending_dest = dest_rc
        self._pending_key = door_key
        self.message = "Choisis une pièce pour cette porte."

    def confirm_pick(self):
        chosen = self.pick_rooms[self.pick_idx]
        if chosen.gem_cost > self.player.gems:
            self.message = "Pas assez de gemmes."
            return

        self.player.gems -= chosen.gem_cost

        r, c = self._pending_dest
        self.manor.set_room(r, c, chosen)

        name = getattr(chosen, "name", None)
        if name is not None and name in self.room_stock and self.room_stock[name] > 0:
            self.room_stock[name] -= 1

        self.state = "PLAY"

        self.player.steps -= 1
        self.player.r, self.player.c = r, c

        entry_msg = self.apply_room_entry_effect(chosen)
        if entry_msg:
            self.message = f"Ajouté: {chosen.name}. {entry_msg}"
        else:
            self.message = f"Ajouté: {chosen.name}."

        self.check_end((r, c))

        if self._pending_key is not None:
            self.door_offers.pop(self._pending_key, None)

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
            * ou si le manoir est bloqué (plus aucune nouvelle salle posable
              ni progression possible à partir des salles accessibles).
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

        # 3) Défaite : manoir bloqué (plus aucun chemin possible / aucune nouvelle salle posable)
        if self.is_player_blocked():
            self.lose(
                "Le manoir est bloqué : plus aucune porte ouvrable ni nouvelle salle à poser."
            )
    def lose(self, cause: str):
        self.win = False
        self.message = cause
        self.state = "END"

    # ---------- Fouille & interactions de salles ----------

    def search_current_room(self):
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

        # Jardin → nourriture ou patte de lapin
        if room.name == "Jardin intérieur":
            if not inv.has_rabbit_foot() and random.random() < 0.3:
                inv.add_item(RabbitFoot())
                self.message = "Tu trouves une patte de lapin porte-bonheur."
            else:
                inv.add_item(Food("Fruits frais", 5))
                self.message = "Tu trouves de la nourriture fraîche (+5 pas)."
            return

        # Veranda → pelle unique
        if room.name == "Veranda":
            if not inv.has_shovel():
                inv.add_item(Shovel())
                self.message = "Tu trouves une pelle appuyée contre le mur."
            else:
                inv.add_item(Food("Collation", 3))
                self.message = "Tu trouves un petit encas (+3 pas)."
            return

        # Salle des coffres → loot massif
        if room.name == "Salle des coffres":
            inv.add_gems(2)
            inv.add_gold(5)
            inv.add_keys(1)
            self.message = "Tu ouvres un coffre rempli : +2 gemmes, +5 or, +1 clé."
            return

        # Salle avec sac → gros loot orienté or
        if room.name == "Salle avec sac":
            inv.add_gold(4)
            inv.add_gems(1)
            inv.add_keys(1)
            self.message = "Le sac est lourd : +4 or, +1 gemme, +1 clé."
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

        # Marchand ambulant → patte de lapin possible en fouille aussi
        if room.name == "Marchand ambulant":
            if not inv.has_rabbit_foot():
                inv.add_item(RabbitFoot())
                self.message = "Le marchand te donne une patte de lapin."
            else:
                inv.add_gold(1)
                self.message = "Il te donne une pièce d'or."
            return

        # Salle piégée (fouille = piège)
        if room.room_type == RoomType.TRAP:
            self.player.steps = max(0, self.player.steps - 3)
            self.message = "Un piège se déclenche ! (-3 pas)"
            return

        # Fouille par défaut
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

        # Veranda : interaction simple
        if room.name == "Veranda":
            if not inv.has_shovel():
                self.message = "Une pelle traîne probablement ici... fouille la salle (T)."
            else:
                self.message = "Rien de plus à faire ici."
            return

        # Boutique / Marchand : ouvrir la boutique si on a de l'or
        if room.name in ("Boutique", "Marchand ambulant"):
            if self.player.gold <= 0:
                self.message = "Tu n'as pas d'or pour acheter quelque chose."
            else:
                self.state = "SHOP"
                self.shop_message = ""
                self.message = "La boutique est ouverte (1-4 pour acheter, Échap pour quitter)."
            return

        self.message = "Rien de spécial à faire ici."

    # ---------- Boucle principale ----------

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.state == "PLAY":
                    self.handle_play_input(event)
                elif self.state == "PICK":
                    self.handle_pick_input(event)
                elif self.state == "SHOP":
                    self.handle_shop_input(event)
                elif self.state == "END":
                    self.handle_end_input(event)

            self.update_blink()
            self.update_pulse()

            self.screen.fill(BG)
            draw_grid(self.screen, self.manor)
            draw_player(self.screen, (self.player.r, self.player.c))

            current_room = self.manor.get_room(self.player.r, self.player.c)

            if self.state == "PLAY":
                draw_direction_hint(
                    self.screen,
                    (self.player.r, self.player.c),
                    self.pending_dir,
                    self._blink_visible
                )

            draw_hud(self.screen, self.player, self.message, self.item_icons, current_room)

            if self.state == "PICK":
                draw_pick_screen_pulse(
                    self.screen,
                    self.pick_rooms,
                    self.pick_idx,
                    self._pulse_phase
                )

            if self.state == "SHOP":
                draw_shop_window(self.screen, self.player.inventory, self.shop_message)

            if self.state == "END":
                draw_end_screen(self.screen, win=self.win)

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    random.seed()
    manoir = Manor()
    player = Player(*manoir.start)
    Game(manoir, player).run()