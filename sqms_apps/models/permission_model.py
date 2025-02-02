from django.db import models
from django.contrib.auth.models import Group

from django.contrib.auth.models import Group
from django.db import models

class PermissionGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    groups = models.ManyToManyField(Group, through='PermissionRoleGroup', related_name="permission_role")

    def __str__(self):
        return self.name

    class Meta:
        db_table     = 'permission_role'  # Nama tabel untuk PermissionGroup
        app_label    = 'sqms_apps'
        verbose_name = "Permission Group"
        verbose_name_plural = "Permission Groups"


class PermissionRoleGroup(models.Model):
    permission_group = models.ForeignKey(PermissionGroup, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        db_table     = 'permission_role_groups'  # Nama tabel untuk relasi
        verbose_name = "Permission Role Group"
        verbose_name_plural = "Permission Role Groups"

class Menu(models.Model):
    name = models.CharField(max_length=100)  # Nama menu
    url = models.CharField(max_length=200, null=True, blank=True)  # URL atau nama route
    permission = models.ForeignKey(
        PermissionGroup, 
        on_delete=models.CASCADE,
        related_name='menus'  # Mempermudah query relasi
    )
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='children'  # Relasi untuk submenu
    )
    is_active = models.BooleanField(default=True)  # Status aktif/non-aktif

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'permission_menu'
        app_label = 'sqms_apps'
        verbose_name = "Menu"
        verbose_name_plural = "Menus"
        ordering = ['name']  # Urutkan berdasarkan nama
