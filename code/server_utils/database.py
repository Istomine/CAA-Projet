# database.py
import json
import os
from threading import Lock

# Chemin vers le fichier de la base de données des utilisateurs (fichier JSON)
USER_DB_FILE = 'user_database.json'

# Initialisation d'un verrou pour assurer la thread-safety
db_lock = Lock()

def load_user_db():
    """Charge la base de données des utilisateurs depuis un fichier JSON."""
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_user_db(user_db):
    """Sauvegarde la base de données des utilisateurs dans un fichier JSON."""
    with db_lock:
        with open(USER_DB_FILE, 'w') as f:
            json.dump(user_db, f, indent=4)

# Charger la base de données au démarrage
user_db = load_user_db()
