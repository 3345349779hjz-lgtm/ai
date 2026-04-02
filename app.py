import os
import base64
import json
import requests
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import io

# 导入配置（从环境变量或配置文件读取）
from config import API_KEY, SECRET_KEY

app = Flask(__name__)

# 配置上传文件夹
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 限制5MB

# 创建上传文件夹
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """检查文件格式是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_access_token():
    """
    获取百度API的access_token（有效期30天）
    参考：https://cloud.baidu.com/doc/OCR/s/hkw3i66qw[citation:8]
    """
    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={API_KEY}&client_secret={SECRET_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        print(f"获取access_token失败: {e}")
        return None


def ocr_general(image_path, access_token, language_type='CHN_ENG'):
    """
    通用文字识别（标准版）
    参数：
        image_path: 图片路径
        access_token: 认证token
        language_type: 语言类型（CHN_ENG/ENG/JAP等）
    返回：识别结果字典
    参考：https://cloud.baidu.com/doc/OCR/s/hkw3i66qw[citation:8]
    """
    # 读取图片并转换为base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # 构造请求
    request_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    params = {
        "image": image_data,
        "language_type": language_type,
        "detect_direction": "true"  # 自动检测图像方向[citation:1]
    }
    
    try:
        response = requests.post(request_url, data=params, headers=headers, timeout=30)
        return response.json()
    except Exception as e:
        return {"error_code": -1, "error_msg": str(e)}


def ocr_accurate(image_path, access_token):
    """
    通用文字识别（高精度版）- 适合复杂背景、倾斜文字
    准确率可提升至97%[citation:2]
    """
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    request_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={access_token}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    params = {"image": image_data}
    
    response = requests.post(request_url, data=params, headers=headers, timeout=30)
    return response.json()


def ocr_general_with_position(image_path, access_token):
    """
    通用文字识别（含位置信息版）- 返回文字坐标
    """
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    request_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general?access_token={access_token}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    params = {"image": image_data}
    
    response = requests.post(request_url, data=params, headers=headers, timeout=30)
    return response.json()


def compress_image(image_path, max_size_kb=1024):
    """
    图片压缩预处理，提升识别速度[citation:2]
    将图片压缩到1MB以内
    """
    img = Image.open(image_path)
    # 保持宽高比，限制最大边长
    max_size = 1500
    if img.width > max_size or img.height > max_size:
        ratio = min(max_size / img.width, max_size / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # 压缩保存
    output_path = image_path.replace('.', '_compressed.')
    img.save(output_path, optimize=True, quality=85)
    return output_path


@app.route('/')
def index():
    """首页，显示学号和姓名"""
    return render_template('index.html', 
                           student_id="202335020520",      # 请替换为你的学号
                           student_name="黄佳圳")           # 请替换为你的姓名


@app.route('/upload', methods=['POST'])
def upload_file():
    """处理图片上传和文字识别"""
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({"error": "没有选择文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "文件名为空"}), 400
    
    # 获取识别类型参数
    ocr_type = request.form.get('ocr_type', 'general')
    
    if file and allowed_file(file.filename):
        # 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 图片预处理（压缩）
        compressed_path = compress_image(filepath)
        
        # 获取access_token（添加缓存机制[citation:2]）
        access_token = get_access_token()
        if not access_token:
            return jsonify({"error": "API认证失败，请检查配置"}), 500
        
        # 根据类型调用不同OCR接口
        if ocr_type == 'accurate':
            result = ocr_accurate(compressed_path, access_token)
        elif ocr_type == 'position':
            result = ocr_general_with_position(compressed_path, access_token)
        else:
            result = ocr_general(compressed_path, access_token)
        
        # 清理临时压缩文件
        if compressed_path != filepath:
            os.remove(compressed_path)
        
        # 解析识别结果
        if 'error_code' in result:
            # 处理错误
            error_msg = result.get('error_msg', '识别失败')
            error_code = result.get('error_code')
            # 常见错误码处理[citation:1][citation:6]
            if error_code == 110:
                error_msg = "Access Token失效，请刷新页面重试"
            elif error_code == 216201:
                error_msg = "图片格式错误，请上传jpg/png/bmp格式"
            elif error_code == 216202:
                error_msg = "图片大小超限，请压缩后重试"
            return jsonify({"error": error_msg, "error_code": error_code}), 500
        
        # 提取文字结果
        words_result = result.get('words_result', [])
        words = [item['words'] for item in words_result]
        full_text = '\n'.join(words)
        
        # 返回结果
        return jsonify({
            "success": True,
            "text": full_text,
            "words_count": len(words),
            "total_lines": result.get('words_result_num', 0),
            "filename": filename
        })
    
    return jsonify({"error": "不支持的文件格式，请上传jpg/png/bmp图片"}), 400


@app.route('/history', methods=['GET'])
def get_history():
    """获取最近的识别历史（可选功能）"""
    # 简化版：返回空列表，可扩展实现历史记录存储
    return jsonify({"history": []})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
