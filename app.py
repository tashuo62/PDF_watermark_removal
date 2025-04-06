from flask import Flask, render_template, request, send_file, make_response, jsonify, Response
import os
import cv2
import numpy as np
import fitz
from PIL import Image
from reportlab.pdfgen import canvas
import json
import time

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def remove_watermark(image_path):
    img = cv2.imread(image_path)
    lower_hsv = np.array([160, 160, 160])
    upper_hsv = np.array([255, 255, 255])
    mask = cv2.inRange(img, lower_hsv, upper_hsv)
    img[mask == 255] = [255, 255, 255]
    cv2.imwrite(image_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 0])

def pdf_to_images(pdf_path, output_folder):
    images = []
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count
    for page_num in range(total_pages):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(600 / 72, 600 / 72), alpha=False, annots=True)
        image_path = os.path.join(output_folder, f"page_{page_num + 1}.png")
        pix.save(image_path, output="png")
        remove_watermark(image_path)
        images.append(image_path)
        print(f"Yielding: current_page={page_num + 1}, total_pages={total_pages}")
        yield json.dumps({
            "current_page": page_num + 1,
            "total_pages": total_pages,
            "message": f"正在处理第 {page_num + 1} 页，共 {total_pages} 页",
            "completed": False
        }) + "\n"
        time.sleep(0.1)
    doc.close()
    yield json.dumps({"images": images, "completed": True}) + "\n"

def images_to_pdf(image_paths, output_path):
    c = canvas.Canvas(output_path)
    for image_path in image_paths:
        with Image.open(image_path) as img:
            width, height = img.size
            width_inch = width / 600
            height_inch = height / 600
            width_pt = width_inch * 72
            height_pt = height_inch * 72
            c.setPageSize((width_pt, height_pt))
            c.drawImage(image_path, 0, 0, width_pt, height_pt, preserveAspectRatio=True)
            c.showPage()
    c.save()
    for image_path in image_paths:
        if os.path.exists(image_path):
            os.remove(image_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        pdf_path = os.path.join(UPLOAD_FOLDER, 'uploaded_file.pdf')
        uploaded_file.save(pdf_path)
        return jsonify({"message": "文件上传成功"})
    return jsonify({"message": "请上传一个 PDF 文件"}), 400

@app.route('/remove_watermark', methods=['GET'])
def remove_watermark_route():
    pdf_path = os.path.join(UPLOAD_FOLDER, 'uploaded_file.pdf')
    if not os.path.exists(pdf_path):
        return jsonify({"message": "请先上传文件"}), 400

    output_pdf_path = 'output_file.pdf'

    def generate():
        with app.app_context():
            generator = pdf_to_images(pdf_path, OUTPUT_FOLDER)
            image_paths = []
            for data in generator:
                parsed_data = json.loads(data)
                if "images" in parsed_data:
                    image_paths = parsed_data["images"]
                    images_to_pdf(image_paths, output_pdf_path)
                    yield json.dumps({"message": "水印去除成功", "completed": True}) + "\n"
                else:
                    # 直接传递原始数据
                    yield data

    return Response(generate(), mimetype='application/json', headers={'X-Accel-Buffering': 'no'})

@app.route('/preview')
def preview():
    output_pdf_path = 'output_file.pdf'
    if os.path.exists(output_pdf_path):
        with open(output_pdf_path, 'rb') as f:
            response = make_response(f.read())
            response.headers.set('Content-Type', 'application/pdf')
            return response
    return jsonify({"message": "文件未生成，请先去除水印"}), 400

@app.route('/download')
def download():
    output_pdf_path = 'output_file.pdf'
    if os.path.exists(output_pdf_path):
        with open(output_pdf_path, 'rb') as f:
            response = make_response(f.read())
            response.headers.set('Content-Type', 'application/pdf')
            response.headers.set('Content-Disposition', 'attachment', filename='output_file.pdf')
            return response
    return jsonify({"message": "文件未生成，请先去除水印"}), 400

if __name__ == '__main__':
    app.run(debug=True)