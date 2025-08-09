from django.shortcuts import render

def main_page(request):
    return render(request, "laundry_manager/main.html")

def laundry_upload_page(request):
    return render(request, "laundry_manager/laundry-upload.html")

def stain_upload_page(request):
    return render(request, "laundry_manager/stain-upload.html")

def result_page(request):
    return render(request, "laundry_manager/result.html")

def laundry_info_page(request):
    return render(request, "laundry_manager/laundry-info.html")

def stain_info_page(request):
    return render(request, "laundry_manager/stain-info.html")

def stain_guide_page(request):
    return render(request, "laundry_manager/stain_guide.html")

def stain_detail_page(request):
    return render(request, "laundry_manager/stain_detail.html")
