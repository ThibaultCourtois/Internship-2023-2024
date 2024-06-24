import re
import math

# Fonction pour calculer la distance euclidienne entre deux points
def distance_euclidienne(p1, p2):
    return math.sqrt((p1['X'] - p2['X'])**2 + (p1['Y'] - p2['Y'])**2 + (p1['Z'] - p2['Z'])**2)

# Fonction pour extraire les coordonnées et la vitesse d'une ligne G1
def extraire_coordonnees_et_vitesse(ligne):
    coordonnees = {'X': None, 'Y': None, 'Z': None, 'F': None}
    matches = re.finditer(r'([XYZF])([0-9\.\-]+)', ligne)
    for match in matches:
        coordonnees[match.group(1)] = float(match.group(2))
    return coordonnees

# Fonction pour mettre à jour la ligne avec la nouvelle vitesse
def mettre_a_jour_vitesse(ligne, nouvelle_vitesse):
    return re.sub(r'F[0-9\.\-]+', f'F{nouvelle_vitesse}', ligne)

# Chemin du fichier G-code
fichier_gcode = 'modif_speed.gcode'

# Seuil de distance et vitesse à ajuster
distance_seuil = 5  # Distance seuil en unités de l'imprimante
nouvelle_vitesse_1 = 1000  # Nouvelle vitesse si la distance dépasse le seuil
nouvelle_vitesse_2 = 1600

# Lire le fichier G-code
with open(fichier_gcode, 'r') as fichier:
    lignes = fichier.readlines()

# Stocker les points précédents pour le calcul de la distance
point_precedent = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}

# Liste pour stocker les lignes modifiées
lignes_modifiees = []

# Traiter chaque ligne du fichier G-code
for ligne in lignes:
    if ligne.startswith('G1'):
        coordonnees = extraire_coordonnees_et_vitesse(ligne)
        # Mettre à jour les coordonnées manquantes avec celles du point précédent
        for axe in 'XYZ':
            if coordonnees[axe] is None:
                coordonnees[axe] = point_precedent[axe]
        distance = distance_euclidienne(point_precedent, coordonnees)
        if distance > distance_seuil:
            ligne = mettre_a_jour_vitesse(ligne, nouvelle_vitesse_1)
        if distance <= distance_seuil:
            ligne = mettre_a_jour_vitesse(ligne, nouvelle_vitesse_2)
        point_precedent = coordonnees
    lignes_modifiees.append(ligne)

# Écrire les lignes modifiées dans un nouveau fichier G-code
with open('new_vitess.gcode', 'w') as fichier:
    fichier.writelines(lignes_modifiees)

print("Le fichier G-code a été modifié avec succès.")
