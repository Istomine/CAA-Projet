from datetime import datetime

def get_user_datetime():
    while True:
        try:
            # Demander une entrée utilisateur
            user_input = input("Entrez une date et une heure au format 'AAAA-MM-JJ HH:MM': ")

            # Convertir l'entrée en objet datetime
            user_datetime = datetime.strptime(user_input, "%Y-%m-%d %H:%M")

            # Convertir en chaîne ISO 8601
            iso_datetime = user_datetime.isoformat()

            print("Date et heure formatées :", iso_datetime)

            # Retourner l'objet datetime
            return iso_datetime
        except ValueError:
            print("Format invalide. Veuillez entrer la date et l'heure au format 'AAAA-MM-JJ HH:MM'.")
