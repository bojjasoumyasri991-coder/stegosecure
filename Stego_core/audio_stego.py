import wave
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


# ================= AUDIO ENCODE ================= #

def text_to_binary(text):
    return ''.join(format(ord(c), '08b') for c in text)

def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(b, 2)) for b in chars)


def encode_audio(input_path, message, output_path):
    password = generate_key()
    encrypted = encrypt_message(message, password)
    binary_data = text_to_binary(encrypted) + "1111111111111110"

    audio = wave.open(input_path, mode="rb")
    frame_bytes = bytearray(list(audio.readframes(audio.getnframes())))

    if len(binary_data) > len(frame_bytes):
        return None, "Message too large for this audio file!"

    for i in range(len(binary_data)):
        frame_bytes[i] = (frame_bytes[i] & 254) | int(binary_data[i])

    modified_audio = wave.open(output_path, "wb")
    modified_audio.setparams(audio.getparams())
    modified_audio.writeframes(bytes(frame_bytes))
    modified_audio.close()
    audio.close()

    return password, None


# ================= AUDIO DECODE ================= #

def decode_audio(audio_path, password):
    audio = wave.open(audio_path, mode="rb")
    frame_bytes = bytearray(list(audio.readframes(audio.getnframes())))
    audio.close()

    extracted = ""
    for byte in frame_bytes:
        extracted += str(byte & 1)

    end_marker = "1111111111111110"
    end_index = extracted.find(end_marker)

    if end_index == -1:
        return "❌ No hidden message found!"

    binary_data = extracted[:end_index]
    encrypted_text = binary_to_text(binary_data)

    try:
        return decrypt_message(encrypted_text, password)
    except:
        return "❌ Invalid Secret Key!"