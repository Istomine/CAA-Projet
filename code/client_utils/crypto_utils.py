import base64

from argon2 import PasswordHasher


def KDF(password,salt,hash_len):
    ph = PasswordHasher(20,65536,5,hash_len,16,"utf-8")
    return ph.hash(password, salt=salt)


def hash_extruder(argon_hash):
    hash = argon_hash.split('$')[-1]
    return base64.b64decode(hash + '==')