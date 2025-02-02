from rest_framework import serializers
from sqms_apps.models.selling_details_view_model import SellingDetailsView

class OreSellingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellingDetailsView
        fields = '__all__'  # Menyertakan semua field dari model

class OreSellingAggregateSerializer(serializers.Serializer): 
    total_ore   = serializers.FloatField()
    total_hpal  = serializers.FloatField()
    total_rkef  = serializers.FloatField()

    def to_representation(self, instance):
        # Pembulatan hasil ke 2 decimal places
        instance['total_ore']  = round(instance['total_ore'], 2)
        instance['total_hpal'] = round(instance['total_hpal'], 2)
        instance['total_rkef'] = round(instance['total_rkef'], 2)
        return super().to_representation(instance)
    

