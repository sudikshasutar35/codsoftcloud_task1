from flask import Flask, render_template, request, send_file
import boto3
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)

# AWS S3
s3 = boto3.client("s3")

# S3 Bucket Name
BUCKET_NAME = "cloud-file-storage-2026-sudiksha"

# File Validation
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# Upload File
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]

    if file.filename == "":
        return "No file selected"

    # Check file type
    if not allowed_file(file.filename):
        return "Invalid file type. Allowed: txt, pdf, png, jpg, jpeg, docx"

    # Check file size
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return "File size exceeds 10 MB limit"

    # Secure filename
    filename = secure_filename(file.filename)

    if filename == "":
        return "Invalid filename"

    # Upload to S3
    s3.upload_fileobj(
        file,
        BUCKET_NAME,
        filename
    )

    return f"File '{filename}' uploaded successfully!"


# View/List Files
@app.route("/files")
def list_files():
    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME
    )

    files = []

    if "Contents" in response:
        for obj in response["Contents"]:
            files.append(obj["Key"])

    return render_template(
        "files.html",
        files=files
    )


# Download File
@app.route("/download/<filename>")
def download_file(filename):
    file_stream = io.BytesIO()

    s3.download_fileobj(
        BUCKET_NAME,
        filename,
        file_stream
    )

    file_stream.seek(0)

    return send_file(
        file_stream,
        as_attachment=True,
        download_name=filename
    )

# Generate Shareable Download Link
@app.route("/share/<filename>")
def share_file(filename):
    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": filename
        },
        ExpiresIn=3600
    )

    return f"Shareable download link (valid for 1 hour): {url}"

# Delete File
@app.route("/delete/<filename>")
def delete_file(filename):
    s3.delete_object(
        Bucket=BUCKET_NAME,
        Key=filename
    )

    return f"File '{filename}' deleted successfully!"


# Run Flask Application
if __name__ == "__main__":
    app.run(debug=True)