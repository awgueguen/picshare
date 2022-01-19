# Picshare

## Installation

Pour installer l'environnement virtuel:

1. Ouvrir dans un premier temps le dossier contenant le git dans VSC:

```bash
code nom_dossier_git
```

Ou depuis Fichier > Ouvrir un dossier
Bien vérifier dans le terminal que s'affiche:

```bash
../kcamill-picshare/
```

2. Puis lancer le script d'installation en utilisant:

```bash
./installation/init.sh
```

3. Pour activer l'environnement virtuel:

```bash
source .venv/bin/activate
```

4. Pour créer la bdd:

```bash
python3 installation/init_db.py
```

5. Divers

Désactiver l'env virtuel

```bash
deactivate
```

---

## Ressources

-   [backlog](https://docs.google.com/spreadsheets/d/17xMIFGWjr49zVxaLiTwf7WM5cqeixjJXqV-JynE_Ijo/edit?usp=sharing)
