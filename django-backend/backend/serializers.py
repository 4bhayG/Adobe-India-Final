from rest_framework import serializers
from .models import PdfFile

class PdfFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdfFile
        fields = '__all__'

