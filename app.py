from flask import Flask, request, render_template, jsonify
import boto3
import csv
from PIL import Image, ImageDraw
import os
from dotenv import load_dotenv

# Load các biến môi trường từ tệp .env
load_dotenv('config.env')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Đọc AWS credentials từ file
with open('credentials.csv', 'r') as file:
    next(file)
    reader = csv.reader(file)
    for line in reader:
        aws_access_key_id = line[0]
        aws_secret_access_key = line[1]

client = boto3.client(
    'rekognition',
    region_name='us-east-1',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        with open(filepath, 'rb') as image:
            response = client.recognize_celebrities(Image={'Bytes': image.read()})

        im = Image.open(filepath)
        draw = ImageDraw.Draw(im)
        w, h = im.size

        for celeb in response['CelebrityFaces']:
            bbox = celeb['Face']['BoundingBox']
            x1 = bbox['Left'] * w
            y1 = bbox['Top'] * h
            x2 = (bbox['Left'] + bbox['Width']) * w
            y2 = (bbox['Top'] + bbox['Height']) * h
            draw.rectangle([x1, y1, x2, y2], width=5, outline='green')

        result_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'result_' + filename)
        im.save(result_image_path)

        # Chỉ giữ phần đường dẫn cần thiết cho hiển thị
        result_image = 'uploads/result_' + filename
        celebrities = [celeb['Name'] for celeb in response['CelebrityFaces']]

        return jsonify({'result_image': result_image, 'celebrities': celebrities})

if __name__ == '__main__':
    # Sử dụng giá trị PORT từ biến môi trường
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, port=port)
