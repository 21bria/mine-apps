from django.contrib.auth.models import User
from django.db import models

class CustomModel(models.Model):
    # Relasi ke model User
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_models', verbose_name="User")

    # Kolom-kolom lainnya
    first_name = models.CharField(max_length=255, verbose_name="First Name")
    last_name = models.CharField(max_length=255, verbose_name="Last Name")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone Number")
    address = models.TextField(blank=True, null=True, verbose_name="Address")
 

    # Menambahkan string representation
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.username})"
    
    # Mengatur Meta untuk plural dan ordering
    class Meta:
        verbose_name = "Custom Model"
        verbose_name_plural = "Custom Models"
        ordering = ['-date_joined']  # Mengurutkan berdasarkan tanggal bergabung (terbaru di atas)
