from rest_framework import serializers
from django.core.files.base import ContentFile
import base64


class Base64ImageField(serializers.ImageField):
    """Сериализатор для декодирования картинок"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)
