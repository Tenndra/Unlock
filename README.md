# Unlock — table virtuelle

Nouvelle interface Python/Kivy pour manipuler les cartes des paquets conservés dans `ressources/decks/`.

## Lancer l'application

1. Installer Python 3.10 ou plus récent.
2. Dans un terminal, à la racine du dépôt :

   ```bash
   python -m venv .venv
   # Windows :
   .venv\Scripts\activate
   # macOS / Linux :
   source .venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```

## Utilisation

- Choisir un paquet dans la liste en haut.
- Cliquer sur un numéro de carte dans la colonne de gauche pour l'ajouter à la table.
- Glisser une carte pour la déplacer ; les cartes ne déplacent jamais le fond.
- Utiliser les boutons de rotation ou le geste à deux doigts pour tourner une carte.
- Retourner une carte pour afficher son recto/verso.
- Défausser une carte puis la restaurer depuis le bouton « Défausse ».

Les images de cartes doivent garder leur nommage actuel : `<identifiant>_r.jpg` et éventuellement `<identifiant>_v.jpg`.
