from pathlib import Path
import random
import csv

# --- INITIALISATION DES PARAMÈTRES GLOBAUX ---
print("Veuillez choisir la longueur de la grille : ")
maxX = int(input())
print("Veuillez choisir la largeur de la grille : ")
maxY = int(input())

# Définition du chemin d'accès pour la politique automatique (fichier CSV)
csv_directory = Path(__file__).parent
csv_path = csv_directory / 'sequence.csv'

class Couple:
    """Représente des coordonnées 2D (x, y) sur la grille."""
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        
    def __eq__(self, other):
        # Permet de comparer deux positions : Couple(1,1) == Couple(1,1) renverra True
        if isinstance(other, Couple):
            return self.x == other.x and self.y == other.y
        return False
        
    def __str__(self):
        # Formatage pour l'affichage console
        return f"({self.x}, {self.y})"
        
    def __hash__(self):
        # Indispensable pour utiliser l'objet 'Couple' dans des listes uniques (set) ou comme clé de dictionnaire
        return hash((self.x, self.y))

class Politique:
    """Définit la méthode de décision du drone (manuel, séquence prédéfinie, ou exhaustif)."""
    def __init__(self, politique):
        if(isinstance(politique, str)):
            self.name = politique
        elif(isinstance(politique, list)):
            self.seq = politique
            self.name = "sequence"

    def sequence(self):
        # Retourne la liste des prochains mouvements si la politique est en mode automatique
        if(self.seq != None and self.name == "sequence"):
            return self.seq

class Etat:
    """
    Représente la photographie exacte d'une situation à un instant T.
    C'est cet objet qui est utilisé par l'IA pour apprendre (Propriété de Markov).
    """
    def __init__(self, pos, batterie, airborn, dock, crashed, obstacle_distance):
        self.pos = pos                         # Position géographique (Couple)
        self.battery = batterie                # Énergie restante (0-100)
        self.airborne = airborn                # Statut de vol (1 = en vol, 0 = au sol)
        self.docked = dock                     # Statut d'amarrage (1 = sur la base, 0 = non)
        self.crashed = crashed                 # Statut d'erreur (1 = détruit, 0 = opérationnel)
        self.obstacle_distance = obstacle_distance # Perception du danger (0 = danger, 2 = sûr)

    def __eq__(self, other):
        # Deux états sont identiques si toutes ces variables sont exactement les mêmes
        if isinstance(other, Etat):
            return (self.pos == other.pos and 
                    self.battery == other.battery and 
                    self.airborne == other.airborne and 
                    self.docked == other.docked and 
                    self.crashed == other.crashed and
                    self.obstacle_distance == other.obstacle_distance)
        return False

    def __hash__(self):
        # Indispensable pour l'exploration exhaustive avec le set()
        return hash((self.pos, self.battery, self.airborne, self.docked, self.crashed, self.obstacle_distance))

class Zone:
    """Gère l'abstraction spatiale et la division du terrain en macro-secteurs."""
    def __init__(self, maxX, maxY, danger: list[Couple], zoneCount):
        self.max = Couple(maxX, maxY)
        self.danger = danger # Liste des coordonnées dangereuses
        self.zoneCount = zoneCount
        self.grille: list[Couple] = [Couple() for _ in range(self.max.x * self.max.y)]

    def zoneOf(self, c: Couple):
        # Découpe la grille en 4 zones
        if c.x <= self.max.x / 2 and c.y <= self.max.y / 2:
            return 1
        elif c.x <= self.max.x / 2 and c.y > self.max.y / 2:
            return 2
        elif c.x > self.max.x / 2 and c.y <= self.max.y / 2:
            return 3
        elif c.x > self.max.x / 2 and c.y > self.max.y / 2:
            return 4

class Drone:
    """Représente l'agent physique naviguant dans l'environnement."""
    def __init__(self, terrain: Zone):
        self.pos = Couple(0, 0)
        self.base = Couple(0, 0)
        self.battery = 100
        self.docked = 0
        self.airborne = 0
        self.crashed = 0
        self.obstacle_distance = 2
        # Historique des zones visitées par le drone
        self.visZone = [terrain.zoneOf(self.pos)] 
        
    def etat(self):
        # Affiche un résumé textuel de l'état du drone
        print(f"position(x,y) = {self.pos} ; base(x,y) = {self.base} ; niveau de la batterie = {self.battery} ; docked = {self.docked} ; airborne = {self.airborne} ; crashed = {self.crashed} ; obstacle_distance = {self.obstacle_distance} ; visZone = {self.visZone}")
        
    def get_etat(self):
        # Génère l'objet 'Etat' formel correspondant à la situation actuelle du drone
        return Etat(self.pos, self.battery, self.airborne, self.docked, self.crashed, self.obstacle_distance)

class Environnement:
    """Moteur physique gérant les règles du monde, les transitions et les conséquences des actions."""
    def __init__(self, maxX, maxY, danger):
        self.terrain = Zone(maxX, maxY, danger, 4)
        self.drone = Drone(self.terrain)
        self.danger = danger

    def takeoff_cmd(self):
        # Commande de décollage : requiert de la batterie et de ne pas être crashé
        if self.drone.crashed == 0 and self.drone.airborne == 0 and self.drone.battery > 0:
            self.drone.airborne = 1
            # Mise à jour immédiate selon la case actuelle
            if self.drone.pos in self.danger:
                self.drone.obstacle_distance = 0
            else:
                self.drone.obstacle_distance = 2
                
    def render(self):
        # Rendu visuel de la grille
        print("\n--- Etat du Terrain ---")
        # Parcours inversé sur Y pour afficher l'origine (0,0) en bas à gauche
        for y in range(self.terrain.max.y - 1, -1, -1):
            line = ""
            for x in range(self.terrain.max.x):
                current_pos = Couple(x, y)
                if self.drone.pos == current_pos:
                    char = "v" if self.drone.crashed == 0 else "x" 
                elif self.drone.base == current_pos:
                    char = "B"
                elif any(d == current_pos for d in self.danger):
                    char = "o"
                else:
                    char = ". "
                line += char + " "
            print(line)
        print("-----------------------\n")
        
    def move_step(self, politique: Politique):
        # Déplacement d'une case adjacente (coût = 1 batterie)
        if self.drone.crashed == 0 and self.drone.airborne == 1 and self.drone.docked == 0 and self.drone.battery > 0:
            next_pos = None
            valid_mov = []
            # Calcul des limites de la grille pour éviter les sorties de carte
            if self.drone.pos.y + 1 < self.terrain.max.y:
                valid_mov.append(Couple(self.drone.pos.x, self.drone.pos.y + 1))
            if self.drone.pos.y - 1 >= 0:
                valid_mov.append(Couple(self.drone.pos.x, self.drone.pos.y - 1))
            if self.drone.pos.x + 1 < self.terrain.max.x:
                valid_mov.append(Couple(self.drone.pos.x + 1, self.drone.pos.y))
            if self.drone.pos.x - 1 >= 0:
                valid_mov.append(Couple(self.drone.pos.x - 1, self.drone.pos.y))
            
            # Application de la décision selon la politique choisie
            if politique.name == "manuel":
                for i, pos in enumerate(valid_mov):
                    print(f"{i} = {pos}")
                next_pos = valid_mov[int(input())]
            elif politique.name == "sequence":
                    if politique.seq:
                        temp = politique.seq[0]
                        politique.seq.pop(0)
                        if temp in valid_mov:
                            next_pos = temp
                        else:
                            # Séquence invalide : le drone sort du terrain
                            self.drone.crashed = 1
                            print("Destruction du drone !")

            # Application de la transition
            if next_pos is not None:
                self.drone.pos = next_pos
                self.drone.battery -= 1
                self.drone.visZone.append(self.terrain.zoneOf(next_pos))
                # Mise à jour du capteur de danger
                if next_pos in self.danger:
                    self.drone.obstacle_distance = 0
                else:
                    self.drone.obstacle_distance = 2

    def avoid_maneuver(self, politique: Politique):
        # Déplacement sécurisé (coût = 2 batterie). Empêche d'aller sur un danger.
        if self.drone.crashed == 0 and self.drone.airborne == 1 and self.drone.docked == 0 and self.drone.battery > 1:
            next_pos = None
            valid_mov = []
            # Mêmes limites de grille, mais on filtre les cases dangereuses
            if self.drone.pos.y + 1 < self.terrain.max.y and Couple(self.drone.pos.x, self.drone.pos.y + 1) not in self.danger:
                valid_mov.append(Couple(self.drone.pos.x, self.drone.pos.y + 1))
            if self.drone.pos.y - 1 >= 0 and Couple(self.drone.pos.x, self.drone.pos.y - 1) not in self.danger:
                valid_mov.append(Couple(self.drone.pos.x, self.drone.pos.y - 1))
            if self.drone.pos.x + 1 < self.terrain.max.x and Couple(self.drone.pos.x + 1, self.drone.pos.y) not in self.danger:
                valid_mov.append(Couple(self.drone.pos.x + 1, self.drone.pos.y))
            if self.drone.pos.x - 1 >= 0 and Couple(self.drone.pos.x - 1, self.drone.pos.y) not in self.danger:
                valid_mov.append(Couple(self.drone.pos.x - 1, self.drone.pos.y))
                
            # Repli : Si aucun mouvement sécurisé n'est possible, on tente un mouvement normal
            if not valid_mov:
                self.move_step(politique)
                self.drone.battery -= 1
                self.drone.obstacle_distance = 2
                return
                
            if politique.name == "manuel":
                for i, pos in enumerate(valid_mov):
                    print(f"{i} = {pos}")
                next_pos = valid_mov[int(input())]
            elif politique.name == "sequence":
                if politique.seq:
                    temp = politique.seq[0]
                    politique.seq.pop(0)
                    if temp in valid_mov:
                        next_pos = temp
                    else:
                        self.drone.crashed = 1
                        print("Destruction du drone !")
                        
            if next_pos is not None:
                self.drone.pos = next_pos
                self.drone.battery -= 2
                self.drone.visZone.append(self.terrain.zoneOf(next_pos))
                if next_pos in self.danger:
                    self.drone.obstacle_distance = 0
                else:
                    self.drone.obstacle_distance = 2

    def return_home(self):
        # Automatisme rapprochant le drone de sa base d'une case (coût = 1 batterie)
        if self.drone.crashed == 0 and self.drone.airborne == 1 and self.drone.docked == 0 and self.drone.battery > 0:
            nextx = self.drone.pos.x
            nexty = self.drone.pos.y

            if self.drone.pos.x < self.drone.base.x:
                nextx += 1
            elif self.drone.pos.x > self.drone.base.x:
                nextx -= 1

            if self.drone.pos.y < self.drone.base.y:
                nexty += 1
            elif self.drone.pos.y > self.drone.base.y:
                nexty -= 1

            next_pos = Couple(nextx, nexty)
            self.drone.pos = next_pos
            self.drone.battery -= 1
            self.drone.visZone.append(self.terrain.zoneOf(next_pos))
            if next_pos in self.danger:
                self.drone.obstacle_distance = 0
            else:
                self.drone.obstacle_distance = 2
    
    def dock_cmd(self):
        # Autorise l'amarrage uniquement si le drone est exactement sur la case de la base
        if self.drone.airborne == 1 and self.drone.crashed == 0 and self.drone.docked == 0 and self.drone.pos.__eq__(self.drone.base):
            self.drone.docked = 1
            self.drone.airborne = 0
        
    def undock_cmd(self):
        # Autorise le désamarrage et le retour en vol
        if self.drone.crashed == 0 and self.drone.docked == 1 and self.drone.battery > 0:
            self.drone.docked = 0
            self.drone.airborne = 1
            self.drone.visZone.append(self.drone.base)
    
    def charge_step(self):
        # Recharge progressive (5 par 5) lorsque le drone est amarré
        if self.drone.crashed == 0 and self.drone.docked == 1:
            if self.drone.battery <= 95:
                self.drone.battery += 5
            else:
                self.drone.battery = 100

    def emergency_stop(self):
        # Met fin à l'exécution de l'agent de manière irréversible
        self.drone.crashed = 1
        self.drone.airborne = 0
        self.drone.docked = 0
        self.drone.obstacle_distance = 0
    
    def successeurs(self, etat: Etat):
        """
        Générateur de graphe. Cette fonction prédit tous les états futurs possibles
        à partir d'un état donné, sans modifier physiquement l'environnement.
        """
        successeurs_list = []
        if etat.crashed == 1:
            return [] # Un état crashé n'a pas de futur
            
        maxX = self.terrain.max.x
        maxY = self.terrain.max.y
        base = self.drone.base
        
        # Fonction utilitaire pour attribuer dynamiquement la perception (0 ou 2) aux états projetés
        def get_obs_dist(pos):
            return 0 if pos in self.danger else 2

        # Prédiction : Si on est au sol, on peut décoller
        if etat.airborne == 0 and etat.docked == 0 and etat.battery > 0:
            successeurs_list.append(Etat(etat.pos, etat.battery, 1, 0, 0, get_obs_dist(etat.pos)))

        # Prédiction : Si on vole, on calcule les mouvements possibles
        if etat.airborne == 1 and etat.docked == 0:
            # 1. Mouvements standards (Coût 1)
            if etat.battery >= 1:
                if etat.pos.y + 1 < maxY:
                    next_pos = Couple(etat.pos.x, etat.pos.y + 1)
                    successeurs_list.append(Etat(next_pos, etat.battery - 1, 1, 0, 0, get_obs_dist(next_pos)))
                if etat.pos.y - 1 >= 0:
                    next_pos = Couple(etat.pos.x, etat.pos.y - 1)
                    successeurs_list.append(Etat(next_pos, etat.battery - 1, 1, 0, 0, get_obs_dist(next_pos)))
                if etat.pos.x + 1 < maxX:
                    next_pos = Couple(etat.pos.x + 1, etat.pos.y)
                    successeurs_list.append(Etat(next_pos, etat.battery - 1, 1, 0, 0, get_obs_dist(next_pos)))
                if etat.pos.x - 1 >= 0:
                    next_pos = Couple(etat.pos.x - 1, etat.pos.y)
                    successeurs_list.append(Etat(next_pos, etat.battery - 1, 1, 0, 0, get_obs_dist(next_pos)))

            # 2. Mouvements d'évitement (Coût 2, atterrissage forcé sur zone sûre)
            if etat.battery >= 2:
                if etat.pos.y + 1 < maxY and Couple(etat.pos.x, etat.pos.y + 1) not in self.danger:
                    next_pos = Couple(etat.pos.x, etat.pos.y + 1)
                    successeurs_list.append(Etat(next_pos, etat.battery - 2, 1, 0, 0, 2))
                if etat.pos.y - 1 >= 0 and Couple(etat.pos.x, etat.pos.y - 1) not in self.danger:
                    next_pos = Couple(etat.pos.x, etat.pos.y - 1)
                    successeurs_list.append(Etat(next_pos, etat.battery - 2, 1, 0, 0, 2))
                if etat.pos.x + 1 < maxX and Couple(etat.pos.x + 1, etat.pos.y) not in self.danger:
                    next_pos = Couple(etat.pos.x + 1, etat.pos.y)
                    successeurs_list.append(Etat(next_pos, etat.battery - 2, 1, 0, 0, 2))
                if etat.pos.x - 1 >= 0 and Couple(etat.pos.x - 1, etat.pos.y) not in self.danger:
                    next_pos = Couple(etat.pos.x - 1, etat.pos.y)
                    successeurs_list.append(Etat(next_pos, etat.battery - 2, 1, 0, 0, 2))

            # 3. Mouvement Return to Home (Coût 1)
            if etat.battery >= 1:
                nextx, nexty = etat.pos.x, etat.pos.y
                if etat.pos.x < base.x:
                    nextx += 1
                elif etat.pos.x > base.x:
                    nextx -= 1
                if etat.pos.y < base.y:
                    nexty += 1
                elif etat.pos.y > base.y:
                    nexty -= 1
                
                if nextx != etat.pos.x or nexty != etat.pos.y:
                    next_pos = Couple(nextx, nexty)
                    successeurs_list.append(Etat(next_pos, etat.battery - 1, 1, 0, 0, get_obs_dist(next_pos)))

            # 4. Amarrage si on est au-dessus de la base
            if etat.pos == base:
                successeurs_list.append(Etat(etat.pos, etat.battery, 0, 1, 0, get_obs_dist(etat.pos)))

        # Prédiction : Si on est amarré
        if etat.docked == 1:
            if etat.battery > 0: # On peut décoller
                successeurs_list.append(Etat(etat.pos, etat.battery, 1, 0, 0, get_obs_dist(etat.pos)))
            
            if etat.battery < 100: # On peut recharger
                new_battery = min(100, etat.battery + 5)
                successeurs_list.append(Etat(etat.pos, new_battery, 0, 1, 0, get_obs_dist(etat.pos)))
        
        # Le cast list(set(...)) permet de supprimer d'éventuels doublons accidentels dans les successeurs
        return list(set(successeurs_list))

def transition(etat: Couple, maxX, maxY):
    # Fonction globale simple retournant les cases adjacentes (peut servir hors de la classe Environnement)
    valid_mov = []
    if etat.y + 1 < maxY:
        valid_mov.append(Couple(etat.x, etat.y + 1))
    if etat.y - 1 >= 0:
        valid_mov.append(Couple(etat.x, etat.y - 1))
    if etat.x + 1 < maxX:
        valid_mov.append(Couple(etat.x + 1, etat.y))
    if etat.x - 1 >= 0:
        valid_mov.append(Couple(etat.x - 1, etat.y))
    return valid_mov

class Graph:
    """Outil de parcours mathématique générant tous les futurs possibles de l'environnement."""
    def __init__(self):
        self.transitions = {}
        self.etats = []
        
    def Explore_ite(self, s0, maxDepth, maxBreadth):
        """
        Algorithme de parcours en profondeur (DFS) itératif.
        Construit l'arbre d'exploration complet depuis l'état initial s0.
        """
        l = [(s0, maxDepth)] # Pile LIFO pour gérer les branches
        S = set() # Registre des états visités (évite les boucles infinies)
        while l:
            (s, currentDepth) = l.pop()
            if s in S:
                continue
            S.add(s)
            
            # Limite de profondeur pour préserver la mémoire
            if currentDepth != -1 and currentDepth <= 0:
                continue
                
            count = 0
            transi = env.successeurs(s) # Appel au moteur de prédiction
            self.transitions[s] = transi
            
            for etat_dest in transi:
                # Limite de largeur (nombre maximum de voisins à explorer)
                if maxBreadth != -1 and count >= maxBreadth:
                    break
                if currentDepth == -1:
                    d = -1
                else:
                    d = currentDepth-1
                if etat_dest not in S:
                    l.append((etat_dest, d))
                count += 1
        return S

# --- BOUCLE PRINCIPALE (MAIN) ---

# Paramétrage initial de l'environnement physique
print("Veuillez rentrer un taux de danger : (en %)")
taux_danger = int(input())/100
danger = []

# Génération aléatoire des positions dangereuses selon le taux défini
for i in range(int(maxX * maxY * taux_danger)):
    danger.append(Couple(random.randrange(maxX), random.randrange(maxY)))
    
env = Environnement(maxX, maxY, danger)
count = 0

print("Veuillez choisir une politique : ")
print("1 : [manuel] ; 2 : [automatique] ; 3 : [exhaustive]")
politique_num = int(input())
sequence_coups = []
politique_name = ""

# Sélection du comportement global du programme
match(politique_num):
    case 1:
        politique = Politique("manuel")
    case 2: 
        # Chargement d'une suite de mouvements depuis un CSV externe
        with open(csv_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file, delimiter=';')
            for ligne in csv_reader:
                for element in ligne:
                    element = element.strip()
                    if element:
                        element_nettoye = element.strip("()")
                        valeurs = element_nettoye.split(",")
                        if len(valeurs) == 2:
                            x_val = int(valeurs[0])
                            y_val = int(valeurs[1])
                            sequence_coups.append(Couple(x_val, y_val))
        politique = Politique(sequence_coups)
    case 3:
        # Mode Génération de Modèle : ne lance pas la simulation physique, génère l'arbre d'état
        politique = Politique("exhaustif")
        graph = Graph()
        etats_visites = graph.Explore_ite(env.drone.get_etat(), -1, -1)
        print(f"Exploration terminée ! {len(etats_visites)} etats découverts.")

# Boucle de jeu interactif pour les politiques 1 et 2
if politique_num != 3:
    while(env.drone.crashed != 1):
        env.render() # Affiche l'état visuel du terrain
        print("Choisissez une action entre : ")
        print("1 : [takeoff] ; 2 : [move] ; 3 : [avoid] ; 4 : [return] ; 5 : [dock] ; 6 : [undock] ; 7 : [charge] ; 8 : [quit]")
        entree = int(input())
        drone = env.drone
        
        # Routage de l'action utilisateur vers la méthode physique correspondante
        match entree:
            case 1:
                if(drone.battery <= 0):
                    print("Le drone ne peut pas décoller, il n'a plus de batterie.")
                else:
                    env.takeoff_cmd()
            case 2:
                env.move_step(politique)
            case 3:
                env.avoid_maneuver(politique)
            case 4:
                env.return_home()
            case 5:
                env.dock_cmd()
            case 6:
                env.undock_cmd()
            case 7:
                env.charge_step()
            case 8:
                env.drone.crashed = 1
                print("Destruction du drone !")
                
        drone.etat() # Affiche le résumé texte pour débogage
        count += 1
        
        # Vérification d'arrêt d'urgence
        if env.drone.crashed == 1:
            env.emergency_stop()
            print("Arret d'urgence, le drone s'est crashe !")