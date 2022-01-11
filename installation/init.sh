#!/bin/bash

echo "-- début du script --"

echo "-- check venv installation --"
sudo pip3 install virtualenv

echo "# création de l'environnement virtuel"
python3 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade pip
pip3 install pycodestyle

echo -e "\n# installation de flask"
pip3 install flask


echo -e "\n# création d'un fichier setting pour FLASK\n"
pip3 install python-dotenv

echo -e "FLASK_APP=run.py\nFLASK_ENV=development" > .flaskenv

echo
echo "-- fin du script --"
echo
echo "pour lancer l'environnement :"
echo "source .venv/bin/activate"
echo
echo "-- informations --"
echo "# la mention (.venv) doit être toujours visible dans le terminal lorsque vous travaillez sur ce projet"
echo "# il suffit de lancer flask via 'flask run' l'ENV de dev étant déjà défini dans le fichier .flaskenv"