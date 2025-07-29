from django.db import models

class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    social_id = models.CharField(max_length=225, null=True, blank=True)

class Clothing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
