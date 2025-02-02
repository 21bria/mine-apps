from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections
import re,json
from django.utils.html import escape
from ....utils.db_utils import get_db_vendor
from ....utils.permissions import get_dynamic_permissions
 # Memanggil fungsi utility
db_vendor = get_db_vendor('sqms_db')

@login_required
def achievement_mral_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }

    return render(request, 'admin-mgoqa/achievement/achievement_mral.html',context)

@login_required
def stockpile_mral_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/achievement/stockpile_mral.html',context)

@login_required
def source_mral_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/achievement/source_mral.html',context)

@login_required
def to_stockpile_mral_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/achievement/source_stockpile_mral.html',context)

@login_required
def to_dome_mral_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/achievement/source_dome_mral.html',context)


# Fungsi untuk sanitasi input
def sanitize_input(value):
    if value is None:
        return None
    return escape(re.sub(r"[;'\"]", "", str(value)))


@login_required
def achievement_mral(request):
   
    # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    # sourceFilter   = request.GET.getlist('sourceFilter')
    sourceFilter = json.loads(request.GET.get('sourceFilter', '[]'))
    print("Initial Source Filter:", sourceFilter)  # Cek nilai awal dari sourceFilter
    areaFilter     = sanitize_input(request.GET.get('areaFilter'))
    pointFilter    = sanitize_input(request.GET.get('pointFilter'))

    # sanitize_input: Fungsi ini membersihkan karakter yang berpotensi menyebabkan SQL injection.

    # Filter list sourceFilter
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]

    print("Data Source ", sourceFilter)
    # print('Data Area ',areaFilter)

   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 1000
    offset = (page - 1) * per_page

    # Query untuk menghitung total data
    count_query = """
        SELECT COUNT(*) FROM details_mral
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
    if areaFilter:
        count_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        count_query += f" AND pile_id = '{pointFilter}'"

    # Hitung total data
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(count_query)
        total_data = cursor.fetchone()[0]

    # Query berdasarkan database
    if db_vendor == 'mysql':
        # Query untuk MySQL
        sql_query = f"""
                SELECT 
                    TRIM(stockpile) stockpile,
                    TRIM(pile_id) pile_id,
                    nama_material,
                    SUM(tonnage) AS total_ore,
                    SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                    SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                    SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                    SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                    CONCAT(ROUND((SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Ni,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Co,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe2O3,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Mgo,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS SiO2,
                    ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) / 
                    (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
                FROM details_mral
                WHERE stockpile <> 'Temp-Rompile_KM09'
        """
   
    elif db_vendor in ['mssql', 'microsoft']:
            # Query untuk SQL Server
        sql_query = f"""
                SELECT 
                    TRIM(stockpile) AS stockpile,
                    TRIM(pile_id) AS pile_id,
                    TRIM(nama_material) nama_material,
                    SUM(tonnage) AS total_ore,
                    SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                    SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                    SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                    SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                    CAST(ROUND((CAST(SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS FLOAT) / SUM(tonnage) * 100), 0) AS NVARCHAR) + '%' AS recovery,
                    COALESCE(CAST(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS Ni,
                    COALESCE(CAST(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS Co,
                    COALESCE(CAST(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS Fe2O3,
                    COALESCE(CAST(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS Fe,
                    COALESCE(CAST(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS Mgo,
                    COALESCE(CAST(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS SiO2,
                    ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) / 
                    (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
                FROM details_mral
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
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

    sql_query += " GROUP BY stockpile, pile_id, nama_material"

    # Query untuk mengambil data dengan pagination
    if db_vendor == 'mysql':
        # Query untuk MySQL
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
       
    elif db_vendor in ['mssql', 'microsoft']:
         # Query untuk SQL Server
        # Adding pagination (OFFSET-FETCH) SQL SERVER
        sql_query += f" ORDER BY stockpile, pile_id "  # You need to specify an ORDER BY for OFFSET-FETCH
        sql_query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"
    else:
        raise ValueError("Unsupported database vendor.")
    

    # Eksekusi query untuk mengambil data
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Hitung jika masih ada data untuk halaman berikutnya
    more_data = len(sql_data) == per_page

    # Hitung total halaman
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    grandTotalOre = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Fe2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []

    # Menghitung grand total dan product grade
    for row in sql_data:
            grandTotalOre += float(row['total_ore'])
            grandTotalIncomplete += float(row['incomplete'])
            grandTotalUnprepared += float(row['unprepared'])
            grandTotalUnRelease  += float(row['unreleased'])
            grandTotalRelease    += float(row['released'])

            # Hitung Product Grade
            data_Ni.append(row['released'] * float(row['Ni']))
            data_Co.append(row['released'] * float(row['Co']))
            data_Fe2O3.append(row['released'] * float(row['Fe2O3']))
            data_Fe.append(row['released'] * float(row['Fe']))
            data_Mgo.append(row['released'] * float(row['Mgo']))
            data_SiO2.append(row['released'] * float(row['SiO2']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'Ni'   : sum_product(data_Ni) / grandTotalRelease if grandTotalRelease != 0 else 0,
        'Co'   : sum_product(data_Co) / grandTotalRelease if grandTotalRelease != 0 else 0,
        'Fe2O3': sum_product(data_Fe2O3) / grandTotalRelease if grandTotalRelease != 0 else 0,
        'Fe'   : sum_product(data_Fe) / grandTotalRelease if grandTotalRelease != 0 else 0,
        'Mgo'  : sum_product(data_Mgo) / grandTotalRelease if grandTotalRelease != 0 else 0,
        'SiO2' : sum_product(data_SiO2) / grandTotalRelease if grandTotalRelease != 0 else 0
    }

    return JsonResponse({
        'data': sql_data,
        'grand_totals': {
            'total_ore'  : grandTotalOre,
            'incomplete' : grandTotalIncomplete,
            'unprepared' : grandTotalUnprepared,
            'unreleased' : grandTotalUnRelease,
            'released'   : grandTotalRelease
        },
        'sum_results': sumResults,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })


@login_required
def stockpile_mral(request):
    # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    # sourceFilter   = request.GET.getlist('sourceFilter')
    sourceFilter = json.loads(request.GET.get('sourceFilter', '[]'))

    areaFilter     = sanitize_input(request.GET.get('areaFilter'))
    pointFilter    = sanitize_input(request.GET.get('pointFilter'))

    # sanitize_input: Fungsi ini membersihkan karakter yang berpotensi menyebabkan SQL injection.

    # Filter list sourceFilter
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]

    print("Data Source ", sourceFilter)
    # print('Data Area ',areaFilter)

   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 1000
    offset = (page - 1) * per_page

    # Query untuk menghitung total data
    count_query = """
        SELECT COUNT(*) FROM details_mral
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
    if areaFilter:
        count_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        count_query += f" AND pile_id = '{pointFilter}'"

    # Hitung total data
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(count_query)
        total_data = cursor.fetchone()[0]

    # Query berdasarkan database
    if db_vendor == 'mysql':
    # Query untuk MySQL
        sql_query = f"""
                    SELECT 
                        stockpile,
                        nama_material,
                        SUM(tonnage) AS total_ore,
                        SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                        SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                        SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                        SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                        CONCAT(ROUND((SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                        COALESCE(FORMAT(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Ni,
                        COALESCE(FORMAT(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Co,
                        COALESCE(FORMAT(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe2O3,
                        COALESCE(FORMAT(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe,
                        COALESCE(FORMAT(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Mgo,
                        COALESCE(FORMAT(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS SiO2,
                        ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                        (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
                    FROM details_mral
                    WHERE stockpile <> 'Temp-Rompile_KM09'
                """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        sql_query = f"""
            SELECT 
                stockpile,
                nama_material,
                SUM(tonnage) AS total_ore,
                SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                CONCAT(ROUND((SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Ni,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Co,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Fe2O3,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Fe,
                COALESCE(FORMAT(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Mgo,
                COALESCE(FORMAT(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS SiO2,
                ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_mral
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
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

    sql_query += " GROUP BY stockpile, nama_material"

    # Query untuk mengambil data dengan pagination
    if db_vendor == 'mysql':
        # Query untuk MySQL
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
    elif db_vendor in ['mssql', 'microsoft']:
         # Query untuk SQL Server
        # Adding pagination (OFFSET-FETCH) SQL SERVER
        sql_query += f" ORDER BY stockpile, nama_material ASC"  # You need to specify an ORDER BY for OFFSET-FETCH
        sql_query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"
    else:
        raise ValueError("Unsupported database vendor.")

    # Eksekusi query untuk mengambil data
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Hitung jika masih ada data untuk halaman berikutnya
    more_data = len(sql_data) == per_page

    # Hitung total halaman
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    grandTotalOre = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Fe2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []

    # Menghitung grand total dan product grade
    for row in sql_data:
            grandTotalOre += float(row['total_ore'])
            grandTotalIncomplete += float(row['incomplete'])
            grandTotalUnprepared += float(row['unprepared'])
            grandTotalUnRelease  += float(row['unreleased'])
            grandTotalRelease    += float(row['released'])

            # Hitung Product Grade
            data_Ni.append(row['released'] * float(row['Ni']))
            data_Co.append(row['released'] * float(row['Co']))
            data_Fe2O3.append(row['released'] * float(row['Fe2O3']))
            data_Fe.append(row['released'] * float(row['Fe']))
            data_Mgo.append(row['released'] * float(row['Mgo']))
            data_SiO2.append(row['released'] * float(row['SiO2']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'Ni': round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Co': round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe2O3': round(sum_product(data_Fe2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe': round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Mgo': round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SiO2': round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
    }

    return JsonResponse({
        'data': sql_data,
        'grand_totals': {
            'total_ore'  : grandTotalOre,
            'incomplete' : grandTotalIncomplete,
            'unprepared' : grandTotalUnprepared,
            'unreleased' : grandTotalUnRelease,
            'released'   : grandTotalRelease
        },
        'sum_results': sumResults,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

@login_required
def source_mral(request):
    # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    sourceFilter   = json.loads(request.GET.get('sourceFilter', '[]'))

    # sanitize_input: Fungsi ini membersihkan karakter yang berpotensi menyebabkan SQL injection.

    # Filter list sourceFilter
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]

   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 1000
    offset = (page - 1) * per_page

    # Query untuk menghitung total data
    count_query = """
        SELECT COUNT(*) FROM details_mral
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

    # eksekusi query
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(count_query)
        total_data = cursor.fetchone()[0]

    # Query berdasarkan database
    if db_vendor == 'mysql':
    # Query untuk MySQL
        sql_query = f"""
            SELECT 
                prospect_area,
                nama_material,
                SUM(tonnage) AS total_ore,
                SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                CONCAT(ROUND((SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Ni,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Co,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe2O3,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe,
                COALESCE(FORMAT(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Mgo,
                COALESCE(FORMAT(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS SiO2,
                ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_mral
            WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        sql_query = f"""
            SELECT 
                prospect_area,
                nama_material,
                SUM(tonnage) AS total_ore,
                SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                CONCAT(ROUND((SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Ni,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Co,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Fe2O3,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Fe,
                COALESCE(FORMAT(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Mgo,
                COALESCE(FORMAT(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS SiO2,
                ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_mral
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

    sql_query += " GROUP BY prospect_area, nama_material"
    # Query untuk mengambil data dengan pagination
    if db_vendor == 'mysql':
        # Query untuk MySQL
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
       
    elif db_vendor in ['mssql', 'microsoft']:
         # Query untuk SQL Server
        # Adding pagination (OFFSET-FETCH) SQL SERVER
        sql_query += f" ORDER BY prospect_area,nama_material "  # You need to specify an ORDER BY for OFFSET-FETCH
        sql_query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"
    else:
        raise ValueError("Unsupported database vendor.")

    # Eksekusi query untuk mengambil data
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Hitung jika masih ada data untuk halaman berikutnya
    more_data = len(sql_data) == per_page

    # Hitung total halaman
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    grandTotalOre = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Fe2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []

    # Menghitung grand total dan product grade
    for row in sql_data:
            grandTotalOre += float(row['total_ore'])
            grandTotalIncomplete += float(row['incomplete'])
            grandTotalUnprepared += float(row['unprepared'])
            grandTotalUnRelease  += float(row['unreleased'])
            grandTotalRelease    += float(row['released'])

            # Hitung Product Grade
            data_Ni.append(row['released'] * float(row['Ni']))
            data_Co.append(row['released'] * float(row['Co']))
            data_Fe2O3.append(row['released'] * float(row['Fe2O3']))
            data_Fe.append(row['released'] * float(row['Fe']))
            data_Mgo.append(row['released'] * float(row['Mgo']))
            data_SiO2.append(row['released'] * float(row['SiO2']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'Ni': round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Co': round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe2O3': round(sum_product(data_Fe2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe': round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Mgo': round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SiO2': round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
    }

    return JsonResponse({
        'data': sql_data,
        'grand_totals': {
            'total_ore'  : grandTotalOre,
            'incomplete' : grandTotalIncomplete,
            'unprepared' : grandTotalUnprepared,
            'unreleased' : grandTotalUnRelease,
            'released'   : grandTotalRelease
        },
        'sum_results': sumResults,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

@login_required
def to_stockpile_mral(request):
    # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    sourceFilter   = json.loads(request.GET.get('sourceFilter', '[]'))
    areaFilter     = sanitize_input(request.GET.get('areaFilter'))
    pointFilter    = sanitize_input(request.GET.get('pointFilter'))

    # sanitize_input: Fungsi ini membersihkan karakter yang berpotensi menyebabkan SQL injection.

    # Filter list sourceFilter
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]

   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 1000
    offset = (page - 1) * per_page

    # Query untuk menghitung total data
    count_query = """
        SELECT COUNT(*) FROM details_mral
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
    if areaFilter:
        count_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        count_query += f" AND pile_id = '{pointFilter}'"

    # Hitung total data
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(count_query)
        total_data = cursor.fetchone()[0]

    # Query berdasarkan database
    if db_vendor == 'mysql':
    # Query untuk MySQL
        sql_query = f"""
            SELECT 
                prospect_area,
                stockpile,
                nama_material,
                SUM(tonnage) AS total_ore,
                SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                CONCAT(ROUND((SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Ni,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Co,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe2O3,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe,
                COALESCE(FORMAT(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Mgo,
                COALESCE(FORMAT(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS SiO2,
                ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_mral
            WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        sql_query = f"""
            SELECT 
                prospect_area,
                stockpile,
                nama_material,
                SUM(tonnage) AS total_ore,
                SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                CONCAT(ROUND((SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Ni,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Co,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Fe2O3,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Fe,
                COALESCE(FORMAT(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Mgo,
                COALESCE(FORMAT(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS SiO2,
                ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_mral
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
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

    sql_query += " GROUP BY prospect_area, stockpile, nama_material"

    # Query untuk mengambil data dengan pagination
    if db_vendor == 'mysql':
        # Query untuk MySQL
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
       
    elif db_vendor in ['mssql', 'microsoft']:
         # Query untuk SQL Server
        # Adding pagination (OFFSET-FETCH) SQL SERVER
        sql_query += f" ORDER BY prospect_area, stockpile,nama_material ASC "  # You need to specify an ORDER BY for OFFSET-FETCH
        sql_query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"
    else:
        raise ValueError("Unsupported database vendor.")
    
    # Eksekusi query untuk mengambil data
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Hitung jika masih ada data untuk halaman berikutnya
    more_data = len(sql_data) == per_page

    # Hitung total halaman
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    grandTotalOre = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Fe2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []

    # Menghitung grand total dan product grade
    for row in sql_data:
            grandTotalOre += float(row['total_ore'])
            grandTotalIncomplete += float(row['incomplete'])
            grandTotalUnprepared += float(row['unprepared'])
            grandTotalUnRelease  += float(row['unreleased'])
            grandTotalRelease    += float(row['released'])

            # Hitung Product Grade
            data_Ni.append(row['released'] * float(row['Ni']))
            data_Co.append(row['released'] * float(row['Co']))
            data_Fe2O3.append(row['released'] * float(row['Fe2O3']))
            data_Fe.append(row['released'] * float(row['Fe']))
            data_Mgo.append(row['released'] * float(row['Mgo']))
            data_SiO2.append(row['released'] * float(row['SiO2']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'Ni': round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Co': round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe2O3': round(sum_product(data_Fe2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe': round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Mgo': round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SiO2': round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
    }

    return JsonResponse({
        'data': sql_data,
        'grand_totals': {
            'total_ore'  : grandTotalOre,
            'incomplete' : grandTotalIncomplete,
            'unprepared' : grandTotalUnprepared,
            'unreleased' : grandTotalUnRelease,
            'released'   : grandTotalRelease
        },
        'sum_results': sumResults,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

# @login_required
def to_dome_mral(request):
    # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    sourceFilter   = json.loads(request.GET.get('sourceFilter', '[]'))
    areaFilter     = sanitize_input(request.GET.get('areaFilter'))
    pointFilter    = sanitize_input(request.GET.get('pointFilter'))

    # Filter list sourceFilter
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]


   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    # Query untuk menghitung total data
    count_query = """
        SELECT COUNT(*) FROM details_mral
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
    if areaFilter:
        count_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        count_query += f" AND pile_id = '{pointFilter}'"

    # Hitung total data
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(count_query)
        total_data = cursor.fetchone()[0]

    # Query berdasarkan database
    if db_vendor == 'mysql':
    # Query untuk MySQL
        sql_query = f"""
            SELECT 
                prospect_area,
                pile_id,
                nama_material,
                SUM(tonnage) AS total_ore,
                SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                CONCAT(ROUND((SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Ni,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Co,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe2O3,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe,
                COALESCE(FORMAT(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Mgo,
                COALESCE(FORMAT(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS SiO2,
                ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_mral
            WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        sql_query = f"""
            SELECT 
                prospect_area,
                pile_id,
                nama_material,
                SUM(tonnage) AS total_ore,
                SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                CONCAT(ROUND((SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) / SUM(tonnage) * 100), 0), '%') AS recovery,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Ni,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Co,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Fe2O3,
                COALESCE(FORMAT(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Fe,
                COALESCE(FORMAT(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS Mgo,
                COALESCE(FORMAT(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 'N2'), '0') AS SiO2,
                ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_mral
            WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    else:
        raise ValueError("Unsupported database vendor.")

    # Menambahkan kondisi berdasarkan input
    if materialFilter:
        sql_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        sql_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        sql_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    elif bulanFilter and tahunFilter:
        sql_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
    elif tahunFilter:
        sql_query += f" AND YEAR(tgl_production) = {tahunFilter}"
    if sourceFilter:
        sql_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

   # Pengelompokan dan pagination
    sql_query += """
        GROUP BY prospect_area, pile_id, nama_material
        ORDER BY prospect_area, pile_id, nama_material ASC
    """

    # Menambahkan pagination (OFFSET-FETCH SQL Server)
    # sql_query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"

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

    # Hitung jika masih ada data untuk halaman berikutnya
    more_data = len(sql_data) == per_page

    # Hitung total halaman
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data': sql_data,
        'pagination': {
            'more'         : more_data,
            'total_pages'  : total_pages,
            'current_page' : page,
            'total_data'   : total_data
        }
    })