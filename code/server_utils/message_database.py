# message_database.py
import json
import os
from threading import Lock

# Chemin vers le fichier de la base de données des messages (fichier JSON)
MESSAGES_DB_FILE = 'messages_database.json'

# Initialisation d'un verrou pour assurer la thread-safety
db_lock = Lock()

def load_messages_db():
    """Charge la base de données des messages depuis un fichier JSON."""
    if os.path.exists(MESSAGES_DB_FILE):
        with open(MESSAGES_DB_FILE, 'r') as f:
            return json.load(f)
    else:
        return []

def save_messages_db(messages_db):
    """Sauvegarde la base de données des messages dans un fichier JSON."""
    with db_lock:
        with open(MESSAGES_DB_FILE, 'w') as f:
            json.dump(messages_db, f, indent=4)

def add_message(message):
    """Ajoute un message à la base de données des messages."""
    messages_db = load_messages_db()
    messages_db.append(message)
    save_messages_db(messages_db)

def get_messages_by_receiver(receiver):
    """
    Recherche et renvoie tous les messages destinés à un certain receiver.

    Args:
        receiver (str): Le nom du destinataire des messages.

    Returns:
        list: Une liste de dictionnaires représentant les messages destinés au receiver spécifié.
    """
    with db_lock:
        messages_db = load_messages_db()
        filtered_messages = [message for message in messages_db if message.get('receiver') == receiver]
    return filtered_messages