from django.shortcuts import render
import requests
from .forms import ImageUploadForm
import os, uuid
from decouple import config

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