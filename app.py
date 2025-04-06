from flask import Flask, render_template, request, send_file, make_response, send_from_directory
import os
import cv2
import numpy as np
import fitz
from PIL import Image
from reportlab.pdfgen import canvas
import tempfile

app = Flask(__name__)

# 确保上传和输出目录存在
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# 图像去除水印函数
def remove_watermark(image_path):
    img = cv2.imread(image_path)
    lower_hsv = np.array([160, 160, 160])  # 水印颜色范围下限
    upper_hsv = np.array([255, 255, 255])  # 水印颜色范围上限
    mask = cv2.inRange(img, lower_hsv, upper_hsv)
    # 直接替换，不使用高斯模糊以保留细节
    img[mask == 255] = [255, 255, 255]
    cv2.imwrite(image_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 0])  # 无损保存


# 将 PDF 转换为图像
def pdf_to_images(pdf_path, output_folder):
    images = []
    doc = fitz.open(pdf_path)
    for page_num in range(doc.page_count):
        page = doc[page_num]
        # 使用 600 DPI 渲染，启用抗锯齿
        pix = page.get_pixmap(matrix=fitz.Matrix(600 / 72, 600 / 72), alpha=False, annots=True)
        image_path = os.path.join(output_folder, f"page_{page_num + 1}.png")
        pix.save(image_path, output="png")  # 保存为 PNG
        images.append(image_path)
        remove_watermark(image_path)  # 去除水印
    doc.close()
    return images


# 将图像合并为 PDF
def images_to_pdf(image_paths, output_path):
    c = canvas.Canvas(output_path)
    for image_path in image_paths:
        with Image.open(image_path) as img:
            width, height = img.size
            # 假设图像为 600 DPI，计算页面尺寸（单位：点）
            width_inch = width / 600
            height_inch = height / 600
            width_pt = width_inch * 72
            height_pt = height_inch * 72
            # 设置页面大小为图像实际尺寸
            c.setPageSize((width_pt, height_pt))
            # 嵌入图像，保持原始分辨率
            c.drawImage(image_path, 0, 0, width_pt, height_pt, preserveAspectRatio=True)
            c.showPage()
    c.save()
    # 清理临时文件
    for image_path in image_paths:
        if os.path.exists(image_path):
            os.remove(image_path)


# 主页路由
@app.route('/')
def index():
    return render_template('index.html')


# 上传文件路由
@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        pdf_path = os.path.join(UPLOAD_FOLDER, 'uploaded_file.pdf')
        uploaded_file.save(pdf_path)
        return render_template('index.html', message='文件上传成功')
    return render_template('index.html', message='请上传一个 PDF 文件')


# 去除水印路由
@app.route('/remove_watermark', methods=['GET'])
def remove_watermark_route():
    pdf_path = os.path.join(UPLOAD_FOLDER, 'uploaded_file.pdf')
    if not os.path.exists(pdf_path):
        return render_template('index.html', message='请先上传文件')

    # 转换 PDF 为图像并去除水印
    image_paths = pdf_to_images(pdf_path, OUTPUT_FOLDER)
    output_pdf_path = 'output_file.pdf'
    # 将图像合并为 PDF
    images_to_pdf(image_paths, output_pdf_path)
    return render_template('index.html', message='水印去除成功')


@app.route('/preview')
def preview():
    output_pdf_path = 'output_file.pdf'

    if os.path.exists(output_pdf_path):
        with open(output_pdf_path, 'rb') as f:
            response = make_response(f.read())
            response.headers.set('Content-Type', 'application/pdf')
            return response
    return render_template('index.html', message='文件未生成，请先去除水印')

@app.route('/download')
def download():
    output_pdf_path = 'output_file.pdf'
    if os.path.exists(output_pdf_path):
        with open(output_pdf_path, 'rb') as f:
            response = make_response(f.read())
            response.headers.set('Content-Type', 'application/pdf')
            response.headers.set('Content-Disposition', 'attachment', filename='output_file.pdf')
            return response
    return render_template('index.html', message='文件未生成，请先去除水印')



if __name__ == '__main__':
    app.run(debug=True)