# CAA-Projet
Implementation Messagerie dans le futur


# Implementation

## Creation de compte (sign_in)

A la creation de compte, on a besoin de deux choses de l'utilisateur :

- Un nom d'utilisateur => username
- Un mot de passe  => password

On a également besoin de deux sels:

1. Pour le hashage du mot de passe de l'utilisateur. Ce hash est utilisé pour l'authentification => sal1
2. Pour la dérivation de la clé symetrique => sal2


Une fois qu'on à nos deux valeurs et deux sels, on va créer les clés pour pouvoir intéragir avec le serveur :
- Le hash pour l'authentification => KDF(password || salt1) = hash_password
- Une paire de clé asymetrique pour le chiffrement => pub_cipher / priv_cipher
- Une paire de clé asymetrique pour la signature => pub_sign / priv_sign
- Une clé symetrique dérivée du mot de passe utilisateur => KDF(password || salt2) = sym


On va chiffrer :
- La clé privée de chiffrement par la clé symetrique => Cipher_sym(priv_sign) = Eb1
- La clé privée de signature par la clé symetrique => Cipher_sym(priv_cipher) = Eb2


On envoit au serveur :
- Username
- Hash_password
- salt1
- salt2
- Eb1
- Eb2
- pub_cipher
- pub_sign

Le serveur recoit les données et les stocks dans une base de donné au format json

## Connexion au compte (login)

L'utilisateur envoit dans un premier temps son nom d'utilisateur au serveur. 

Une fois que le serveur à recu le nom d'utilisateur, il transmet le sel correpondant au client. Si le compte n'existe pas, le serveur transmet un sel aléatoire au client. 

Le client, une fois le sel recu, peut reconstituer le hash mot de passe et le transmettre au serveur.

Si le mot de passe hashé ne correpond pas à ce que le serveur à dans la base de donnée,on recommence la procedure de login.

Si le mot de passe correspond. L'utilisateur est authentifié et on lui transmet les informations pour pouvoir dechiffrer ou envoyer des messages :

- Son nom d'utilisateur => username
- Son mot de passe hashé => hash_password
- Sa clé publique de chiffrement => pub_cipher
- Sa clé publique de signature => pub_sign
- Le sel pour récuper la clé symetrique => salt2
- Le cipher de la clé privée de chiffremeent et de la signature => Eb1 / Eb2


## Envois de message 

Pour executer cette fonction l'utilisateur doit être authentifié. C'est-à-dire être en possesion d'un Username/Hash_password correcte. Il devra les transmettre a chaque fois 

Voici les étapes pour l'envois d'un message dans le future :

1. On crée notre message => M
2. On donne une date à laquelle, on peut le déchiffrer => D
3. On crée la clé symetrique pour chiffrer le message => sym_m
4. On chiffre le message avec la clé symetrique => Cipher_sym_m(M) = C
5. On chiffre la clé symetrique avec la clé publique de la personne à qui on veut envoyer le message => Cipher_pub_cipher(sym_m) = I
6. On signe C || D avec la clé privée de signature de l'expediteur. Cela nous permet de savoir de façon sûr qu'une date est liée à un message => S
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

On doit recree une nouvelle clé symetrique pour chiffré les clés privées => KDF(new_password || new_salt2) = sym_m
On chiffre les clés privées de signature et de chiffrement => Cipher_sym(priv_cipher) = Eb1 / Cipher_sym(priv_sign) = Eb2

On recalcule un nouveau hash de mot de passe => KDF(new_password || new_sal1) = hash_password

Une fois ces étapes effectuées, on peut revoyer au serveur :
- Le cipher de la clé privée de chiffrement par la clé symetrique => Eb1
- Le cipher de la clé privée de signature par la clé symetrique => Eb2
- Le nouveau sel pour le hash du mot de passe => salt1
- Le nouveau hash => hash_password
- Le nouveau sel de la clé symetrique => salt2


# Detail d'implementation 

## Parametres

J'ai suivie le recommandation du ANSSI en therme de taille de parametre cryptographique. L'année choisie est 2030 sur le site keylenght.com

Ce qui me donne ces parametres recommandé : 

* Taille de clé symetrique 128 bits
* Taille des parametres de la courbes Eliptique 256 bits
* Taille de hash 256 bits 

## Algorithme de chiffrement

### Symetrique

Pour le chiffrement symetrique, j'utilise PyNaCl qui utilise XChacha20 pour le chiffrement dans la classe Aead.
Et Poly1305 comme MAC.

La taille de la clé est de 256 bits (un sel de 128 bits et utilisé)
La taille du nonce est de 192 bits.
La taille du compteur est de 64 bits
La taille du bloque est de 512 bits


### Asymetrique

Pour le chiffremeent asymetrique, il se fait sur la courbe eliptique Curve25519 dans la classe Box de PyNaCl

La taille de la clé est de 256 bits

TROUVER DES TAILLES DE PARAM SI POSSIBLE

## Algorithme de signature

L'algorithme de signature est Ed25519

La taille des clés est de 256 bits
La taille du seed est de 256 bits
La taille de la signature est de 512 bits

## Algorithme dérivation de clé

L'algorithme de dérivation de clé est Argon2id.

La taille du sel est de 128 bits
La taille de la clé/hash est de 256 bits

Étant donné que tous les hachages sont effectués côté client et que le serveur n'a pas à supporter la charge de ces calculs, j'ai décidé d'augmenter la valeur des paramètres.


Pour le nombre de thread. Par défaut il y en a 4, j'ai mis a 5 threads
Pour le cout mémoire,la valeur reste inchangé.
Le nombre d'iteration (time_cost). Par defaut il y est a 1, j'ai mis a 20
Le cout en temps est de 0,5 sec en moyenne.

Des tests ont été fait au prealable en local sur mon ordinateur. 

# Amélioration de l'application 

## 1 Mise en place d'un OTP

## 2 Mise en place d'un tunnel TLS

<!-- Lors de la connexion, on établie un canal SSL/TLS entre le serveur et le client. Dans un premier temps, lorsque le canal est confidentiel, on transmet notre nom d'utilisateur. -->



# Potentiel d'amélioration

En l'état actule il n'y a pas de verification de la robustesse du mot de passe. La fonction est en place, mais il manque le code qui applique une politique de mot de passe.
