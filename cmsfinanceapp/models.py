from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class file_data(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    excel_file = models.FileField(upload_to='excel', max_length=None)
    def __str__(self):
        return str(self.username)