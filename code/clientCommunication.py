import json
import os
import nacl.hash
import socket
import nacl.secret
import nacl.utils

from nacl.public import PrivateKey, Box, PublicKey
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey


from client_utils.communication_utils import process_file, test_socket
from client_utils.crypto_utils import KDF, hash_extruder
from client_utils.time_utils import get_user_datetime
from client_utils.user_input import request_new_credentials, request_new_password

host = '127.0.0.10'
port = 65432
path_revceived_message = 'messages/received'


def sign_in(client_socket : socket.socket):
    try:
        if test_socket(client_socket):
            return

        client_socket.sendall(b'signin')

        if client_socket.recv(5).decode() == 'notok':
            print("The server is not ready to receive information")
            return

        # Creation des creds
        username , password = request_new_credentials()
        # Creation des sels
        salt1 = nacl.utils.random(16)
        salt2 = nacl.utils.random(16)
        # Creation du hash pour l'authentification 256 bits
        hash_password = hash_extruder(KDF(password, salt1, 32))
        # Generation des clés pour le chiffrement
        priv_cipher = PrivateKey.generate()
        pub_cipher = priv_cipher.public_key
        # Generation des clés pour la signature
        priv_sign = SigningKey.generate()
        pub_sign = priv_sign.verify_key
        # Generation de la clé symetrique 256 bits
        sym = hash_extruder(KDF(password, salt2, 32))
        # Creation Aead pour chiffrement symetrique
        cipher = nacl.secret.Aead(sym)
        # Chiffrement des clés privées
        Eb1 = cipher.encrypt(priv_sign.encode(encoder=HexEncoder))
        Eb2 = cipher.encrypt(priv_cipher.encode(encoder=HexEncoder))

        sign_in_data = {
            'username' : username,
            'hash_password' : HexEncoder.encode(hash_password).decode('utf-8'),
            'salt1' : HexEncoder.encode(salt1).decode('utf-8'),
            'salt2' : HexEncoder.encode(salt2).decode('utf-8'),
            'Eb1' :HexEncoder.encode(Eb1).decode('utf-8'),
            'Eb2' : HexEncoder.encode(Eb2).decode('utf-8'),
            'pub_cipher' : pub_cipher.encode(encoder=HexEncoder).decode('utf-8'),
            'pub_sign' : pub_sign.encode(encoder=HexEncoder).decode('utf-8'),
        }

        serialized_data = json.dumps(sign_in_data).encode('utf-8')
        client_socket.sendall(serialized_data)

        if client_socket.recv(5).decode() == 'notok':
            print("Error during signing, please try again")
            return

        print("User created !")

    except Exception as e:
        print("Error in sign_in :", e)


def login(username, password, client_socket :socket.socket):
    try:
        if test_socket(client_socket):
            return

        client_socket.sendall(b'login')

        if client_socket.recv(5).decode() == 'notok':
            print("The server is not ready to receive information")
            return

        client_socket.sendall(username.encode())

        salt1 = client_socket.recv(1024)

        hash_password = hash_extruder(KDF(password, salt1, 32))

        client_socket.sendall(hash_password)
        serialized_data = client_socket.recv(1024).decode()

        if serialized_data == 'notok':
            print("The user of password is wrong")
            return None

        client_data = json.loads(serialized_data)

        return client_data

    except Exception as e:
        print("Error in login_procedure :", e)


def send_message(sender,client_socket : socket.socket):
    try:
        if test_socket(client_socket):
            return

        client_socket.sendall(b'sendmsg')

        if client_socket.recv(5).decode() == 'notok':
            print("The server is not ready to receive information")
            return

        # Authentification
        client_socket.sendall(sender.get("username").encode())
        client_socket.sendall(HexEncoder.encode(sender.get("hash_password")))

        # Attendre la réponse du serveur
        server_response = client_socket.recv(5)
        if server_response == b'notok':
            print("Incorrect authentication")
            return

        receiver = input("Who is the receiver ? : ").strip()

        client_socket.sendall(b'key :' + receiver.encode())

        key = client_socket.recv(1024)

        if key.decode() == 'notok':
            print(f"Key not found for {receiver}")
            return

        pub_cipher_receiver =  PublicKey(HexEncoder.decode(key))

        # Recuperation du chemin vers le fichier
        file_path = input("Enter path to message: ").strip()

        # Creation d'une clé symetrique
        sym_m = nacl.utils.random(nacl.secret.Aead.KEY_SIZE)

        # Recuperation du contenue du fichier et chiffrement de ce dernier
        c_message , c_file_name = process_file(file_path, sym_m, 'encrypt')

        # Date de déchiffrement du message
        date = get_user_datetime()  # Date formaté AAAA-MM-JJ HH:MM

        # Chiffrement de la clé symetrique
        cipher_asym = Box(sender.get("priv_cipher"), pub_cipher_receiver)
        i = cipher_asym.encrypt(sym_m)

        # Singature du hash du message chiffré + nom du fichier chiffré + date
        c_message = HexEncoder.encode(c_message).decode('utf-8')
        c_file_name = HexEncoder.encode(c_file_name).decode('utf-8')
        data_to_sign = nacl.hash.sha512( c_message.encode() + c_file_name.encode() + date.encode(), encoder=HexEncoder)
        s = sender.get("priv_sign").sign(data_to_sign)

        send_data = {
            'sender': sender.get("username"),
            'receiver': receiver,
            'date': date,
            'signature' : HexEncoder.encode(s).decode('utf-8'),
            'cipher_message' : c_message,
            'cipher_file_name': c_file_name,
            'cipher_sym_key' : HexEncoder.encode(i).decode('utf-8')
        }
        serialized_data = json.dumps(send_data).encode('utf-8')
        client_socket.sendall(serialized_data)

        if client_socket.recv(8).decode() == 'received':
            print("Message sent")

    except Exception as e:
        print("Error in send_message :", e)


def receive_message(sender, client_socket : socket.socket,uuid_store):
    try:

        if test_socket(client_socket):
            return
        client_socket.sendall(b'recvmsg')

        # Attendre le signal 'ok' du serveur
        if client_socket.recv(2) != b'ok':
            print("The server is not ready to receive information")
            return

        # Authentification
        client_socket.sendall(sender.get("username").encode())
        client_socket.sendall(HexEncoder.encode(sender.get("hash_password")))

        # Attendre la réponse du serveur après l'envoi du mot de passe
        server_response = client_socket.recv(5)
        if server_response == b'notok':
            print("Incorrect authentication")
            return

        # Envoyé le id de message deja telechargé
        json_all_uuids = json.dumps(list(uuid_store.keys()))
        client_socket.sendall(json_all_uuids.encode())


        # Recevoir les messages JSON du serveur
        received_data = client_socket.recv(4096)

        # Désérialiser les données JSON
        messages = json.loads(received_data.decode('utf-8'))

        # Traitement des messages reçus
        for msg in messages:
            # Clé de l'emetteur du message
            pub_sign = VerifyKey(HexEncoder.decode(msg.get("pub_sign").encode('utf-8')))

            # Controle de la signature
            signature = HexEncoder.decode(msg.get("signature").encode('utf-8'))
            try:
                # Si la signature est juste la fonction renvoit les données signé
                hashed_data = pub_sign.verify(signature)

                # On regarde si on a controler la signature du bon message
                control_data = nacl.hash.sha512(msg['cipher_message'].encode() + msg['cipher_file_name'].encode() + msg['date'].encode(), encoder=HexEncoder)
                if hashed_data.decode() != control_data.decode():
                    raise nacl.exceptions.BadSignatureError

            except nacl.exceptions.BadSignatureError:
                print(f"Signature control failed for {msg['id']} the message was skipped")
                continue

            # Dechiffrement du message
            file_name = ""
            message = ""
            is_ciphered = False
            if msg.get("cipher_sym_key") is None:
                print(f"Message with id : {msg.get('id')} will be available on : {msg.get('date')}")
                file_name = msg.get("cipher_file_name")
                message = msg.get("cipher_message")
                is_ciphered = True
            else:
                # Clé symetrique chiffrée. Elle chiffre le message et le nom du fichier
                cipher_sym_m = HexEncoder.decode(msg.get("cipher_sym_key").encode('utf-8'))
                # Clé publique de l'emetteur du message. Controle de signature
                pub_cipher = PublicKey(HexEncoder.decode(msg.get("pub_cipher").encode('utf-8')))

                # Reconstruction de la Box asymetrique pour déchiffrer la clé symetrique
                reconstructed_cipher_box = Box(sender.get("priv_cipher"),pub_cipher)
                # Dechiffrement de la clé symetrique
                sym_m = reconstructed_cipher_box.decrypt(cipher_sym_m)
                # Reconstruction du systeme de chiffrement symetrique
                sym_cipher = nacl.secret.Aead(sym_m)
                # Dechiffrement du nom du fichier et du message
                file_name = sym_cipher.decrypt(HexEncoder.decode(msg.get("cipher_file_name").encode('utf-8'))).decode()
                message = sym_cipher.decrypt(HexEncoder.decode(msg.get("cipher_message").encode('utf-8'))).decode()


            # Creation du fichier peut importe s'il est chiffré ou pas
            file_path = os.path.join(path_revceived_message, file_name)
            with open(file_path, "w", encoding='utf-8') as file:
                file.write(message)

            # Savoir quel fichier son chiffré pour recuperer que leur clé
            uuid_store[msg.get('id')] = is_ciphered

    except Exception as e:
        print("Error in receive_message :", e)


def change_password(sender, client_socket : socket.socket):
    try:
        if test_socket(client_socket):
            return False

        client_socket.sendall(b'changepswd')

        if client_socket.recv(5).decode() == 'notok':
            print("The server is not ready to receive information")
            return False

        # Authentification
        client_socket.sendall(sender.get("username").encode())
        client_socket.sendall(HexEncoder.encode(sender.get("hash_password")))

        # Attendre la réponse du serveur après l'envoi du mot de passe
        server_response = client_socket.recv(5)
        if server_response == b'notok':
            print("Incorrect authentication")
            return

        new_password = request_new_password()

        # Creation des nouveaux sels
        salt1 = nacl.utils.random(16)
        salt2 = nacl.utils.random(16)

        # Creation du hash pour l'authentification 256 bits
        hash_password = hash_extruder(KDF(new_password, salt1, 32))

        # Generation de la clé symetrique 256 bits
        sym = hash_extruder(KDF(new_password, salt2, 32))

        cipher_sym = nacl.secret.Aead(sym)

        # Chiffrement des clés privées
        Eb1 = cipher_sym.encrypt(sender.get("priv_sign").encode(encoder=HexEncoder))
        Eb2 = cipher_sym.encrypt(sender.get("priv_cipher").encode(encoder=HexEncoder))

        changed_paswd_data = {
            'hash_password' : HexEncoder.encode(hash_password).decode('utf-8'),
            'salt1' : HexEncoder.encode(salt1).decode('utf-8'),
            'salt2' : HexEncoder.encode(salt2).decode('utf-8'),
            'Eb1' :HexEncoder.encode(Eb1).decode('utf-8'),
            'Eb2' : HexEncoder.encode(Eb2).decode('utf-8'),
        }

        serialized_data = json.dumps(changed_paswd_data).encode('utf-8')
        client_socket.sendall(serialized_data)

        if client_socket.recv(5).decode() == 'notok':
            print("The server is not ready to receive information, please try again")
            return False

        print("Password changed !")
        return True

    except Exception as e:
        print("Error in change_password :", e)


def receive_keys(sender, client_socket : socket.socket,uuid_store):
    try:

        if test_socket(client_socket):
            return
        client_socket.sendall(b'recvkeys')

        # Étape 1 : Attendre le signal 'ok' du serveur
        if client_socket.recv(2) != b'ok':
            print("The server is not ready to receive information")
            return

        # Authentification
        client_socket.sendall(sender.get("username").encode())
        client_socket.sendall(HexEncoder.encode(sender.get("hash_password")))

        # Attendre la réponse du serveur après l'envoi du mot de passe
        server_response = client_socket.recv(5)
        if server_response == b'notok':
            print("Incorrect authentication")
            return

        # Envoyé le id de message chiffré
        json_all_uuids = json.dumps([uuid for uuid, value in uuid_store.items() if value is True])
        client_socket.sendall(json_all_uuids.encode())

        # Étape 6 : Recevoir les messages JSON du serveur
        received_data = client_socket.recv(4096)

        # Désérialiser les données JSON
        messages = json.loads(received_data.decode('utf-8'))

        for msg in messages:

            if msg['cipher_sym_key'] is None:
                print(f"Message with id : {msg.get('id')} will be available on : {msg.get('date')}")
            else:
                # Clé symetrique chiffrée. Elle chiffre le message et le nom du fichier
                cipher_sym_m = HexEncoder.decode(msg.get("cipher_sym_key").encode('utf-8'))
                # Clé publique de l'emetteur du message. Controle de signature
                pub_cipher = PublicKey(HexEncoder.decode(msg.get("pub_cipher").encode('utf-8')))

                # Reconstruction de la Box asymetrique pour déchiffrer la clé symetrique
                reconstructed_cipher_box = Box(sender.get("priv_cipher"), pub_cipher)
                # Dechiffrement de la clé symetrique
                sym_m = reconstructed_cipher_box.decrypt(cipher_sym_m)
                # Reconstruction du systeme de chiffrement symetrique
                # Dechiffrement du nom du fichier et du message
                encrypted_file_name = msg.get("cipher_file_name")
                file_path = os.path.join(path_revceived_message, encrypted_file_name)
                decrypted_message , decrypted_file_name = process_file(file_path,sym_m,'decrypt')

                file_path = os.path.join(path_revceived_message, decrypted_file_name)
                with open(file_path, "w", encoding='utf-8') as file:
                    file.write(decrypted_message)

                uuid_store[msg.get('id')] = False

    except Exception as e:
        print("Error in receive_keys :", e)

