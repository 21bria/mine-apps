from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.permissions import AllowAny
from rest_framework import status
from sqms_apps.models.selling_details_view_model import SellingDetailsView
from ..serializers.OreSelling import OreSellingAggregateSerializer
from ..serializers.monthlySerializer import MonthlySerializer
from django.db.models import Q, Case, When, F, Value, Sum, Min, Max, Count, FloatField
from datetime import datetime, timedelta

def get_month_label(month_number):
    month_labels = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    return month_labels.get(month_number, '')


class OreSellingView(APIView):
    permission_classes = [AllowAny]  # Menonaktifkan autentikasi untuk testing
    
    def get_queryset(self):
        return SellingDetailsView.objects.all()

    def get(self, request):
            total_ore = SellingDetailsView.objects.aggregate(
                total_tonnage=Sum(F('tonnage')),
                total_hpal=Sum(Case(
                    When(sale_adjust='HPAL', then=F('tonnage')),
                    default=Value(0, output_field=FloatField()),
                    output_field=FloatField()  
                )),
                total_rkef=Sum(Case(
                     When(sale_adjust='RKEF', then=F('tonnage')),
                    default=Value(0, output_field=FloatField()),
                    output_field=FloatField()  
                 ))
            )

            # Menggunakan serializer untuk pembulatan dan pengembalian data
            serializer = OreSellingAggregateSerializer({
                'total_ore' : total_ore['total_tonnage'],
                'total_hpal': total_ore['total_hpal'],
                'total_rkef': total_ore['total_rkef']
            })

            return Response(serializer.data, status=status.HTTP_200_OK)

class OreSellingYearView(APIView):
    permission_classes = [AllowAny]  # Menonaktifkan autentikasi untuk testing
    
    def get_queryset(self):
        return SellingDetailsView.objects.all()

    def get(self, request):
        filter_year = request.GET.get('filter_year', None)
        if not filter_year:
            filter_year = datetime.now().year

        try:
            # Agregasi data berdasarkan bulan
            data = (
                SellingDetailsView.objects.filter(date_wb__year=filter_year)
                .values('date_wb__month')  # Group by bulan
                .annotate(
                    total_tonnage=Sum(F('tonnage')),
                    total_hpal=Sum(
                        Case(
                            When(sale_adjust='HPAL', then=F('tonnage')),
                            default=Value(0, output_field=FloatField()),
                            output_field=FloatField(),
                        )
                    ),
                    total_rkef=Sum(
                        Case(
                            When(sale_adjust='RKEF', then=F('tonnage')),
                            default=Value(0, output_field=FloatField()),
                            output_field=FloatField(),
                        )
                    ),
                )
                .order_by('date_wb__month')
            )

            # # Format hasil menjadi bentuk yang sesuai
            # result = {
            #     'monthly_data': [
            #         {
            #             'month'     : entry['date_wb__month'],
            #             'total'     : entry['total_tonnage'] or 0,
            #             'total_hpal': entry['total_hpal'] or 0,
            #             'total_rkef': entry['total_rkef'] or 0,
            #         }
            #         for entry in data
            #     ]
            # }

            # return Response(result, status=status.HTTP_200_OK)

            # Format hasil menggunakan serializer
            serialized_data = MonthlySerializer(
                data=[
                    {
                        'month'     : get_month_label(entry['date_wb__month']),
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

       