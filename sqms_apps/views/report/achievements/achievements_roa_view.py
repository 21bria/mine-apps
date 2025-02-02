from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections
from datetime import datetime
from django.utils.html import escape
import re,json
from ....utils.db_utils import get_db_vendor
from ....utils.permissions import get_dynamic_permissions

 # Memanggil fungsi utility
db_vendor = get_db_vendor('sqms_db')

@login_required
def achievement_roa_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/achievement/achievement_roa.html',context)

@login_required
def stockpile_roa_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/achievement/stockpile_roa.html',context)

@login_required
def source_roa_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/achievement/source_roa.html',context)

@login_required
def to_stockpile_roa_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/achievement/source_stockpile_roa.html',context)

@login_required
def to_dome_roa_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/achievement/source_dome_roa.html',context)

# Fungsi untuk sanitasi input
def sanitize_input(value):
    if value is None:
        return None
    return escape(re.sub(r"[;'\"]", "", str(value)))


@login_required
def achievement_roa(request):
   # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    sourceFilter = json.loads(request.GET.get('sourceFilter', '[]'))
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
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
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
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
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
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

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

    # Hitung jika masih ada data untuk halaman berikutnya
    more_data = len(sql_data) == per_page

    # Hitung total halaman
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    grandTotalOre        = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Al2O3 = []
    data_CaO   = []
    data_Cr2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []
    data_MC    = []
    data_SM    = []

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
            data_Al2O3.append(row['released'] * float(row['Al2O3']))
            data_CaO.append(row['released'] * float(row['CaO']))
            data_Cr2O3.append(row['released'] * float(row['Cr2O3']))
            data_Fe.append(row['released'] * float(row['Fe']))
            data_Mgo.append(row['released'] * float(row['Mgo']))
            data_SiO2.append(row['released'] * float(row['SiO2']))
            data_MC.append(row['released'] * float(row['MC']))
            data_SM.append(row['released'] * float(row['SM']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'Ni'    : round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Co'    : round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Al2O3' : round(sum_product(data_Al2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'CaO'   : round(sum_product(data_CaO) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Cr2O3' : round(sum_product(data_Cr2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe'    : round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Mgo'   : round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SiO2'  : round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'MC'    : round(sum_product(data_MC) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SM'    : round(sum_product(data_SM) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
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
def stockpile_roa(request):
    # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    sourceFilter = json.loads(request.GET.get('sourceFilter', '[]'))
    areaFilter     = sanitize_input(request.GET.get('areaFilter'))
    pointFilter    = sanitize_input(request.GET.get('pointFilter'))

    # sanitize_input: Fungsi ini membersihkan karakter yang berpotensi menyebabkan SQL injection.

    # Filter list sourceFilter
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]

    # print("Data Source ", sourceFilter)
    # print('Data Area ',areaFilter)
    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 1000
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
        sql_query = """
            SELECT
                stockpile,
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
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_roa
            WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        sql_query = """
            SELECT
                stockpile,
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
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
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
        sql_query += f" ORDER BY stockpile,nama_material "  # You need to specify an ORDER BY for OFFSET-FETCH
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

    grandTotalOre        = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Al2O3 = []
    data_CaO   = []
    data_Cr2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []
    data_MC    = []
    data_SM    = []

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
            data_Al2O3.append(row['released'] * float(row['Al2O3']))
            data_CaO.append(row['released'] * float(row['CaO']))
            data_Cr2O3.append(row['released'] * float(row['Cr2O3']))
            data_Fe.append(row['released'] * float(row['Fe']))
            data_Mgo.append(row['released'] * float(row['Mgo']))
            data_SiO2.append(row['released'] * float(row['SiO2']))
            data_MC.append(row['released'] * float(row['MC']))
            data_SM.append(row['released'] * float(row['SM']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'Ni'    : round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Co'    : round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Al2O3' : round(sum_product(data_Al2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'CaO'   : round(sum_product(data_CaO) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Cr2O3' : round(sum_product(data_Cr2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe'    : round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Mgo'   : round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SiO2'  : round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'MC'    : round(sum_product(data_MC) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SM'    : round(sum_product(data_SM) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
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
def source_roa(request):
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

    # print("Data Source ", sourceFilter)
    # print('Data Area ',areaFilter)

   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 1000
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
        sql_query = """
            SELECT
                prospect_area,
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
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_roa
            WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        sql_query = """
            SELECT
                prospect_area,
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
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
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
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

    sql_query += " GROUP BY prospect_area, nama_material"

    # Query untuk mengambil data dengan pagination
    if db_vendor == 'mysql':
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
    elif db_vendor in ['mssql', 'microsoft']:
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

    grandTotalOre        = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Al2O3 = []
    data_CaO   = []
    data_Cr2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []
    data_MC    = []
    data_SM    = []

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
            data_Al2O3.append(row['released'] * float(row['Al2O3']))
            data_CaO.append(row['released'] * float(row['CaO']))
            data_Cr2O3.append(row['released'] * float(row['Cr2O3']))
            data_Fe.append(row['released'] * float(row['Fe']))
            data_Mgo.append(row['released'] * float(row['Mgo']))
            data_SiO2.append(row['released'] * float(row['SiO2']))
            data_MC.append(row['released'] * float(row['MC']))
            data_SM.append(row['released'] * float(row['SM']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'Ni'    : round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Co'    : round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Al2O3' : round(sum_product(data_Al2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'CaO'   : round(sum_product(data_CaO) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Cr2O3' : round(sum_product(data_Cr2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe'    : round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Mgo'   : round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SiO2'  : round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'MC'    : round(sum_product(data_MC) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SM'    : round(sum_product(data_SM) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
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
def to_stockpile_roa(request):
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
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]

   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 1000
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
        sql_query = """
            SELECT
                prospect_area,
                stockpile,
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
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_roa
            WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        sql_query = """
            SELECT
                prospect_area,
                stockpile,
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
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
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
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

    sql_query += " GROUP BY prospect_area,stockpile, nama_material"

    # Query untuk mengambil data dengan pagination
    if db_vendor == 'mysql':
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
       
    elif db_vendor in ['mssql', 'microsoft']:
        # Adding pagination (OFFSET-FETCH) SQL SERVER
        sql_query += f" ORDER BY prospect_area,stockpile "  # You need to specify an ORDER BY for OFFSET-FETCH
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

    grandTotalOre        = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Al2O3 = []
    data_CaO   = []
    data_Cr2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []
    data_MC    = []
    data_SM    = []

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
            data_Al2O3.append(row['released'] * float(row['Al2O3']))
            data_CaO.append(row['released'] * float(row['CaO']))
            data_Cr2O3.append(row['released'] * float(row['Cr2O3']))
            data_Fe.append(row['released'] * float(row['Fe']))
            data_Mgo.append(row['released'] * float(row['Mgo']))
            data_SiO2.append(row['released'] * float(row['SiO2']))
            data_MC.append(row['released'] * float(row['MC']))
            data_SM.append(row['released'] * float(row['SM']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'Ni'    : round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Co'    : round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Al2O3' : round(sum_product(data_Al2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'CaO'   : round(sum_product(data_CaO) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Cr2O3' : round(sum_product(data_Cr2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe'    : round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Mgo'   : round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SiO2'  : round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'MC'    : round(sum_product(data_MC) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SM'    : round(sum_product(data_SM) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
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
        'pagination' : {
            'more': more_data,
            'total_pages' : total_pages,
            'current_page': page,
            'total_data'  : total_data
        }
    })

@login_required
def to_dome_roa(request):
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
    per_page = 1000
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
        sql_query = """
            SELECT
                prospect_area,
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
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_roa
            WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        sql_query = """
            SELECT
                prospect_area,
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
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
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
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

    sql_query += " GROUP BY prospect_area, pile_id, nama_material"

    # Query untuk mengambil data dengan pagination
    if db_vendor == 'mysql':
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
       
    elif db_vendor in ['mssql', 'microsoft']:
        # Adding pagination (OFFSET-FETCH) SQL SERVER
        sql_query += f" ORDER BY prospect_area, pile_id,nama_material ASC "  # You need to specify an ORDER BY for OFFSET-FETCH
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

    grandTotalOre        = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Al2O3 = []
    data_CaO   = []
    data_Cr2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []
    data_MC    = []
    data_SM    = []

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
            data_Al2O3.append(row['released'] * float(row['Al2O3']))
            data_CaO.append(row['released'] * float(row['CaO']))
            data_Cr2O3.append(row['released'] * float(row['Cr2O3']))
            data_Fe.append(row['released'] * float(row['Fe']))
            data_Mgo.append(row['released'] * float(row['Mgo']))
            data_SiO2.append(row['released'] * float(row['SiO2']))
            data_MC.append(row['released'] * float(row['MC']))
            data_SM.append(row['released'] * float(row['SM']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'Ni'    : round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Co'    : round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Al2O3' : round(sum_product(data_Al2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'CaO'   : round(sum_product(data_CaO) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Cr2O3' : round(sum_product(data_Cr2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe'    : round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Mgo'   : round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SiO2'  : round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'MC'    : round(sum_product(data_MC) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'SM'    : round(sum_product(data_SM) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
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
        'pagination' : {
            'more'        : more_data,
            'total_pages' : total_pages,
            'current_page': page,
            'total_data'  : total_data
        }
    })
