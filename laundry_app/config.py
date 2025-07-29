from django.conf import settings
import os

SECRET_KEY_OCR = 'ZlRPVGx6a2tOS2dYU2pyVk9FdWJldkllYnhjVnhUeEw='
APIGW_URL = 'https://69lnq1awui.apigw.ntruss.com/custom/v1/44707/b2d9494addb1b568c3910aa475973ee922e646f3f22b829529ba0b927df12ff1/general'

OUTPUT_RESULTS_FOLDER = os.path.join(settings.BASE_DIR, 'output_results')