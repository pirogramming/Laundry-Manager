from django.shortcuts import render

# Create your views here.
def main_page(request):
    return render(request, 'laundry_manager/main.html')

def upload_page(request):
    return render(request, 'laundry_manager/upload.html')
def result_page(request):
    return render(request, 'laundry_manager/result.html')