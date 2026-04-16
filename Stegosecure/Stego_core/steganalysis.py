from PIL import Image
import wave
import os
import base64

END_MARKER = "1111111111111110"


# ================= HELPER ================= #

def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    try:
        return ''.join(chr(int(b, 2)) for b in chars)
    except:
        return ""


# ================= TEXT DETECTOR ================= #

def detect_zero_width(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        count = content.count('\u200b') + content.count('\u200c') + content.count('\u200d')

        if count > 5:
            return "⚠ Hidden Data Detected"
        else:
            return "✅ No Hidden Data Detected"

    except:
        return "❌ Error analyzing file"


# ================= IMAGE DETECTOR ================= #

def detect_image_lsb(image_path):
    try:
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

        end_index = binary_data.find(END_MARKER)

        if end_index == -1:
            return "✅ No Hidden Data Detected"

        binary_message = binary_data[:end_index]
        extracted_text = binary_to_text(binary_message)

        try:
            base64.b64decode(extracted_text, validate=True)
            return "⚠ Hidden Data Detected"
        except:
            return "✅ No Hidden Data Detected"

    except:
        return "❌ Error analyzing file"


# ================= AUDIO DETECTOR ================= #

def detect_audio_lsb(audio_path):
    try:
        audio = wave.open(audio_path, mode="rb")
        frame_bytes = bytearray(list(audio.readframes(audio.getnframes())))
        audio.close()

        # Extract LSB bits
        bits = ''.join(str(byte & 1) for byte in frame_bytes)

        # Try to find marker
        end_index = bits.find(END_MARKER)

        if end_index == -1:
            return "✅ No Hidden Data Detected"

        # Extract binary before marker
        binary_message = bits[:end_index]

        # Ensure length divisible by 8
        if len(binary_message) % 8 != 0:
            return "✅ No Hidden Data Detected"

        # Convert to text
        extracted_text = binary_to_text(binary_message)

        # AES encrypted text should be valid Base64 and long enough
        try:
            decoded = base64.b64decode(extracted_text, validate=True)

            # Additional validation:
            # AES block size multiple check
            if len(decoded) > 16 and len(decoded) % 16 == 0:
                return "⚠ Hidden Data Detected"
            else:
                return "✅ No Hidden Data Detected"

        except:
            return "✅ No Hidden Data Detected"

    except Exception as e:
        return "❌ Error analyzing file"

# ================= MASTER ================= #

def run_steganalysis(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    if ext in ['.png', '.jpg', '.jpeg']:
        return detect_image_lsb(filepath)

    elif ext == '.wav':
        return detect_audio_lsb(filepath)

    elif ext == '.txt':
        return detect_zero_width(filepath)

    else:
        return "Unsupported file type"