from server_utils.serverCommunication import *

HOST = '127.0.0.10'  # Adresse IP du serveur
PORT = 65432        # Port d'écoute

def handle_client(client_socket, addr):
    try:

        while True:
            print(f"Gestion de la connexion client : {addr}")

            # Recevoir le premier message pour déterminer l'action (login ou signin)
            initial_message = client_socket.recv(10).decode().strip()

            if initial_message.startswith('login'):
                # Si le message commence par 'Login', déléguer au login_handler
                if login_handler(client_socket):
                    handle_app(client_socket)
            elif initial_message.startswith('signin'):
                # Si le message commence par 'signin', déléguer au sign_in_handler
                sign_in_handler(client_socket)
            elif initial_message.startswith('exit'):
                break
            else:
                client_socket.sendall(b'notok')  # Message inconnu


    except Exception as e:
        print(f"Erreur dans handle_client : {e}")
    finally:
        print(f"Connexion fermée pour {addr}")


def handle_app(client_socket):
    try:

        while True:
            # Recevoir le premier message pour déterminer l'action (login ou signin)
            initial_message = client_socket.recv(10).decode().strip()

            if initial_message.startswith('sendmsg'):
                message_handler(client_socket)
            elif initial_message.startswith('recvmsg'):
                send_messages(client_socket)
            elif initial_message.startswith('changepswd'):
                if change_password(client_socket):
                    print("Password changed !")
                    break
                print("Password didn't change")
            elif initial_message.startswith('recvkeys'):
                send_keys(client_socket)
            else:
               break


    except Exception as e:
        print(f"Erreur dans handle_client : {e}")


def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Serveur en écoute sur {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            print(f"Connexion acceptée de {addr}")
            handle_client(conn, addr)
            conn.close()




if __name__ == "__main__":
    run_server()