from django.shortcuts import render
from django.http import JsonResponse
from sqms_apps.models import Material

# Create your views here.
def material_list(request):
    material = Material.objects.all()
    data =  {
        'result' : list(material.values('nama_material','created_at'))
    }
    return JsonResponse(data)
