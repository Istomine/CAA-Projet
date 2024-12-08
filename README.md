# CAA-Projet
Implementation Messagerie dans le futur


# Implementation

## Creation de compte

A la creation de compte, on a besoin de deux choses de l'utilisateur :

- Un nom d'utilisateur
- Un mot de passe (avec contrôle de la robustesse du mot de passe)

On applique une politique de mot de passe assez strict pour garantir qu'on ait des mot de passe solide :

- Longeur minimum 12 caractères
- Longeur maximale 64 caractères
- Utilisation d'au minimum 1 majuscules
- Utilisation d'au minimum 1 chiffres
- Utilisation d'au minimum 1 symboles spécial
- Autorisation des caractère ascii uniquement 

Etant donnée qu'il n'est plus recommandé d'imposer des exigences strict en therme de complexité de mot de passe. Une complexite en longeur sera imposé

Une fois qu'on à nos deux valeurs, on va créer les clés pour pouvoir intéragir avec le serveur :
- Une paire de clé asymetrique pour le chiffrement
- Une paire de clé asymetrique pour la signature
- Une clé symetrique dérivée du mot de passe utilisateur => KDF(password || sel1)
- Le cipher de la clé privée de chiffrement par la clé symetrique
- Le cipher de la clé privée de signature pat la clé symetrique
- Le hash de KDF(password || sel1) pour l'authentification

## Connexion au compte

Lors de la connexion, on établie un canal SSL/TLS entre le serveur et le client. Dans un premier temps, lorsque le canal est confidentiel, on transmet notre nom d'utilisateur.

Une fois que le serveur à recu le nom d'utilisateur, il transmet le sel correpondant au client

Le client, une fois le sel recu, peut reconstituer le hash mot de passe et le transmettre au serveur.

Si le mot de passe hashé ne correpond pas à ce que le serveur à dans la base de donnée, on coupe la connexion TLS.

Si le mot de passe correspond. L'utilisateur est authentifié et on lui transmet les informations pour pouvoir dechiffrer les messages recu ou envoyer des messages :

- Sa clé publique de chiffrement
- Sa clé publique de signature
- Le sel pour récuper la clé symetrique
- le cipher de la clé privée du chiffremeent et de la signature

## Envois de message 

Voici les étapes pour l'envois d'un message dans le future :

1. On crée notre message M
2. On donne une date à laquelle, on peut le déchiffrer. On obtient D
3. On crée la clé symetrique pour chiffrer le message
4. On chiffre le message avec la clé symetrique, on obtient C
5. On chiffre la clé symetrique avec la clé publique de la personne à qui on veut envoyer le message, on obtient I
6. On signe C || D avec la clé privée de signature. On obtient S
7. On transmet au serveur S, D, C , I , Destinataire du message

## Reception du message 

Si Alice envoit un message à Bob. Ce dernier peut le récuper, mais temps que la date que Alice à décidée n'est pas atteinte, Bob ne pourra pas déchiffrer le message.

Bob peut donc dans un premier temps juste récuperer C, le message chiffré.
Il peut également récuperer la clé publique de signature d'Alice pour controler que c'est elle qui envoit.

Une fois la date arrivée, le serveur peut envoyé la clé de déchiffrement à Bob.

# Amélioration de l'application 

## 1 Mise en place d'un OTP

## 2 
