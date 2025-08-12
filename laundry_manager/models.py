from django.db import models
from django.conf import settings

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='laundry_symbols/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image uploaded at {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
    
'''class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    social_id = models.CharField(max_length=225, null=True, blank=True)'''

class Clothing(models.Model):
   #user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    clothing_type = models.CharField(max_length=255, null=True, blank=True)
    fabric = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=255, null=True, blank=True)
    thickness = models.CharField(max_length=255, null=True, blank=True)
    sensitivity = models.CharField(max_length=255, null=True, blank=True)
    structure = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Stain(models.Model):
    clothing = models.ForeignKey(Clothing, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)

class LaundrySymbol(models.Model):
    clothing = models.ForeignKey(Clothing, on_delete=models.CASCADE)
    symbol_type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    image_url = models.CharField(max_length=255, null=True, blank=True)

class WashingCourse(models.Model):
    course_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

class WashingMode(models.Model):
    water_temp = models.IntegerField(null=True, blank=True)
    wash_strength = models.CharField(max_length=255, null=True, blank=True)
    rinse_count = models.IntegerField(null=True, blank=True)
    spin_level = models.CharField(max_length=255, null=True, blank=True)
    prewash = models.BooleanField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

class Recommendation(models.Model):
    clothing = models.ForeignKey(Clothing, on_delete=models.CASCADE)
    stain = models.ForeignKey(Stain, on_delete=models.CASCADE)
    laundry = models.ForeignKey(LaundrySymbol, on_delete=models.CASCADE)
    course = models.ForeignKey(WashingCourse, on_delete=models.CASCADE)
    mode = models.ForeignKey(WashingMode, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class LaundryHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='laundry_histories'
    )
    
    # 사용자가 입력한 정보
    materials = models.CharField(max_length=255, help_text="입력받은 소재 정보 (쉼표로 구분)")
    symbols = models.TextField(help_text="인식/입력된 세탁기호 목록 (쉼표로 구분)")
    stains = models.CharField(max_length=255, blank=True, help_text="입력받은 얼룩 정보 (쉼표로 구분)")
    
    # 최종 추천 결과
    recommendation_result = models.TextField(help_text="사용자에게 보여준 최종 추천 세탁법 텍스트")
    
    # 기록 생성일
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Django 기본 User 모델은 username 속성을 가집니다.
        return f"[{self.user.username}]님의 세탁 기록 ({self.created_at.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ['-created_at'] # 최신 기록부터 보이도록 정렬