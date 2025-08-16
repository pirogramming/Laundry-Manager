from django.db import models
from django.conf import settings
from django.templatetags.static import static


class UploadedImage(models.Model):
    image = models.ImageField(upload_to="laundry_symbols/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image uploaded at {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"


"""class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    social_id = models.CharField(max_length=225, null=True, blank=True)
"""


class Clothing(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
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
        related_name="laundry_histories",
    )

    # 사용자가 입력한 정보
    materials = models.CharField(
        max_length=255, help_text="입력받은 소재 정보 (쉼표로 구분)"
    )
    symbols = models.TextField(help_text="인식/입력된 세탁기호 목록 (쉼표로 구분)")
    stains = models.CharField(
        max_length=255, blank=True, help_text="입력받은 얼룩 정보 (쉼표로 구분)"
    )

    # 최종 추천 결과
    recommendation_result = models.TextField(
        help_text="사용자에게 보여준 최종 추천 세탁법 텍스트"
    )

    # 기록 생성일
    created_at = models.DateTimeField(auto_now_add=True)

    def get_stain_image_url(self):
        STAIN_IMAGE_MAP = {
            "혈흔": "blood.webp",
            "화장품 얼룩": "cosmetic.webp",
            "땀 얼룩": "sweat-armpit.webp",
            "커피와 차 얼룩": "coffee.webp",
            "펜과 잉크 얼룩": "pen.webp",
            "강황 얼룩": "curcuma.webp",
            "겨자, 케첩, 소스 얼룩": "sauce.webp",
            "곰팡이 얼룩": "mold.webp",
            "과일 및 야채 얼룩": "fruit.webp",
            "껌 얼룩": "gum.webp",
            "꽃가루 얼룩": "flower.webp",
            "녹 얼룩": "rust.webp",
            "대변, 소변, 구토 얼룩": "poop.webp",
            "먼지와 진흙얼룩": "dust.webp",
            "모발 염료 및 염색약 얼룩": "hair-dye.webp",
            "매니큐어 얼룩": "manicure.webp",
            "반려동물 소변 및 배설물 얼룩": "poop.webp",
            "세탁과 건조 후 생긴 얼룩": "after-laundry.webp",
            "섬유 유연제 얼룩": "fabric-softner.webp",
            "아보카도 얼룩": "avocado.webp",
            "아이스크림 얼룩": "icecream.webp",
            "염색약, 페인트 등의 색상 얼룩": "hair-dye.webp",
            "음식 얼룩": "food-stain.webp",
            "윤활유 및 기름 얼룩": "oil.webp",
            "적포도주 얼룩": "wine.webp",
            "주스 얼룩": "juice.webp",
            "자외선 차단제, 크림 및 로션 얼룩": "suncream.webp",
            "잔디의 녹색 색소 얼룩": "grass.webp",
            "청바지 얼룩": "jean.webp",
            "초콜릿 얼룩": "chocolate.webp",
            "치약 얼룩": "toothpaste.webp",
            "카레와 향신료 얼룩": "curry.webp",
            "크레용 및 염색약 얼룩": "crayon.webp",  # '왁스'에서 '염색약'으로 수정 제안
            "탈취제 얼룩": "deodorant.webp",
            "토마토 얼룩": "tomato.webp",
        }

        if not self.stains:
            return static("stain_image/default.webp")

        primary_stain = self.stains.split(",")[0].strip()

        image_filename = STAIN_IMAGE_MAP.get(primary_stain, "default.webp")

        return static(f"stain_image/{image_filename}")

    def __str__(self):
        # Django 기본 User 모델은 username 속성을 가집니다.
        return f"[{self.user.username}]님의 세탁 기록 ({self.created_at.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ['-created_at'] # 최신 기록부터 보이도록 정렬


# 문의하기 처리를 위한 model    
class Inquiry(models.Model):
    INQUIRY_TYPE_CHOICES = [
        ('서비스 이용 문의', '서비스 이용 문의'),
        ('버그/오류 제보', '버그/오류 제보'),
        ('세탁소 제휴 문의', '세탁소 제휴 문의'),
        ('기타', '기타'),
    ]

    name = models.CharField(max_length=50, verbose_name="이름")
    email = models.EmailField(verbose_name="이메일")
    inquiry_type = models.CharField(max_length=50, choices=INQUIRY_TYPE_CHOICES, verbose_name="문의 유형")
    subject = models.CharField(max_length=200, verbose_name="제목")
    message = models.TextField(verbose_name="내용")
    privacy_agree = models.BooleanField(default=False, verbose_name="개인정보 수집 동의")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    is_resolved = models.BooleanField(default=False, verbose_name="답변 완료 여부")

    def __str__(self):
        return f'[{self.inquiry_type}] {self.subject} - {self.name}'
        ordering = ["-created_at"]  # 최신 기록부터 보이도록 정렬


class FavoriteItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)

    class Meta:
        # 한 사용자가 같은 항목을 두 번 즐겨찾기 하지 못하도록 설정
        unique_together = ("user", "title")

    def __str__(self):
        return f"{self.user.username}의 즐겨찾기: {self.title}"
