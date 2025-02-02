# views.py
import logging
from django.http import JsonResponse
from django.db import connections, DatabaseError
from plotly.offline import plot
import plotly.graph_objs as go
from prophet import Prophet
import pandas as pd
from datetime import datetime, timedelta
from ...utils.utils import validate_month,validate_year
from ...models.ore_productions_model import OreProductions
import itertools
from django.db.models import Sum
from datetime import timedelta
from django.utils.timezone import now
from django.db.models.functions import TruncWeek
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database.
import json
from ...utils.db_utils import get_db_vendor

# Memanggil fungsi utility
db_vendor = get_db_vendor('sqms_db')

class NaNEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float) and (obj != obj):  # Memeriksa NaN
            return None
        return super().default(obj)

def get_month_label(month_number):
    month_labels = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    return month_labels.get(month_number, '')

# Project to Date Ore
def get_ore_ptd(request):
    query = """
        SELECT
            COALESCE(ROUND(SUM(CASE WHEN stockpile!= 'Temp-Rompile_KM09' THEN tonnage ELSE 0 END), 2), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END), 2), 0) AS total_lim,
            COALESCE(ROUND(SUM(CASE WHEN nama_material = 'SAP' AND stockpile != 'Temp-Rompile_KM09' THEN tonnage ELSE 0 END), 2), 0) AS total_sap
        FROM ore_production
    """
    try:
        # Use the correct database connection
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

        total_ore = [entry[0] for entry in data]
        data_hpal = [entry[1] for entry in data]
        data_rkef = [entry[2] for entry in data]

        return JsonResponse({
            'data_hpal': data_hpal,
            'data_rkef': data_rkef,
            'total_ore': total_ore,
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)    

def get_sap_ptd(request):
    query = """
        SELECT
            COALESCE(SUM(tonnage), 0) AS total
        FROM ore_production
        WHERE 
            sale_adjust = 'RKEF'
            AND stockpile != 'Temp-Rompile_KM09'
    """
    try:
        # with connection.cursor() as cursor: ini untuk default Database
        with connections['sqms_db'].cursor as cursor:
            cursor.execute(query)
            data = cursor.fetchone()  # Menggunakan fetchone() karena kita hanya mengambil satu baris

        # Ubah data menjadi integer
        data_rkef = data[0] if data and data[0] is not None else 0

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'data_rkef': data_rkef
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

# YTD Ore Productions
def get_grade_hpal(request):
    # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)

    if filter_year:
        filter_sql = "AND YEAR(tgl_production)= %s"
        params = [filter_year]
    else:
        current_year = datetime.now().year
        filter_sql = "AND YEAR(tgl_production) = %s"
        params = [current_year]

    # Query berdasarkan database
    if db_vendor == 'mysql':
        query = """
            SELECT
                COALESCE (FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Ni,
                COALESCE (FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Co,
                COALESCE (FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Al2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Cr2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Fe,
                COALESCE (FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mgo,
                COALESCE (FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS SiO2,
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mc
            FROM details_roa
            WHERE 
                nama_material ='LIM' 
                {}
        """.format(filter_sql)
    elif db_vendor in ['mssql', 'microsoft']:
          query = """
            SELECT
                COALESCE (FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Ni,
                COALESCE (FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Co,
                COALESCE (FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Al2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Cr2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Fe,
                COALESCE (FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Mgo,
                COALESCE (FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS SiO2,
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Mc
            FROM details_roa
            WHERE 
                nama_material ='LIM' 
                {}
        """.format(filter_sql)
    else:
        raise ValueError("Unsupported database vendor.")

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam list:   
        data_Ni    = [entry[0] for entry in data]  
        data_Co    = [entry[1] for entry in data]  
        data_Al2O3 = [entry[2] for entry in data]  
        data_Cr2O3 = [entry[3] for entry in data]  
        data_Fe    = [entry[4] for entry in data]  
        data_Mgo   = [entry[5] for entry in data]  
        data_SiO2  = [entry[6] for entry in data]  
        data_Mc    = [entry[7] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'hpal_Ni'    : data_Ni,
            'hpal_Co'    : data_Co,
            'hpal_Al2O3' : data_Al2O3,
            'hpal_Cr2O3' : data_Cr2O3,
            'hpal_Fe'    : data_Fe,
            'hpal_Mgo'   : data_Mgo,
            'hpal_SiO2'  : data_SiO2,
            'hpal_Mc'    : data_Mc
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_grade_rkef(request):
    # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)

    if filter_year:
        filter_sql = "AND YEAR(tgl_production)= %s"
        params = [filter_year]
    else:
        current_year = datetime.now().year
        filter_sql = "AND YEAR(tgl_production) = %s"
        params = [current_year]

    # Query berdasarkan database
    if db_vendor == 'mysql':
        query = """
            SELECT
                COALESCE (FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Ni,
                COALESCE (FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Co,
                COALESCE (FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Al2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Cr2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Fe,
                COALESCE (FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mgo,
                COALESCE (FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS SiO2,
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mc
            FROM details_roa
            WHERE 
                nama_material ='SAP' AND stockpile <> 'Temp-Rompile_KM09'
                {}
        """.format(filter_sql)
    elif db_vendor in ['mssql', 'microsoft']:
          query = """
            SELECT
                COALESCE (FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Ni,
                COALESCE (FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Co,
                COALESCE (FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Al2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Cr2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Fe,
                COALESCE (FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Mgo,
                COALESCE (FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS SiO2,
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Mc
            FROM details_roa
            WHERE 
                nama_material ='SAP' AND stockpile <> 'Temp-Rompile_KM09'
                {}
        """.format(filter_sql)
    else:
        raise ValueError("Unsupported database vendor.")
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam list:   
        data_Ni    = [entry[0] for entry in data]  
        data_Co    = [entry[1] for entry in data]  
        data_Al2O3 = [entry[2] for entry in data]  
        data_Cr2O3 = [entry[3] for entry in data]  
        data_Fe    = [entry[4] for entry in data]  
        data_Mgo   = [entry[5] for entry in data]  
        data_SiO2  = [entry[6] for entry in data]  
        data_Mc    = [entry[7] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'rkef_Ni'    : data_Ni,
            'rkef_Co'    : data_Co,
            'rkef_Al2O3' : data_Al2O3,
            'rkef_Cr2O3' : data_Cr2O3,
            'rkef_Fe'    : data_Fe,
            'rkef_Mgo'   : data_Mgo,
            'rkef_SiO2'  : data_SiO2,
            'rkef_Mc'    : data_Mc
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_total_lim(request):
    # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)

    if filter_year:
        filter_sql = "AND YEAR(tgl_production)= %s"
        params = [filter_year]
    else:
        current_year = datetime.now().year
        filter_sql = "AND YEAR(tgl_production) = %s"
        params = [current_year]

    query = """
        SELECT
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(SUM(tonnage * ROA_Ni) / SUM(tonnage), 0) AS ni
        FROM details_roa
        WHERE 
            nama_material = 'LIM'
            AND sample_number <> 'Unprepared'
            AND ROA_Ni IS NOT NULL
            {}
    """.format(filter_sql)
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam list:   
        data_hpal = [entry[0] for entry in data] 
        data_ni   = [entry[1] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'data_hpal' : data_hpal,
            'data_ni'   : data_ni
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_total_sap(request):
    # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)

    if filter_year:
        filter_sql = "AND YEAR(tgl_production) = %s"
        params = [filter_year]
    else:
        current_year = datetime.now().year
        filter_sql = "AND YEAR(tgl_production) = %s"
        params = [current_year]

    query = """
        SELECT
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(SUM(tonnage * ROA_Ni) / SUM(tonnage), 0) AS ni
        FROM details_roa
        WHERE 
            nama_material = 'SAP'
            AND sample_number <> 'Unprepared'
            AND ROA_Ni IS NOT NULL
            {}
    """.format(filter_sql)

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam tiga list:   
        data_rkef = [entry[0] for entry in data] 
        data_ni   = [entry[1] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'data_rkef' : data_rkef,
            'data_ni'   : data_ni
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_ytd_ore(request):
 # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)

    if filter_year:
        filter_sql = "WHERE YEAR(tgl_production) = %s"
        params = [filter_year]
    else:
        current_year = datetime.now().year
        filter_sql = "WHERE YEAR(tgl_production) = %s"
        params = [current_year]
    query = """
        SELECT
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN id_material = '7' THEN tonnage ELSE 0 END), 2), 0) AS total_lim,
            COALESCE(ROUND(SUM(CASE WHEN id_material = '10' THEN tonnage ELSE 0 END), 2), 0) AS total_sap
        FROM ore_productions
        {}
    """.format(filter_sql)
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam  list: 
        x_data    = [entry[0] for entry in data]  
        total_lim = [entry[1] for entry in data] 
        total_sap = [entry[2] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data'   : x_data,
            'total_lim': total_lim,
            'total_sap': total_sap
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500)

def get_chart_ore_class(request):
 # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)
    # filter_year = 2023

    if filter_year:
        filter_sql = "WHERE YEAR(tgl_production) = %s"
        params = [filter_year]
    else:
        current_year = datetime.now().year
        filter_sql = "WHERE YEAR(tgl_production) = %s"
        params = [current_year]

    query = """
       SELECT
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGLO' THEN tonnage ELSE 0 END), 2), 0) AS LGLO,
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGLO' THEN tonnage ELSE 0 END), 2), 0) AS MGLO,
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGLO' THEN tonnage ELSE 0 END), 2), 0) AS HGLO,
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGSO' THEN tonnage ELSE 0 END), 2), 0) AS LGSO,
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGSO' THEN tonnage ELSE 0 END), 2), 0) AS MGSO,
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGSO' THEN tonnage ELSE 0 END), 2), 0) AS HGSO
        FROM ore_productions
        {}

    """.format(filter_sql)
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Pisahkan data ke dalam  list: 
        # Menyusun ulang data sesuai urutan yang diinginkan
            y_data = [entry for entry in chart_data[0]]

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'y_data': y_data,

        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_chart_data(request):
   # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)
    # filter_year = 2023

    if filter_year:
        filter_sql = "WHERE YEAR(tgl_production) = %s"
        params = [filter_year]
    else:
        current_year =  datetime.now().year
        filter_sql = "WHERE YEAR(tgl_production) = %s"
        params = [current_year]

    query = """
        SELECT
            MONTH(tgl_production) AS bulan, 
            YEAR(tgl_production) AS tahun, 
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN id_material = '7' THEN tonnage ELSE 0 END), 2), 0) AS total_lim,
            COALESCE(ROUND(SUM(CASE WHEN id_material = '10' THEN tonnage ELSE 0 END), 2), 0) AS total_sap
        FROM ore_productions
        {}
        GROUP BY MONTH(tgl_production), YEAR(tgl_production)
        ORDER BY MIN(tgl_production);
    """.format(filter_sql)

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Pisahkan data ke dalam tiga list: x_data, y_data_material_lim, y_data_material_sap
        # x_data = [entry[0] for entry in chart_data]  # Label bulan

         # Convert numeric month to month label
        x_data = [get_month_label(entry[0]) for entry in chart_data]  # Convert month number to label
        y_data_material_lim = [entry[3] for entry in chart_data]  # Total tonase material lim
        y_data_material_sap = [entry[4] for entry in chart_data]  # Total tonase material sap

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data'             : x_data,
            'y_data_material_lim': y_data_material_lim,
            'y_data_material_sap': y_data_material_sap
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

# MTD - Ore Production
def get_chart_ore_daily(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []

   # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks = request.GET.get('filter_days')

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        # Jika tidak ada tanggal yang diberikan, gunakan tanggal hari ini
        tanggal = datetime.now().date()
    
    hari_ini = tanggal
    # hari_ini    = datetime.now().date()
    tgl_pertama = hari_ini.replace(day=1)
    # tgl_terakhir = hari_ini.replace(day=1).replace(month=hari_ini.month + 1) - timedelta(days=1)
    tgl_terakhir = (hari_ini.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    last_day = tgl_terakhir.day

    query = """
            SELECT
                tanggal.left_date,
                COALESCE(total_lim, 0) AS lim_total,
                COALESCE(total_sap, 0) AS sap_total,
                COALESCE(total_ore, 0) AS total
            FROM
                tanggal
            LEFT JOIN (
                SELECT
                    left_date,
                    ROUND(SUM(CASE WHEN id_material = 7 THEN tonnage ELSE 0 END), 2) AS total_lim,
                    ROUND(SUM(CASE WHEN id_material = 10 THEN tonnage ELSE 0 END), 2) AS total_sap,
                    SUM(tonnage) AS total_ore
                FROM
                    ore_productions
                WHERE
                    tgl_production BETWEEN %s AND %s
                GROUP BY
                    left_date
            ) AS subquery ON tanggal.left_date = subquery.left_date
            WHERE
                tanggal.left_date <= %s
            ORDER BY tanggal.left_date asc
        """

    params.extend([tgl_pertama, tgl_terakhir, last_day])


    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        x_data     = [entry[0] for entry in chart_data]  
        y_data_lim = [entry[1] for entry in chart_data]  
        y_data_sap = [entry[2] for entry in chart_data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data': x_data,
            'y_data_lim': y_data_lim,
            'y_data_sap': y_data_sap
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_daily_ore_class(request):
 # Ambil data dari database menggunakan cursor SQL
    filter_year   = request.GET.get('filter_year')
    filter_month  = request.GET.get('filter_month')
    # Ambil bulan dan tahun saat ini jika filter bulan tidak disediakan
    current_month = datetime.now().month
    current_year  = datetime.now().year

    # Bangun klausa WHERE sesuai dengan filter yang diberikan
    filter_sql = "WHERE 1=1"  # Klausa awal
    params = []

    if filter_year:
        filter_sql += " AND YEAR(tgl_production) = %s"
        params.append(filter_year)
    else:
        filter_sql += " AND YEAR(tgl_production) = %s"
        params.append(current_year)

    if filter_month:
        filter_sql += " AND MONTH(tgl_production) = %s"
        params.append(filter_month)
    else:
        filter_sql += " AND MONTH(tgl_production) = %s"
        params.append(current_month)
    # Query SQL
    query = """
        SELECT
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGLO' THEN tonnage ELSE 0 END), 2), 0) AS LGLO,
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGLO' THEN tonnage ELSE 0 END), 2), 0) AS MGLO,
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGLO' THEN tonnage ELSE 0 END), 2), 0) AS HGLO,
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGSO' THEN tonnage ELSE 0 END), 2), 0) AS LGSO,
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGSO' THEN tonnage ELSE 0 END), 2), 0) AS MGSO,
            COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGSO' THEN tonnage ELSE 0 END), 2), 0) AS HGSO
        FROM ore_productions
        {}
    """.format(filter_sql)

    try:
        # Eksekusi query dengan parameter yang diberikan
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Pisahkan data ke dalam  list: 
        # Menyusun ulang data sesuai urutan yang diinginkan
            y_data = [entry for entry in chart_data[0]]

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'y_data': y_data,

        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_mtd_ore(request):

   # Ambil data dari database menggunakan cursor SQL
    filter_year   = request.GET.get('filter_year')
    filter_month  = request.GET.get('filter_month')
    # Ambil bulan dan tahun saat ini jika filter bulan tidak disediakan
    current_month = datetime.now().month
    current_year  = datetime.now().year

    # Bangun klausa WHERE sesuai dengan filter yang diberikan
    filter_sql = "WHERE 1=1"  # Klausa awal
    params = []

    if filter_year:
        filter_sql += " AND YEAR(tgl_production) = %s"
        params.append(filter_year)
    else:
        filter_sql += " AND YEAR(tgl_production) = %s"
        params.append(current_year)

    if filter_month:
        filter_sql += " AND MONTH(tgl_production) = %s"
        params.append(filter_month)
    else:
        filter_sql += " AND MONTH(tgl_production) = %s"
        params.append(current_month)
    # Query SQL
    query = """
         SELECT
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN id_material = '7' THEN tonnage ELSE 0 END), 2), 0) AS total_lim,
            COALESCE(ROUND(SUM(CASE WHEN id_material = '10' THEN tonnage ELSE 0 END), 2), 0) AS total_sap
        FROM ore_productions
        {}
    """.format(filter_sql)
    try:
        # Eksekusi query dengan parameter yang diberikan
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

    # Pisahkan data ke dalam  list: 
        x_data    = [entry[0] for entry in data]  
        total_lim = [entry[1] for entry in data] 
        total_sap = [entry[2] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data'   : x_data,
            'total_lim': total_lim,
            'total_sap': total_sap
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_mtd_grade_hpal(request):
    # Ambil filter dari request
    filter_year  = validate_year(request.GET.get('filter_year'))
    filter_month = validate_month(request.GET.get('filter_month'))

    # Gunakan default jika filter tidak valid
    current_year  = datetime.now().year
    current_month = datetime.now().month
    filter_year   = filter_year or current_year
    filter_month  = filter_month or current_month

    # Bangun klausa WHERE dengan parameterisasi
    filter_sql = "WHERE nama_material = 'LIM' AND YEAR(tgl_production) = %s AND MONTH(tgl_production) = %s"
    params     = [filter_year, filter_month]

    if db_vendor == 'mysql':
        query = f"""
            SELECT
                COALESCE (FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Ni,
                COALESCE (FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Co,
                COALESCE (FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Al2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Cr2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Fe,
                COALESCE (FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mgo,
                COALESCE (FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS SiO2,
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mc
            FROM details_roa
            {filter_sql}
        """
    elif db_vendor in ['mssql', 'microsoft']:
        query = f"""
            SELECT
                COALESCE(FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Ni,
                COALESCE(FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Co,
                COALESCE(FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Al2O3,
                COALESCE(FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Cr2O3,
                COALESCE(FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Fe,
                COALESCE(FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Mgo,
                COALESCE(FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS SiO2,
                COALESCE(FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Mc
            FROM details_roa
            {filter_sql}
        """
    else:
            raise ValueError("Unsupported database vendor.")

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam list
        data_Ni     = [entry[0] for entry in data]
        data_Co     = [entry[1] for entry in data]
        data_Al2O3  = [entry[2] for entry in data]
        data_Cr2O3  = [entry[3] for entry in data]
        data_Fe     = [entry[4] for entry in data]
        data_Mgo    = [entry[5] for entry in data]
        data_SiO2   = [entry[6] for entry in data]
        data_Mc     = [entry[7] for entry in data]

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'hpal_Ni'   : data_Ni,
            'hpal_Co'   : data_Co,
            'hpal_Al2O3': data_Al2O3,
            'hpal_Cr2O3': data_Cr2O3,
            'hpal_Fe'   : data_Fe,
            'hpal_Mgo'  : data_Mgo,
            'hpal_SiO2' : data_SiO2,
            'hpal_Mc'   : data_Mc
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def get_mtd_grade_rkef(request):
     # Ambil filter dari request
    filter_year  = validate_year(request.GET.get('filter_year'))
    filter_month = validate_month(request.GET.get('filter_month'))

    # Gunakan default jika filter tidak valid
    current_year  = datetime.now().year
    current_month = datetime.now().month
    filter_year   = filter_year or current_year
    filter_month  = filter_month or current_month

    # Bangun klausa WHERE dengan parameterisasi
    filter_sql = "WHERE nama_material = 'SAP' AND stockpile <> 'Temp-Rompile_KM09' AND YEAR(tgl_production) = %s AND MONTH(tgl_production) = %s"
    params     = [filter_year, filter_month]

    if db_vendor == 'mysql':
        query = f"""
            SELECT
                COALESCE (FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Ni,
                COALESCE (FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Co,
                COALESCE (FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Al2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Cr2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Fe,
                COALESCE (FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mgo,
                COALESCE (FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS SiO2,
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mc
            FROM details_roa
            {filter_sql}
        """
    elif db_vendor in ['mssql', 'microsoft']:
        query = f"""
            SELECT
                COALESCE(FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Ni,
                COALESCE(FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Co,
                COALESCE(FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Al2O3,
                COALESCE(FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Cr2O3,
                COALESCE(FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Fe,
                COALESCE(FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Mgo,
                COALESCE(FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS SiO2,
                COALESCE(FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Mc
            FROM details_roa
            {filter_sql}
        """
    else:
            raise ValueError("Unsupported database vendor.")
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam list:   
        data_Ni    = [entry[0] for entry in data]  
        data_Co    = [entry[1] for entry in data]  
        data_Al2O3 = [entry[2] for entry in data]  
        data_Cr2O3 = [entry[3] for entry in data]  
        data_Fe    = [entry[4] for entry in data]  
        data_Mgo   = [entry[5] for entry in data]  
        data_SiO2  = [entry[6] for entry in data]  
        data_Mc    = [entry[7] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'rkef_Ni'    : data_Ni,
            'rkef_Co'    : data_Co,
            'rkef_Al2O3' : data_Al2O3,
            'rkef_Cr2O3' : data_Cr2O3,
            'rkef_Fe'    : data_Fe,
            'rkef_Mgo'   : data_Mgo,
            'rkef_SiO2'  : data_SiO2,
            'rkef_Mc'    : data_Mc
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

# For Summary
def getTotalOreByYear(request):
    query = """
       SELECT
            DATE_FORMAT(tgl_production, '%Y') AS tahun,
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END), 2), 0) AS total_lim,
            COALESCE(ROUND(SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END), 2), 0) AS total_sap
        FROM ore_production
        WHERE 
            stockpile != 'Temp-Rompile_KM09'
        GROUP BY YEAR(tgl_production)
        ORDER BY MIN(tgl_production);
    """
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

        # Pisahkan data ke dalam  list: 
        tahun      = [entry[0] for entry in data]  
        total      = [entry[1] for entry in data]  
        total_hpal = [entry[2] for entry in data] 
        total_rkef = [entry[3] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'tahun'     : tahun,
            'total'     : total,
            'total_hpal': total_hpal,
            'total_rkef': total_rkef
        })
    except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def getOreHPAL(request):
    query = """
        SELECT 
	        sampling_areas.sampling_area, 
            COALESCE(round(SUM(ore_productions.tonnage),0),0)tonnage
        FROM ore_productions
        Left Join materials ON ore_productions.id_material = materials.id
        Left Join sampling_areas ON ore_productions.id_stockpile = sampling_areas.id
        WHERE nama_material = 'LIM'
        Group By sampling_areas.sampling_area
        Order By MIN(sampling_areas.sampling_area);
  """
    
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

        # Pisahkan data ke dalam  list: 
        stockpile = [entry[0] for entry in data]  
        total     = [entry[1] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'stockpile': stockpile,
            'total'    : total

        })
    except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def getOreRKEF(request):
    query = """
        SELECT 
	        sampling_areas.sampling_area, 
            COALESCE(round(SUM(ore_productions.tonnage),0),0)tonnage
        FROM ore_productions
        Left Join materials ON ore_productions.id_material = materials.id
        Left Join sampling_areas ON ore_productions.id_stockpile = sampling_areas.id
        WHERE nama_material = 'SAP' AND sampling_area <> 'Temp-Rompile_KM09'
        Group By sampling_areas.sampling_area
        Order By MIN(sampling_areas.sampling_area);
  """

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

        # Pisahkan data ke dalam  list: 
        stockpile = [entry[0] for entry in data]  
        total     = [entry[1] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'stockpile': stockpile,
            'total'    : total
        })
    
    except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

# Get by Stockpile
def get_stockpile_hpal(request):
    offset = int(request.GET.get('offset', 0))  # Offset untuk pagination
    limit  = int(request.GET.get('limit', 10))  # Limit bar per halaman
   
    # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)
    if filter_year:
        params = [filter_year, filter_year, offset, limit]
    else:
        params = [None, None, offset, limit]

   # Query berdasarkan database
    if db_vendor == 'mysql':
    # Query untuk MySQL
        query = """
            SELECT 
                mine_sources_point_dumping.dumping_point, 
                COALESCE(ROUND(SUM(ore_productions.tonnage), 0), 0) AS tonnage
            FROM ore_productions
            LEFT JOIN materials ON ore_productions.id_material = materials.id
            LEFT JOIN mine_sources_point_dumping ON ore_productions.id_stockpile = mine_sources_point_dumping.id
            WHERE nama_material = 'LIM' 
                AND (%s IS NULL OR YEAR(tgl_production) = %s)
            GROUP BY mine_sources_point_dumping.dumping_point
            ORDER BY tonnage DESC
            LIMIT %s, %s;
        """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        query = """
            SELECT 
                mine_sources_point_dumping.dumping_point, 
                COALESCE(ROUND(SUM(ore_productions.tonnage), 0), 0) AS tonnage
            FROM ore_productions
            LEFT JOIN materials ON ore_productions.id_material = materials.id
            LEFT JOIN mine_sources_point_dumping ON ore_productions.id_stockpile = mine_sources_point_dumping.id
            WHERE nama_material = 'LIM'
                AND (%s IS NULL OR YEAR(tgl_production) = %s)
            GROUP BY mine_sources_point_dumping.dumping_point
            ORDER BY tonnage DESC
            OFFSET %s ROWS FETCH NEXT %s ROWS ONLY;
        """
    else:
        raise ValueError("Unsupported database vendor.")

    try:
        with connections['sqms_db'].cursor() as cursor:
            # cursor.execute(query, params * 2)  # Dua kali karena parameter digunakan dua kali dalam query
            cursor.execute(query, params)  # Parameter query
            data = cursor.fetchall()

        # Pisahkan data ke dalam list
        data_x = [entry[0] for entry in data],
        data_y = [entry[1] for entry in data]  # Ubah menjadi array satu dimensi

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'data_x': data_x,
            'data_y': data_y
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
def get_stockpile_rkef(request):
    offset = int(request.GET.get('offset', 0))  # Offset untuk pagination
    limit  = int(request.GET.get('limit', 10))  # Limit bar per halaman
    # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)
    if filter_year:
        params = [filter_year, filter_year, offset, limit]
    else:
        params = [None, None, offset, limit]
    # Query berdasarkan database
    if db_vendor == 'mysql':
    # Query untuk MySQL
        query = """
            SELECT 
                mine_sources_point_dumping.dumping_point, 
                COALESCE(ROUND(SUM(ore_productions.tonnage), 0), 0) AS tonnage
            FROM ore_productions
            LEFT JOIN materials ON ore_productions.id_material = materials.id
            LEFT JOIN mine_sources_point_dumping ON ore_productions.id_stockpile = mine_sources_point_dumping.id
            WHERE nama_material = 'SAP' 
                AND (%s IS NULL OR YEAR(tgl_production) = %s)
            GROUP BY mine_sources_point_dumping.dumping_point
            ORDER BY tonnage DESC
            LIMIT %s, %s;
        """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        query = """
            SELECT 
                mine_sources_point_dumping.dumping_point, 
                COALESCE(ROUND(SUM(ore_productions.tonnage), 0), 0) AS tonnage
            FROM ore_productions
            LEFT JOIN materials ON ore_productions.id_material = materials.id
            LEFT JOIN mine_sources_point_dumping ON ore_productions.id_stockpile = mine_sources_point_dumping.id
            WHERE nama_material = 'SAP'
                AND (%s IS NULL OR YEAR(tgl_production) = %s)
            GROUP BY mine_sources_point_dumping.dumping_point
            ORDER BY tonnage DESC
            OFFSET %s ROWS FETCH NEXT %s ROWS ONLY;
        """
    else:
        raise ValueError("Unsupported database vendor.")
    try:
        with connections['sqms_db'].cursor() as cursor:
            # cursor.execute(query, params * 2)  # Dua kali karena parameter digunakan dua kali dalam query
            cursor.execute(query, params)  # Parameter query
            data = cursor.fetchall()

        # Pisahkan data ke dalam list
        data_x = [entry[0] for entry in data],
        data_y = [entry[1] for entry in data]  # Ubah menjadi array satu dimensi

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'data_x': data_x,
            'data_y': data_y
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# Forecast production with prophet
# def forecast_production(request):
#     # Data historis
#     data = {
#         'week': ['2024-10-01', '2024-10-08', '2024-10-15', '2024-10-22', '2024-10-29'],
#         'production': [500, 600, 550, 700, 650]
#     }
 
#     # Membuat DataFrame
#     df = pd.DataFrame(data)
#     df['week'] = pd.to_datetime(df['week'])
#     df = df.rename(columns={'week': 'ds', 'production': 'y'})

#     # Model Prophet
#     model = Prophet()
#     model.fit(df)

#     # Prediksi untuk 1 minggu ke depan
#     future = model.make_future_dataframe(periods=1, freq='W')
#     forecast = model.predict(future)

#     # Pisahkan data aktual dan prediksi
#     actual = df[['ds', 'y']].rename(columns={'y': 'actual'})
#     forecast_data = forecast[['ds', 'yhat']].rename(columns={'yhat': 'forecast'})

#     # Gabungkan data historis dengan prediksi
#     merged_data = pd.merge(forecast_data, actual, on='ds', how='left')

#     # Siapkan data untuk frontend
#     chart_data = {
#         'dates' : merged_data['ds'].astype(str).tolist(),
#         'actual': merged_data['actual'].tolist(),  # Data historis (actual)
#         'forecast': merged_data['forecast'].tolist()  # Prediksi
#     }
#     return JsonResponse(chart_data)
#     # dates    = merged_data['ds'].astype(str).tolist(),
#     # actual   = merged_data['actual'].tolist(),  # Data historis (actual)
#     # forecast = merged_data['forecast'].tolist()  # Prediksi


#     # return JsonResponse({
#     #                 'dates'   : dates,
#     #                 'actual'  : actual,
#     #                 'forecast': forecast,
#     #         })

def forecast_production(request):
    query = """
            SELECT * FROM weekly_production_summary
        """
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query)  
            data = cursor.fetchall()

        # Konversi ke DataFrame
        df = pd.DataFrame(list(data), columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'])  # Pastikan kolom tanggal berbentuk datetime
        # Pastikan semua tanggal adalah Senin
        # df['ds'] = df['ds'] - pd.to_timedelta(df['ds'].dt.weekday, unit='d')  # Geser ke Senin

        # Ganti NaN dengan 0 pada kolom 'y'
        df['y'] = df['y'].fillna(0)

        # Model Prophet
        model = Prophet()
        model.fit(df)

        # Prediksi 1 minggu ke depan
        # future = model.make_future_dataframe(periods=1, freq='W') #parameter freq='W' yang secara default mengacu pada minggu
        # Prediksi 1 minggu ke depan, mulai dari Senin
        future = model.make_future_dataframe(periods=1, freq='W-MON')  # Mengatur minggu dimulai dari Senin

        forecast = model.predict(future)

        # Pastikan yhat_lower tidak bernilai negatif
        forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)

        # Gabungkan data actual dan forecast
        actual = df[['ds', 'y']].rename(columns={'y': 'actual'})  # Data historis

        forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(columns={'yhat': 'forecast'})

        # Replace NaN in both actual and forecast columns with None
        forecast_data = forecast_data.where(pd.notnull(forecast_data), None)
        actual = actual.where(pd.notnull(actual), None)

        # Gabungkan data actual dan forecast
        merged_data = pd.merge(forecast_data, actual, on='ds', how='left')

        # Debugging: Periksa isi merged_data dan kolom-kolomnya
        # print(merged_data.head())

        # Pastikan data aktual untuk setiap tanggal ada
        merged_data['actual'] = merged_data['actual'].fillna(0)  # Ganti NaN dengan 0

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'dates'     : merged_data['ds'].astype(str).tolist(),
            'actual'    : merged_data['actual'].tolist(),  # Aktifkan ini
            'forecast'  : merged_data['forecast'].tolist(),
            'yhat_lower': merged_data['yhat_lower'].tolist(),
            'yhat_upper': merged_data['yhat_upper'].tolist()
        })
       
    
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# YTD Samples Count
def get_sample_ytd(request):
   # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)
    # filter_year = 2023

    if filter_year:
        filter_sql = "WHERE type_sample IN('CKS','GCD','GCDQAQC','PDS','QAQC','SPC') AND YEAR (tgl_produksi) = %s"
        params = [filter_year]
    else:
        current_year =  datetime.now().year
        filter_sql = "WHERE type_sample IN('CKS','GCD','GCDQAQC','PDS','QAQC','SPC') AND YEAR (tgl_produksi) = %s"
        params = [current_year]

    query = """
        SELECT
            MONTH(tgl_produksi) AS bulan, 
            YEAR(tgl_produksi) AS tahun, 
            COALESCE(COUNT(sample_number), 0) AS total
        FROM laboratory_performance_tat
        {}
        GROUP BY MONTH(tgl_produksi), YEAR(tgl_produksi)
        ORDER BY MIN(tgl_produksi);      
    """.format(filter_sql)

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert numeric month to month label
        x_data = [get_month_label(entry[0]) for entry in chart_data]  # Convert month number to label
        y_data = [entry[2] for entry in chart_data]  # Total tonase material lim

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data': x_data,
            'y_data': y_data
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_sample_mtd(request):
    # Ambil filter dari request
    filter_year = request.GET.get('filter_year')
    filter_month = request.GET.get('filter_month')

    # Gunakan default jika filter tidak valid
    try:
        filter_year  = int(filter_year) if filter_year else datetime.now().year
        filter_month = int(filter_month) if filter_month else datetime.now().month
    except ValueError:
        filter_year  = datetime.now().year
        filter_month = datetime.now().month

    # SQL query dengan parameter
    filter_sql = """
        WHERE type_sample IN ('CKS', 'GCD', 'GCDQAQC', 'PDS', 'QAQC', 'SPC')
        AND YEAR(tgl_produksi) = %s
        AND MONTH(tgl_produksi) = %s
    """
    params = [filter_year, filter_month]

    # Query berdasarkan database
    if db_vendor == 'mysql':
    # Query untuk MySQL
        query = f"""
            SELECT
                YEAR(tgl_produksi) AS tahun,
                MONTH(tgl_produksi) AS bulan,
                WEEK(tgl_produksi, 1) AS minggu_ke, -- ISO Week
                COUNT(CASE WHEN sample_number IS NOT NULL THEN 1 END) AS total
            FROM laboratory_performance_tat
            {filter_sql}
            GROUP BY 
                YEAR(tgl_produksi),
                MONTH(tgl_produksi),
                WEEK(tgl_produksi, 1) -- ISO Week
            ORDER BY 
                minggu_ke;
        """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        query = f"""
                SELECT
                    YEAR(tgl_produksi) AS tahun,
                    MONTH(tgl_produksi) AS bulan,
                    DATEPART(ISOWK, tgl_produksi) AS minggu_ke,  -- Menggunakan ISO Week
                    COUNT(CASE WHEN sample_number IS NOT NULL THEN 1 END) AS total
                FROM laboratory_performance_tat
                {filter_sql}
                GROUP BY 
                    YEAR(tgl_produksi),
                    MONTH(tgl_produksi),
                    DATEPART(ISOWK, tgl_produksi)  -- Menggunakan ISO Week
                ORDER BY 
                    minggu_ke;
            """
    else:
        raise ValueError("Unsupported database vendor.")


    try:
        # Eksekusi query
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert numeric month to month label
        x_data = [f"Minggu {entry[2]}" for entry in chart_data]  # Minggu ke dalam bulan
        y_data = [entry[3] for entry in chart_data]  # Total sampel
        total_samples = sum(y_data)  # Hitung jumlah total sampel

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data': x_data,
            'y_data': y_data,
            'total' : total_samples 
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': 'Database error occurred'}, status=500)
    
def get_sample_this_week(request):
   # Query berdasarkan database
    if db_vendor == 'mysql':
    # Query untuk MySQL
        query = """
        SELECT 
                YEAR(tgl_produksi) AS tahun,
                MONTH(tgl_produksi) AS bulan,
                WEEK(tgl_produksi, 1) AS minggu_ke, -- Menggunakan ISO Week
                DAY(tgl_produksi) AS hari,
                COUNT(sample_number) AS total
            FROM 
                laboratory_performance_tat
            WHERE 
                type_sample IN ('CKS', 'GCD', 'GCDQAQC', 'PDS', 'QAQC', 'SPC')
                AND YEAR(tgl_produksi) = YEAR(CURDATE())
                AND MONTH(tgl_produksi) = MONTH(CURDATE())
                AND WEEK(tgl_produksi, 1) = WEEK(CURDATE(), 1) -- Membandingkan minggu ISO
            GROUP BY 
                YEAR(tgl_produksi),
                MONTH(tgl_produksi),
                WEEK(tgl_produksi, 1),
                DAY(tgl_produksi)
            ORDER BY 
                minggu_ke,
                hari;
        """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        query = """
                SELECT 
                    YEAR(tgl_produksi) AS tahun,
                    MONTH(tgl_produksi) AS bulan,
                    DATEDIFF(WEEK, DATEADD(DAY, 1 - DAY(tgl_produksi), tgl_produksi), tgl_produksi) + 1 AS minggu_ke,
                    DAY(tgl_produksi) AS hari,
                    COUNT(sample_number) AS total
                FROM 
                    laboratory_performance_tat
                WHERE 
                    type_sample IN ('CKS', 'GCD', 'GCDQAQC', 'PDS', 'QAQC', 'SPC')
                    AND YEAR(tgl_produksi) = YEAR(GETDATE())
                    AND MONTH(tgl_produksi) = MONTH(GETDATE())
                    AND DATEDIFF(WEEK, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()), GETDATE()) + 1 =
                        DATEDIFF(WEEK, DATEADD(DAY, 1 - DAY(tgl_produksi), tgl_produksi), tgl_produksi) + 1
                GROUP BY 
                    YEAR(tgl_produksi),
                    MONTH(tgl_produksi),
                    DATEDIFF(WEEK, DATEADD(DAY, 1 - DAY(tgl_produksi), tgl_produksi), tgl_produksi) + 1,
                    DAY(tgl_produksi)
                ORDER BY 
                    minggu_ke,
                    hari;
            """
    else:
        raise ValueError("Unsupported database vendor.")

    try:
        # Eksekusi query
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query)
            chart_data = cursor.fetchall()

        # Convert numeric month to month label
        x_data = [f"Days {entry[3]}" for entry in chart_data] 
        y_data = [entry[4] for entry in chart_data]  # Total sampel
        total_samples = sum(y_data)  # Hitung jumlah total sampel

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data': x_data,
            'y_data': y_data,
            'total' : total_samples 
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': 'Database error occurred'}, status=500)
    
def get_sample_this_days(request):
    # Contoh date_filter yang diterima
    date_filter = 'today'  # Default nilai awal
    query = None

    if db_vendor.lower() == 'mysql':
        if date_filter == 'today':
            query_today = """
                SELECT 
                    DAY(tgl_produksi) AS hari,
                    COUNT(sample_number) AS total
                FROM 
                    laboratory_performance_tat
                WHERE 
                    type_sample IN ('CKS', 'GCD', 'GCDQAQC', 'PDS', 'QAQC', 'SPC')
                    AND DATE(tgl_produksi) = CURDATE()
                GROUP BY 
                    DAY(tgl_produksi)
                ORDER BY 
                    hari;
            """
            query_yesterday = """
                SELECT 
                    DAY(tgl_produksi) AS hari,
                    COUNT(sample_number) AS total
                FROM 
                    laboratory_performance_tat
                WHERE 
                    type_sample IN ('CKS', 'GCD', 'GCDQAQC', 'PDS', 'QAQC', 'SPC')
                    AND DATE(tgl_produksi) = CURDATE() - INTERVAL 1 DAY
                GROUP BY 
                    DAY(tgl_produksi)
                ORDER BY 
                    hari;
            """
        else:
            raise ValueError("Unsupported date filter. Use 'today'.")
    elif db_vendor.lower() in ['mssql', 'microsoft']:
        if date_filter == 'today':
            query_today = """
                SELECT 
                    DAY(tgl_produksi) AS hari,
                    COUNT(sample_number) AS total
                FROM 
                    laboratory_performance_tat
                WHERE 
                    type_sample IN ('CKS', 'GCD', 'GCDQAQC', 'PDS', 'QAQC', 'SPC')
                    AND CONVERT(DATE, tgl_produksi) = CONVERT(DATE, GETDATE())
                GROUP BY 
                    DAY(tgl_produksi)
                ORDER BY 
                    hari;
            """
            query_yesterday = """
                SELECT 
                    DAY(tgl_produksi) AS hari,
                    COUNT(sample_number) AS total
                FROM 
                    laboratory_performance_tat
                WHERE 
                    type_sample IN ('CKS', 'GCD', 'GCDQAQC', 'PDS', 'QAQC', 'SPC')
                    AND CONVERT(DATE, tgl_produksi) = CONVERT(DATE, DATEADD(DAY, -1, GETDATE()))
                GROUP BY 
                    DAY(tgl_produksi)
                ORDER BY 
                    hari;
            """
        else:
            raise ValueError("Unsupported date filter. Use 'today'.")

    else:
        raise ValueError("Unsupported database vendor. Use 'mysql' or 'mssql'.")

    # Eksekusi query untuk today, jika tidak ada data, fallback ke yesterday
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query_today)
            chart_data = cursor.fetchall()

            # Jika tidak ada data untuk today, ambil data yesterday
            if not chart_data:  # Cek jika hasil query kosong
                cursor.execute(query_yesterday)
                chart_data = cursor.fetchall()

        # Format data untuk JSON response
        x_data = [f"Day {entry[0]}" for entry in chart_data]
        y_data = [entry[1] for entry in chart_data]

        return JsonResponse({
            'x_data': x_data,
            'y_data': y_data
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': 'Database error occurred'}, status=500)






