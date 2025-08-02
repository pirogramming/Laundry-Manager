from django.shortcuts import render

# Create your views here.
def main_page(request):
    return render(request, 'laundry_manager/main.html')

def laundry_upload_page(request):
    return render(request, 'laundry_manager/laundry-upload.html')
def stain_upload_page(request):
    return render(request, 'laundry_manager/stain-upload.html')
def result_page(request):
    return render(request, 'laundry_manager/result.html')
def laundry_info_page(request):
    return render(request, 'laundry_manager/laundry-info.html')