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
