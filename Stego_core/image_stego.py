from PIL import Image
import hashlib
import base64
import secrets
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ================= AES ================= #

def generate_key():
    return secrets.token_hex(16)

def aes_key(password):
    return hashlib.sha256(password.encode()).digest()

def encrypt_message(message, password):
    key = aes_key(password)
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    encrypted = cipher.encrypt(pad(message.encode(), AES.block_size))
    return base64.b64encode(iv + encrypted).decode()

def decrypt_message(cipher_text, password):
    key = aes_key(password)
    raw = base64.b64decode(cipher_text)
    iv = raw[:16]
    encrypted = raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
    return decrypted.decode()


# ================= LSB ENCODE ================= #

def text_to_binary(text):
    return ''.join(format(ord(c), '08b') for c in text)

def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(b, 2)) for b in chars)


def encode_image(input_path, message, output_path):
    password = generate_key()
    encrypted = encrypt_message(message, password)
    signature = "STEGOSECURE2026"
    binary_signature = text_to_binary(signature)
    binary_data = binary_signature + text_to_binary(encrypted) + "1111111111111110"

    img = Image.open(input_path)
    img = img.convert("RGB")
    pixels = img.load()

    width, height = img.size
    index = 0

    for y in range(height):
        for x in range(width):
            if index >= len(binary_data):
                break

            r, g, b = pixels[x, y]

            if index < len(binary_data):
                r = (r & ~1) | int(binary_data[index])
                index += 1

            if index < len(binary_data):
                g = (g & ~1) | int(binary_data[index])
                index += 1

            if index < len(binary_data):
                b = (b & ~1) | int(binary_data[index])
                index += 1

            pixels[x, y] = (r, g, b)

        if index >= len(binary_data):
            break

    img.save(output_path)

    return password


# ================= LSB DECODE ================= #

def decode_image(image_path, password):
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = img.load()

    width, height = img.size
    binary_data = ""

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            binary_data += str(r & 1)
            binary_data += str(g & 1)
            binary_data += str(b & 1)

    end_marker = "1111111111111110"
    end_index = binary_data.find(end_marker)

    if end_index == -1:
        return "❌ No hidden message found!"

    binary_data = binary_data[:end_index]
    encrypted_text = binary_to_text(binary_data)

    try:
        return decrypt_message(encrypted_text, password)
    except:
        return "❌ Invalid Secret Key!"