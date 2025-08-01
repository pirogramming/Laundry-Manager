# laundry_app/views.py
import json
import requests
import os
import uuid
import time
import re

from django.shortcuts import render
from django.conf import settings
from .forms import ImageUploadForm
from .models import UploadedImage
import json
import re 

import requests
from .forms import ImageUploadForm
import os, uuid
from decouple import config
from dotenv import load_dotenv

load_dotenv()

washing_symbols_data = []

SECRET_KEY_OCR = os.getenv("SECRET_KEY_OCR")
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
APIGW_URL = config("APIGW_URL")

WASHING_SYMBOLS_DEFINITIONS = []
JSON_FILE_PATH = os.path.join(settings.BASE_DIR, 'laundry_app', 'washing_symbol.json')

try:
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        WASHING_SYMBOLS_DEFINITIONS = json.load(f)
    print("세탁 기호 정의 파일 'washing_symbol.json' 로드 완료.")
except FileNotFoundError:
    print(f"오류: '{JSON_FILE_PATH}' 파일을 찾을 수 없습니다. 앱이 제대로 작동하지 않을 수 있습니다.")
except json.JSONDecodeError:
    print(f"오류: '{JSON_FILE_PATH}' 파일의 JSON 형식이 올바르지 않습니다.")
except Exception as e:
    print(f"세탁 기호 정의 파일 로드 중 알 수 없는 오류 발생: {e}")

def perform_ocr(image_path):
    file_extension = os.path.splitext(image_path)[1][1:].lower()

    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        request_json = {
            'images': [
                {
                    'format': file_extension,
                    'name': os.path.basename(image_path)
                }
            ],
            'requestId': str(uuid.uuid4()),
            'version': 'V2',
            'timestamp': int(round(time.time() * 1000))
        }

        payload = {'message': json.dumps(request_json).encode('UTF-8')}
        headers = {
            'X-OCR-SECRET': SECRET_KEY_OCR,
        }
        files = [('file', image_bytes)]

        response = requests.request("POST", APIGW_URL, headers=headers, data=payload, files=files)
        response.raise_for_status()

        return response.json()
    except requests.exceptions.HTTPError as e:
        error_msg = f"API 요청 실패: HTTP 상태 코드 {e.response.status_code}"
        try:
            error_details = e.response.json()
            error_msg += f" - {error_details.get('code', '')}: {error_details.get('message', '')}"
        except json.JSONDecodeError:
            error_msg += f" - {e.response.text}"
        print(error_msg)
        return {"error": True, "message": error_msg}
    except requests.exceptions.ConnectionError as e:
        print(f"네트워크 연결 오류: {e}")
        return {"error": True, "message": "네트워크 연결 오류입니다. 인터넷 상태를 확인해주세요."}
    except requests.exceptions.Timeout as e:
        print(f"요청 시간 초과: {e}")
        return {"error": True, "message": "API 요청 시간이 초과되었습니다."}
    except Exception as e:
        print(f"OCR 중 알 수 없는 오류 발생: {e}")
        return {"error": True, "message": f"OCR 처리 중 알 수 없는 오류 발생: {e}"}

#json 파일에서 기호에 대한 정의를 불러오는 함수..인자로 OCR 결과값을 받는다
def get_washing_symbol_definition(ocr_result):
    full_ocr_text = ""
    extracted_texts = []
    
    if 'images' in ocr_result and len(ocr_result['images']) > 0 and 'fields' in ocr_result['images'][0]:
        for field in ocr_result['images'][0]['fields']:
            text = field['inferText']
            extracted_texts.append(text)
            full_ocr_text += text + " "

    if not full_ocr_text:
        return "이미지에서 텍스트를 인식할 수 없습니다.", extracted_texts

    matched_definition = "인식된 기호에 대한 설명을 찾을 수 없습니다."
    
    for definition in WASHING_SYMBOLS_DEFINITIONS:
        keywords = definition.get("keywords", [])
        
        for keyword in keywords:
            lower_keyword = keyword.lower()
            lower_full_ocr_text = full_ocr_text.lower()

            if re.match(r'^\d+\s?°?C$', keyword):
                ocr_match = re.search(r'(\d+)\s?°?C', lower_full_ocr_text)
                keyword_num_match = re.search(r'(\d+)', lower_keyword)
                
                if ocr_match and keyword_num_match and int(ocr_match.group(1)) == int(keyword_num_match.group(1)):
                    return definition["description"], extracted_texts
            
            elif lower_keyword in lower_full_ocr_text:
                return definition["description"], extracted_texts
    
    return matched_definition, extracted_texts

def upload_view(request):
    form = ImageUploadForm()
    uploaded_image_url = None
    uploaded_image_name = None
    recognized_texts = []
    symbol_definition = ""
    error_message = None

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_instance = form.save()
            uploaded_image_url = uploaded_instance.image.url
            uploaded_image_name = uploaded_instance.image.name
            image_path = uploaded_instance.image.path

            print(f"파일이 {image_path} 에 저장되었습니다.")

            ocr_json_result = perform_ocr(image_path)

            if ocr_json_result.get("error"):
                error_message = ocr_json_result['message']
            else:
                definition, texts = get_washing_symbol_definition(ocr_json_result)
                recognized_texts = texts
                symbol_definition = definition

            # ✅ 오류 방지용 config 접근 (기본값: "output/")
            output_results_folder = getattr(config, "OUTPUT_RESULTS_FOLDER", "output/")
            os.makedirs(output_results_folder, exist_ok=True)

            output_data = {
                "filename": os.path.basename(image_path),
                "recognized_texts": recognized_texts,
                "symbol_definition": symbol_definition,
                "ocr_raw_response": ocr_json_result
            }

            output_file_name = os.path.join(
                output_results_folder,
                f"{os.path.splitext(os.path.basename(image_path))[0]}_result.json"
            )
            try:
                with open(output_file_name, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)
                print(f"결과가 '{output_file_name}' 파일에 저장되었습니다.")
            except Exception as e:
                print(f"결과 JSON 파일 저장 중 오류 발생: {e}")

    context = {
        'form': form,
        'uploaded_image_url': uploaded_image_url,
        'uploaded_image_name': uploaded_image_name,
        'recognized_texts': recognized_texts,
        'symbol_definition': symbol_definition,
        'error_message': error_message,
    }
    return render(request, 'laundry_manager/index.html', context)



def classify_laundry_symbol(image_path):
    api_key = config("ROBOFLOW_API_KEY")
    api_url = f"https://classify.roboflow.com/laundry-symbols-o1ui8/3?api_key={api_key}"
    
    with open(image_path, "rb") as image_file:
        response = requests.post(api_url, files={"file": image_file})
        result = response.json()
    
    try:
        prediction = result["predictions"][0]["class"]
        confidence = result["predictions"][0]["confidence"]
        return prediction, confidence
    except (KeyError, IndexError):
        return "분류 실패", 0
    
def upload_and_classify(request):
    result = None

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = request.FILES['image']
            
            # temp 폴더 없으면 생성
            if not os.path.exists("temp"):
                os.makedirs("temp")
                
            ext = image_file.name.split('.')[-1]
            filename = f"{uuid.uuid4().hex}.{ext}"
            image_path = os.path.join("temp", filename)

            # 파일 저장
            with open(image_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)

            result = classify_laundry_symbol(image_path)
            os.remove(image_path)  # 삭제는 여기서 OK

    else:
        form = ImageUploadForm()

    return render(request, "laundry_manager/upload.html", {
        "form": form,
        "result": result,
    })