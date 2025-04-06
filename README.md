# 🧼 PDF Watermark Remover Web App

这是一个基于 Flask 的 Web 应用，用户可以上传带水印的 PDF 文件，系统会通过图像处理算法去除水印，并提供预览与下载功能。


![描述](https://github.com/tashuo62/blog_img/blob/main/img/2025-04-06%20155608.png)
![描述](https://github.com/tashuo62/blog_img/blob/main/img/2025-04-06%20155628.png)
![描述](https://github.com/tashuo62/blog_img/blob/main/img/2025-04-06%20155641.png)

---

## ✨ 特性 Features

- ✅ 上传 PDF，自动转换为图像处理
- 🧠 使用 OpenCV 去除水印区域
- 🔍 预览处理后的 PDF
- ⬇️ 下载无水印 PDF 文件
- 🖼️ 支持 JPG/PNG 格式转换（依赖 PIL）

---

## 🚀 快速开始 Quick Start

### 环境准备

你需要安装 Python 3.7+，然后安装依赖：



```bash
pip install -r requirements.txt

