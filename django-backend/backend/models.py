from django.db import models
import os

# Create your models here.

def pdf_upload_path(instance, filename):
    return os.path.join(f"PDFsUploaded/{instance.category}", filename)

class PdfFile(models.Model):
    CATEGORY_CHOICES = [
        ("current", "Current PDF"),
        ("past", "Past PDF"),
    ]
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    file = models.FileField(upload_to=pdf_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name