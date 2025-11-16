# Projet_POO_2025_BluePrince

Projet réalisé dans le cadre du cours de Programmation Orienté Objet de Python - Master SI 2025-2026 (Sorbonne Université).  
Version 2D simplifiée du jeu *The Blue Prince*, avec génération progressive d’un manoir, gestion d’inventaire et événements aléatoires.

---

##  Installation

### 1. Cloner le projet
```bash
git clone <https://github.com/Gabro787/Projet_POO_2025_BluePrince.git>
```

### 2. (Optionnel) Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```
Si le fichier n’existe pas :
```bash
pip install pygame
```

---

##  Lancer le jeu

Depuis la racine du projet :
```bash
python game.py
```

Une fenêtre s’ouvre avec :
- le manoir (5×9 cases)
- le joueur en position
- le HUD (inventaire, ressources, informations salle)

---

##  Commandes

| Action | Touche |
|-------|--------|
| Monter | Z |
| Descendre | S |
| Gauche | Q |
| Droite | D |
| Valider / Choisir salle | Entrée |
| Annuler | Échap |
| Utiliser un objet | Espace |
| Naviguer choix | ← → ou A / E |

---

##  Règles du jeu (résumé)

- Le joueur part de l’**Entrée**, en bas du manoir.
- Objectif : atteindre l’**Antechambre**, tout en haut.
- Chaque déplacement consomme **1 pas**.
- Lorsqu’on découvre une case vide, **3 salles** sont proposées.
- Certaines salles coûtent des **gemmes** pour être placées.
- Certaines donnent du **loot** (nourriture, clés, dés, pièces…).
- Certaines sont des **pièges** (perte de pas).
- Certaines sont des **magasins** (achats avec l’or).
- Mort si les **pas atteignent 0**.  
- Victoire en atteignant l’Antechambre.

---

##  Inventaire

L’inventaire contient :
- **Pas** (steps)
- **Or** (gold)
- **Gemmes**
- **Clés**
- **Dés (reroll)**
- **Nourriture** (restaure des pas)
- **Objets permanents**

### Objets permanents et effets :
| Objet | Effet |
|-------|--------|
| Shovel (Pelle) | Permet de creuser. |
| Hammer (Marteau) | Peut ouvrir certains coffres/pièges. |
| Lockpick Kit | Permet de crocheter certaines portes. |
| Metal Detector | Augmente loot clés/gemmes. |
| Rabbit Foot | Augmente toutes les probabilités de loot. |

---

##  Système de portes

Chaque porte a un niveau :

- **0 – UNLOCKED** : toujours ouvert  
- **1 – LOCKED** : clé OU kit de crochetage  
- **2 – DOUBLE LOCKED** : nécessite une clé  

La gestion des ressources est automatique via `door.open()`.

---

##  Système aléatoire

Le fichier `random_manager.py` gère :
- tirage des objets (nourriture, clés, dés, gemmes, permanents)
- modifications selon les permanents (détecteur / patte de lapin)
- coffres, casiers, dig spots
- magasins
- effets de salles

---

##  Génération du manoir

Le manoir est une grille **5 × 9** :
- Chaque salle possède portes, couleur, coût, rareté, effets.
- Les salles uniques (VRN, GBD, CEL, MCH) n’apparaissent qu’une fois.
- Le joueur place une pièce parmi 3 propositions.

---

## 🖼 Organisation du projet

```
blue-prince/
│
├── game.py              # Lancement du jeu + boucle principale
├── player.py            # Joueur + déplacements + ressources
├── inventory.py         # Inventaire et objets
├── items.py             # Objets consommables / permanents
├── random_manager.py    # Gestion du hasard et loot
├── manoir.py            # Structure du manoir
├── room.py              # Classe salle
├── room_data.py         # Catalogue de salles
├── door.py              # Système de portes
├── ui.py                # Interface graphique (pygame)
├── sprites.py           # Chargement des tilesets
├── constants.py         # Paramètres du jeu
└── assets/              # Images et sprites
```

---

##  Points importants

- Nécessite **Python 3.10+**  
- Nécessite **pygame**  
- Bien placer les fichiers images dans `assets/`  
- Le jeu fonctionne sur Windows, Mac, Linux  
- Le manoir est différent à chaque partie grâce à l’aléatoire  

---

##  Auteurs  
Projet réalisé par le groupe :  
- Gabriel  : génération du manoir, portes, salles  
- Sergen : joueur, inventaire, objets, aléatoire  
- Souleymane  : interface graphique pygame  

---

##  Bon jeu !