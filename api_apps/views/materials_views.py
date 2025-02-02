from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.permissions import AllowAny
from rest_framework import status
from sqms_apps.models import Material
from ..serializers.materials import MaterialsSerializer

class MaterialView(APIView):
    """
    ViewSet untuk Material: Mendukung operasi GET, POST, PUT, dan DELETE.
    """
    # permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    permission_classes = [AllowAny] #menonaktifkan autentikasi

    def get_queryset(self):
        """
        Mengembalikan queryset dari Material untuk digunakan di view.
        """
        return Material.objects.all()

    def get(self, request, pk=None):
        """
        Jika `pk` diberikan, ambil detail Material tertentu.
        Jika tidak, ambil semua Material.
        """
        if pk:
            material = get_object_or_404(Material, pk=pk)
            serializer = MaterialsSerializer(material)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            materials = Material.objects.all()
            serializer = MaterialsSerializer(materials, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = MaterialsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        """
        Perbarui data Material berdasarkan `pk`.
        """
        material = get_object_or_404(Material, pk=pk)
        serializer = MaterialsSerializer(material, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Hapus data Material berdasarkan `pk`.
        """
        material = get_object_or_404(Material, pk=pk)
        material.delete()
        return Response({"message": "Material deleted successfully."}, status=status.HTTP_204_NO_CONTENT)