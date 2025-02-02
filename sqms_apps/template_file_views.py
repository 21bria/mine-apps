import os
from django.shortcuts import render
from django.conf import settings
from .utils.permissions import get_dynamic_permissions

def format_downloads(request):
    # Path ke folder format-upload
    folder_path = os.path.join(settings.BASE_DIR, 'static/format-upload')

    # List semua file dalam folder
    files = []
    for idx, filename in enumerate(os.listdir(folder_path), start=1):
        if filename.endswith('.xlsx'):  # Filter file dengan ekstensi .xlsx
            files.append({
                "no"   : idx,
                "name" : filename,
                "path" : f"format-upload/{filename}",
            })
    
     # Ambil permissions dinamis dari database
    permissions = get_dynamic_permissions(request.user)
    context = {
        'files': files,
        'permissions': permissions,
    }      

    return render(request, "template-downloads.html", context)
