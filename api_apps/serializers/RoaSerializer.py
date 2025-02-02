from rest_framework import serializers

class ROASerializer(serializers.Serializer):
    Ni    = serializers.FloatField()
    Co    = serializers.FloatField()
    Al2O3 = serializers.FloatField()
    Cr2O3 = serializers.FloatField()
    Fe    = serializers.FloatField()
    MgO   = serializers.FloatField()
    SiO2  = serializers.FloatField()
    Mc    = serializers.FloatField()

    def to_representation(self, instance):
        # Gunakan format() untuk dua angka di belakang koma
        instance['Ni']    = "{:.2f}".format(instance['Ni'])
        instance['Co']    = "{:.2f}".format(instance['Co'])
        instance['Al2O3'] = "{:.2f}".format(instance['Al2O3'])
        instance['Cr2O3'] = "{:.2f}".format(instance['Cr2O3'])
        instance['Fe']    = "{:.2f}".format(instance['Fe'])
        instance['MgO']   = "{:.2f}".format(instance['MgO'])
        instance['SiO2']  = "{:.2f}".format(instance['SiO2'])
        instance['Mc']    = "{:.2f}".format(instance['Mc'])
        return super().to_representation(instance)
    