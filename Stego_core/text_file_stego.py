import secrets
import hashlib
import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from nltk.corpus import wordnet

# ================= ZERO WIDTH ================= #

ZW_ZERO = '\u200b'
ZW_ONE  = '\u200c'
ZW_END  = '\u200d'

SENTINEL = "<<ZWS>>"

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
    return unpad(cipher.decrypt(encrypted), AES.block_size).decode()

# ================= ZERO WIDTH ================= #

def text_to_binary(text):
    return ''.join(format(ord(c), '08b') for c in text)

def binary_to_text(binary):
    chars = []
    for i in range(0, len(binary), 8):
        byte = binary[i:i+8]
        if len(byte) == 8:
            chars.append(chr(int(byte, 2)))
    return ''.join(chars)

def binary_to_zw(binary):
    return ''.join(ZW_ZERO if b == '0' else ZW_ONE for b in binary) + ZW_END

def zw_to_binary(text):
    binary = ""
    for ch in text:
        if ch == ZW_ZERO:
            binary += '0'
        elif ch == ZW_ONE:
            binary += '1'
        elif ch == ZW_END:
            break
    return binary

# ================= SYNONYM ================= #

def get_synonyms(word):
    synonyms = []
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            name = lemma.name().replace('_',' ')
            if name.lower() != word.lower():
                synonyms.append(name.lower())
    return list(set(synonyms))


def synonym_encode(message):
    words = message.split()
    encoded_words = []
    binary_key = ""
    mapping = []

    for word in words:
        syns = get_synonyms(word)

        if syns:
            alt = syns[0]
            pair = [word, alt]

            index = secrets.randbelow(2)
            encoded_words.append(pair[index])
            binary_key += str(index)

            mapping.append(pair)
        else:
            encoded_words.append(word)
            binary_key += '0'
            mapping.append([word, word])

    encoded_text = " ".join(encoded_words)

    mapping_str = base64.b64encode(json.dumps(mapping).encode()).decode()

    return encoded_text, binary_key, mapping_str


def synonym_decode(content):

    if "<<MAP>>" not in content:
        return "❌ No synonym data found!"

    try:
        map_part = content.split("<<MAP>>")[1].split("<<ENDMAP>>")[0]
        mapping = json.loads(base64.b64decode(map_part).decode())
    except:
        return "❌ Mapping corrupted!"

    # 🔥 ALWAYS return original words
    decoded_words = [pair[0] for pair in mapping]

    return " ".join(decoded_words)

# ================= ENCODE ================= #

def encode_text_file(input_path, message, output_path, method):

    password = generate_key()

    with open(input_path, "r", encoding="utf-8") as f:
        cover = f.read()

    # ---------- ZERO ----------
    if method == "zero":

        encrypted = aes_encrypt(message, password)
        payload = "STEGO|" + encrypted

        binary = text_to_binary(payload)
        hidden = binary_to_zw(binary)

        stego = cover + SENTINEL + hidden
        key = password

    # ---------- SYNONYM ----------
    elif method == "synonym":

        encoded_msg, binary_key, mapping_str = synonym_encode(message)

        stego = (
            cover +
            "\n<<SYN>>" + encoded_msg +
            "\n<<MAP>>" + mapping_str + "<<ENDMAP>>"
        )

        key = binary_key  # shown to user

    # ---------- HYBRID ----------
    elif method == "hybrid":

        encoded_msg, binary_key, mapping_str = synonym_encode(message)

        combined = encoded_msg + "||" + mapping_str

        encrypted = aes_encrypt(combined, password)
        payload = "STEGO|" + encrypted

        binary = text_to_binary(payload)
        hidden = binary_to_zw(binary)

        stego = cover + SENTINEL + hidden
        key = password + "|" + binary_key

    else:
        return "❌ Invalid method"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(stego)

    return key

# ================= DECODE ================= #

def decode_text_file(file_path, key):

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # ================= PRIORITY: SYNONYM ================= #
    if "<<MAP>>" in content:
        return synonym_decode(content)

    # ================= ZERO / HYBRID ================= #
    elif "<<ZWS>>" in content:

        hidden = content.split("<<ZWS>>", 1)[1]
        binary = zw_to_binary(hidden)

        if not binary:
            return "❌ No hidden message found!"

        extracted = binary_to_text(binary)

        if not extracted.startswith("STEGO|"):
            return "❌ Corrupted stego data!"

        encrypted = extracted.replace("STEGO|", "", 1)

        try:
            # HYBRID
            if "|" in key:
                password, binary_key = key.split("|")

                decrypted = aes_decrypt(encrypted, password)

                if "||" not in decrypted:
                    return "❌ Corrupted hybrid data!"

                encoded_msg, mapping_str = decrypted.split("||", 1)

                fake_content = "<<MAP>>" + mapping_str + "<<ENDMAP>>"
                return synonym_decode(fake_content)

            # ZERO
            else:
                return aes_decrypt(encrypted, key)

        except:
            return "❌ Wrong key or corrupted data!"

    # ================= NONE ================= #
    else:
        return "❌ No hidden message found!"