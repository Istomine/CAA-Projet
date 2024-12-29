import json
import socket
import uuid
from datetime import datetime, timedelta

import nacl.utils
from nacl.encoding import HexEncoder

from server_utils.database import user_db, save_user_db
from server_utils.message_database import add_message, get_messages_by_receiver

# Recoit les message
def message_handler(client_socket: socket.socket):
    try:
        # Envoyer 'ok' pour indiquer que le serveur est prêt
        client_socket.sendall(b'ok')

        # Authentification
        username = client_socket.recv(20).decode()
        hash_password_client = client_socket.recv(100).decode()

        if username not in user_db or hash_password_client != user_db[username]['hash_password']:
            client_socket.sendall(b'notok')
            return
        client_socket.sendall(b'ok')

        # Réception de la demande de clé publique
        key_request = client_socket.recv(50).decode()
        if not key_request.startswith('key :'):
            client_socket.sendall(b'notok')
            return

        # Destinataire
        username = key_request[5:].strip()

        # Vérifier si le destinataire existe
        if username not in user_db:
            client_socket.sendall(b'notok')
            return

        # Étape 3 : Envoyer la clé publique du destinataire
        pub_key = user_db[username]['pub_cipher'].encode('utf-8')
        client_socket.sendall(pub_key)


        # Étape 4 : Réception des données sérialisées
        serialized_data = b''
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            serialized_data += data
            # Supposons que le client envoie toutes les données en une seule fois
            if len(data) < 4096:
                break
        print("Données sérialisées reçues")

        # Désérialiser les données
        send_data = json.loads(serialized_data)

        # Étape 5 : Stockage du message dans la base de données des messages
        message_entry = {
            'id' : uuid.uuid4().hex,
            'sender': send_data['sender'],
            'receiver': send_data['receiver'],
            'date': send_data['date'],
            'signature':  send_data['signature'],
            'cipher_message': send_data['cipher_message'],
            'cipher_file_name': send_data['cipher_file_name'],
            'cipher_sym_key': send_data['cipher_sym_key']
        }

        add_message(message_entry)

        # Étape 6 : Envoyer une confirmation au client
        client_socket.sendall(b'received')


    except Exception as e:
        print(f"Error in message_handler : {e}")

# Envoit les message aux clients
def send_messages(client_socket: socket.socket):
    # Envoyer 'ok' pour indiquer que le serveur est prêt
    client_socket.sendall(b'ok')

    # Authentification
    username = client_socket.recv(5).decode()
    hash_password_client = client_socket.recv(100).decode()

    if username not in user_db or hash_password_client != user_db[username]['hash_password']:
        client_socket.sendall(b'notok')
        return
    client_socket.sendall(b'ok')


    id_message = client_socket.recv(4096).decode()
    id_message = json.loads(id_message)


    # Filtrer les messages destinés à l'utilisateur
    user_messages = get_messages_by_receiver(username)

    # Obtenir la date et l'heure courantes
    now = datetime.utcnow() + timedelta(hours=1)

    # Préparer les messages à renvoyer
    response_messages = []
    for msg in user_messages:

        # On controle que le message n'a pas déjà été envoyé pour cette session
        if msg.get('id') in id_message:
            continue

        # Convertir la date du message en objet datetime
        try:
            msg_date = datetime.fromisoformat(msg.get('date'))
        except ValueError:
            # Si le format de la date est incorrect, ignorer ce message
            continue

        # Vérifier si la date du message est dans le passé
        if msg_date < now:
            cipher_sym_key = msg.get('cipher_sym_key')
        else:
            cipher_sym_key = None

        # Préparer le message à inclure dans la réponse
        response_msg = {
            'id' : msg.get('id'),
            'sender': msg.get('sender'),
            'receiver': msg.get('receiver'),
            'date': msg.get('date'),
            'signature': msg.get('signature'),
            'pub_sign' : user_db[msg.get('sender')]['pub_sign'],
            'pub_cipher': user_db[msg.get('sender')]['pub_cipher'],
            'cipher_message': msg.get('cipher_message'),
            'cipher_file_name': msg.get('cipher_file_name'),
            'cipher_sym_key': cipher_sym_key
        }

        response_messages.append(response_msg)

    serialized_data = json.dumps(response_messages).encode('utf-8')
    client_socket.sendall(serialized_data)


def send_keys(client_socket: socket.socket):
    # Envoyer 'ok' pour indiquer que le serveur est prêt
    client_socket.sendall(b'ok')

    # Authentification
    username = client_socket.recv(5).decode()
    hash_password_client = client_socket.recv(100).decode()

    if username not in user_db or hash_password_client != user_db[username]['hash_password']:
        client_socket.sendall(b'notok')
        return
    client_socket.sendall(b'ok')

    # ID des messages dont on a besoin la clé
    id_message = client_socket.recv(4096).decode()
    id_message = json.loads(id_message)

    # Filtrer les messages destinés à l'utilisateur
    user_messages = get_messages_by_receiver(username)

    # Obtenir la date et l'heure courantes
    now = datetime.utcnow() + timedelta(hours=1)


    # Préparer les messages à renvoyer
    response_messages = []
    for msg in user_messages:

        # On traite que les messages deja present chez le client
        if msg.get('id') not in id_message:
            continue

        # Convertir la date du message en objet datetime
        try:
            msg_date = datetime.fromisoformat(msg.get('date'))
        except ValueError:
            # Si le format de la date est incorrect, ignorer ce message
            continue

        # Vérifier si la date du message est dans le passé
        if msg_date < now:
            cipher_sym_key = msg.get('cipher_sym_key')
        else:
            cipher_sym_key = None

        # Préparer le message à inclure dans la réponse
        response_msg = {
            'id': msg.get('id'),
            'date': msg.get('date'),
            'pub_cipher': user_db[msg.get('sender')]['pub_cipher'],
            'cipher_file_name': msg.get('cipher_file_name'),
            'cipher_sym_key': cipher_sym_key
        }

        response_messages.append(response_msg)

    serialized_data = json.dumps(response_messages).encode('utf-8')
    client_socket.sendall(serialized_data)


def change_password(client_socket: socket.socket):
    try:
        # Envoyer 'ok' pour indiquer que le serveur est prêt
        client_socket.sendall(b'ok')

        # Authentification
        username = client_socket.recv(5).decode()
        hash_password_client = client_socket.recv(100).decode()

        if username not in user_db or hash_password_client != user_db[username]['hash_password']:
            client_socket.sendall(b'notok')
            return
        client_socket.sendall(b'ok')

        # Étape 4: Recevoir les nouvelles données de mot de passe (JSON)
        # Étape 2 : Recevoir les données d'inscription sérialisées
        serialized_data = b''
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            serialized_data += data
            # Supposons que le client envoie toutes les données en une seule fois
            if len(data) < 4096:
                break

        if not serialized_data:
            client_socket.sendall(b'notok')
            print("Aucune donnée reçue pour le changement de mot de passe.")
            return False

        changed_paswd_data = json.loads(serialized_data.decode('utf-8'))

        # Mettre à jour la base de données utilisateur
        user_db[username]['hash_password'] = changed_paswd_data['hash_password']
        user_db[username]['salt1'] = changed_paswd_data['salt1']
        user_db[username]['salt2'] = changed_paswd_data['salt2']
        user_db[username]['Eb1'] = changed_paswd_data['Eb1']
        user_db[username]['Eb2'] = changed_paswd_data['Eb2']

        save_user_db(user_db)

        # Envoyer 'ok' pour indiquer que le changement de mot de passe a réussi
        client_socket.sendall(b'ok')
        return True


    except Exception as e:
        print(f"Erreur lors du changement de mot de passe: {e}")
        return False


def sign_in_handler(client_socket: socket.socket):
    try:

        client_socket.sendall(b'ok')

        # Étape 2 : Recevoir les données d'inscription sérialisées
        serialized_data = b''
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            serialized_data += data
            # Supposons que le client envoie toutes les données en une seule fois
            if len(data) < 4096:
                break
        print("Données d'inscription sérialisées reçues")

        # Désérialiser les données
        sign_in_data = json.loads(serialized_data)

        username = sign_in_data['username']

        # Vérifier si l'utilisateur existe déjà
        if username in user_db:
            client_socket.sendall(b'notok')
            print(f"Inscription échouée : l'utilisateur '{username}' existe déjà")
            return

        # Enregistrer l'utilisateur dans la base de données sérializé
        user_db[username] = {
            'username': username,
            'hash_password': sign_in_data['hash_password'],
            'salt1': sign_in_data['salt1'],
            'salt2': sign_in_data['salt2'],
            'Eb1': sign_in_data['Eb1'],
            'Eb2': sign_in_data['Eb2'],
            'pub_cipher' : sign_in_data['pub_cipher'],
            'pub_sign' : sign_in_data['pub_sign'],
        }

        # Sauvegarder la base de données
        save_user_db(user_db)
        print(f"Utilisateur '{username}' inscrit avec succès")

        # Envoyer une confirmation au client
        client_socket.sendall(b'ok')

    except Exception as e:
        print(f"Erreur dans sign_in_handler : {e}")
        try:
            client_socket.sendall(b'error')
        except:
            pass


def login_handler(client_socket: socket.socket):
    try:
        client_socket.sendall(b'ok')

        # Étape 2 : Recevoir le nom d'utilisateur
        username = client_socket.recv(1024).decode().strip()

        if username in user_db:
            salt1 = HexEncoder.decode(user_db[username]['salt1'].encode('utf-8'))  # Utilisateur existe
        else:
            salt1 = nacl.utils.random(16)  # Utilisateur inexiste

        # Envoyer salt1 au client
        client_socket.sendall(salt1)

        # Recevoir le hash du mot de passe du client
        hash_password_client = HexEncoder.encode(client_socket.recv(1024)).decode('utf-8')

        # Comparer avec le hash stocké
        if  username in user_db and hash_password_client == user_db[username]['hash_password']:
            print(f"Utilisateur '{username}' authentifié avec succès")

            # Préparer les données à envoyer
            data_to_send = {
                'username': user_db[username]['username'],
                'hash_password': user_db[username]['hash_password'],
                'pub_cipher': user_db[username]['pub_cipher'],
                'pub_sign': user_db[username]['pub_sign'],
                'salt2': user_db[username]['salt2'],
                'Eb1': user_db[username]['Eb1'],
                'Eb2': user_db[username]['Eb2']
            }

            # Sérialiser en JSON
            serialized_data = json.dumps(data_to_send).encode('utf-8')

            # Envoyer les données sérialisées
            client_socket.sendall(serialized_data)
            return True
        else:
            client_socket.sendall(b'notok')
            return False


    except Exception as e:
        print(f"Erreur dans login_handler : {e}")


