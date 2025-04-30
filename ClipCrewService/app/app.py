import os
import boto3
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv

# load .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///clipcrew.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# S3 config
s3 = boto3.client('s3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)
S3_BUCKET = os.getenv('S3_BUCKET_NAME')

# clip model
class Clip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    s3_key = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

#upload endpoint
@app.route('/upload', methods=['POST'])
def upload_clip():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = secure_filename(file.filename)
        s3_key = f"clips/{filename}"

        # Upload file to S3
        try:
            s3.upload_fileobj(file, S3_BUCKET, s3_key)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
        new_clip = Clip(
            title=request.form.get('title', 'Untitled'),
            description=request.form.get('description', ''),
            s3_key=s3_key
        )
        db.session.add(new_clip)
        db.session.commit()
        
        return jsonify({"message": "File uploaded successfully", "clip_id": new_clip.id}), 201
    

@app.route("/")
def index():
    return "Welcome to ClipCrew Service!"