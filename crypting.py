# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 13:04:21 2020

@author: https://www.thepythoncode.com/article/encrypt-decrypt-files-symmetric-python
"""

from cryptography.fernet import Fernet


def write_key(loc):
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open(loc+"key.key", "wb") as key_file:
        key_file.write(key)


def load_key(loc):
    """
    Loads the key from the current directory named `key.key`
    """
    return open(loc+"key.key", "rb").read()


def encrypt(loc, filename, key):
    """
    Given a filename (str) and key (bytes), it encrypts the file and write it
    """
    f = Fernet(key)
    with open(loc+filename, "rb") as file:
        # read all file data
        file_data = file.read()
    # encrypt data
    encrypted_data = f.encrypt(file_data)
    # write the encrypted file
    with open(loc+filename, "wb") as file:
        file.write(encrypted_data)


def decrypt(loc, filename, key):
    """
    Given a filename (str) and key (bytes), it decrypts the file and write it
    """
    f = Fernet(key)
    with open(loc+filename, "rb") as file:
        # read the encrypted data
        encrypted_data = file.read()
    # decrypt data
    decrypted_data = f.decrypt(encrypted_data)
    # write the original file
    with open(loc+filename, "wb") as file:
        file.write(decrypted_data)


# # String-example
# # generate and write a new key
# # write_key()

# # load the previously generated key
# key = load_key()

# message = "some secret message".encode()

# # initialize the Fernet class
# f = Fernet(key)

# # encrypt the message
# encrypted = f.encrypt(message)
# # print how it looks
# print(encrypted)

# decrypted_encrypted = f.decrypt(encrypted)
# print(decrypted_encrypted)


# # File-example
# # load the key
# key = load_key()
# # file name
# file = "test.txt"
# # encrypt it
# encrypt(file, key)
# # decrypt the file
# decrypt(file, key)
