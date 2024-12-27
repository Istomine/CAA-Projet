import os
import socket

import nacl.utils
import nacl.secret
from nacl.encoding import HexEncoder


# Chiffrement et déchiffrement des messages
def process_file(file_path,sym_m ,mode='encrypt'):
    try:
        if mode == 'encrypt':
            # Lire le message à partir du fichier
            with open(file_path, 'r') as file:
                message = file.read().strip()
            print(f"Message read from file: {message}")

            # Lire le nom du fichier
            file_name = os.path.basename(file_path)

            cipher_sym = nacl.secret.Aead(sym_m)

            # Chiffrer le message
            encrypted_message = cipher_sym.encrypt(message.encode())

            # Chiffrer le nom du fichier
            encrypted_file_name = cipher_sym.encrypt(file_name.encode())

            # Réécrire le fichier avec le message chiffré
            return encrypted_message ,encrypted_file_name

        elif mode == 'decrypt':
            # Lire le message chiffré à partir du fichier
            with open(file_path, 'rb') as file:
                encrypted_message = file.read()

            encrypted_message = HexEncoder.decode(encrypted_message)

            # Lire le nom du fichier
            encrypted_file_name = os.path.basename(file_path)
            encrypted_file_name = HexEncoder.decode(encrypted_file_name.encode())

            cipher_sym = nacl.secret.Aead(sym_m)

            # Déchiffrer le message
            decrypted_message = cipher_sym.decrypt(encrypted_message).decode()


            # Déchiffrer le nom du fichier
            decrypted_file_name = cipher_sym.decrypt(encrypted_file_name).decode()


            # Réécrire le fichier avec le message déchiffré
            return decrypted_message , decrypted_file_name

        else:
            print("Invalid mode. Use 'encrypt' or 'decrypt'.")
    except FileNotFoundError:
        print(f"Error: The file at '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def test_socket(client_socket :socket.socket):
    if client_socket is None:
        print("Le socket client est invalide.")
        return True

    try:
        # Tentative d'envoi d'une donnée pour vérifier la connexion
        client_socket.sendall(b'')
    except (socket.error, socket.timeout):
        print("Le socket client n'est pas connecté.")
        return True

    return False

