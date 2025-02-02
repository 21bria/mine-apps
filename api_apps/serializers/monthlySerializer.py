from rest_framework import serializers
from rest_framework.serializers import Serializer, CharField, FloatField

class MonthlySerializer(serializers.Serializer):
    # month = serializers.IntegerField()
    month = serializers.CharField()  # Mengganti IntegerField dengan CharField
    total = serializers.FloatField()
    total_hpal = serializers.FloatField()
    total_rkef = serializers.FloatField()

    def to_representation(self, instance):
        # Pembulatan hasil ke 2 decimal places
        instance['total']      = round(instance['total'], 2)
        instance['total_hpal'] = round(instance['total_hpal'], 2)
        instance['total_rkef'] = round(instance['total_rkef'], 2)
        return super().to_representation(instance)