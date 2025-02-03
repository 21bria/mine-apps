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
from itertools import accumulate
from datetime import timedelta
from django.utils.timezone import now
logger = logging.getLogger(__name__) 
from ...utils.db_utils import get_db_vendor

 # Memanggil fungsi utility
db_vendor = get_db_vendor('sqms_db')
import json

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

# Get Mine Category
def get_mine_category_ptd(request):
    query = """
         SELECT
            ROUND(SUM(bcm),2) AS bcm_total,
            ROUND(COALESCE(SUM(CASE WHEN category_mine ='Mining' THEN bcm ELSE 0 END),0),2) mining,
            ROUND(COALESCE(SUM(CASE WHEN category_mine ='Project' THEN bcm ELSE 0 END),0),2) project
        FROM mine_productions 
    """
    try:
        # Use the correct database connection
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

        bcm_total = [entry[0] for entry in data]
        mining    = [entry[1] for entry in data]
        project   = [entry[2] for entry in data]

        return JsonResponse({
            'mining'   : mining,
            'project'  : project,
            'bcm_total': bcm_total
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)    
    
def get_mine_category_ytd(request):
    # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)

    if filter_year:
        filter_sql = "WHERE YEAR(date_production) = %s"
        params = [filter_year]
    else:
        current_year = datetime.now().year
        filter_sql = "WHERE YEAR(date_production) = %s"
        params = [current_year]

    query = """
            SELECT
                ROUND(SUM(bcm),2) AS bcm_total,
                ROUND(COALESCE(SUM(CASE WHEN category_mine ='Mining' THEN bcm ELSE 0 END),0),2) mining,
                ROUND(COALESCE(SUM(CASE WHEN category_mine ='Project' THEN bcm ELSE 0 END),0),2) project
            FROM mine_productions 
                {}
    """.format(filter_sql)

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam list:   
        bcm_total = [entry[0] for entry in data]
        mining    = [entry[1] for entry in data]
        project   = [entry[2] for entry in data]

        return JsonResponse({
            'mining'   : mining,
            'project'  : project,
            'bcm_total': bcm_total
        })
    
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 

def get_mine_category_mtd(request):
    # Ambil filter dari request
    filter_year = request.GET.get('filter_year')
    filter_month = request.GET.get('filter_month')

    # Gunakan default jika filter tidak valid
    try:
        filter_year = int(filter_year) if filter_year else datetime.now().year
        filter_month = int(filter_month) if filter_month else datetime.now().month
    except ValueError:
        filter_year = datetime.now().year
        filter_month = datetime.now().month

    # Query SQL dengan parameter binding
    query = """
        SELECT
            ROUND(SUM(bcm), 2) AS bcm_total,
            ROUND(COALESCE(SUM(CASE WHEN category_mine = 'Mining' THEN bcm ELSE 0 END), 0), 2) AS mining,
            ROUND(COALESCE(SUM(CASE WHEN category_mine = 'Project' THEN bcm ELSE 0 END), 0), 2) AS project
        FROM mine_productions
        WHERE YEAR(date_production) = %s AND MONTH(date_production) = %s
    """

    params = [filter_year, filter_month]  # Parameter yang digunakan untuk query

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam list
        bcm_total = [entry[0] for entry in data]
        mining    = [entry[1] for entry in data]
        project   = [entry[2] for entry in data]

        return JsonResponse({
            'mining'    : mining,
            'project'   : project,
            'bcm_total' : bcm_total
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
def get_mine_category_wtd(request):

    # Query SQL
    query = """
        SELECT
            ROUND(SUM(bcm), 2) AS bcm_total,
            ROUND(COALESCE(SUM(CASE WHEN category_mine = 'Mining' THEN bcm ELSE 0 END), 0), 2) AS mining,
            ROUND(COALESCE(SUM(CASE WHEN category_mine = 'Project' THEN bcm ELSE 0 END), 0), 2) AS project
        FROM 
            mine_productions
        WHERE 
            YEAR(date_production) = YEAR(GETDATE()) -- Tahun saat ini         
            AND 
            DATEPART(WEEK, date_production) = DATEPART(WEEK, GETDATE()) -- Minggu saat ini
    """

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

        # Pisahkan data ke dalam list
        bcm_total = [entry[0] for entry in data]
        mining    = [entry[1] for entry in data]
        project   = [entry[2] for entry in data]

        return JsonResponse({
            'mining'    : mining,
            'project'   : project,
            'bcm_total' : bcm_total
        })

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# YTD Ore Productions
def get_ytd_card_mine(request):
    # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)

    if filter_year:
        filter_sql = "WHERE YEAR(date_production) = %s"
        params = [filter_year]
    else:
        current_year = datetime.now().year
        filter_sql = "WHERE YEAR(date_production) = %s"
        params = [current_year]
    query = """
         SELECT
            ROUND(SUM(bcm),2) AS bcm_total,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN bcm ELSE 0 END),0),2) TopSoil,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN bcm ELSE 0 END),0),2) OB,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN bcm ELSE 0 END),0),2) LGLO,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN bcm ELSE 0 END),0),2) MGLO,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN bcm ELSE 0 END),0),2) HGLO,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN bcm ELSE 0 END),0),2) Waste,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN bcm ELSE 0 END),0),2) MWS,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN bcm ELSE 0 END),0),2) LGSO,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN bcm ELSE 0 END),0),2) MGSO,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN bcm ELSE 0 END),0),2) HGSO,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN bcm ELSE 0 END),0),2) Quarry,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN bcm ELSE 0 END),0),2) Biomass,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN bcm ELSE 0 END),0),2) Ballast
        FROM mine_productions 
        {}
    """.format(filter_sql)
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Pisahkan data ke dalam  list: 
        bcm_total = [entry[0] for entry in data]
        TopSoil   = [entry[1] for entry in data]
        OB        = [entry[2] for entry in data]
        LGLO      = [entry[3] for entry in data]
        MGLO      = [entry[4] for entry in data]
        HGLO      = [entry[5] for entry in data]
        Waste     = [entry[6] for entry in data]
        MWS       = [entry[7] for entry in data]
        LGSO      = [entry[8] for entry in data]
        MGSO      = [entry[9] for entry in data]
        HGSO      = [entry[10] for entry in data]
        Quarry    = [entry[11] for entry in data]
        Biomass   = [entry[12] for entry in data]

        return JsonResponse({
            'TopSoil'  : TopSoil,
            'OB'       : OB,
            'LGLO'     : LGLO,
            'MGLO'     : MGLO,
            'HGLO'     : HGLO,
            'Waste'    : Waste,
            'MWS'      : MWS,
            'LGSO'     : LGSO,
            'HGSO'     : HGSO,
            'MGSO'     : MGSO,
            'Quarry'   : Quarry,
            'Biomass'  : Biomass,
            'bcm_total': bcm_total
        })
    
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500)

def get_mine_chart_ytd(request):
    params = []

    # Mendapatkan teks tanggal dari permintaan HTTP
    filter_year = request.GET.get('filter_year', None) 
    vendors         = request.GET.get('vendors') 
    sources_area    = request.GET.get('sources_area') 
    category_mine   = request.GET.get('category_mine') 

    if filter_year:
        tanggal = filter_year
    else:
        tanggal = datetime.now().year

    tahun = tanggal


    # Menginisialisasi query dasar
    query = """
        SELECT 
            t1.tahun,t1.bulan,
            ROUND(COALESCE(SUM(DISTINCT t1.TopSoil),0),2) as TopSoil,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil),0),2) as Soil_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.OB),0),2) as OB,
            ROUND(COALESCE(SUM(DISTINCT t2.OB_Plan),0),2) as OB_Plan,
            ROUND(COALESCE(SUM(DISTINCT t1.LGLO),0),2) as LGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGLO_plan),0),2) as LGLO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.MGLO),0),2) as MGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGLO_plan),0),2) as MGLO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.HGLO),0),2) as HGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGLO_plan),0),2) as HGLO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Waste),0),2) as Waste,
            ROUND(COALESCE(SUM(DISTINCT t2.Waste_plan),0),2) as Waste_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.MWS),0),2) as MWS,
            ROUND(COALESCE(SUM(DISTINCT t2.MWS_plan),0),2) as MWS_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.LGSO),0),2) as LGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGSO_plan),0),2) as LGSO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.MGSO),0),2) as MGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGSO_plan),0),2) as MGSO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.HGSO),0),2) as HGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGSO_plan),0),2) as HGSO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Quarry),0),2) as Quarry,
            ROUND(COALESCE(SUM(DISTINCT t2.Quarry_plan),0),2) as Quarry_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Ballast),0),2) as Ballast,
            ROUND(COALESCE(SUM(DISTINCT t2.Ballast_plan),0),2) as Ballast_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Biomass),0),2) as Biomass,
            ROUND(COALESCE(SUM(DISTINCT t2.Biomass_plan),0),2) as Biomass_plan
        FROM 
            (
                SELECT 
                    YEAR(date_production) as tahun,
                    MONTH(date_production) as bulan,
                    category_mine,
                    sources_area,vendors,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN tonnage ELSE 0 END),0),2) TopSoil,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN tonnage ELSE 0 END),0),2) OB,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN tonnage ELSE 0 END),0),2) LGLO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN tonnage ELSE 0 END),0),2) MGLO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN tonnage ELSE 0 END),0),2) HGLO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN tonnage ELSE 0 END),0),2) Waste,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN tonnage ELSE 0 END),0),2) MWS,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN tonnage ELSE 0 END),0),2) LGSO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN tonnage ELSE 0 END),0),2) MGSO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN tonnage ELSE 0 END),0),2) HGSO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN tonnage ELSE 0 END),0),2) Quarry,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN tonnage ELSE 0 END),0),2) Ballast,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN tonnage ELSE 0 END),0),2) Biomass
                FROM mine_productions
                WHERE YEAR(date_production) = %s
                GROUP BY YEAR(date_production), MONTH(date_production), category_mine, sources_area, vendors
            ) AS t1
        LEFT JOIN (
           SELECT 
                YEAR(date_plan) as tahun,
                MONTH(date_plan) as bulan,
                category,sources,vendors,
                ROUND(COALESCE(SUM(TopSoil),0),2) as TopSoil,
                ROUND(COALESCE(SUM(OB),0),2) as OB_Plan,
                ROUND(COALESCE(SUM(LGLO),0),2) as LGLO_plan,
                ROUND(COALESCE(SUM(MGLO),0),2) as MGLO_plan,
                ROUND(COALESCE(SUM(HGLO),0),2) as HGLO_plan,
                ROUND(COALESCE(SUM(Waste),0),2) as Waste_plan,
                ROUND(COALESCE(SUM(MWS),0),2) as MWS_plan,
                ROUND(COALESCE(SUM(LGSO),0),2) as LGSO_plan,
                ROUND(COALESCE(SUM(MGSO),0),2) as MGSO_plan,
                ROUND(COALESCE(SUM(HGSO),0),2) as HGSO_plan,
                ROUND(COALESCE(SUM(Quarry),0),2) as Quarry_plan,
                ROUND(COALESCE(SUM(Ballast),0),2) as Ballast_plan,
                ROUND(COALESCE(SUM(Biomass),0),2) as Biomass_plan
            FROM plan_productions
            WHERE YEAR(date_plan) = %s
            GROUP BY YEAR(date_plan), MONTH(date_plan), category, sources, vendors
        ) AS t2  
        ON CONCAT(t2.tahun, t2.bulan, t2.category, t2.sources, t2.vendors) = CONCAT(t1.tahun, t1.bulan, t1.category_mine, t1.sources_area, t1.vendors)
    """

    # Tambahkan tahun ke params
    params.extend([tahun, tahun])

    # List untuk menampung filter
    filters = []

    # Tambahkan filter berdasarkan parameter yang ada jika ada nilai
    if category_mine:
        filters.append("t1.category_mine = %s")
        filters.append("t2.category = %s")
        params.extend([category_mine, category_mine])  # Append for both subqueries

    if sources_area:
        filters.append("t1.sources_area = %s")
        filters.append("t2.sources = %s")
        params.extend([sources_area, sources_area])  

    if vendors:
        filters.append("t1.vendors = %s")
        filters.append("t2.vendors = %s")
        params.extend([vendors, vendors]) 

    # Gabungkan filter jika ada
    if filters:
        query += " WHERE " + " AND ".join(filters) 

    # Menyelesaikan query
    query += """
            GROUP BY t1.tahun, t1.bulan
    """   
    # Execute the query with params
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['tahun','bulan', 'TopSoil', 'Soil_plan','OB','OB_plan','LGLO','LGLO_plan',
                                   'MGLO', 'MGLO_plan','HGLO','HGLO_plan','Waste','Waste_plan','MWS', 'MWS_plan','LGSO','LGSO_plan','MGSO','MGSO_plan',
                                   'HGSO', 'HGSO_plan','Quarry','Quarry_plan','Ballast','Ballast_plan','Biomass','Biomass_plan'])

    
        # Membuat kolom tahun dan bulan
        df['tahun'] = df['tahun']
        df['bulan'] = df['bulan']

        # Mengelompokkan berdasarkan tahun dan bulan, lalu menghitung total
        grouped_totals = df.groupby(['tahun', 'bulan']).agg({
            'TopSoil': 'sum',
            'OB'     : 'sum',
            'LGLO'   : 'sum',
            'MGLO'   : 'sum',
            'HGLO'   : 'sum',
            'Waste'  : 'sum',
            'MWS'    : 'sum',
            'LGSO'   : 'sum',
            'MGSO'   : 'sum',
            'HGSO'   : 'sum',
            'Quarry' : 'sum',
            'Ballast': 'sum',
            'Biomass': 'sum'
        }).reset_index()

        # Untuk total PLAN
        plan_totals = df.groupby(['tahun', 'bulan']).agg({
            'Soil_plan'   : 'sum',
            'OB_plan'     : 'sum',
            'LGLO_plan'   : 'sum',
            'MGLO_plan'   : 'sum',
            'HGLO_plan'   : 'sum',
            'Waste_plan'  : 'sum',
            'MWS_plan'    : 'sum',
            'LGSO_plan'   : 'sum',
            'MGSO_plan'   : 'sum',
            'HGSO_plan'   : 'sum',
            'Quarry_plan' : 'sum',
            'Ballast_plan': 'sum',
            'Biomass_plan': 'sum'
        }).reset_index()

        # Menghitung total untuk setiap bulan
        grouped_totals['Total'] = grouped_totals[['TopSoil','OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO', 
                                                   'Quarry', 'Ballast', 'Biomass']].sum(axis=1)
        
        plan_totals['Total'] = plan_totals[['Soil_plan','OB_plan','LGLO_plan','MGLO_plan','HGLO_plan','Waste_plan','MWS_plan', 
                                            'LGSO_plan','MGSO_plan','HGSO_plan','Quarry_plan','Ballast_plan','Biomass_plan']].sum(axis=1)

        # Membuat DataFrame baru hanya dengan kolom bulan dan total
        monthly_actual = grouped_totals[['bulan', 'Total']]
        monthly_plan   = plan_totals[['bulan', 'Total']]

        # Mengambil data dari DataFrame
        actual = monthly_actual['Total'].tolist()
        plan   = monthly_plan['Total'].tolist()

        # Define month names
        bulan_names = ["Jan", "Feb", "Mar", "Ap", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        # Convert month numbers to month names for the x-axis
        bulan = [bulan_names[b - 1] for b in monthly_actual['bulan'].tolist()]
 

        response_data = {
            'x_data'   : bulan,
            'y_plan'   : plan,
            'y_actual' : actual,
            # 'plan_accumulated'  : plan_accumulated,
            # 'actual_accumulated': actual_accumulated,
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)


    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

# MTD - Ore Production
def get_chart_mine_daily(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
    # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks  = request.GET.get('filter_days')  
    vendors       = request.GET.get('vendors') 
    sources_area  = request.GET.get('sources_area') 
    category_mine = request.GET.get('category_mine') 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        tanggal = datetime.now().date()

    hari_ini     = tanggal
    tgl_pertama  = hari_ini.replace(day=1)
    tgl_terakhir = (hari_ini.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    last_day     = tgl_terakhir.day

    bulan = tanggal.month
    tahun = tanggal.year

    # Menginisialisasi query dasar
    query = """
            SELECT 
                t1.left_date,
                ROUND(COALESCE(SUM(DISTINCT tonnage),0),2) as total_tonnage,
                ROUND(COALESCE(SUM(DISTINCT plan_data),0),2) as total_plan
            FROM tanggal t1
            LEFT JOIN (
                SELECT 
                    left_date,
                    category_mine,
			        sources_area,
			        mine_productions.vendors,
                    ref_material, 
                    SUM(tonnage) AS tonnage,
                    ROUND(COALESCE(SUM(DISTINCT TopSoil+OB+LGLO+MGLO+HGLO+Waste+MWS+LGSO+MGSO+HGSO+Quarry+Ballast+Biomass),0),2) as plan_data
                FROM mine_productions
                LEFT JOIN
                     plan_productions ON mine_productions.ref_material = plan_productions.ref_plan 
                WHERE date_production BETWEEN %s AND %s
        """
    # Tambahkan tanggal awal dan akhir ke params
    params.append(tgl_pertama)
    params.append(tgl_terakhir)

    # List untuk menampung filter
    filters = []
 
     # Tambahkan filter berdasarkan parameter yang ada
    if category_mine:
        filters.append("category_mine = %s")
        params.append(category_mine)

    if sources_area:
        filters.append("sources_area = %s")
        params.append(sources_area)

    if vendors:
        filters.append("mine_productions.vendors = %s")
        params.append(vendors)


    # Gabungkan filter jika ada
    if filters:
            query += " AND " + " AND ".join(filters)

    # Menyelesaikan query
    query += """
            GROUP BY left_date,date_production,category_mine,sources_area,mine_productions.vendors,t_load,ref_material) AS t2 on t1.left_date = t2.left_date
            WHERE 
                t1.left_date <= %s
            GROUP BY
                t1.left_date
            ORDER By 
                t1.left_date asc
        """

    # Menambahkan last_day ke params
    params.append(last_day)

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['left_date', 'total_bcm', 'total_plan'])

        # Extract data dari DataFrame
        left_date   = df['left_date'].tolist()  
        total_plan  = df['total_plan'].tolist()  
        total_bcm   = df['total_bcm'].tolist()  

        actual_accumulated = [round(total, 2) for total in itertools.accumulate(total_bcm)]
        plan_accumulated   = [round(total, 2) for total in itertools.accumulate(total_plan)]

        # Define month names
        bulan_names = ["Jan", "Feb", "Mar", "Ap", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        bulan   = [bulan_names[bulan - 1]]
        # Ambil elemen pertama
        bulan_label = bulan[0] if bulan else '' 

        response_data = {
            'x_data'            : left_date,
            'y_plan'            : total_plan,
            'y_actual'          : total_bcm,
            'plan_accumulated'  : plan_accumulated,
            'actual_accumulated': actual_accumulated,
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

def get_chart_material_daily(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
    # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks  = request.GET.get('filter_days')  
    vendors       = request.GET.get('vendors') 
    sources_area  = request.GET.get('sources_area') 
    category_mine = request.GET.get('category_mine') 

    # tanggal_teks  = '2024-08-01'  
    # category_mine = 'Mining' 
    # sources_area  = 'Pit DS' 
    # vendors       = 'PB'

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        tanggal = datetime.now().date()

    hari_ini     = tanggal
    tgl_pertama  = hari_ini.replace(day=1)
    tgl_terakhir = (hari_ini.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    last_day     = tgl_terakhir.day

    tahun = tanggal.year
    bulan = tanggal.month

    # Menginisialisasi query dasar
    query = """
            SELECT 
                 t1.left_date,
                 -- ROUND(COALESCE(SUM(DISTINCT total),0),2) as total_tonagge,
                 -- ROUND(COALESCE(SUM(DISTINCT plan),0),2) as total_plan,
                 ROUND(COALESCE(SUM(DISTINCT TopSoil),0),2) as TopSoil,
                 ROUND(COALESCE(SUM(DISTINCT Soil_plan),0),2) as Soil_plan,
                 ROUND(COALESCE(SUM(DISTINCT OB),0),2) as OB,
                 ROUND(COALESCE(SUM(DISTINCT OB_Plan),0),2) as OB_Plan,
                 ROUND(COALESCE(SUM(DISTINCT LGLO),0),2) as LGLO,
                 ROUND(COALESCE(SUM(DISTINCT LGLO_plan),0),2) as LGLO_plan,
                 ROUND(COALESCE(SUM(DISTINCT MGLO),0),2) as MGLO,
                 ROUND(COALESCE(SUM(DISTINCT MGLO_plan),0),2) as MGLO_plan,
                 ROUND(COALESCE(SUM(DISTINCT HGLO),0),2) as HGLO,
                 ROUND(COALESCE(SUM(DISTINCT HGLO_plan),0),2) as HGLO_plan,
                 ROUND(COALESCE(SUM(DISTINCT Waste),0),2) as Waste,
                 ROUND(COALESCE(SUM(DISTINCT Waste_plan),0),2) as Waste_plan,
                 ROUND(COALESCE(SUM(DISTINCT MWS),0),2) as MWS,
                 ROUND(COALESCE(SUM(DISTINCT MWS_plan),0),2) as MWS_plan,
                 ROUND(COALESCE(SUM(DISTINCT LGSO),0),2) as LGSO,
                 ROUND(COALESCE(SUM(DISTINCT LGSO_plan),0),2) as LGSO_plan,
                 ROUND(COALESCE(SUM(DISTINCT MGSO),0),2) as MGSO,
                 ROUND(COALESCE(SUM(DISTINCT MGSO_plan),0),2) as MGSO_plan,
                 ROUND(COALESCE(SUM(DISTINCT HGSO),0),2) as HGSO,
                 ROUND(COALESCE(SUM(DISTINCT HGSO_plan),0),2) as HGSO_plan,
                 ROUND(COALESCE(SUM(DISTINCT Quarry),0),2) as Quarry,
                 ROUND(COALESCE(SUM(DISTINCT Quarry_plan),0),2) as Quarry_plan,
                 ROUND(COALESCE(SUM(DISTINCT Ballast),0),2) as Ballast,
                 ROUND(COALESCE(SUM(DISTINCT Ballast_plan),0),2) as Ballast_plan,
                 ROUND(COALESCE(SUM(DISTINCT Biomass),0),2) as Biomass,
                 ROUND(COALESCE(SUM(DISTINCT Biomass_plan),0),2) as Biomass_plan
            FROM tanggal t1
            LEFT JOIN (
                    SELECT 
                        left_date,
                        ref_material, 
                        -- SUM(tonnage) AS total,
                        -- ROUND(COALESCE(SUM(DISTINCT TopSoil+OB+LGLO+MGLO+HGLO+Waste+MWS+LGSO+MGSO+HGSO+Quarry+Ballast+Biomass),0),2) as plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN tonnage ELSE 0 END),0),2) TopSoil,
                        ROUND(COALESCE(SUM(DISTINCT TopSoil),0),2) as Soil_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN tonnage ELSE 0 END),0),2) LGLO,
                        ROUND(COALESCE(SUM(DISTINCT LGLO),0),2) as LGLO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN tonnage ELSE 0 END),0),2) OB,
                        ROUND(COALESCE(SUM(DISTINCT OB),0),2) as OB_Plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN tonnage ELSE 0 END),0),2) MGLO,
                        ROUND(COALESCE(SUM(DISTINCT MGLO),0),2) as MGLO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN tonnage ELSE 0 END),0),2) HGLO,
                        ROUND(COALESCE(SUM(DISTINCT HGLO),0),2) as HGLO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN tonnage ELSE 0 END),0),2) Waste,
                        ROUND(COALESCE(SUM(DISTINCT Waste),0),2) as Waste_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN tonnage ELSE 0 END),0),2) MWS,
                        ROUND(COALESCE(SUM(DISTINCT MWS),0),2) as MWS_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN tonnage ELSE 0 END),0),2) LGSO,
                        ROUND(COALESCE(SUM(DISTINCT LGSO),0),2) as LGSO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN tonnage ELSE 0 END),0),2) MGSO,
                        ROUND(COALESCE(SUM(DISTINCT MGSO),0),2) as MGSO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN tonnage ELSE 0 END),0),2) HGSO,
                        ROUND(COALESCE(SUM(DISTINCT HGSO),0),2) as HGSO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN tonnage ELSE 0 END),0),2) Quarry,
                        ROUND(COALESCE(SUM(DISTINCT Quarry),0),2) as Quarry_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN tonnage ELSE 0 END),0),2) Ballast,
                        ROUND(COALESCE(SUM(DISTINCT Ballast),0),2) as Ballast_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN tonnage ELSE 0 END),0),2) Biomass,
                        ROUND(COALESCE(SUM(DISTINCT Biomass),0),2) as Biomass_plan
                 	FROM mine_productions
                	LEFT JOIN 
                        plan_productions ON mine_productions.ref_material = plan_productions.ref_plan   
                    WHERE date_production BETWEEN %s AND %s
        """
    # Tambahkan tanggal awal dan akhir ke params
    params.append(tgl_pertama)
    params.append(tgl_terakhir)

    # List untuk menampung filter
    filters = []
 
     # Tambahkan filter berdasarkan parameter yang ada
    if category_mine:
            filters.append("category_mine = %s")
            params.append(category_mine)

    if sources_area:
            filters.append("sources_area = %s")
            params.append(sources_area)

    if vendors:
            filters.append("plan_productions.vendors = %s")
            params.append(vendors)

        # Gabungkan filter jika ada
    if filters:
            query += " AND " + " AND ".join(filters)

    # Menyelesaikan query
    query += """
                GROUP BY left_date, ref_material
            ) AS t2 on t1.left_date = t2.left_date
            WHERE 
                t1.left_date <= %s
            GROUP BY
                t1.left_date
            ORDER By 
                t1.left_date asc
        """

    # Menambahkan last_day ke params
    params.append(last_day)

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['left_date','TopSoil', 'Soil_plan','OB','OB_plan','LGLO','LGLO_plan',
                                   'MGLO', 'MGLO_plan','HGLO','HGLO_plan','Waste','Waste_plan','MWS', 'MWS_plan','LGSO','LGSO_plan','MGSO','MGSO_plan',
                                   'HGSO', 'HGSO_plan','Quarry','Quarry_plan','Ballast','Ballast_plan','Biomass','Biomass_plan'])

        # Menghitung total dari kolom 
        actual_total = df[['TopSoil','OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']].sum()
        plan_total   = df[['Soil_plan','OB_plan','LGLO_plan','MGLO_plan','HGLO_plan','Waste_plan','MWS_plan', 
                         'LGSO_plan','MGSO_plan','HGSO_plan','Quarry_plan','Ballast_plan','Biomass_plan']].sum()


        x_data      = ['TopSoil', 'OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']
        actual_data = actual_total.tolist()
        plan_data   = plan_total.tolist()

        # actual_accumulated = [round(total, 2) for total in itertools.accumulate(actual_data)]
        # plan_accumulated   = [round(total, 2) for total in itertools.accumulate(plan_data)]

        # Define month names
        bulan_names = ["Jan", "Feb", "Mar", "Ap", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        bulan = [bulan_names[bulan - 1]]

        # Ambil elemen pertama
        bulan_label = bulan[0] if bulan else '' 

        response_data = {
            'x_data'   : x_data,
            'y_plan'   : plan_data,
            'y_actual' : actual_data,
            # 'plan_accumulated'  : plan_accumulated,
            # 'actual_accumulated': actual_accumulated,
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)


    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

# For Days
def get_MineByDays(request):
    # params = []
    # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks  = request.GET.get('filter_days') 
    vendors       = request.GET.get('vendors') 
    sources_area  = request.GET.get('sources_area') 
    category_mine = request.GET.get('category_mine') 
    # tanggal_teks  = '2024-01-09' 
    # category_mine = 'Mining' 
    # sources_area  = 'Pit BR1'
    # vendors       = 'PB' 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        tanggal = datetime.now().date()
    
    query = """
        SELECT 
            ROUND(SUM(total_tonnage),2) AS total_tonnage,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil+t2.OB+t2.LGLO+t2.MGLO+t2.HGLO+t2.Waste+t2.MWS+t2.LGSO+t2.MGSO+t2.HGSO+t2.Quarry+t2.Ballast+t2.Biomass),0),2) as total_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN total_tonnage ELSE 0 END),0),2) TopSoil,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil),0),2) as Soil_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN total_tonnage ELSE 0 END),0),2) OB,
            ROUND(COALESCE(SUM(DISTINCT t2.OB),0),2) as OB_Plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN total_tonnage ELSE 0 END),0),2) LGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGLO),0),2) as LGLO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN total_tonnage ELSE 0 END),0),2) MGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGLO),0),2) as MGLO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN total_tonnage ELSE 0 END),0),2) HGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGLO),0),2) as HGLO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN total_tonnage ELSE 0 END),0),2) Waste,
            ROUND(COALESCE(SUM(DISTINCT t2.Waste),0),2) as Waste_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN total_tonnage ELSE 0 END),0),2) MWS,
            ROUND(COALESCE(SUM(DISTINCT t2.MWS),0),2) as MWS_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN total_tonnage ELSE 0 END),0),2) LGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGSO),0),2) as LGSO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN total_tonnage ELSE 0 END),0),2) MGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGSO),0),2) as MGSO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN total_tonnage ELSE 0 END),0),2) HGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGSO),0),2) as HGSO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN total_tonnage ELSE 0 END),0),2) Quarry,
            ROUND(COALESCE(SUM(DISTINCT t2.Quarry),0),2) as Quarry_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN total_tonnage ELSE 0 END),0),2) Ballast,
            ROUND(COALESCE(SUM(DISTINCT t2.Ballast),0),2) as Ballast_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN total_tonnage ELSE 0 END),0),2) Biomass,
            ROUND(COALESCE(SUM(DISTINCT t2.Biomass),0),2) as Biomass_plan
         FROM 
         (SELECT date_production, nama_material,category_mine,sources_area,vendors,ref_material, SUM(tonnage) AS total_tonnage
		  FROM mine_productions
          GROUP BY date_production, nama_material,category_mine,sources_area,vendors,ref_material
		  ) AS t1
        LEFT JOIN 
            plan_productions AS t2 ON t1.ref_material = t2.ref_plan

        WHERE date_production = %s
        """

    filters = []
    params  = [tanggal]

    if category_mine:
        filters.append("t1.category_mine = %s")
        params.append(category_mine)

    if sources_area:
        filters.append("t1.sources_area = %s")
        params.append(sources_area)

    if vendors:
        filters.append("t1.vendors = %s")
        params.append(vendors)

    if filters:
        query += " AND "+" AND ".join(filters)

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['total_tonnage', 'total_plan', 'TopSoil', 'Soil_plan','OB','OB_plan','LGLO','LGLO_plan',
                                   'MGLO', 'MGLO_plan','HGLO','HGLO_plan','Waste','Waste_plan','MWS', 'MWS_plan','LGSO','LGSO_plan','MGSO','MGSO_plan',
                                   'HGSO', 'HGSO_plan','Quarry','Quarry_plan','Ballast','Ballast_plan','Biomass','Biomass_plan'])
   
        # Extract data dari DataFrame
        actual_total = df[['TopSoil','OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']].sum()
        plan_total   = df[['Soil_plan','OB_plan','LGLO_plan','MGLO_plan','HGLO_plan','Waste_plan','MWS_plan', 
                         'LGSO_plan','MGSO_plan','HGSO_plan','Quarry_plan','Ballast_plan','Biomass_plan']].sum()

        x_data = ['TopSoil', 'OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']
        y_data = actual_total.tolist()
        y_plan = plan_total.tolist()
        label_date = tanggal.strftime("%Y/%m/%d")

        # Kirim data JSON ke template menggunakan JsonResponse
        response_data = {
            'x_data'   : x_data,
            'y_actual' : y_data,
            'y_plan'   : y_plan,
        }

        return JsonResponse(response_data)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

def get_MineByHours(request):
    # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks  = request.GET.get('filter_days') 
    vendors       = request.GET.get('vendors') 
    sources_area  = request.GET.get('sources_area') 
    category_mine = request.GET.get('category_mine') 
    # tanggal_teks  = '2024-01-09' 
    # category_mine = 'Mining' 
    # sources_area  = 'Pit BR1'
    # vendors       = 'PB' 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        # Jika tidak ada tanggal yang diberikan, gunakan tanggal hari ini
        tanggal = datetime.now().date()

    filters = []
    params = [tanggal]

    # Menggunakan alias `mine_productions` untuk kondisi dalam subquery
    if category_mine:
        filters.append("mine_productions.category_mine = %s")
        params.append(category_mine)

    if sources_area:
        filters.append("mine_productions.sources_area = %s")
        params.append(sources_area)

    if vendors:
        filters.append("mine_productions.vendors = %s")
        params.append(vendors)


    query = """
        SELECT
            t1.id, 		
            t1.left_time,
            COALESCE(SUM(total_tonnage),0) AS total,
            COALESCE(SUM(plan_data),0) as plan_data
        FROM tanggal_jam  t1
            LEFT JOIN (
                    SELECT 
                        date_production,
					    t_load,
						shift,
			            category_mine,
			            sources_area,
			            mine_productions.vendors,
			            ref_material,
						SUM(tonnage) AS total_tonnage,
						ROUND(COALESCE(SUM(DISTINCT TopSoil+OB+LGLO+MGLO+HGLO+Waste+MWS+LGSO+MGSO+HGSO+Quarry+Ballast+Biomass),0)/22,2) as plan_data
                        FROM mine_productions
                    LEFT JOIN
                    plan_productions ON mine_productions.ref_material = plan_productions.ref_plan   
        WHERE date_production = %s
        """

    if filters:
        query += " AND "+" AND ".join(filters)

    # Menyelesaikan query
    query += """
         GROUP BY date_production,shift,category_mine,sources_area,mine_productions.vendors,t_load,ref_material) AS t2 on t1.left_time = t_load
         GROUP BY
            t1.id,t1.left_time
          ORDER By 
            t1.id asc
        """
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['id', 'left_time', 'total', 'plan_data'])

        # Extract data dari DataFrame
        total     = df['total'].tolist()  
        plan      = df['plan_data'].tolist()  

        # Mengonversi 'left_time' ke string dengan menambahkan nol di depan jika perlu
        x_data = df['left_time'] = df['left_time'].apply(lambda x: f"{x:02d}")
        
        label_date = tanggal.strftime("%Y/%m/%d")

        # Kirim data JSON ke template menggunakan JsonResponse
        response_data = {
            'x_data' : x_data.tolist(),
            'y_actual' : total,
            'y_plan' : plan,
        }

        return JsonResponse(response_data)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

# Get Material on 5 weeks
def get_mine_chart_weeks(request):
    params = []
    # Mendapatkan teks tanggal dari permintaan HTTP
    vendors         = request.GET.get('vendors') 
    sources_area    = request.GET.get('sources_area') 
    category_mine   = request.GET.get('category_mine') 

    # Menginisialisasi query dasar
    
    # Query berdasarkan database
    if db_vendor == 'mysql':
        query = """
         SELECT 
            t1.week_actual,
            ROUND(COALESCE(SUM(DISTINCT t1.TopSoil),0),2) as TopSoil,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil),0),2) as Soil_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.OB),0),2) as OB,
            ROUND(COALESCE(SUM(DISTINCT t2.OB_Plan),0),2) as OB_Plan,
            ROUND(COALESCE(SUM(DISTINCT t1.LGLO),0),2) as LGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGLO_plan),0),2) as LGLO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.MGLO),0),2) as MGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGLO_plan),0),2) as MGLO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.HGLO),0),2) as HGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGLO_plan),0),2) as HGLO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Waste),0),2) as Waste,
            ROUND(COALESCE(SUM(DISTINCT t2.Waste_plan),0),2) as Waste_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.MWS),0),2) as MWS,
            ROUND(COALESCE(SUM(DISTINCT t2.MWS_plan),0),2) as MWS_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.LGSO),0),2) as LGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGSO_plan),0),2) as LGSO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.MGSO),0),2) as MGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGSO_plan),0),2) as MGSO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.HGSO),0),2) as HGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGSO_plan),0),2) as HGSO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Quarry),0),2) as Quarry,
            ROUND(COALESCE(SUM(DISTINCT t2.Quarry_plan),0),2) as Quarry_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Ballast),0),2) as Ballast,
            ROUND(COALESCE(SUM(DISTINCT t2.Ballast_plan),0),2) as Ballast_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Biomass),0),2) as Biomass,
            ROUND(COALESCE(SUM(DISTINCT t2.Biomass_plan),0),2) as Biomass_plan
        FROM 
            (
                SELECT 
                    -- DATEADD(week, DATEDIFF(week, 0, date_production), 0) AS week_actual,
                    DATE(DATE_SUB(date_production, INTERVAL (DAYOFWEEK(date_production) - 1) DAY)) AS week_actual,
                    category_mine,
                    sources_area,vendors,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN tonnage ELSE 0 END),0),2) TopSoil,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN tonnage ELSE 0 END),0),2) OB,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN tonnage ELSE 0 END),0),2) LGLO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN tonnage ELSE 0 END),0),2) MGLO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN tonnage ELSE 0 END),0),2) HGLO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN tonnage ELSE 0 END),0),2) Waste,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN tonnage ELSE 0 END),0),2) MWS,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN tonnage ELSE 0 END),0),2) LGSO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN tonnage ELSE 0 END),0),2) MGSO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN tonnage ELSE 0 END),0),2) HGSO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN tonnage ELSE 0 END),0),2) Quarry,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN tonnage ELSE 0 END),0),2) Ballast,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN tonnage ELSE 0 END),0),2) Biomass
                FROM mine_productions
                WHERE 
                -- (date_production >= DATEADD(week, - 19, GETDATE())) 
                (date_production >= DATE_SUB(CURDATE(), INTERVAL 19 WEEK)) 
                GROUP BY 
                -- DATEADD(week, DATEDIFF(week, 0, date_production), 0), 
                 DATE(DATE_SUB(date_production, INTERVAL (DAYOFWEEK(date_production) - 1) DAY)), -- Start of week
                category_mine, sources_area, vendors
            ) AS t1
        LEFT JOIN (
           SELECT 
				-- DATEADD(week, DATEDIFF(week, 0, date_plan), 0) AS week_plan,
                DATE(DATE_SUB(date_plan, INTERVAL (DAYOFWEEK(date_plan) - 1) DAY)) AS week_plan,
                category,sources,vendors,
                ROUND(COALESCE(SUM(TopSoil),0),2) as TopSoil,
                ROUND(COALESCE(SUM(OB),0),2) as OB_Plan,
                ROUND(COALESCE(SUM(LGLO),0),2) as LGLO_plan,
                ROUND(COALESCE(SUM(MGLO),0),2) as MGLO_plan,
                ROUND(COALESCE(SUM(HGLO),0),2) as HGLO_plan,
                ROUND(COALESCE(SUM(Waste),0),2) as Waste_plan,
                ROUND(COALESCE(SUM(MWS),0),2) as MWS_plan,
                ROUND(COALESCE(SUM(LGSO),0),2) as LGSO_plan,
                ROUND(COALESCE(SUM(MGSO),0),2) as MGSO_plan,
                ROUND(COALESCE(SUM(HGSO),0),2) as HGSO_plan,
                ROUND(COALESCE(SUM(Quarry),0),2) as Quarry_plan,
                ROUND(COALESCE(SUM(Ballast),0),2) as Ballast_plan,
                ROUND(COALESCE(SUM(Biomass),0),2) as Biomass_plan
            FROM plan_productions
            WHERE 
            -- (date_plan >= DATEADD(week, - 19, GETDATE())) 
            date_plan >= DATE_SUB(CURDATE(), INTERVAL 19 WEEK)
            GROUP BY 
            -- DATEADD(week, DATEDIFF(week, 0, date_plan), 0),
            DATE(DATE_SUB(date_plan, INTERVAL (DAYOFWEEK(date_plan) - 1) DAY)), -- Start of week
            category, sources, vendors
        ) AS t2  ON CONCAT(t2.week_plan, t2.category, t2.sources, t2.vendors) = CONCAT(t1.week_actual, t1.category_mine, t1.sources_area, t1.vendors)
    """

    elif db_vendor in ['mssql', 'microsoft']:
         # Query untuk SQL Server
        query = """
            SELECT 
                t1.week_actual,
                ROUND(COALESCE(SUM(DISTINCT t1.TopSoil),0),2) as TopSoil,
                ROUND(COALESCE(SUM(DISTINCT t2.TopSoil),0),2) as Soil_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.OB),0),2) as OB,
                ROUND(COALESCE(SUM(DISTINCT t2.OB_Plan),0),2) as OB_Plan,
                ROUND(COALESCE(SUM(DISTINCT t1.LGLO),0),2) as LGLO,
                ROUND(COALESCE(SUM(DISTINCT t2.LGLO_plan),0),2) as LGLO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.MGLO),0),2) as MGLO,
                ROUND(COALESCE(SUM(DISTINCT t2.MGLO_plan),0),2) as MGLO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.HGLO),0),2) as HGLO,
                ROUND(COALESCE(SUM(DISTINCT t2.HGLO_plan),0),2) as HGLO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.Waste),0),2) as Waste,
                ROUND(COALESCE(SUM(DISTINCT t2.Waste_plan),0),2) as Waste_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.MWS),0),2) as MWS,
                ROUND(COALESCE(SUM(DISTINCT t2.MWS_plan),0),2) as MWS_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.LGSO),0),2) as LGSO,
                ROUND(COALESCE(SUM(DISTINCT t2.LGSO_plan),0),2) as LGSO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.MGSO),0),2) as MGSO,
                ROUND(COALESCE(SUM(DISTINCT t2.MGSO_plan),0),2) as MGSO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.HGSO),0),2) as HGSO,
                ROUND(COALESCE(SUM(DISTINCT t2.HGSO_plan),0),2) as HGSO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.Quarry),0),2) as Quarry,
                ROUND(COALESCE(SUM(DISTINCT t2.Quarry_plan),0),2) as Quarry_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.Ballast),0),2) as Ballast,
                ROUND(COALESCE(SUM(DISTINCT t2.Ballast_plan),0),2) as Ballast_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.Biomass),0),2) as Biomass,
                ROUND(COALESCE(SUM(DISTINCT t2.Biomass_plan),0),2) as Biomass_plan
            FROM 
                (
                    SELECT 
                        DATEADD(week, DATEDIFF(week, 0, date_production), 0) AS week_actual,
                        category_mine,
                        sources_area,vendors,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN tonnage ELSE 0 END),0),2) TopSoil,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN tonnage ELSE 0 END),0),2) OB,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN tonnage ELSE 0 END),0),2) LGLO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN tonnage ELSE 0 END),0),2) MGLO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN tonnage ELSE 0 END),0),2) HGLO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN tonnage ELSE 0 END),0),2) Waste,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN tonnage ELSE 0 END),0),2) MWS,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN tonnage ELSE 0 END),0),2) LGSO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN tonnage ELSE 0 END),0),2) MGSO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN tonnage ELSE 0 END),0),2) HGSO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN tonnage ELSE 0 END),0),2) Quarry,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN tonnage ELSE 0 END),0),2) Ballast,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN tonnage ELSE 0 END),0),2) Biomass
                    FROM mine_productions
                    WHERE 
                    (date_production >= DATEADD(week, - 5, GETDATE())) 
                    GROUP BY 
                    DATEADD(week, DATEDIFF(week, 0, date_production), 0), 
                    category_mine, sources_area, vendors
                ) AS t1
            LEFT JOIN (
            SELECT 
                    DATEADD(week, DATEDIFF(week, 0, date_plan), 0) AS week_plan,
                    category,sources,vendors,
                    ROUND(COALESCE(SUM(TopSoil),0),2) as TopSoil,
                    ROUND(COALESCE(SUM(OB),0),2) as OB_Plan,
                    ROUND(COALESCE(SUM(LGLO),0),2) as LGLO_plan,
                    ROUND(COALESCE(SUM(MGLO),0),2) as MGLO_plan,
                    ROUND(COALESCE(SUM(HGLO),0),2) as HGLO_plan,
                    ROUND(COALESCE(SUM(Waste),0),2) as Waste_plan,
                    ROUND(COALESCE(SUM(MWS),0),2) as MWS_plan,
                    ROUND(COALESCE(SUM(LGSO),0),2) as LGSO_plan,
                    ROUND(COALESCE(SUM(MGSO),0),2) as MGSO_plan,
                    ROUND(COALESCE(SUM(HGSO),0),2) as HGSO_plan,
                    ROUND(COALESCE(SUM(Quarry),0),2) as Quarry_plan,
                    ROUND(COALESCE(SUM(Ballast),0),2) as Ballast_plan,
                    ROUND(COALESCE(SUM(Biomass),0),2) as Biomass_plan
                FROM plan_productions
                WHERE 
                (date_plan >= DATEADD(week, - 5, GETDATE())) 
                GROUP BY 
                DATEADD(week, DATEDIFF(week, 0, date_plan), 0),
                category, sources, vendors
            ) AS t2  ON CONCAT(t2.week_plan, t2.category, t2.sources, t2.vendors) = CONCAT(t1.week_actual, t1.category_mine, t1.sources_area, t1.vendors)
        """
    else:
        raise ValueError("Unsupported database vendor.")

    # List untuk menampung filter
    filters = []

    # Tambahkan filter berdasarkan parameter yang ada jika ada nilai
    if category_mine:
        filters.append("t1.category_mine = %s")
        filters.append("t2.category = %s")
        params.extend([category_mine, category_mine])  # Append for both subqueries

    if sources_area:
        filters.append("t1.sources_area = %s")
        filters.append("t2.sources = %s")
        params.extend([sources_area, sources_area])  

    if vendors:
        filters.append("t1.vendors = %s")
        filters.append("t2.vendors = %s")
        params.extend([vendors, vendors]) 

    # Gabungkan filter jika ada
    if filters:
        query += " WHERE " + " AND ".join(filters) 

    # Menyelesaikan query
    query += """
            GROUP BY t1.week_actual
    """   
    # Execute the query with params
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['week_actual', 'TopSoil', 'Soil_plan','OB','OB_plan','LGLO','LGLO_plan',
                                   'MGLO', 'MGLO_plan','HGLO','HGLO_plan','Waste','Waste_plan','MWS', 'MWS_plan','LGSO','LGSO_plan','MGSO','MGSO_plan',
                                   'HGSO', 'HGSO_plan','Quarry','Quarry_plan','Ballast','Ballast_plan','Biomass','Biomass_plan'])

    
        # Membuat kolom week
        df['week_actual'] = df['week_actual']

        # Mengelompokkan berdasarkan week, lalu menghitung total
        grouped_totals = df.groupby(['week_actual']).agg({
            'TopSoil': 'sum',
            'OB'     : 'sum',
            'LGLO'   : 'sum',
            'MGLO'   : 'sum',
            'HGLO'   : 'sum',
            'Waste'  : 'sum',
            'MWS'    : 'sum',
            'LGSO'   : 'sum',
            'MGSO'   : 'sum',
            'HGSO'   : 'sum',
            'Quarry' : 'sum',
            'Ballast': 'sum',
            'Biomass': 'sum'
        }).reset_index()

        # Untuk total PLAN
        plan_totals = df.groupby(['week_actual']).agg({
            'Soil_plan'   : 'sum',
            'OB_plan'     : 'sum',
            'LGLO_plan'   : 'sum',
            'MGLO_plan'   : 'sum',
            'HGLO_plan'   : 'sum',
            'Waste_plan'  : 'sum',
            'MWS_plan'    : 'sum',
            'LGSO_plan'   : 'sum',
            'MGSO_plan'   : 'sum',
            'HGSO_plan'   : 'sum',
            'Quarry_plan' : 'sum',
            'Ballast_plan': 'sum',
            'Biomass_plan': 'sum'
        }).reset_index()

        # Menghitung total untuk setiap bulan
        grouped_totals['Total'] = grouped_totals[['TopSoil','OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO', 
                                                   'Quarry', 'Ballast', 'Biomass']].sum(axis=1)
        
        plan_totals['Total'] = plan_totals[['Soil_plan','OB_plan','LGLO_plan','MGLO_plan','HGLO_plan','Waste_plan','MWS_plan', 
                                            'LGSO_plan','MGSO_plan','HGSO_plan','Quarry_plan','Ballast_plan','Biomass_plan']].sum(axis=1)

        # Membuat DataFrame baru hanya dengan kolom bulan dan total
        weekly_actual = grouped_totals[['week_actual', 'Total']]
        weekly_plan   = plan_totals[['week_actual', 'Total']]

        # Mengambil data dari DataFrame
        actual = weekly_actual['Total'].tolist()
        plan   = weekly_plan['Total'].tolist()
        week   = weekly_plan['week_actual'].tolist()
        

       # Ubah format tanggal dalam 'week' jika berupa Timestamp
        week = [date.strftime("%Y-%m-%d") for date in week]

        # Hitung akumulasi
        actual_accumulated = [round(total, 2) for total in itertools.accumulate(actual)]
        plan_accumulated   = [round(total, 2) for total in itertools.accumulate(plan)]

        response_data = {
            'x_data'   : week,
            'y_plan'   : plan,
            'y_actual' : actual,
            'plan_accumulated'  : plan_accumulated,
            'actual_accumulated': actual_accumulated,
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)


    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

# Get this week material
def get_material_on_week(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
    # Mendapatkan teks tanggal dari permintaan HTTP
    vendors       = request.GET.get('vendors') 
    sources_area  = request.GET.get('sources_area') 
    category_mine = request.GET.get('category_mine') 
 
    # category_mine = 'Mining' 
    # sources_area  = 'Pit DS' 
    # vendors       = 'PB'

    # Menginisialisasi query dasar
   
    # Query berdasarkan database
    if db_vendor == 'mysql':
        query = """
                            SELECT 
                                ref_material, 
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN tonnage ELSE 0 END),0),2) TopSoil,
                                ROUND(COALESCE(SUM(DISTINCT TopSoil),0),2) as Soil_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN tonnage ELSE 0 END),0),2) LGLO,
                                ROUND(COALESCE(SUM(DISTINCT LGLO),0),2) as LGLO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN tonnage ELSE 0 END),0),2) OB,
                                ROUND(COALESCE(SUM(DISTINCT OB),0),2) as OB_Plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN tonnage ELSE 0 END),0),2) MGLO,
                                ROUND(COALESCE(SUM(DISTINCT MGLO),0),2) as MGLO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN tonnage ELSE 0 END),0),2) HGLO,
                                ROUND(COALESCE(SUM(DISTINCT HGLO),0),2) as HGLO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN tonnage ELSE 0 END),0),2) Waste,
                                ROUND(COALESCE(SUM(DISTINCT Waste),0),2) as Waste_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN tonnage ELSE 0 END),0),2) MWS,
                                ROUND(COALESCE(SUM(DISTINCT MWS),0),2) as MWS_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN tonnage ELSE 0 END),0),2) LGSO,
                                ROUND(COALESCE(SUM(DISTINCT LGSO),0),2) as LGSO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN tonnage ELSE 0 END),0),2) MGSO,
                                ROUND(COALESCE(SUM(DISTINCT MGSO),0),2) as MGSO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN tonnage ELSE 0 END),0),2) HGSO,
                                ROUND(COALESCE(SUM(DISTINCT HGSO),0),2) as HGSO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN tonnage ELSE 0 END),0),2) Quarry,
                                ROUND(COALESCE(SUM(DISTINCT Quarry),0),2) as Quarry_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN tonnage ELSE 0 END),0),2) Ballast,
                                ROUND(COALESCE(SUM(DISTINCT Ballast),0),2) as Ballast_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN tonnage ELSE 0 END),0),2) Biomass,
                                ROUND(COALESCE(SUM(DISTINCT Biomass),0),2) as Biomass_plan
                            FROM mine_productions
                            LEFT JOIN 
                                plan_productions ON mine_productions.ref_material = plan_productions.ref_plan   
                            WHERE 
                                YEAR(date_production) = YEAR(CURDATE())
                                AND 
                                MONTH(date_production)=04
                                -- DATEPART(WEEK, date_production) = DATEPART(WEEK, GETDATE()) -- Minggu saat ini
                                -- WEEK(date_production, 1) = WEEK(CURDATE(), 1) -- Minggu saat ini
                """
    elif db_vendor in ['mssql', 'microsoft']:
        # Query untuk SQL Server
             query = """
                            SELECT 
                                ref_material, 
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN tonnage ELSE 0 END),0),2) TopSoil,
                                ROUND(COALESCE(SUM(DISTINCT TopSoil),0),2) as Soil_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN tonnage ELSE 0 END),0),2) LGLO,
                                ROUND(COALESCE(SUM(DISTINCT LGLO),0),2) as LGLO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN tonnage ELSE 0 END),0),2) OB,
                                ROUND(COALESCE(SUM(DISTINCT OB),0),2) as OB_Plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN tonnage ELSE 0 END),0),2) MGLO,
                                ROUND(COALESCE(SUM(DISTINCT MGLO),0),2) as MGLO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN tonnage ELSE 0 END),0),2) HGLO,
                                ROUND(COALESCE(SUM(DISTINCT HGLO),0),2) as HGLO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN tonnage ELSE 0 END),0),2) Waste,
                                ROUND(COALESCE(SUM(DISTINCT Waste),0),2) as Waste_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN tonnage ELSE 0 END),0),2) MWS,
                                ROUND(COALESCE(SUM(DISTINCT MWS),0),2) as MWS_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN tonnage ELSE 0 END),0),2) LGSO,
                                ROUND(COALESCE(SUM(DISTINCT LGSO),0),2) as LGSO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN tonnage ELSE 0 END),0),2) MGSO,
                                ROUND(COALESCE(SUM(DISTINCT MGSO),0),2) as MGSO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN tonnage ELSE 0 END),0),2) HGSO,
                                ROUND(COALESCE(SUM(DISTINCT HGSO),0),2) as HGSO_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN tonnage ELSE 0 END),0),2) Quarry,
                                ROUND(COALESCE(SUM(DISTINCT Quarry),0),2) as Quarry_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN tonnage ELSE 0 END),0),2) Ballast,
                                ROUND(COALESCE(SUM(DISTINCT Ballast),0),2) as Ballast_plan,
                                ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN tonnage ELSE 0 END),0),2) Biomass,
                                ROUND(COALESCE(SUM(DISTINCT Biomass),0),2) as Biomass_plan
                            FROM mine_productions
                            LEFT JOIN 
                                plan_productions ON mine_productions.ref_material = plan_productions.ref_plan   
                            WHERE 
                                YEAR(date_production) = YEAR(GETDATE()) -- MsSQL
                                AND 
                                MONTH(date_production)=04
                                -- DATEPART(WEEK, date_production) = DATEPART(WEEK, GETDATE()) -- Minggu saat ini
                                -- WEEK(date_production, 1) = WEEK(CURDATE(), 1) -- Minggu saat ini
                """
    else:
        raise ValueError("Unsupported database vendor.")

    # List untuk menampung filter
    filters = []
 
     # Tambahkan filter berdasarkan parameter yang ada
    if category_mine:
            filters.append("category_mine = %s")
            params.append(category_mine)

    if sources_area:
            filters.append("sources_area = %s")
            params.append(sources_area)

    if vendors:
            filters.append("plan_productions.vendors = %s")
            params.append(vendors)

        # Gabungkan filter jika ada
    if filters:
            query += " AND " + " AND ".join(filters)

    # Menyelesaikan query
    query += """
                GROUP BY ref_material
        """


    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['ref_material','TopSoil', 'Soil_plan','OB','OB_plan','LGLO','LGLO_plan',
                                   'MGLO', 'MGLO_plan','HGLO','HGLO_plan','Waste','Waste_plan','MWS', 'MWS_plan','LGSO','LGSO_plan','MGSO','MGSO_plan',
                                   'HGSO', 'HGSO_plan','Quarry','Quarry_plan','Ballast','Ballast_plan','Biomass','Biomass_plan'])

        # Menghitung total dari kolom 
        actual_total = df[['TopSoil','OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']].sum()
        plan_total   = df[['Soil_plan','OB_plan','LGLO_plan','MGLO_plan','HGLO_plan','Waste_plan','MWS_plan', 
                         'LGSO_plan','MGSO_plan','HGSO_plan','Quarry_plan','Ballast_plan','Biomass_plan']].sum()


        x_data      = ['TopSoil', 'OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']
        actual_data = actual_total.tolist()
        plan_data   = plan_total.tolist()

        # actual_accumulated = [round(total, 2) for total in itertools.accumulate(actual_data)]
        # plan_accumulated   = [round(total, 2) for total in itertools.accumulate(plan_data)]


        response_data = {
            'x_data'   : x_data,
            'y_plan'   : plan_data,
            'y_actual' : actual_data,
            # 'plan_accumulated'  : plan_accumulated,
            # 'actual_accumulated': actual_accumulated,
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)


    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

