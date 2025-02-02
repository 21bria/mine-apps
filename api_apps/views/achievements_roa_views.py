from rest_framework.views import APIView
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime
from ..serializers.achievementsSerializer import roaAchievementsSerializer
from django.db import connections
from django.utils.html import escape
import re,json
from sqms_apps.utils.db_utils import get_db_vendor

# Memanggil fungsi utility
db_vendor = get_db_vendor('sqms_db')

# Fungsi untuk sanitasi input
def sanitize_input(value):
    if value is None:
        return None
    return escape(re.sub(r"[;'\"]", "", str(value)))

class AchievementsRoaView(APIView):
    permission_classes = [AllowAny]  # Menonaktifkan autentikasi untuk testing

    def get(self, request):
        # Ambil dan sanitasi input dari request
        start_date     = sanitize_input(request.GET.get('startDate'))
        end_date       = sanitize_input(request.GET.get('endDate'))
        materialFilter = sanitize_input(request.GET.get('materialFilter'))
        cutDate        = sanitize_input(request.GET.get('cutDate'))
        bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
        tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
        sourceFilter   = json.loads(request.GET.get('sourceFilter', '[]'))
        stockpileFilter     = sanitize_input(request.GET.get('stockpileFilter'))
        domeFilter    = sanitize_input(request.GET.get('domeFilter'))

        # sanitize_input: Fungsi ini membersihkan karakter yang berpotensi menyebabkan SQL injection.
        # Filter list sourceFilter
        sourceFilter = [sanitize_input(source) for source in sourceFilter if source]

        # Pagination setup
        page = int(request.GET.get('page', 1))
        per_page = 50
        offset = (page - 1) * per_page

        # Query untuk menghitung total data
        count_query = """
            SELECT COUNT(*) FROM details_roa
            WHERE stockpile <> 'Temp-Rompile_KM09'
        """
        
        # Menambahkan kondisi ke count_query berdasarkan input
        if materialFilter:
            count_query += f" AND nama_material = '{materialFilter}'"
        if cutDate:
            count_query += f" AND tgl_production <= '{cutDate}'"
        if start_date and end_date:
            count_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
        if bulanFilter and tahunFilter:
            count_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
        if tahunFilter:
            count_query += f" AND YEAR(tgl_production) = {tahunFilter}"
        if sourceFilter:
            count_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
        if stockpileFilter:
            count_query += f" AND stockpile = '{stockpileFilter}'"
        if domeFilter:
            count_query += f" AND pile_id = '{domeFilter}'"

        # Hitung total data
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(count_query)
            total_data = cursor.fetchone()[0]

        # Query berdasarkan database
        if db_vendor == 'mysql':
        # Query untuk MySQL
            sql_query = """
                SELECT
                    stockpile,
                    pile_id,
                    nama_material,
                    SUM(tonnage) AS total_ore,
                    SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number ='Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                    SUM(CASE WHEN batch_status = 'Complete' AND sample_number ='Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                    SUM(CASE WHEN ROA_Ni IS NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                    SUM(CASE WHEN ROA_Ni  IS NOT NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                    CONCAT(ROUND((SUM(CASE WHEN ROA_Ni  IS NOT NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Ni,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Co,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Al2O3,
                    COALESCE (FORMAT(SUM(tonnage * ROA_CaO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS CaO,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Cr2O3,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Fe2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Fe2O3,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Fe,
                    COALESCE (FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mgo,
                    COALESCE (FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS SiO2,
                    COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mc,
                    ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                    (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS Sm
                FROM details_roa
                WHERE stockpile <> 'Temp-Rompile_KM09'
        """
        elif db_vendor in ['mssql', 'microsoft']:
        # Query untuk SQL Server
            sql_query = """
                SELECT
                    stockpile,
                    pile_id,
                    nama_material,
                    SUM(tonnage) AS total_ore,
                    SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number ='Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                    SUM(CASE WHEN batch_status = 'Complete' AND sample_number ='Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                    SUM(CASE WHEN ROA_Ni IS NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                    SUM(CASE WHEN ROA_Ni  IS NOT NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                    CONCAT(ROUND((SUM(CASE WHEN ROA_Ni  IS NOT NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Ni,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Co,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Al2O3,
                    COALESCE (FORMAT(SUM(tonnage * ROA_CaO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS CaO,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Cr2O3,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Fe2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Fe2O3,
                    COALESCE (FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Fe,
                    COALESCE (FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Mgo,
                    COALESCE (FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS SiO2,
                    COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Mc,
                    ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                    (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS Sm
                FROM details_roa
                WHERE stockpile <> 'Temp-Rompile_KM09'
        """
        else:
            raise ValueError("Unsupported database vendor.")

        # Menambahkan kondisi ke query berdasarkan input
        if materialFilter:
            sql_query += f" AND nama_material = '{materialFilter}'"
        if cutDate:
            sql_query += f" AND tgl_production <= '{cutDate}'"
        if start_date and end_date:
            sql_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
        if bulanFilter and tahunFilter:
            sql_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
        if tahunFilter:
            sql_query += f" AND YEAR(tgl_production) = {tahunFilter}"
        if sourceFilter:
            sql_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
        if stockpileFilter:
            sql_query += f" AND stockpile = '{stockpileFilter}'"
        if domeFilter:
            sql_query += f" AND pile_id = '{domeFilter}'"

        sql_query += """
            GROUP BY stockpile, pile_id, nama_material
            ORDER BY stockpile,pile_id,nama_material ASC
        """
        # Query untuk mengambil data dengan pagination
        if db_vendor == 'mysql':
            sql_query += f" LIMIT {per_page} OFFSET {offset};"
        
        elif db_vendor in ['mssql', 'microsoft']:
            # Adding pagination (OFFSET-FETCH) SQL SERVER
            sql_query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"
        else:
            raise ValueError("Unsupported database vendor.")

        # Eksekusi query untuk mengambil data
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(sql_query)
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Serialize data
        serializer = roaAchievementsSerializer(data=sql_data, many=True)
        serializer.is_valid(raise_exception=True)

        # Hitung jika masih ada data untuk halaman berikutnya
        more_data = len(sql_data) == per_page

        # Hitung total halaman
        total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)
        next_page = page + 1 if page < total_pages else None
        prev_page = page - 1 if page > 1 else None

        return Response({
            'pagination': {
                'next'         : next_page,
                'previous'     : prev_page,
                'current_page' : page,
                'more'         : more_data,
                'total_pages'  : total_pages,
                'total_data'   : total_data
            },
            'data': serializer.data
            
        })


