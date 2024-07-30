from flask import Flask, render_template, request, url_for, jsonify, send_from_directory
from cryptography.fernet import Fernet
import barcode
from barcode.writer import ImageWriter
import os
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO)

# 환경 변수에서 키를 가져오거나 새 키를 생성
key = os.getenv('FERNET_KEY', Fernet.generate_key())
cipher_suite = Fernet(key)

app = Flask(__name__)

def encrypt_data(data):
    try:
        data = data.encode()
        cipher_text = cipher_suite.encrypt(data)
        logging.info("Data encrypted successfully")
        return cipher_text
    except Exception as e:
        logging.error(f"Encryption error: {e}")
        return None

def decrypt_data(cipher_text):
    try:
        plain_text = cipher_suite.decrypt(cipher_text)
        logging.info("Data decrypted successfully")
        return plain_text.decode()
    except Exception as e:
        logging.error(f"Decryption error: {e}")
        return None

def generate_barcode(serial_number, customer_name, customer_number):
    try:
        barcode_dir = os.path.join(app.root_path, 'static', 'Barcodes')
        filename = f"{serial_number} {customer_name} {customer_number}"
        CODE128 = barcode.get_barcode_class('code128')
        code128 = CODE128(serial_number, writer=ImageWriter())
        full_filename = code128.save(os.path.join(barcode_dir, filename))
        logging.info(f"Barcode generated successfully: {full_filename}")
        return full_filename
    except Exception as e:
        logging.error(f"Barcode generation error: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    barcode_image = None
    barcode_list = os.listdir(os.path.join(app.root_path, 'static', 'Barcodes'))
    if request.method == 'POST':
        serial_number = request.form.get('serial_number')
        encrypted_serial_number = encrypt_data(serial_number)
        decrypted_serial_number = decrypt_data(encrypted_serial_number)
        customer_name = request.form.get('customer_name')
        customer_number = request.form.get('customer_number')
        
        # 바코드 생성 함수를 호출합니다.
        barcode_image = generate_barcode(decrypted_serial_number, customer_name, customer_number)
        if barcode_image:
            barcode_image = os.path.basename(barcode_image)  # 파일 이름만 추출
            barcode_list.append(barcode_image)

    return render_template('index.html', barcode_image=barcode_image, barcode_list=barcode_list)

@app.route('/barcodes', methods=['GET'])
def barcodes():
    barcode_list = os.listdir(os.path.join(app.root_path, 'static', 'Barcodes'))
    return jsonify(barcode_list)

@app.route('/delete_image', methods=['POST'])
def delete_image():
    filename = request.json.get('filename')
    file_path = os.path.join(app.root_path, 'static', 'Barcodes', filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.info(f"Barcode deleted successfully: {filename}")
        return 'OK', 200
    else:
        logging.error(f"Barcode deletion error: {filename} not found")
        return 'File not found', 404

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    barcode_dir = os.path.join(app.root_path, 'static', 'Barcodes')
    return send_from_directory(barcode_dir, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
