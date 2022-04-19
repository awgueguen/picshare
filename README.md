# Picshare

### Sommaire

- [Description](#escription)
- [Résolution](#résolution)
- [Installation (Mac/Linux)](#installation-linux--mac)
- [Ressources](#ressources)

## Description

Picshare est un site de partage d'images dans le même esprit que des sites tels que Flickr ou Instagram.\
Il permet à des utilisateurs des partager des photos associés à une description, un nom ainsi que des #hastags.\
Les utilisateurs peuvent ensuite commenter d'autres images & rajouter des #hastags à leur tour.

---

## Résolution

Le but principal de cet exercice était de confronter un premier socle de compétences sur Python a un projet doté d'un contexte plus réaliste. Pour cela sont utilisés notamment:

- **Flask**
- **Jinja**
- **SQLite**

Le choix a été fait de ne pas utiliser un ORM tel que **SQLAlchemy** afin de se confronter à la complexité du langage **SQL**.\
Afin de tester au mieux le site, la génération de la BDD est accompagnée d'un seeding.

Dans le but d'éviter au maximum toute répétition de code, voici quelques fonctions - trouvables dans `methods.py` :

```python
convert_data(rv: list, method='GET')
```

Permet de faciliter la traduction d'informations visées au front.

```python
rename_picture(request)
```

Renomme automatiquement tous les fichiers déposés sur le serveur.

```python
extract_tags(string: str, recurse=False)
```

Fonction récupérant l'intégralité des tags contenus dans un commentaire ou une description.

---

## Installation (Linux / Mac)

Pour installer l'environnement virtuel:

1. Ouvrir dans un premier temps le dossier contenant le git dans VSC:

```bash
code nom_dossier_git
```

Ou depuis Fichier > Ouvrir un dossier
Bien vérifier dans le terminal que s'affiche:

```bash
../picshare/
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

- [backlog](https://docs.google.com/spreadsheets/d/17xMIFGWjr49zVxaLiTwf7WM5cqeixjJXqV-JynE_Ijo/edit?usp=sharing)
