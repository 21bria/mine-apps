from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.permissions import AllowAny
from rest_framework import status
from sqms_apps.models.ore_production_model import OreProductionsView
from ..serializers.OreProduction import OreProductionAggregateSerializer
from ..serializers.monthlySerializer import MonthlySerializer
from django.db.models import Q, Case, When, F, Value, Sum, Min, Max, Count, FloatField
from datetime import datetime

def get_month_label(month_number):
    month_labels = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    return month_labels.get(month_number, '')

class OreProductionView(APIView):
    permission_classes = [AllowAny]  # Menonaktifkan autentikasi untuk testing
    
    def get_queryset(self):
        return OreProductionsView.objects.all()

    def get(self, request):
            # total = OreProductionsView.objects.aggregate(Sum('tonnage'))
            # print('total:', total)

           # Calculate
            total_ore = OreProductionsView.objects.aggregate(
                total_tonnage=Sum(Case(
                    When(stockpile='Temp-Rompile_KM09', then=Value(0, output_field=FloatField())), 
                    default=F('tonnage'),
                    output_field=FloatField()
                )),
                total_lim=Sum(Case(
                    When(nama_material='LIM', then=F('tonnage')),
                    default=Value(0, output_field=FloatField()),
                    output_field=FloatField()  
                )),
                total_sap=Sum(Case(
                    # ~Q(stockpile='Temp-Rompile_KM09'): Ini adalah cara untuk menulis not equal menggunakan negasi Q objects di Django. 
                    When(Q(nama_material='SAP') & ~Q(stockpile='Temp-Rompile_KM09'), then=F('tonnage')),
                    default=Value(0, output_field=FloatField()),
                    output_field=FloatField()
                 ))
            )

            print('total:', total_ore)

            # return Response({
            #     'total_ore': total_ore['total_tonnage'],
            #     'total_lim': total_ore['total_lim'],
            #     'total_sap': total_ore['total_sap'],
            # }, status=status.HTTP_200_OK)

            # Menggunakan serializer untuk pembulatan dan pengembalian data
            serializer = OreProductionAggregateSerializer({
                'total_ore': total_ore['total_tonnage'],
                'total_lim': total_ore['total_lim'],
                'total_sap': total_ore['total_sap']
            })

            return Response(serializer.data, status=status.HTTP_200_OK)
    
class OreProductionYearView(APIView):
    permission_classes = [AllowAny]  # Menonaktifkan autentikasi untuk testing
    
    def get_queryset(self):
        return OreProductionsView.objects.all()

    def get(self, request):
        filter_year = request.GET.get('filter_year', None)
        if not filter_year:
            filter_year = datetime.now().year
        try:
            # Agregasi data berdasarkan bulan
            data = (
                OreProductionsView.objects.filter(tgl_production__year=filter_year)
                .values('tgl_production__month')  # Group by bulan
                .annotate(
                    total_tonnage=Sum(F('tonnage')),
                    total_hpal=Sum(
                        Case(
                            When(nama_material='LIM', then=F('tonnage')),
                            default=Value(0, output_field=FloatField()),
                            output_field=FloatField(),
                        )
                    ),
                    total_rkef=Sum(
                        Case(
                            When(nama_material='SAP', then=F('tonnage')),
                            default=Value(0, output_field=FloatField()),
                            output_field=FloatField(),
                        )
                    ),
                )
                .order_by('tgl_production__month')
            )

            # Format hasil menggunakan serializer
            serialized_data = MonthlySerializer(
                data=[
                    {
                        'month'     : get_month_label(entry['tgl_production__month']),
                        'total'     : entry['total_tonnage'] or 0,
                        'total_hpal': entry['total_hpal'] or 0,
                        'total_rkef': entry['total_rkef'] or 0,
                    }
                    for entry in data
                ],
                many=True,
            )
            serialized_data.is_valid(raise_exception=True)  # Validasi data

            return Response({'monthly_data': serialized_data.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)