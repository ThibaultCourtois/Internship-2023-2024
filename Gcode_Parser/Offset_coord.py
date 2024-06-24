import re

def lire_et_offset_gcode(fichier_gcode, fichier_sortie, ofx, ofy):
    # Fonction pour extraire les coordonnées d'une ligne G1
    def extraire_coordonnees(ligne):
        coordonnees = {'X': None, 'Y': None, 'Z': None}
        matches = re.finditer(r'([XYZ])([0-9\.\-]+)', ligne)
        for match in matches:
            coordonnees[match.group(1)] = float(match.group(2))
        return coordonnees

    # Fonction pour appliquer le décalage aux coordonnées
    def appliquer_offset(coordonnees, ofx, ofy):
        if coordonnees['X'] is not None:
            coordonnees['X'] += ofx
        if coordonnees['Y'] is not None:
            coordonnees['Y'] += ofy
        return coordonnees

    # Fonction pour mettre à jour la ligne avec les nouvelles coordonnées
    def mettre_a_jour_ligne(ligne, coordonnees):
        nouvelle_ligne = ligne
        for axe in 'XYZ':
            if coordonnees[axe] is not None:
                nouvelle_ligne = re.sub(rf'{axe}[0-9\.\-]+', f'{axe}{coordonnees[axe]:.3f}', nouvelle_ligne)
        return nouvelle_ligne

    # Lire le fichier G-code
    with open(fichier_gcode, 'r') as fichier:
        lignes = fichier.readlines()

    # Liste pour stocker les lignes modifiées
    lignes_modifiees = []

    # Traiter chaque ligne du fichier G-code
    for ligne in lignes:
        if ligne.startswith('G1'):
            coordonnees = extraire_coordonnees(ligne)
            coordonnees = appliquer_offset(coordonnees, ofx, ofy)
            ligne = mettre_a_jour_ligne(ligne, coordonnees)
        lignes_modifiees.append(ligne)

    # Écrire les lignes modifiées dans un nouveau fichier G-code
    with open(fichier_sortie, 'w') as fichier:
        fichier.writelines(lignes_modifiees)

    print("Le fichier G-code a été décalé et modifié avec succès.")

# Utilisation de la fonction
fichier_gcode = 'need_to_offset.gcode'
fichier_sortie = 'offset.gcode'
offset_x = -2.054  # Décalage en X
offset_y = 3.487  # Décalage en Y

lire_et_offset_gcode(fichier_gcode, fichier_sortie, offset_x, offset_y)
