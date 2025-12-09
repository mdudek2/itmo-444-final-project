import os
import json
import uuid
import boto3
import threading
from flask import Flask, request, jsonify
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
from resume_parser import parse_resume

app = Flask(__name__)

S3_BUCKET = "mdudek2-resume-bucket"

def get_secret():
    secret_name = "resume-app"
    region_name = "us-east-2"

    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret_string = get_secret_value_response["SecretString"]
        return json.loads(secret_string)
    except ClientError:
        raise

# Initialize S3 client with secrets
secret = get_secret()

s3_client = boto3.client(
    's3',
    aws_access_key_id=secret["AWS_KEY_ID"],
    aws_secret_access_key=secret["AWS_SECRET_ACCESS_KEY"],
    region_name="us-east-2"
)

# Helper function to delete file after a delay
def delete_file_later(file_path, delay=300):
   
    # delete function
    def delete():
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

    timer = threading.Timer(delay, delete)
    timer.start()

# upload route
@app.route('/upload', methods=['POST'])
def upload_resume():
    
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    file_path = f"/tmp/{filename}"
    file.save(file_path)

    # Schedule file deletion in 5 minutes
    delete_file_later(file_path, delay=300)

    # Parse resume
    parsed_data = parse_resume(file_path)

    # Generate a randomized filename
    random_id = str(uuid.uuid4())
    s3_key = f"resumes/{random_id}.json"

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(parsed_data),
            ContentType="application/json"
        )
   
    except ClientError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    return jsonify({
        'status': 'success',
        's3_key': s3_key,
        'parsed_json': parsed_data  # send the JSON back to the frontend
    })
