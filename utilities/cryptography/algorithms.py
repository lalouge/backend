import random, uuid, base64

class AlphanumericCipher:
    def __init__(self):
        self.characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.key = self.generate_key()

    def generate_key(self):
        # Generating a random permutation of alphanumeric characters
        key = list(self.characters)
        random.shuffle(key)
        return dict(zip(self.characters, key))

    def encrypt(self, message):
        # Encrypt the message using the substitution cipher
        encrypted_message = ''.join([self.key.get(char, char) for char in message])
        return encrypted_message

    def decrypt(self, encrypted_message):
        # Decrypt the message using the inverse of the substitution cipher
        inverted_key = {v: k for k, v in self.key.items()}
        decrypted_message = ''.join([inverted_key.get(char, char) for char in encrypted_message])
        return decrypted_message


# # Example usage
# cipher = AlphanumericCipher()
# message = f"AGENT-ramses-ramsesnjasap11@gmail.com-1"
# print("Message::: ", message)
# # # Encrypt the message
# encrypted_message = cipher.encrypt(message)
# print("Encrypted Message::: ", encrypted_message)
# byte_encrypted = base64.b64encode(encrypted_message.encode("utf-8"))
# print("Byte Encrypted::: ", byte_encrypted)
# print(type(byte_encrypted))

# print("Byte String Encrypted::: ", byte_encrypted.decode("utf-8"))
# print(type(byte_encrypted.decode("utf-8")))

# print(bytes(byte_encrypted.decode("utf-8"), "utf-8"))
# # print(base64.b64encode(byte_encrypted.decode("utf-8").encode("utf-8")))
# # print(type(base64.b64decode(byte_encrypted.decode("utf-8").encode("utf-8"))))

# byte_decrypted = base64.b64decode(byte_encrypted).decode("utf-8")

# # # # Decrypt the message
# decrypted_message = cipher.decrypt(byte_decrypted)
# print("Decrypted:", decrypted_message)
