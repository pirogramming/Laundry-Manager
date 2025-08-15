from django import forms
from .models import UploadedImage
from .models import Inquiry

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedImage
        fields = ['image']
        labels = {
            'image': '세탁 기호 이미지 선택',
        }

class ImageAnalysisForm(forms.Form):
    image = forms.ImageField()



class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        # 폼에서 사용할 필드를 지정합니다.
        fields = ['name', 'email', 'inquiry_type', 'subject', 'message', 'privacy_agree']