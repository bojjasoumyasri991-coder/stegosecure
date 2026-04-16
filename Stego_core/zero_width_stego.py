# Zero Width Characters Mapping
ZWC = {
    "0": "\u200B",   # Zero Width Space
    "1": "\u200C"    # Zero Width Non-Joiner
}

# Reverse Mapping
REVERSE_ZWC = {
    "\u200B": "0",
    "\u200C": "1"
}

# Convert text → binary
def text_to_binary(text):
    return ''.join(format(ord(char), '08b') for char in text)

# Convert binary → text
def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(char, 2)) for char in chars if len(char) == 8)

# Encode secret message into cover text
def encode_zero_width(cover_text, secret_message):
    # Add delimiter to mark end
    secret_message += "###"

    binary_secret = text_to_binary(secret_message)

    # Convert binary to zero-width characters
    hidden_data = ''.join(ZWC[bit] for bit in binary_secret)

    # Append to cover text
    encoded_text = cover_text + hidden_data

    return encoded_text

# Decode secret message from text
def decode_zero_width(encoded_text):
    binary_data = ""

    # Extract zero-width characters
    for char in encoded_text:
        if char in REVERSE_ZWC:
            binary_data += REVERSE_ZWC[char]

    # Convert binary → text
    decoded_message = binary_to_text(binary_data)

    # Remove delimiter
    if "###" in decoded_message:
        return decoded_message.split("###")[0]
    else:
        return "No hidden message found!"