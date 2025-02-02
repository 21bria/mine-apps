from rest_framework.views import APIView
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Case, When, F, Value, Sum, Min, Max, Count, FloatField
from datetime import datetime
from ..serializers.RoaSerializer import ROASerializer
from sqms_apps.models.details_roa_view_model import DetailsRoa

# Grade of Year (HPAL & RKEF)
class hpalGradeRoaView(APIView):
    permission_classes = [AllowAny]  # Menonaktifkan autentikasi untuk testing

    def get(self, request):
        # Mendapatkan filter tahun dari query params
        filter_year = request.GET.get('filter_year', None)
        if not filter_year:
            filter_year = datetime.now().year

        try:
            # Query untuk agregasi data berdasarkan tahun dan nama_material='LIM'
            data = (
                DetailsRoa.objects.filter(
                    tgl_production__year=filter_year,  # Filter berdasarkan tahun
                    nama_material='LIM'  # Filter berdasarkan nama_material = 'LIM'
                )
                .aggregate(
                    Ni = Sum( F('tonnage') * F('ROA_Ni')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Ni__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Co=Sum(F('tonnage') * F('ROA_Co')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Co__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Al2O3=Sum(F('tonnage') * F('ROA_Al2O3')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Al2O3__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Cr2O3=Sum(F('tonnage') * F('ROA_Cr2O3')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Cr2O3__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Fe=Sum(F('tonnage') * F('ROA_Fe')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Fe__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    MgO=Sum(F('tonnage') * F('ROA_MgO')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_MgO__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    SiO2=Sum(F('tonnage') * F('ROA_SiO2')) / Sum(
                        Case(
                           When(~Q(sample_number='Unprepared') & Q(ROA_SiO2__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Mc=Sum(F('tonnage') * F('ROA_MC')) / Sum(
                        Case(
                           When(~Q(sample_number='Unprepared') & Q(ROA_MC__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    )
                )
            )

            # Format data untuk serializer
            result_data = [{
                'Ni'    : data['Ni'] or 0,
                'Co'    : data['Co'] or 0,
                'Al2O3' : data['Al2O3'] or 0,
                'Cr2O3' : data['Cr2O3'] or 0,
                'Fe'    : data['Fe'] or 0,
                'MgO'   : data['MgO'] or 0,
                'SiO2'  : data['SiO2'] or 0,
                'Mc'    : data['Mc'] or 0
            }]

            # Serialisasi hasil data
            serialized_data = ROASerializer(data=result_data, many=True)
            serialized_data.is_valid(raise_exception=True)

            return Response({'grade_hpal': serialized_data.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class rkefGradeRoaView(APIView):
    permission_classes = [AllowAny]  # Menonaktifkan autentikasi untuk testing

    def get(self, request):
        # Mendapatkan filter tahun dari query params
        filter_year = request.GET.get('filter_year', None)
        if not filter_year:
            filter_year = datetime.now().year
        try:
            data = (
                DetailsRoa.objects.filter(
                    tgl_production__year=filter_year,  # Filter berdasarkan tahun
                    nama_material='SAP'  # Filter berdasarkan nama_material = 'SAP'
                ).exclude(
                    stockpile='Temp-Rompile_KM09'  # Exclude stockpile dengan nilai 'Temp-Rompile_KM09'
                )
                .aggregate(
                    # F('tonnage'): Merujuk ke nilai kolom tonnage di tabel database.
                    Ni = Sum( F('tonnage') * F('ROA_Ni')) / Sum(
                        Case(
                            # ~Q(sample_number='Unprepared'): Menangani logika <> dalam SQL.
                            # Q(ROA_Ni__isnull=False): Memastikan ROA_Ni tidak NULL.
                            When(~Q(sample_number='Unprepared') & Q(ROA_Ni__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Co=Sum(F('tonnage') * F('ROA_Co')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Co__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Al2O3=Sum(F('tonnage') * F('ROA_Al2O3')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Al2O3__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Cr2O3=Sum(F('tonnage') * F('ROA_Cr2O3')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Cr2O3__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Fe=Sum(F('tonnage') * F('ROA_Fe')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Fe__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    MgO=Sum(F('tonnage') * F('ROA_MgO')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_MgO__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    SiO2=Sum(F('tonnage') * F('ROA_SiO2')) / Sum(
                        Case(
                           When(~Q(sample_number='Unprepared') & Q(ROA_SiO2__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Mc=Sum(F('tonnage') * F('ROA_MC')) / Sum(
                        Case(
                           When(~Q(sample_number='Unprepared') & Q(ROA_MC__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    )
                )
            )

            # Format data untuk serializer
            result_data = [{
                'Ni'    : data['Ni'] or 0,
                'Co'    : data['Co'] or 0,
                'Al2O3' : data['Al2O3'] or 0,
                'Cr2O3' : data['Cr2O3'] or 0,
                'Fe'    : data['Fe'] or 0,
                'MgO'   : data['MgO'] or 0,
                'SiO2'  : data['SiO2'] or 0,
                'Mc'    : data['Mc'] or 0
            }]

            # Serialisasi hasil data
            serialized_data = ROASerializer(data=result_data, many=True)
            serialized_data.is_valid(raise_exception=True)

            return Response({'grade_rkef': serialized_data.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Grade of month (HPAL & RKEF)
class hpalGradeMonthRoaView(APIView):
    permission_classes = [AllowAny]  # Menonaktifkan autentikasi untuk testing

    def get(self, request):

        # Ambil filter dari request
        filter_year  = request.GET.get('filter_year',None)
        filter_month = request.GET.get('filter_month',None)
    
        # Gunakan default jika filter tidak valid
        current_year  = datetime.now().year
        current_month = datetime.now().month

        filter_year   = filter_year or current_year
        filter_month  = filter_month or current_month

        try:
            # Query untuk agregasi data berdasarkan tahun dan nama_material='LIM'
            data = (
                DetailsRoa.objects.filter(
                    tgl_production__year=filter_year,  # Filter berdasarkan tahun
                    tgl_production__month=filter_month,  # Filter berdasarkan bulan
                    nama_material='LIM'  # Filter berdasarkan nama_material = 'LIM'
                )
                .aggregate(
                    Ni = Sum( F('tonnage') * F('ROA_Ni')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Ni__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Co=Sum(F('tonnage') * F('ROA_Co')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Co__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Al2O3=Sum(F('tonnage') * F('ROA_Al2O3')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Al2O3__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Cr2O3=Sum(F('tonnage') * F('ROA_Cr2O3')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Cr2O3__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Fe=Sum(F('tonnage') * F('ROA_Fe')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Fe__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    MgO=Sum(F('tonnage') * F('ROA_MgO')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_MgO__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    SiO2=Sum(F('tonnage') * F('ROA_SiO2')) / Sum(
                        Case(
                           When(~Q(sample_number='Unprepared') & Q(ROA_SiO2__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Mc=Sum(F('tonnage') * F('ROA_MC')) / Sum(
                        Case(
                           When(~Q(sample_number='Unprepared') & Q(ROA_MC__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    )
                )
            )

            # Format data untuk serializer
            result_data = [{
                'Ni'    : data['Ni'] or 0,
                'Co'    : data['Co'] or 0,
                'Al2O3' : data['Al2O3'] or 0,
                'Cr2O3' : data['Cr2O3'] or 0,
                'Fe'    : data['Fe'] or 0,
                'MgO'   : data['MgO'] or 0,
                'SiO2'  : data['SiO2'] or 0,
                'Mc'    : data['Mc'] or 0
            }]

            # Serialisasi hasil data
            serialized_data = ROASerializer(data=result_data, many=True)
            serialized_data.is_valid(raise_exception=True)

            return Response({'grade_hpal': serialized_data.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class rkefGradeMonthRoaView(APIView):
    permission_classes = [AllowAny]  # Menonaktifkan autentikasi untuk testing

    def get(self, request):
        # Ambil filter dari request
        # GET /api_apps/ore-production/grade-rkef/month/?filter_year=2024&filter_month=12
        filter_year  = request.GET.get('filter_year',None)
        filter_month = request.GET.get('filter_month',None)
    
        # Gunakan default jika filter tidak valid
        current_year  = datetime.now().year
        current_month = datetime.now().month

        filter_year   = filter_year or current_year
        filter_month  = filter_month or current_month

        try:
            data = (
                DetailsRoa.objects.filter(
                    tgl_production__year=filter_year,  # Filter berdasarkan tahun
                    tgl_production__month=filter_month,  # Filter berdasarkan bulan
                    nama_material='SAP'  # Filter berdasarkan nama_material = 'SAP'
                ).exclude(
                    stockpile='Temp-Rompile_KM09'  # Exclude stockpile dengan nilai 'Temp-Rompile_KM09'
                )
                .aggregate(
                    # F('tonnage'): Merujuk ke nilai kolom tonnage di tabel database.
                    Ni = Sum( F('tonnage') * F('ROA_Ni')) / Sum(
                        Case(
                            # ~Q(sample_number='Unprepared'): Menangani logika <> dalam SQL.
                            # Q(ROA_Ni__isnull=False): Memastikan ROA_Ni tidak NULL.
                            When(~Q(sample_number='Unprepared') & Q(ROA_Ni__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Co=Sum(F('tonnage') * F('ROA_Co')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Co__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Al2O3=Sum(F('tonnage') * F('ROA_Al2O3')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Al2O3__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Cr2O3=Sum(F('tonnage') * F('ROA_Cr2O3')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Cr2O3__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Fe=Sum(F('tonnage') * F('ROA_Fe')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_Fe__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    MgO=Sum(F('tonnage') * F('ROA_MgO')) / Sum(
                        Case(
                            When(~Q(sample_number='Unprepared') & Q(ROA_MgO__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    SiO2=Sum(F('tonnage') * F('ROA_SiO2')) / Sum(
                        Case(
                           When(~Q(sample_number='Unprepared') & Q(ROA_SiO2__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    ),
                    Mc=Sum(F('tonnage') * F('ROA_MC')) / Sum(
                        Case(
                           When(~Q(sample_number='Unprepared') & Q(ROA_MC__isnull=False), then=F('tonnage')),
                            default=Value(0),
                            output_field=FloatField()
                        )
                    )
                )
            )

            # Format data untuk serializer
            result_data = [{
                'Ni'    : data['Ni'] or 0,
                'Co'    : data['Co'] or 0,
                'Al2O3' : data['Al2O3'] or 0,
                'Cr2O3' : data['Cr2O3'] or 0,
                'Fe'    : data['Fe'] or 0,
                'MgO'   : data['MgO'] or 0,
                'SiO2'  : data['SiO2'] or 0,
                'Mc'    : data['Mc'] or 0
            }]

            # Serialisasi hasil data
            serialized_data = ROASerializer(data=result_data, many=True)
            serialized_data.is_valid(raise_exception=True)

            return Response({'grade_rkef': serialized_data.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)