import secrets
import hashlib
import base64
import json
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from nltk.corpus import wordnet

# Zero-width chars
ZW_ZERO = '\u200b'
ZW_ONE = '\u200c'
ZW_END = '\u200d'


# ================= AES ================= #

def generate_key():
    return secrets.token_hex(16)

def aes_key(password):
    return hashlib.sha256(password.encode()).digest()

def aes_encrypt(message, password):
    key = aes_key(password)
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    encrypted = cipher.encrypt(pad(message.encode(), AES.block_size))
    return base64.b64encode(iv + encrypted).decode()

def aes_decrypt(cipher_text, password):
    key = aes_key(password)
    raw = base64.b64decode(cipher_text)
    iv = raw[:16]
    encrypted = raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
    return decrypted.decode()


# ================= ZERO WIDTH ================= #

def text_to_binary(text):
    return ''.join(format(ord(c), '08b') for c in text)

def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(b, 2)) for b in chars)

def binary_to_zw(binary):
    return ''.join(ZW_ZERO if b=='0' else ZW_ONE for b in binary) + ZW_END

def zw_to_binary(text):
    binary=""
    for ch in text:
        if ch==ZW_ZERO: binary+='0'
        elif ch==ZW_ONE: binary+='1'
        elif ch==ZW_END: break
    return binary


# ================= SYNONYM ================= #

def get_synonyms(word):
    synonyms=set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            name=lemma.name().replace('_',' ')
            if name.lower()!=word.lower():
                synonyms.add(name.lower())
    return list(synonyms)

def synonym_encode(message):
    words=message.split()
    encoded=[]
    binary_key=""

    for word in words:
        syns=get_synonyms(word)
        if len(syns)>=2:
            index=secrets.randbelow(2)
            encoded.append(syns[index])
            binary_key+=str(index)
        else:
            encoded.append(word)
            binary_key+='0'

    return " ".join(encoded), binary_key


# ================= MAIN FUNCTION ================= #

def encode_text_file(input_path, message, output_path, method):
    password = generate_key()

    with open(input_path,"r",encoding="utf-8") as f:
        cover=f.read()

    # ---------- ZERO WIDTH ----------
    if method=="zero":
        encrypted=aes_encrypt(message,password)
        binary=text_to_binary(encrypted)
        hidden=binary_to_zw(binary)
        stego=cover+hidden
        key=password

    # ---------- SYNONYM ----------
    elif method=="synonym":
        encoded_msg,binary_key=synonym_encode(message)
        stego=cover+"\n"+encoded_msg
        key=binary_key

    # ---------- HYBRID ----------
    elif method=="hybrid":
        encoded_msg,binary_key=synonym_encode(message)
        encrypted=aes_encrypt(encoded_msg,password)
        binary=text_to_binary(encrypted)
        hidden=binary_to_zw(binary)
        stego=cover+hidden
        key=password+"|"+binary_key

    with open(output_path,"w",encoding="utf-8") as f:
        f.write(stego)

    return key


def decode_text_file(file_path, key, method):
    with open(file_path,"r",encoding="utf-8") as f:
        content=f.read()

    # ZERO
    if method=="zero":
        binary=zw_to_binary(content)
        encrypted=binary_to_text(binary)
        return aes_decrypt(encrypted,key)

    # SYNONYM
    elif method=="synonym":
        return "Message encoded using synonym method. Key: "+key

    # HYBRID
    elif method=="hybrid":
        password,binary_key=key.split("|")
        binary=zw_to_binary(content)
        encrypted=binary_to_text(binary)
        return aes_decrypt(encrypted,password)