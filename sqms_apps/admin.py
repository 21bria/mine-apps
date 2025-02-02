# sqms_apps/admin.py
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin

# from .models import YourModel1  # Gantilah dengan model dari sqms_apps

class SqmsAdminSite(admin.AdminSite):
    site_header = "SQMS Admin"
    site_title  = "SQMS Admin"
    index_title = "Welcome to SQMS Admin"
    site_url    = "/sqms_apps/index-mgoqa"  # URL aplikasi untuk tombol "View Site"

sqms_site = SqmsAdminSite(name='sqms_admin')

# Daftarkan model Group dan User ke sqms_admin_site
sqms_site.register(Group, GroupAdmin)
sqms_site.register(User, UserAdmin)
