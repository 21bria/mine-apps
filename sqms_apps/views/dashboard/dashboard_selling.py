# views.py
import logging
from django.http import JsonResponse
from django.db import connections, DatabaseError
from django.contrib.auth.decorators import login_required
import pandas as pd
from datetime import datetime, timedelta
import itertools
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database
from ...utils.db_utils import get_db_vendor

 # Memanggil fungsi utility
db_vendor = get_db_vendor('sqms_db')

def get_month_label(month_number):
    month_labels = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    return month_labels.get(month_number, '')

#Project to Date Sellings
def get_sale_ptd(request):
    query = """
       SELECT
            COALESCE(ROUND(SUM(tonnage), 0), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END), 0), 0) AS total_hpal,
            COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END), 0), 0) AS total_rkef
        FROM details_selling
    """
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

        total_sale = [entry[0] for entry in data]   
        data_hpal  = [entry[1] for entry in data] 
        data_rkef  = [entry[2] for entry in data] 
        

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'data_hpal' : data_hpal,
            'data_rkef' : data_rkef,
            'total_sale': total_sale
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

# YTD Ore Productions
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
        # x_data              = [entry[0] for entry in chart_data]  # Label bulan
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

#YTD Ore Sale 
def get_chart_sale_ytd(request):
 # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)
    # filter_year = 2023

    if filter_year:
        filter_sql = "WHERE YEAR(date_wb) = %s"
        params = [filter_year]
    else:
        current_year =  datetime.now().year
        filter_sql = "WHERE YEAR(date_wb) = %s"
        params = [current_year]

    query = """
        SELECT
            MONTH(date_wb) AS bulan,
            YEAR(date_wb) AS tahun,
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END), 2), 0) AS total_hpal,
            COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END), 2), 0) AS total_rkef
        FROM details_selling
        {}
        GROUP BY MONTH(date_wb), YEAR(date_wb)
        ORDER BY MIN(date_wb);
    """.format(filter_sql)
    
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Pisahkan data ke dalam tiga list
        # x_data      = [entry[0] for entry in chart_data]  # Label bulan
        x_data = [get_month_label(entry[0]) for entry in chart_data]  # Convert month number to label
        y_data_hpal = [entry[3] for entry in chart_data]  # Total tonase material lim
        y_data_rkef = [entry[4] for entry in chart_data]  # Total tonase material sap

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data'     : x_data,
            'y_data_hpal': y_data_hpal,
            'y_data_rkef': y_data_rkef
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_pie_sale_ytd(request):
 # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)

    if filter_year:
        filter_sql = "WHERE YEAR(date_wb) = %s"
        params = [filter_year]
    else:
        current_year =  datetime.now().year
        filter_sql = "WHERE YEAR(date_wb) = %s"
        params = [current_year]

    query = """
        SELECT
           COALESCE(ROUND(SUM(tonnage), 1),0) AS total,        
           factory_stock
        FROM details_selling
        {}
        GROUP BY factory_stock;
    """.format(filter_sql)

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Pisahkan data ke dalam tiga list
        x_data  = [entry[0] for entry in chart_data] 
        y_data  = [entry[1] for entry in chart_data] 

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data': x_data,
            'y_data': y_data
        }) 
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_ytd_sale(request):
 # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)

    if filter_year:
        filter_sql = "WHERE YEAR(date_wb) = %s"
        params = [filter_year]
    else:
        current_year = datetime.now().year
        filter_sql = "WHERE YEAR(date_wb) = %s"
        params = [current_year]
    query = """
        SELECT
            COALESCE(SUM(tonnage), 1) AS total,
            COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END), 1), 0) AS total_hpal,
            COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END), 1), 0) AS total_rkef
        FROM details_selling
        {}
    """.format(filter_sql)

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam  list: 
        x_data    = [entry[0] for entry in data]  
        total_hpal = [entry[1] for entry in data] 
        total_rkef = [entry[2] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data'    : x_data,
            'total_hpal': total_hpal,
            'total_rkef': total_rkef
        })
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

# Grade YTD
def getGradeHpalbyYtd(request):
    material = request.GET.get('material', 'LIM')  # Default ke 'LIM' jika tidak ada parameter
    filter_year = request.GET.get('filter_year', None)

    # Tentukan tahun berdasarkan parameter atau gunakan tahun berjalan
    if filter_year:
        params_year = [filter_year]
    else:
        current_year = datetime.now().year
        params_year = [current_year]

    query = """
        SELECT  
            MONTH(t1.date_wb) AS bulan,
            ROUND(SUM(t1.netto_ton), 2) AS total_selling,
            COALESCE(SUM(t1.netto_ton * t1.ni) / 
                NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0), 
                0) AS ni,
            COALESCE(SUM(t1.netto_ton * t2.Ni) / 
                NULLIF(SUM(CASE WHEN t2.Ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0), 
                0) AS ni_pds,
            COALESCE(SUM(t1.netto_ton * t3.ni) / 
                NULLIF(SUM(CASE WHEN t3.ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0), 
                0) AS ni_coa
        FROM details_selling_awk AS t1
        LEFT JOIN inventory_by_dome AS t2 ON t2.pile_id = t1.sampling_point
        LEFT JOIN selling_official_surveyor_awk AS t3 ON t3.product_code = t1.delivery_order
        WHERE t1.nama_material = %s AND YEAR(t1.date_wb) = %s
        GROUP BY MONTH(t1.date_wb)
        ORDER BY MONTH(t1.date_wb) ASC
    """
    
    try:
        # Eksekusi query
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, [material] + params_year)
            chart_data = cursor.fetchall()

        # Proses hasil query menjadi JSON
        # bulan         = [entry[0] for entry in chart_data]
        bulan         = [get_month_label(entry[0]) for entry in chart_data]  
        total_selling = [entry[1] for entry in chart_data]
        ni            = [entry[2] for entry in chart_data]
        ni_pds        = [entry[3] for entry in chart_data]
        ni_coa        = [entry[4] for entry in chart_data]

        # Hitung akumulasi
        running_total = 0
        running_ni = 0
        running_ni_pds = 0
        running_ni_coa = 0

        total_plus = []
        ni_sum = []
        ni_pds_sum = []
        ni_coa_sum = []

        for i in range(len(total_selling)):
            running_total += total_selling[i]
            total_plus.append(running_total)

            # Akumulasi rata-rata tertimbang
            running_ni      = (running_ni * (running_total - total_selling[i]) + total_selling[i] * ni[i]) / running_total
            running_ni_pds  = (running_ni_pds * (running_total - total_selling[i]) + total_selling[i] * ni_pds[i]) / running_total
            running_ni_coa  = (running_ni_coa * (running_total - total_selling[i]) + total_selling[i] * ni_coa[i]) / running_total

            ni_sum.append(round(running_ni, 2))
            ni_pds_sum.append(round(running_ni_pds, 2))
            ni_coa_sum.append(round(running_ni_coa, 2))

        # Kirim data JSON
        return JsonResponse({
            'bulan': bulan,
            'total'      : total_selling,
            'total_plus' : total_plus,
            'ni_sum'     : ni_sum,
            'ni_pds_sum' : ni_pds_sum,
            'ni_coa_sum' : ni_coa_sum
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': 'Database error occurred'}, status=500)
    
def getGradeRkefbyYtd(request):
    material    = request.GET.get('material', 'SAP')  # Default ke 'LIM' jika tidak ada parameter
    filter_year = request.GET.get('filter_year', None)

    # Tentukan tahun berdasarkan parameter atau gunakan tahun berjalan
    if filter_year:
        params_year = [filter_year]
    else:
        current_year = datetime.now().year
        params_year = [current_year]


    query = """
        SELECT  
            MONTH(t1.date_wb) AS bulan,
            ROUND(SUM(t1.netto_ton), 2) AS total_selling,
            COALESCE(SUM(t1.netto_ton * t1.ni) / 
                NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0), 
                0) AS ni,
            COALESCE(SUM(t1.netto_ton * t2.Ni) / 
                NULLIF(SUM(CASE WHEN t2.Ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0), 
                0) AS ni_pds,
            COALESCE(SUM(t1.netto_ton * t3.ni) / 
                NULLIF(SUM(CASE WHEN t3.ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0), 
                0) AS ni_coa
        FROM details_selling_awk AS t1
        LEFT JOIN inventory_by_dome AS t2 ON t2.pile_id = t1.sampling_point
        LEFT JOIN selling_official_surveyor_awk AS t3 ON t3.product_code = t1.delivery_order
        WHERE t1.nama_material = %s AND YEAR(t1.date_wb) = %s
        GROUP BY MONTH(t1.date_wb)
        ORDER BY MONTH(t1.date_wb) ASC
    """
    
    try:
        # Eksekusi query
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, [material] + params_year)
            chart_data = cursor.fetchall()

        # Proses hasil query menjadi JSON
        # bulan         = [entry[0] for entry in chart_data]
        bulan         = [get_month_label(entry[0]) for entry in chart_data]  
        total_selling = [entry[1] for entry in chart_data]
        ni            = [entry[2] for entry in chart_data]
        ni_pds        = [entry[3] for entry in chart_data]
        ni_coa        = [entry[4] for entry in chart_data]

        # Hitung akumulasi
        running_total = 0
        running_ni = 0
        running_ni_pds = 0
        running_ni_coa = 0

        total_plus = []
        ni_sum = []
        ni_pds_sum = []
        ni_coa_sum = []

        for i in range(len(total_selling)):
            running_total += total_selling[i]
            total_plus.append(running_total)

            # Akumulasi rata-rata tertimbang
            running_ni      = (running_ni * (running_total - total_selling[i]) + total_selling[i] * ni[i]) / running_total
            running_ni_pds  = (running_ni_pds * (running_total - total_selling[i]) + total_selling[i] * ni_pds[i]) / running_total
            running_ni_coa  = (running_ni_coa * (running_total - total_selling[i]) + total_selling[i] * ni_coa[i]) / running_total

            ni_sum.append(round(running_ni, 2))
            ni_pds_sum.append(round(running_ni_pds, 2))
            ni_coa_sum.append(round(running_ni_coa, 2))

        # Kirim data JSON
        return JsonResponse({
            'bulan': bulan,
            'total'      : total_selling,
            'total_plus' : total_plus,
            'ni_sum'     : ni_sum,
            'ni_pds_sum' : ni_pds_sum,
            'ni_coa_sum' : ni_coa_sum
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': 'Database error occurred'}, status=500)
    
def getTypeSellingYtd(request):
    # Mendapatkan parameter filter_year dan filter_material
    material = request.GET.get('filter_material', None)
    filter_year = request.GET.get('filter_year', None)

    # Tentukan tahun berdasarkan parameter atau gunakan tahun berjalan
    if filter_year:
        try:
            # Pastikan filter_year berupa integer
            params_year = [int(filter_year)]  # convert filter_year ke integer
        except ValueError:
            # Jika filter_year tidak bisa di-convert jadi integer, defaultkan ke tahun berjalan
            params_year = [datetime.now().year]
    else:
        current_year = datetime.now().year
        params_year = [current_year]

    # SQL dinamis berdasarkan keberadaan parameter material
    query = """
        SELECT  
            MONTH(date_wb) bulan,
            ROUND(SUM(netto_ton),2) AS total_selling,
            COALESCE(SUM(CASE WHEN type_selling = 'DAP' THEN netto_ton ELSE 0 END), 0) AS DAP,
            COALESCE(SUM(CASE WHEN type_selling = 'EXW' THEN netto_ton ELSE 0 END), 0) AS Exwork
        FROM details_selling
        WHERE YEAR(date_wb) = %s
    """
    params = params_year  # Set params dengan tahun yang sudah terkonversi

    # Tambahkan filter material jika ada
    if material:
        query += " AND nama_material = %s"
        params.append(material)  # Tambahkan material sebagai parameter query

    query += """
        GROUP BY MONTH(date_wb)
        ORDER BY MONTH(date_wb) ASC
    """

    try:
        # Eksekusi query
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Proses hasil query menjadi JSON
        bulan          = [get_month_label(entry[0]) for entry in chart_data]  
        total_selling  = [entry[1] for entry in chart_data]
        Dap_sel        = [entry[2] for entry in chart_data]
        Exwork         = [entry[3] for entry in chart_data]

        # Hitung sum total untuk DAP dan Exwork
        total_DAP  = sum(Dap_sel)
        total_Exwork = sum(Exwork)

        # Kirim data JSON
        return JsonResponse({
            'bulan'       : bulan,
            'total'       : total_selling,
            'DAP'         : Dap_sel,
            'Exwork'      : Exwork,
            'total_DAP'   : round(total_DAP, 2),
            'total_Exwork': round(total_Exwork, 2)
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': 'Database error occurred'}, status=500)


# MTD - Ore Sale
def get_daily_sale_discharge(request):
 # Ambil data dari database menggunakan cursor SQL
    filter_year   = request.GET.get('filter_year')
    filter_month  = request.GET.get('filter_month')
    # Ambil bulan dan tahun saat ini jika filter bulan tidak disediakan
    current_month = datetime.now().month
    current_year  = datetime.now().year

    # create klausa WHERE sesuai dengan filter yang diberikan
    filter_sql = "WHERE 1=1"  # Klausa awal
    params = []

    if filter_year:
        filter_sql += " AND YEAR(date_wb) = %s"
        params.append(filter_year)
    else:
        filter_sql += " AND YEAR(date_wb) = %s"
        params.append(current_year)

    if filter_month:
        filter_sql += " AND MONTH(date_wb) = %s"
        params.append(filter_month)
    else:
        filter_sql += " AND MONTH(date_wb) = %s"
        params.append(current_month)
    # Query SQL
    query = """
        SELECT
           COALESCE(ROUND(SUM(tonnage), 1),0) AS total,        
           factory_stock
        FROM details_selling
        {}
        GROUP BY factory_stock;
    """.format(filter_sql)

    # Eksekusi query dengan parameter yang diberikan
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        chart_data = cursor.fetchall()

    # Pisahkan data ke dalam tiga list
    x_data  = [entry[0] for entry in chart_data] 
    y_data  = [entry[1] for entry in chart_data] 

    # Kirim data JSON ke template menggunakan JsonResponse
    return JsonResponse({
        'x_data': x_data,
        'y_data': y_data
    }) 

def get_chart_sale_daily(request):
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
    # hari_ini     = datetime.now().date()
    tgl_pertama  = hari_ini.replace(day=1)
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
                    ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN netto_weigth_f ELSE 0 END), 2)/1000 AS total_lim,
                    ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN netto_weigth_f ELSE 0 END), 2)/1000 AS total_sap,
                    SUM(netto_weigth_f)/1000 AS total_ore
                FROM
                    ore_sellings
                WHERE
                    date_wb BETWEEN %s AND %s
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

        # Loop Data
        x_data     = [entry[0] for entry in chart_data]  
        y_data_lim = [entry[1] for entry in chart_data]  
        y_data_sap = [entry[2] for entry in chart_data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data'    : x_data,
            'y_data_lim': y_data_lim,
            'y_data_sap': y_data_sap
        })
    except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_chart_sale_time(request):
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
    
    tgl_sale = tanggal

    query = """
              SELECT
                tanggal_jam.left_time,
                COALESCE(tonnage, 0) AS total
            FROM
                tanggal_jam
            LEFT JOIN (
                SELECT
                    gwt,
                    ROUND(SUM(tonnage), 2) AS tonnage
                FROM
                    sale_hpal_time
                WHERE
                    date_gwt = %s
                GROUP BY
                    gwt
            ) AS subquery ON tanggal_jam.left_time = subquery.gwt
            Order By tanggal_jam.id ASC;
        """

    params.extend([tgl_sale])

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Loop Data
        x_data  = [entry[0] for entry in chart_data]  
        y_data  = [entry[1] for entry in chart_data]  

        # Akumulasi data y_data
        # accumulated_data = list(itertools.accumulate(y_data))
        # Akumulasi data y_data dan bulatkan hasilnya
        accumulated_data = [round(total, 2) for total in itertools.accumulate(y_data)]

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data'       : x_data,
            'y_data'       : y_data,
            'accumulated'  : accumulated_data
        })
    except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_mtd_sale(request):

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
        filter_sql += " AND YEAR(date_wb) = %s"
        params.append(filter_year)
    else:
        filter_sql += " AND YEAR(date_wb) = %s"
        params.append(current_year)

    if filter_month:
        filter_sql += " AND MONTH(date_wb) = %s"
        params.append(filter_month)
    else:
        filter_sql += " AND MONTH(date_wb) = %s"
        params.append(current_month)
    # Query SQL
    query = """
         SELECT
                SUM(netto_weigth_f)/1000 AS total,
                ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN netto_weigth_f ELSE 0 END), 2)/1000 AS total_hpal,
                ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN netto_weigth_f ELSE 0 END), 2)/1000 AS total_rkef
        FROM ore_sellings
        {}
    """.format(filter_sql)
    try:
        # Eksekusi query dengan parameter yang diberikan
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

    # Pisahkan data ke dalam  list: 
        x_data     = [entry[0] for entry in data]  
        total_hpal = [entry[1] for entry in data] 
        total_rkef = [entry[2] for entry in data]  

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data'    : x_data,
            'total_hpal': total_hpal,
            'total_rkef': total_rkef
        })
    except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

# This week summary
def getTotalbyWeekSelling(request):
    # Query berdasarkan database
    if db_vendor == 'mysql':
         query = """
            SELECT
                    YEAR(date_wb) AS tahun,
                    MONTH(date_wb) AS bulan,
                    WEEK(date_wb, 1) AS minggu_ke, -- Menggunakan mode ISO untuk minggu
                    COALESCE(SUM(tonnage), 0) AS total,
                    COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END), 2), 0) AS total_hpal,
                    COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END), 2), 0) AS total_rkef
                FROM details_selling
                WHERE WEEK(date_wb, 1) = WEEK(CURDATE(), 1) -- Filter untuk minggu saat ini
                AND YEAR(date_wb) = YEAR(CURDATE()) -- Filter untuk tahun saat ini
                GROUP BY YEAR(date_wb), MONTH(date_wb), WEEK(date_wb, 1)
                ORDER BY MIN(date_wb);
            """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        query = """
            SELECT
                YEAR(date_wb) AS tahun,
                MONTH(date_wb) AS bulan,
                DATEPART(WEEK, date_wb) AS minggu_ke,
                COALESCE(SUM(tonnage), 0) AS total,
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END), 2), 0) AS total_hpal,
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END), 2), 0) AS total_rkef
            FROM details_selling
            WHERE DATEPART(WEEK, date_wb) = DATEPART(WEEK, GETDATE())
            AND YEAR(date_wb) = YEAR(GETDATE())
            GROUP BY MONTH(date_wb), YEAR(date_wb), DATEPART(WEEK, date_wb)
            ORDER BY MIN(date_wb);
        """
    else:
        raise ValueError("Unsupported database vendor.")
  
    try:
        # Eksekusi query
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query)
            chart_data = cursor.fetchall()

        # Convert numeric month to month label
        minggu_ke  = [entry[2] for entry in chart_data]  
        total_hpal = [entry[4] for entry in chart_data]
        total_rkef = [entry[5] for entry in chart_data]
        

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'total_hpal' : total_hpal,
            'total_rkef' : total_rkef,
            'y_minggu'   : minggu_ke 
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': 'Database error occurred'}, status=500)

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

def getTotalSaleByYear(request):
    query = """
        SELECT
            DATE_FORMAT(date_wb, '%Y') AS tahun,
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END), 2), 0) AS total_hpal,
            COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END), 2), 0) AS total_rkef
        FROM details_selling
        WHERE tonnage >0
        GROUP BY YEAR(date_wb)
        ORDER BY MIN(date_wb);
  """
    
    logger.info("Using database connection: sqms_db")
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

@login_required
def gradeByDaysHpal(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
     # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks = request.GET.get('filter_days') 
    # tanggal_teks = '2024-07-01' 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        # Jika tidak ada tanggal yang diberikan, gunakan tanggal hari ini
        tanggal = datetime.now().date()
    
    hari_ini     = tanggal
    # hari_ini     = datetime.now().date()
    tgl_pertama  = hari_ini.replace(day=1)
    tgl_terakhir = (hari_ini.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    last_day     = tgl_terakhir.day

    query = """
                SELECT 
                    tanggal.left_date,
                    COALESCE(tonnage, 0) AS total_ore,
                    COALESCE(tonnage_plup, 0) AS total_pulp,
					COALESCE(tonnage_official, 0) AS total_official,
                    COALESCE(ni, 0) AS ni_internal,
                    COALESCE(ni_pulp, 0) AS pulp_anindya,
					COALESCE(ni_official,0) AS ni_official
                FROM tanggal   
                LEFT JOIN (
                            SELECT 
                                left_date
                                ,SUM(tonnage) AS tonnage
                                ,COALESCE(SUM(tonnage * ni) / NULLIF(SUM(CASE  WHEN  ni IS NOT NULL THEN tonnage ELSE 0  END ), 0),  0) AS ni
                            FROM split_sample_awk_hpal
                            WHERE date_wb BETWEEN %s AND  %s 
                                GROUP BY left_date) AS t1 on tanggal.left_date = t1.left_date
                LEFT JOIN (
                            SELECT 
                                left_date
                                ,SUM(split_pulp_awk_hpal.tonnage) AS tonnage_plup
                                ,COALESCE(SUM(split_pulp_awk_hpal.tonnage * split_pulp_awk_hpal.ni) / NULLIF(SUM(CASE  WHEN  split_pulp_awk_hpal.ni IS NOT NULL THEN split_pulp_awk_hpal.tonnage ELSE 0  END ), 0),  0) AS ni_pulp,
								COALESCE(SUM(DISTINCT selling_official_surveyor_awk.tonnage), 0) AS tonnage_official,
								COALESCE(SUM(DISTINCT selling_official_surveyor_awk.tonnage * selling_official_surveyor_awk.ni) / 
								NULLIF(SUM(DISTINCT CASE WHEN  selling_official_surveyor_awk.ni IS NOT NULL THEN selling_official_surveyor_awk.tonnage ELSE 0  END ), 0),  0) AS ni_official
                            FROM split_pulp_awk_hpal
							LEFT JOIN selling_official_surveyor_awk ON split_pulp_awk_hpal.delivery_order = selling_official_surveyor_awk.product_code
                            WHERE date_wb BETWEEN %s AND  %s
                            GROUP BY left_date) AS t2 on tanggal.left_date= t2.left_date
                WHERE 
                        tanggal.left_date <= %s
                ORDER By 
                        tanggal.left_date asc
        """

    params = [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir, last_day]

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['left_date', 'total_ore', 'total_pulp','total_official', 'ni_internal', 'pulp_anindya','ni_official'])

        # Extract data dari DataFrame
        left_date      = df['left_date'].tolist()  
        total_ore      = df['total_ore'].tolist()  
        total_pulp     = df['total_pulp'].tolist()  
        total_official = df['total_official'].tolist()  
        ni_internal    = df['ni_internal'].tolist()  
        pulp_anindya   = df['pulp_anindya'].tolist()  
        ni_official    = df['ni_official'].tolist()  

      
        # Kirim data JSON ke template menggunakan JsonResponse
        response_data = {
            'left_date'     : left_date,
            'total_ore'     : total_ore,
            'total_pulp'    : total_pulp,
            'total_official': total_official,
            'ni_internal'   : ni_internal,
            'pulp_anindya'  : pulp_anindya,
            'ni_official'   : ni_official

        }

        return JsonResponse(response_data)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

@login_required   
def gradeByDaysRkef(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
     # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks = request.GET.get('filter_days') 
    # tanggal_teks = '2024-07-01' 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        # Jika tidak ada tanggal yang diberikan, gunakan tanggal hari ini
        tanggal = datetime.now().date()
    
    hari_ini     = tanggal
    # hari_ini     = datetime.now().date()
    tgl_pertama  = hari_ini.replace(day=1)
    tgl_terakhir = (hari_ini.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    last_day     = tgl_terakhir.day

    query = """
                  SELECT 
                    tanggal.left_date,
                    COALESCE(tonnage, 0) AS total_ore,
                    COALESCE(tonnage_plup, 0) AS total_pulp,
					COALESCE(tonnage_official, 0) AS total_official,
                    COALESCE(ni, 0) AS ni_internal,
                    COALESCE(ni_pulp, 0) AS pulp_anindya,
					COALESCE(ni_official,0) AS ni_official
                FROM tanggal   
                LEFT JOIN (
                            SELECT 
                                left_date
                                ,SUM(tonnage) AS tonnage
                                ,COALESCE(SUM(tonnage * ni) / NULLIF(SUM(CASE  WHEN  ni IS NOT NULL THEN tonnage ELSE 0  END ), 0),  0) AS ni
                            FROM split_sample_awk_rkef
                            WHERE date_wb BETWEEN %s AND  %s
                                GROUP BY left_date) AS t1 on tanggal.left_date = t1.left_date
                LEFT JOIN (
                            SELECT 
                                left_date
                                ,SUM(split_pulp_awk_rkef.tonnage) AS tonnage_plup
                                ,COALESCE(SUM(split_pulp_awk_rkef.tonnage * split_pulp_awk_rkef.ni) / NULLIF(SUM(CASE  WHEN  split_pulp_awk_rkef.ni IS NOT NULL THEN split_pulp_awk_rkef.tonnage ELSE 0  END ), 0),  0) AS ni_pulp,
								COALESCE(SUM(DISTINCT selling_official_surveyor_awk.tonnage), 0) AS tonnage_official,
								COALESCE(SUM(DISTINCT selling_official_surveyor_awk.tonnage * selling_official_surveyor_awk.ni) / 
								NULLIF(SUM(DISTINCT CASE WHEN  selling_official_surveyor_awk.ni IS NOT NULL THEN selling_official_surveyor_awk.tonnage ELSE 0  END ), 0),  0) AS ni_official
                            FROM split_pulp_awk_rkef
							LEFT JOIN selling_official_surveyor_awk ON split_pulp_awk_rkef.delivery_order = selling_official_surveyor_awk.product_code
                            WHERE date_wb BETWEEN %s AND  %s
                            GROUP BY left_date) AS t2 on tanggal.left_date= t2.left_date
                WHERE 
                        tanggal.left_date <= %s
                ORDER By 
                        tanggal.left_date asc
        """

    params = [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir, last_day]

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['left_date', 'total_ore', 'total_pulp','total_official', 'ni_internal', 'pulp_anindya','ni_official'])

        # Extract data dari DataFrame
        left_date      = df['left_date'].tolist()  
        total_ore      = df['total_ore'].tolist()  
        total_pulp     = df['total_pulp'].tolist()  
        total_official = df['total_official'].tolist()  
        ni_internal    = df['ni_internal'].tolist()  
        pulp_anindya   = df['pulp_anindya'].tolist()  
        ni_official    = df['ni_official'].tolist()  

      
        # Kirim data JSON ke template menggunakan JsonResponse
        response_data = {
            'left_date'     : left_date,
            'total_ore'     : total_ore,
            'total_pulp'    : total_pulp,
            'total_official': total_official,
            'ni_internal'   : ni_internal,
            'pulp_anindya'  : pulp_anindya,
            'ni_official'   : ni_official

        }

        return JsonResponse(response_data)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)
    
    # Get Samples Selling Count

@login_required 
def get_sample_selling_ytd(request):
   # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)
    # filter_year = 2023

    if filter_year:
        filter_sql = "WHERE type_sample IN('HOS','ROS','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC') AND YEAR (tgl_produksi) = %s"
        params = [filter_year]
    else:
        current_year =  datetime.now().year
        filter_sql = "WHERE type_sample IN('HOS','ROS','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC') AND YEAR (tgl_produksi) = %s"
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

@login_required 
def get_sample_selling_mtd(request):
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
        WHERE type_sample IN ('HOS','ROS','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC')
        AND YEAR(tgl_produksi) = %s
        AND MONTH(tgl_produksi) = %s
    """
    params = [filter_year, filter_month]

    # Query berdasarkan database
    if db_vendor == 'mysql':
        query = f"""
            SELECT
                YEAR(tgl_produksi) AS tahun,
                MONTH(tgl_produksi) AS bulan,
                WEEK(tgl_produksi, 1) AS minggu_ke, -- Menggunakan ISO Week
                COUNT(CASE WHEN sample_number IS NOT NULL THEN 1 END) AS total
            FROM laboratory_performance_tat
            {filter_sql}
            GROUP BY 
                YEAR(tgl_produksi),
                MONTH(tgl_produksi),
                WEEK(tgl_produksi, 1)  -- Menggunakan ISO Week
            ORDER BY 
                minggu_ke;
        """
    elif db_vendor in ['mssql', 'microsoft']:
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

@login_required    
def get_sample_selling_this_week(request):
    # Query berdasarkan database
    if db_vendor == 'mysql':
        query = """
            SELECT 
                    YEAR(tgl_produksi) AS tahun,
                    MONTH(tgl_produksi) AS bulan,
                    WEEK(tgl_produksi, 1) AS minggu_ke,  -- Menggunakan ISO Week
                    DAY(tgl_produksi) AS hari,
                    COUNT(sample_number) AS total
                FROM 
                    laboratory_performance_tat
                WHERE 
                    type_sample IN ('HOS','ROS','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC')
                    AND YEAR(tgl_produksi) = YEAR(CURDATE())
                    AND MONTH(tgl_produksi) = MONTH(CURDATE())
                    AND WEEK(tgl_produksi, 1) = WEEK(CURDATE(), 1)  -- Menggunakan ISO Week
                GROUP BY 
                    YEAR(tgl_produksi),
                    MONTH(tgl_produksi),
                    WEEK(tgl_produksi, 1),  -- Menggunakan ISO Week
                    DAY(tgl_produksi)
                ORDER BY 
                    minggu_ke,
                    hari;
            """
    elif db_vendor in ['mssql', 'microsoft']:
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
                type_sample IN ('HOS','ROS','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC')
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
    
def get_sample_selling_this_days(request):
   

    # Query berdasarkan database
    if db_vendor == 'mysql':
        # Query untuk mengambil data hari ini
        query_today = """
            SELECT 
                DAY(tgl_produksi) AS hari,
                COUNT(sample_number) AS total
            FROM 
                laboratory_performance_tat
            WHERE 
                type_sample IN ('HOS','ROS','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC')
                -- AND CONVERT(DATE, tgl_produksi) = CONVERT(DATE, GETDATE())  -- Filter untuk hari ini MsSQL
                AND DATE(tgl_produksi) = CURDATE()  -- Filter untuk hari ini
            GROUP BY 
                DAY(tgl_produksi)
            ORDER BY 
                hari;
        """

        # Query untuk mengambil data hari sebelumnya
        query_yesterday = """
            SELECT 
                DAY(tgl_produksi) AS hari,
                COUNT(sample_number) AS total
            FROM 
                laboratory_performance_tat
            WHERE 
                type_sample IN ('HOS','ROS','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC')
                -- AND CONVERT(DATE, tgl_produksi) = CONVERT(DATE, DATEADD(DAY, -1, GETDATE()))  -- Filter untuk hari sebelumnya MsSQL
                AND DATE(tgl_produksi) = CURDATE() - INTERVAL 1 DAY  -- Filter untuk hari sebelumnya
            GROUP BY 
                DAY(tgl_produksi)
            ORDER BY 
                hari;
        """

    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk mengambil data hari ini
        query_today = """
            SELECT 
                DAY(tgl_produksi) AS hari,
                COUNT(sample_number) AS total
            FROM 
                laboratory_performance_tat
            WHERE 
                type_sample IN ('HOS','ROS','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC')
                AND CONVERT(DATE, tgl_produksi) = CONVERT(DATE, GETDATE())  -- Filter untuk hari ini MsSQL
            GROUP BY 
                DAY(tgl_produksi)
            ORDER BY 
                hari;
        """
        # Query untuk mengambil data hari sebelumnya
        query_yesterday = """
            SELECT 
                DAY(tgl_produksi) AS hari,
                COUNT(sample_number) AS total
            FROM 
                laboratory_performance_tat
            WHERE 
                type_sample IN ('HOS','ROS','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC')
                AND CONVERT(DATE, tgl_produksi) = CONVERT(DATE, DATEADD(DAY, -1, GETDATE()))  -- Filter untuk hari sebelumnya MsSQL
            GROUP BY 
                DAY(tgl_produksi)
            ORDER BY 
                hari;
        """

    else:
        raise ValueError("Unsupported database vendor.")
    
    try:
        # Eksekusi query untuk hari ini
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query_today)
            chart_data_today = cursor.fetchall()

        # Jika data untuk hari ini kosong, ambil data untuk hari sebelumnya
        if not chart_data_today:
            with connections['sqms_db'].cursor() as cursor:
                cursor.execute(query_yesterday)
                chart_data = cursor.fetchall()
        else:
            chart_data = chart_data_today

        # Format data untuk JSON response
        x_data = [f"Days {entry[0]}" for entry in chart_data] 
        y_data = [entry[1] for entry in chart_data]  # Total sampel

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'x_data': x_data,
            'y_data': y_data
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': 'Database error occurred'}, status=500)





