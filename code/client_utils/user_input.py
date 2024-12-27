def request_credentials(welcomeMessage):
    print(welcomeMessage)
    username = input("Enter your username: ").strip()
    password = input("Enter your password: ").strip()

    if not username or not password:
        print("Username and password cannot be empty.")
        return request_credentials(welcomeMessage)  # Retry if input is empty

    return username, password


def request_new_credentials():
    username, password = request_credentials(" ")

    # TODO : Appliquer la politique de mot de passe Ici

    return username, password


def request_new_password():
    password = input("Enter your new password: ").strip()

    if not password:
        print("Password cannot be empty.")
        return request_new_password()  # Retry if input is empty

    return password

def menu_choise_1():
    print("=== Menu ===")
    options = {
        "1": "Login",
        "2": "Register",
        "3": "Exit"
    }

    for key, value in options.items():
        print(f"{key}. {value}")

    while True:
        user_choice = input("Enter your choice: ").strip()
        if user_choice in options:
            return int(user_choice)
        else:
            print("Invalid choice. Please try again.")

def menu_choise_2():
    print("=== Client menu ===")
    options = {
        "1": "Send message",
        "2": "Receive message",
        "3": "Change password",
        "4": "Receive Keys",
        "5": "Exit"
    }

    for key, value in options.items():
        print(f"{key}. {value}")

    while True:
        user_choice = input("Enter your choice: ").strip()
        if user_choice in options:
            return int(user_choice)
        else:
            print("Invalid choice. Please try again.")