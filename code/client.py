import ssl
from socket import create_connection

from client_utils.user_input import *
from clientCommunication import *

HOST = '127.0.0.10'  # Adresse IP du serveur
PORT = 65432

def handle_server(client_socket):
    # Stockage des uuid de message recu
    uuid_store = {}
    try:
        while True:
            user_input = menu_choise_1()

            if user_input == 1:
                username, password = request_credentials("Login procedure")
                client_data = login(username, password, client_socket)
                if client_data is not None:
                    handler_app(client_socket, client_data,password,uuid_store)
            elif user_input == 2:
                print("Create Account :")
                sign_in(client_socket)
            elif user_input == 3:
                client_socket.sendall(b'exit')
                break

    except Exception as e:
        print(f"Error in handle_client : {e}")


def handler_app(client_socket, client_data,password,uuid_store):
    try:

        reconstructed_salt2 = HexEncoder.decode(client_data.get("salt2").encode('utf-8'))

        reconstructed_sym = hash_extruder(KDF(password, reconstructed_salt2, 32))
        reconstructed_cipher = nacl.secret.Aead(reconstructed_sym)

        Eb1 = HexEncoder.decode(client_data.get("Eb1").encode('utf-8'))
        Eb2 = HexEncoder.decode(client_data.get("Eb2").encode('utf-8'))

        priv_sign = SigningKey(reconstructed_cipher.decrypt(Eb1), encoder=HexEncoder)
        priv_cipher = PrivateKey(reconstructed_cipher.decrypt(Eb2), encoder=HexEncoder)

        sender = {
            'username': client_data.get("username"),
            'hash_password': HexEncoder.decode(client_data.get("hash_password").encode('utf-8')),
            'pub_cipher': PublicKey(HexEncoder.decode(client_data.get("pub_cipher").encode('utf-8'))),
            'priv_cipher': priv_cipher,
            'pub_sign': VerifyKey(HexEncoder.decode(client_data.get("pub_sign").encode('utf-8'))),
            'priv_sign': priv_sign,
        }

        while True:
            user_input = menu_choise_2()

            if user_input == 1:
                send_message(sender, client_socket)
            elif user_input == 2:
                receive_message(sender, client_socket,uuid_store)
            elif user_input == 3:
                if change_password(sender,client_socket) :
                    break
            elif user_input == 4:
                receive_keys(sender,client_socket,uuid_store)
            else:
                client_socket.sendall(b'end')
                break

    except Exception as e:
        print(f"Error in handler_app: {e}")


def main():
    print("Welcome to DelayPost !")



    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations('certif/client/rootCA.crt')

    with create_connection((HOST,PORT )) as client_socket:
        with context.wrap_socket(client_socket, server_hostname=HOST) as secure_socket:
            handle_server(secure_socket)

    client_socket.close()


if __name__ == "__main__":
    main()