#!/bin/bash

echo "-- début du script --"

echo -e "\n-- check venv installation --\n"
sudo pip3 install virtualenv
# vérifie que le module est bien installé

echo -e "\n# création de l'environnement virtuel\n"
python3 -m venv .venv
# installation de l'environnement dans le dossier
source .venv/bin/activate
# active temporairement le venv

echo -e "\n# installation via le fichier requirements.txt\n"
pip3 install --upgrade pip
pip3 install -r installation/requirements.txt
# installe les modules depuis le fichier requirements.txt

echo -e "\n# création du fichier .flaskenv"

echo -e "FLASK_APP=app.py\nFLASK_ENV=development" > .flaskenv
# définit un ensemble de variables, afin d'arrêter le développement et passer
# en production changer la ligne 20.

echo -e "\n-- fin du script --\n"

echo "pour lancer l'environnement :"
echo "source .venv/bin/activate"

echo -e "\n-- informations --\n"
echo "# la mention (.venv) doit être toujours visible dans le terminal lorsque vous travaillez sur ce projet"
echo "# il suffit de lancer flask via 'flask run' l'ENV de dev étant déjà défini dans le fichier .flaskenv"
