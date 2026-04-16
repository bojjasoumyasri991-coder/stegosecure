from flask import Flask, render_template, request, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename

from config import *

from Stego_core.text_file_stego import encode_text_file, decode_text_file
from Stego_core.zero_width_stego import encode_zero_width, decode_zero_width
from Stego_core.image_stego import encode_image, decode_image
from Stego_core.audio_stego import encode_audio, decode_audio
from Stego_core.steganalysis import (
    detect_zero_width,
    detect_image_lsb,
    detect_audio_lsb,
    run_steganalysis
)

app = Flask(__name__, template_folder="templates", static_folder="static")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

# ---------------- HOME ---------------- #
@app.route("/")
def home():
    return render_template("home.html")


# ---------------- TEXT STEGO ---------------- #
@app.route("/text", methods=["GET", "POST"])
def text_stego():
    if request.method=="POST":
        file=request.files.get("file")
        message=request.form.get("message")
        method=request.form.get("method")

        if not file or not message:
            return render_template("text_stego.html",
                                   error="⚠️ All fields required!")

        filename=secure_filename(file.filename)
        filepath=os.path.join(UPLOAD_FOLDER,filename)
        file.save(filepath)

        output_filename="encoded_"+filename
        output_path=os.path.join(OUTPUT_FOLDER,output_filename)

        secret_key=encode_text_file(filepath,message,output_path,method)

        return render_template("text_stego.html",
                               success="✅ Encoding Successful!",
                               secret_key=secret_key,
                               output_file=output_filename)

    return render_template("text_stego.html")

@app.route("/decode_text", methods=["POST"])
def decode_text():
    file = request.files.get("file")
    password = request.form.get("password")

    # ✅ FIXED VALIDATION
    if not file or not password:
        return render_template("text_stego.html",
                               error="⚠️ File and key required!")

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # ✅ NO METHOD PASSED
    decoded = decode_text_file(filepath, password)

    return render_template("text_stego.html",
                           decoded_message=decoded)
# ---------------- ZERO WIDTH STEGO ---------------- #
@app.route("/zero_width", methods=["POST"])
def zero_width_stego():

    cover = request.form.get("cover")
    secret = request.form.get("secret")

    if not cover or not secret:
        return render_template("text_stego.html",
                               error="⚠️ Cover text and secret required!")

    # Encode
    encoded_text = encode_zero_width(cover, secret)

    # Decode immediately (IMPORTANT)
    decoded_message = decode_zero_width(encoded_text)

    return render_template("text_stego.html",
                           zw_encoded=encoded_text,
                           zw_decoded=decoded_message,
                           success="✅ Zero Width Encoding Successful!")


# ---------------- IMAGE STEGO ---------------- #
@app.route("/image", methods=["GET", "POST"])
def image_stego():
    if request.method == "POST":
        file = request.files.get("file")
        message = request.form.get("message")

        if not file or not message:
            return render_template("image_stego.html",
                                   error="⚠️ All fields required!")

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        output_filename = "encoded_" + filename
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        secret_key = encode_image(input_path, message, output_path)

        return render_template("image_stego.html",
                               success="✅ Encoding Successful!",
                               secret_key=secret_key,
                               output_file=output_filename)

    return render_template("image_stego.html")


@app.route("/decode_image", methods=["POST"])
def decode_image_route():
    file = request.files.get("file")
    password = request.form.get("password")

    if not file or not password:
        return render_template("image_stego.html",
                               error="⚠️ File and secret key required!")

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    decoded = decode_image(filepath, password)

    return render_template("image_stego.html",
                           decoded_message=decoded)


# ---------------- AUDIO STEGO ---------------- #
@app.route("/audio", methods=["GET", "POST"])
def audio_stego():
    if request.method == "POST":
        file = request.files.get("file")
        message = request.form.get("message")

        if not file or not message:
            return render_template("audio_stego.html",
                                   error="⚠️ All fields required!")

        if not file.filename.endswith(".wav"):
            return render_template("audio_stego.html",
                                   error="⚠️ Only WAV files supported!")

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        output_filename = "encoded_" + filename
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        secret_key, error = encode_audio(input_path, message, output_path)

        if error:
            return render_template("audio_stego.html", error=error)

        return render_template("audio_stego.html",
                               success="✅ Encoding Successful!",
                               secret_key=secret_key,
                               output_file=output_filename)

    return render_template("audio_stego.html")


@app.route("/decode_audio", methods=["POST"])
def decode_audio_route():
    file = request.files.get("file")
    password = request.form.get("password")

    if not file or not password:
        return render_template("audio_stego.html",
                               error="⚠️ File and secret key required!")

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    decoded = decode_audio(filepath, password)

    return render_template("audio_stego.html",
                           decoded_message=decoded)


# ---------------- STEGANALYSIS ---------------- #
@app.route('/steganalysis', methods=['GET', 'POST'])
def steganalysis():

    if request.method == 'POST':

        file = request.files.get('file')

        if not file or file.filename == '':
            return render_template(
                'steganalysis.html',
                result=None,
                error="Please select a file."
            )

        unique_name = str(uuid.uuid4()) + "_" + file.filename
        filepath = os.path.join(UPLOAD_FOLDER, unique_name)

        file.save(filepath)

        result = run_steganalysis(filepath)

        try:
            os.remove(filepath)
        except:
            pass

        return render_template(
            'steganalysis.html',
            result=result,
            error=None
        )

    return render_template(
        'steganalysis.html',
        result=None,
        error=None
    )


# ---------------- DOWNLOAD ---------------- #
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)