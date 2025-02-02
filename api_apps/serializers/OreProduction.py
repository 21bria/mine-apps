from rest_framework import serializers
from sqms_apps.models.ore_production_model import OreProductionsView

class OreProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OreProductionsView
        fields = '__all__'  # Menyertakan semua field dari model

class OreProductionAggregateSerializer(serializers.Serializer): 
    total_ore = serializers.FloatField()
    total_lim = serializers.FloatField()
    total_sap = serializers.FloatField()

    def to_representation(self, instance):
        # Pembulatan hasil ke 2 decimal places
        instance['total_ore'] = round(instance['total_ore'], 2)
        instance['total_lim'] = round(instance['total_lim'], 2)
        instance['total_sap'] = round(instance['total_sap'], 2)
        return super().to_representation(instance)