from sqms_apps.models import Material
from rest_framework import serializers

class MaterialsSerializer(serializers.ModelSerializer):
		class Meta:
			model  = Material
			fields = '__all__' #menampilkan semua field pada class Material
			# fields = ('nama_material', 'created_at')