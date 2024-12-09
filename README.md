# CAA-Projet
Implementation Messagerie dans le futur


# Implementation

## Creation de compte

A la creation de compte, on a besoin de deux choses de l'utilisateur :

- Un nom d'utilisateur => username
- Un mot de passe (avec contrôle de la robustesse du mot de passe) => password

On applique une politique de mot de passe assez strict pour garantir qu'on ait des mot de passe solide :

- Longeur minimum 12 caractères
- Longeur maximale 64 caractères
- Utilisation d'au minimum 1 majuscules
- Utilisation d'au minimum 1 chiffres
- Utilisation d'au minimum 1 symboles spécial
- Autorisation des caractère ascii uniquement 

Etant donnée qu'il n'est plus recommandé d'imposer des exigences strict en therme de complexité de mot de passe. Une complexite en longeur sera imposé

Une fois qu'on à nos deux valeurs, on va créer les clés pour pouvoir intéragir avec le serveur :
- Le hash pour l'authentification => KDF(password || sel1) = password_hash
- Une paire de clé asymetrique pour le chiffrement => pub_cipher / priv_cipher
- Une paire de clé asymetrique pour la signature => pub_sign / priv_sign
- Une clé symetrique dérivée du mot de passe utilisateur => KDF(password || sel2) = sym


Et on va chiffrer :
- Le cipher de la clé privée de chiffrement par la clé symetrique => Cipher_sym(priv_cipher) = Eb1
- Le cipher de la clé privée de signature par la clé symetrique => Cipher_sym(priv_sign) = Eb2


On envoit au serveur :
- Username
- Hash_password
- salt1
- pub_cipher
- pub_sign
- salt2
- Eb1
- Eb2

## Connexion au compte

<!-- Lors de la connexion, on établie un canal SSL/TLS entre le serveur et le client. Dans un premier temps, lorsque le canal est confidentiel, on transmet notre nom d'utilisateur. -->

L'utilisateur envoit dans un premier temps son nom d'utilisateur au serveur. 

Une fois que le serveur à recu le nom d'utilisateur, il transmet le sel correpondant au client. Si le compte n'existe pas, le serveur transmet un sel aléatoire au client. 

Le client, une fois le sel recu, peut reconstituer le hash mot de passe et le transmettre au serveur.

Si le mot de passe hashé ne correpond pas à ce que le serveur à dans la base de donnée, on redemande au client de saisir son mot de passe.

Si le mot de passe correspond. L'utilisateur est authentifié et on lui transmet les informations pour pouvoir dechiffrer les messages recu ou envoyer des messages :

- Sa clé publique de chiffrement => pub_cipher
- Sa clé publique de signature => pub_sign
- Le sel pour récuper la clé symetrique => salt2
- le cipher de la clé privée du chiffremeent et de la signature => Eb1 / Eb2

## Envois de message 

Voici les étapes pour l'envois d'un message dans le future :

1. On crée notre message => M
2. On donne une date à laquelle, on peut le déchiffrer => D
3. On crée la clé symetrique pour chiffrer le message => sym_m
4. On chiffre le message avec la clé symetrique => Cipher_sym_m(M) = C
5. On chiffre la clé symetrique avec la clé publique de la personne à qui on veut envoyer le message => Cipher_pub_cipher(sym_m) = I
6. On signe C || D avec la clé privée de signature de la personne qui envoit le message. Cela nous permet de savoir de façon sûr qu'une date est liée à un message => S
7. On transmet au serveur S, D, C , I , Destinataire du message

## Reception du message 

La personne ayant reçu un message peut le télécharger à tout moment depuis le serveur. Toutefois, elle ne reçoit pas immédiatement la clé permettant de déchiffrer le contenu. Cette clé lui est transmise uniquement lorsque la date spécifiée est atteinte.

La personne ayant reçu le message peut également recuperer la clé publique de signature de la personne qui a envoyer le message pour controler la signature.

Le serveur transmet au destinataire :
- C, le message chiffré
- S, la signature du message
- D, la date de déchiffrement
- pub_sign, la clé pour controler la signature

Une fois qu'on a atteint la date, le destinataire recoit :
- I, la clé de déchiffremeent 

## Changement de mot de passe 

Pour pouvoir changer de mot de passe, on doit d'abord être connecté. 

Le serveur nous restransmet les fichiers suivant pour qu'on puisse les rechiffrer :
- Le cipher de la clé privée de chiffrement par la clé symetrique => Eb1
- Le cipher de la clé privée de signature par la clé symetrique => Eb2

On doit recree une nouvelle clé symetrique pour chiffré les clés privées => KDF(new_password || new_salt2) = sym_m
On chiffre les clés privées de signature et de chiffrement => Cipher_sym(priv_cipher) = Eb1 / Cipher_sym(priv_sign) = Eb2

On recalcule un nouveau hash de mot de passe => KDF(new_password || new_sal1) = hash_password

Une fois ces étapes effectuées, on peut revoyer au serveur :
- Le cipher de la clé privée de chiffrement par la clé symetrique => Eb1
- Le cipher de la clé privée de signature par la clé symetrique => Eb2
- Le nouveau sel pour le hash du mot de passe => salt1
- Le nouveau hash => hash_password
- Le nouveau sel de la clé symetrique => salt2

# Amélioration de l'application 

## 1 Mise en place d'un OTP

## 2 Mise en place d'un tunnel TLS

## Déchiffrement offline (a voir)

## Envoit groupé
