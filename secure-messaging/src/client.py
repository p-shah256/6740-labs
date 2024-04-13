import argparse
import hashlib
import json
import os
import random
import socket
from pathlib import Path

import yaml
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import helpers

# TODO: 1. session key management
#       2. logout protocol, forget
#       3. create PK and SK
#       4. validate attempts
"""
{
        user : { 
            session_key : "",
            socket : socket,
            PK : user's PK
            },
        }
"""


class Client:
    def __init__(self, username, password, p, g, server_port):
        self.username = username

        self.password = int(hashlib.sha3_512(password.encode()).hexdigest(), 16)

        # FIXME: check if 'a' can stay the same for all diffie hellman exchanges

        # TODO double check this range
        # https://www.ibm.com/docs/en/zvse/6.2?topic=overview-diffie-hellman
        self.a = random.randint(1, p - 2)
        self.p = p
        self.g = g

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect(("localhost", server_port))
        # TODO: store server's session key here
        self.session_keys = {}

        # TODO: check if handshake is sucessful
        self.handshake()
        # TODO: if sucessful, create KEYS

    def handshake(self):
        self.send({"val": pow(self.g, self.a, self.p), "username": self.username})

    def send(self, message):
        message = json.dumps(message).encode()
        header = len(message).to_bytes(helpers.HEADER_LENGTH, byteorder="big")
        self.server_socket.send(header + message)
        # TODO listen for server response somehow

    def login(self):
        pass

    def start_cli(self):
        while True:
            user_input = input(">").split()

            # 1. parse the input
            command = user_input[0].lower()
            if len(user_input) > 1:
                user = user_input[1].lower()

            if command == "list":
                pass
            elif command == "send":
                # 1. set if session key with that user is already setup
                #       if already setup, use that to communicate
                # 2. else set it up
                pass
            elif command == "logout":
                pass
            else:
                print("invalid command")

    def send_message(self, input: list[str]) -> None:
        """
        {   msg_length: "",
            ---------- encrypted ----------
            payload_type: "",
            sender: "",
            payload : "",
            ---------- encrypted ----------
            IV : "",
            HMAC signature: ""}


        :param input:
        """
        try:
            user = input[0].lower()
            message = input[1:]
            # 1. check if session key with that user is already setup
            if user in self.session_keys:
                message = self.encrypt_send(user, f" ".join(message).encode())
                self.session_keys[user].socket.sendall(message)
                pass
            else:
                self.setup_keys(user)
            # 2. else set it up

        except IndexError:
            raise ValueError

    def encrypt_send(self, user: str, message: bytes) -> bytes:
        iv = os.urandom(32)
        cipher = Cipher(
            algorithm=algorithms.AES256(self.session_keys[user].key),
            mode=modes.CBC(iv),
        )
        en = cipher.encryptor()

        # prepare the message
        payload_type = en.update(b"message") + en.finalize()
        encrypted_sender = en.update(f"{user}".encode()) + en.finalize()
        encrypted_payload = en.update(message) + en.finalize()
        signature = self.HMAC_sign(user, message)

        message_dict = {
            "iv": iv,
            "payload_type": payload_type,
            "encrypted_sender": encrypted_sender,
            "encrypted_payload": encrypted_payload,
            "signature": signature,
        }
        message_json = json.dumps(message_dict)
        message_size = len(message_json)

        final_message = {
            "message_length": message_size,
            "message": message_json,
        }
        return json.dumps(final_message).encode()

    def setup_keys(self, user: str):
        pass

    def HMAC_sign(self, user: str, message: bytes) -> bytes:
        """
        Signs a message using HMAC

        :param user: user the message is for
        :param message: bytes to sign
        :return: signature in bytes
        """
        h = hmac.HMAC(self.session_keys[user][key], hashes.SHA256())
        h.update(message)
        signature = h.finalize()
        return signature

    def authenticate(self):
        """
        1. get PK from the server
        2. validate the other side's certs, PK
        3. validate K
        """

    def logout(self):
        pass


p = Path(__file__).parent.parent
with open(p / "config.yml") as config_file:
    config = yaml.safe_load(config_file)


c = Client(
    username="AzureDiamond",
    password="hunter2",
    p=config["dh"]["p"],
    g=config["dh"]["g"],
    server_port=config["server"]["port"],
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client for communicating with server")
    parser.add_argument("username", help="Your username")
    parser.add_argument("password", help="Your password")
    args = parser.parse_args()

    c = Client(
        args.username,
        args.password,
        p=config["dh"]["p"],
        g=config["dh"]["g"],
        server_port=config["server"]["port"],
    )

    # TODO: check if login is sucessful
    c.start_cli()
    # TODO: else ask for a new password
