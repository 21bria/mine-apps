from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections, DatabaseError
from django.utils.html import escape
import json,re
from ....utils.permissions import get_dynamic_permissions

# Fungsi untuk sanitasi input
def sanitize_input(value):
    if value is None:
        return None
    return escape(re.sub(r"[;'\"]", "", str(value)))

@login_required
def splitRange_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/selling/list-selling-split-range.html',context)

def splitSamples_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/selling/split-samples/list-samples-split.html',context)

@login_required
def rangeSplitAWK(request):
    delivery_order = request.GET.get('delivery_order')
    startDate      = request.GET.get('startDate')
    endDate        = request.GET.get('endDate')
    bulanFilter    = request.GET.get('bulanFilter')
    tahunFilter    = request.GET.get('tahunFilter')
    materialFilter = request.GET.get('materialFilter')

    sql_query = """
            SELECT 
                    delivery_order,
                    sale_adjust,
                    SUM(netto_ton) AS tonnage,
                    COALESCE(FORMAT(SUM(netto_ton * ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND ni  IS NOT NULL THEN netto_ton ELSE 0 END), 'N2'), '0') AS Ni,
                    COALESCE(FORMAT(SUM(netto_ton * co) / SUM(CASE WHEN sample_number  IS NOT NULL AND co  IS NOT NULL THEN netto_ton ELSE 0 END), 'N2'), '0') AS Co,
                    COALESCE(FORMAT(SUM(netto_ton * fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND fe  IS NOT NULL THEN netto_ton ELSE 0 END), 'N2'), '0') AS Fe,
                    COALESCE(FORMAT(SUM(netto_ton * mgo) / SUM(CASE WHEN sample_number  IS NOT NULL AND mgo  IS NOT NULL THEN netto_ton ELSE 0 END), 'N2'), '0') AS MgO,
                    COALESCE(FORMAT(SUM(netto_ton * sio2) / SUM(CASE WHEN sample_number  IS NOT NULL AND sio2  IS NOT NULL THEN netto_ton ELSE 0 END), 'N2'), '0') AS SiO2
            FROM
            details_selling_awk
            WHERE awk_order='YES'
        """

    
    if delivery_order:
        sql_query += f" AND delivery_order = '{delivery_order}'"

    if materialFilter:
        sql_query += f" AND sale_adjust = '{materialFilter}'"    

    if startDate and endDate:
        sql_query += f" AND date_wb BETWEEN '{startDate}' AND '{endDate}'"

    if bulanFilter and tahunFilter:
        sql_query += f" AND MONTH(date_wb) = {bulanFilter} AND YEAR(date_wb) = {tahunFilter}"

    if tahunFilter:
        sql_query += f" AND YEAR(date_wb) = {tahunFilter}"
    

    sql_query += """
            GROUP BY delivery_order,sale_adjust
            ORDER BY delivery_order ASC
        """

    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    # print(data)  # Cetak hasil query
    return JsonResponse({'data': sql_data})

@login_required
def rangeSplitPulpAWK(request):
    delivery_order = request.GET.get('delivery_order')
    startDate      = request.GET.get('startDate')
    endDate        = request.GET.get('endDate')
    bulanFilter    = request.GET.get('bulanFilter')
    tahunFilter    = request.GET.get('tahunFilter')
    materialFilter = request.GET.get('materialFilter')

    sql_query = """
            SELECT 
                    delivery_order,
                    sale_adjust,
                    SUM(netto_ton) AS tonnage,
                    COALESCE(FORMAT(SUM(netto_ton * ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND ni  IS NOT NULL THEN netto_ton ELSE 0 END), 'N2'), '0') AS Ni,
                    COALESCE(FORMAT(SUM(netto_ton * co) / SUM(CASE WHEN sample_number  IS NOT NULL AND co  IS NOT NULL THEN netto_ton ELSE 0 END), 'N2'), '0') AS Co,
                    COALESCE(FORMAT(SUM(netto_ton * fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND fe  IS NOT NULL THEN netto_ton ELSE 0 END), 'N2'), '0') AS Fe,
                    COALESCE(FORMAT(SUM(netto_ton * mgo) / SUM(CASE WHEN sample_number  IS NOT NULL AND mgo  IS NOT NULL THEN netto_ton ELSE 0 END), 'N2'), '0') AS MgO,
                    COALESCE(FORMAT(SUM(netto_ton * sio2) / SUM(CASE WHEN sample_number  IS NOT NULL AND sio2  IS NOT NULL THEN netto_ton ELSE 0 END), 'N2'), '0') AS SiO2
            FROM
            details_selling_awk_pulp
            WHERE awk_order='YES'
        """
    
    if delivery_order:
        sql_query += f" AND delivery_order = '{delivery_order}'"

    if materialFilter:
        sql_query += f" AND sale_adjust = '{materialFilter}'"    

    if startDate and endDate:
        sql_query += f" AND date_wb BETWEEN '{startDate}' AND '{endDate}'"

    if bulanFilter and tahunFilter:
        sql_query += f" AND MONTH(date_wb) = {bulanFilter} AND YEAR(date_wb) = {tahunFilter}"

    if tahunFilter:
        sql_query += f" AND YEAR(date_wb) = {tahunFilter}"

    sql_query += """
            GROUP BY delivery_order,sale_adjust
            ORDER BY delivery_order ASC
        """

    # with connection.cursor() as cursor:
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    # print(data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})

@login_required
def rangeOfficialAwk(request):
    materialFilter = request.GET.get('materialFilter')
    startDate      = request.GET.get('startDate')
    endDate        = request.GET.get('endDate')
    bulanFilter    = request.GET.get('bulanFilter')
    tahunFilter    = request.GET.get('tahunFilter')

    sql_query = """
            SELECT 
                DISTINCT details_selling_awk.delivery_order,
                selling_official_surveyor_awk.product_code,
                selling_official_surveyor_awk.so_number,
                COALESCE(selling_official_surveyor_awk.tonnage,'0') as tonnage,
                COALESCE(selling_official_surveyor_awk.ni,'0') as ni,
                COALESCE(selling_official_surveyor_awk.co,'0') as co,
                COALESCE(selling_official_surveyor_awk.al2o3,'0')as al2o3,
                COALESCE(selling_official_surveyor_awk.fe,'0') as fe,
                COALESCE(selling_official_surveyor_awk.mgo,'0') as mgo,
                COALESCE(selling_official_surveyor_awk.sio2,'0') as sio2,
                COALESCE(selling_official_surveyor_awk.mc,'0') as mc
            FROM 
                selling_official_surveyor_awk          
            LEFT JOIN  
                details_selling_awk ON details_selling_awk.delivery_order = selling_official_surveyor_awk.product_code
        """

    if materialFilter:
        sql_query += f" WHERE sale_adjust = '{materialFilter}'"
  
    if startDate and endDate:
        sql_query += f" AND date_wb BETWEEN '{startDate}' AND '{endDate}'"

    if bulanFilter and tahunFilter:
        sql_query += f" AND MONTH(date_wb) = {bulanFilter} AND YEAR(date_wb) = {tahunFilter}"

    if tahunFilter:
        sql_query += f" AND YEAR(date_wb) = {tahunFilter}"

    sql_query += """
            ORDER BY delivery_order ASC
        """

    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    # print(data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})

def mralSamplesSplit(request):
    typeFilter   = request.GET.get('typeFilter')
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    codeFilter   = json.loads(request.GET.get('codeFilter', '[]'))

    # Filter list codeFilter
    codeFilter = [sanitize_input(code) for code in codeFilter if code]

    sql_query = """
       SELECT 
            TRIM(t1.delivery_order)delivery_order,
            TRIM(t1.new_awk_sub) new_awk_sub,
            TRIM(t1.sample_number) sample_number,
            COALESCE(SUM(t1.netto_ton), 0) AS tonnage_split,              
            COALESCE(SUM(t1.netto_ton * t1.ni) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS ni_split,
            COALESCE(SUM(t1.netto_ton * t1.co) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.co IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS co_split,
            COALESCE(SUM(t1.netto_ton * t1.fe) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS fe_split,
            COALESCE(SUM(t1.netto_ton * t1.mgo) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS mgo_split,
            COALESCE(SUM(t1.netto_ton * t1.sio2) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sio2 IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS sio2_split,
            COALESCE(t2.tonnage_pulp, 0) AS tonnage_pulp,
            COALESCE(t2.ni, 0) AS ni_pulp,
            COALESCE(t2.co, 0) AS co_pulp,
            COALESCE(t2.fe, 0) AS fe_pulp,
            COALESCE(t2.mgo, 0) AS mgo_pulp,
            COALESCE(t2.sio2, 0) AS sio2_pulp
        FROM details_selling_awk_mral AS t1
        LEFT JOIN (
            SELECT 
                delivery_order,
                new_awk_sub,
                sample_number,
                COALESCE(SUM(netto_ton), 0) AS tonnage_pulp,
                COALESCE(SUM(netto_ton * ni) / SUM(CASE WHEN sample_number IS NOT NULL AND ni IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS ni,
                COALESCE(SUM(netto_ton * co) / SUM(CASE WHEN sample_number IS NOT NULL AND co IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS co,
                COALESCE(SUM(netto_ton * fe) / SUM(CASE WHEN sample_number IS NOT NULL AND fe IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS fe,
                COALESCE(SUM(netto_ton * mgo) / SUM(CASE WHEN sample_number IS NOT NULL AND mgo IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS mgo,
                COALESCE(SUM(netto_ton * sio2) / SUM(CASE WHEN sample_number IS NOT NULL AND sio2 IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS sio2
            FROM details_selling_awk_pulp_mral
            GROUP BY delivery_order,new_awk_sub,sample_number) AS t2 ON t1.delivery_order = t2.delivery_order AND t1.new_awk_sub=t2.new_awk_sub
        WHERE 1=1
    """

     # **Filter pada query utama t1**
    params = []
    
    if typeFilter:
        sql_query += " AND t1.sale_adjust = %s"
        params.append(typeFilter)

    if startDate and endDate:
        sql_query += " AND t1.date_wb BETWEEN %s AND %s"
        params.extend([startDate, endDate])

    if codeFilter:
        placeholders = ', '.join(['%s'] * len(codeFilter))
        sql_query += f" AND t1.delivery_order IN ({placeholders})"
        params.extend(codeFilter)

    sql_query += """
        GROUP BY t1.delivery_order, t1.new_awk_sub, t1.sample_number, 
                 t2.tonnage_pulp, t2.ni, t2.co, t2.fe, t2.mgo, t2.sio2
        ORDER BY t1.delivery_order, t1.new_awk_sub ASC
    """

    # **Eksekusi Query**
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query, params)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    return JsonResponse({'data': sql_data})

def roaSamplesSplit(request):
    typeFilter  = request.GET.get('typeFilter')
    startDate   = request.GET.get('startDate')
    endDate     = request.GET.get('endDate')
    codeFilter  = json.loads(request.GET.get('codeFilter', '[]'))

    # Filter list codeFilter
    codeFilter = [sanitize_input(code) for code in codeFilter if code]

    sql_query = """
       SELECT 
            TRIM(t1.delivery_order)delivery_order,
            TRIM(t1.new_awk_sub) new_awk_sub,
            TRIM(t1.sample_number) sample_number,
            COALESCE(SUM(t1.netto_ton), 0) AS tonnage_split,
            COALESCE(SUM(t1.netto_ton * t1.ni) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS ni_split,
            COALESCE(SUM(t1.netto_ton * t1.co) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.co IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS co_split,
            COALESCE(SUM(t1.netto_ton * t1.fe) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS fe_split,
            COALESCE(SUM(t1.netto_ton * t1.al2o3) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.al2o3 IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS al2o3_split,
            COALESCE(SUM(t1.netto_ton * t1.mgo) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS mgo_split,
            COALESCE(SUM(t1.netto_ton * t1.sio2) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sio2 IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS sio2_split,
            COALESCE(t2.tonnage_pulp, 0) AS tonnage_pulp,
            COALESCE(t2.ni, 0) AS ni_pulp,
            COALESCE(t2.co, 0) AS co_pulp,
            COALESCE(t2.fe, 0) AS fe_pulp,
            COALESCE(t2.al2o3, 0) AS al2o3_pulp,
            COALESCE(t2.mgo, 0) AS mgo_pulp,
            COALESCE(t2.sio2, 0) AS sio2_pulp
        FROM details_selling_awk AS t1
        LEFT JOIN (
            SELECT 
                delivery_order,
                new_awk_sub,
                sample_number,
                COALESCE(SUM(netto_ton), 0) AS tonnage_pulp,
                COALESCE(SUM(netto_ton * ni) / SUM(CASE WHEN sample_number IS NOT NULL AND ni IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS ni,
                COALESCE(SUM(netto_ton * co) / SUM(CASE WHEN sample_number IS NOT NULL AND co IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS co,
                COALESCE(SUM(netto_ton * fe) / SUM(CASE WHEN sample_number IS NOT NULL AND fe IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS fe,
                COALESCE(SUM(netto_ton * al2o3) / SUM(CASE WHEN sample_number IS NOT NULL AND al2o3 IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS al2o3,
                COALESCE(SUM(netto_ton * mgo) / SUM(CASE WHEN sample_number IS NOT NULL AND mgo IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS mgo,
                COALESCE(SUM(netto_ton * sio2) / SUM(CASE WHEN sample_number IS NOT NULL AND sio2 IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS sio2
            FROM details_selling_awk_pulp
            GROUP BY delivery_order,new_awk_sub,sample_number) AS t2 ON t1.delivery_order = t2.delivery_order AND t1.new_awk_sub=t2.new_awk_sub
        WHERE 1=1
    """

     # **Filter pada query utama t1**
    params = []
    
    if typeFilter:
        sql_query += " AND t1.sale_adjust = %s"
        params.append(typeFilter)

    if startDate and endDate:
        sql_query += " AND t1.date_wb BETWEEN %s AND %s"
        params.extend([startDate, endDate])

    if codeFilter:
        placeholders = ', '.join(['%s'] * len(codeFilter))
        sql_query += f" AND t1.delivery_order IN ({placeholders})"
        params.extend(codeFilter)

    sql_query += """
        GROUP BY t1.delivery_order,t1.new_awk_sub,t1.sample_number, t2.tonnage_pulp,t1.ni,t2.ni, t2.co, t2.fe,t2.al2o3,t2.mgo, t2.sio2
        ORDER BY t1.delivery_order,t1.new_awk_sub ASC
    """

    # **Eksekusi Query**
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query, params)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
    
    return JsonResponse({'data': sql_data})

def rangeOfficiaSplit(request):
    typeFilter   = request.GET.get('materialFilter')
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    bulanFilter  = request.GET.get('bulanFilter')
    tahunFilter  = request.GET.get('tahunFilter')

    sql_query = """
        SELECT 
            TRIM(t1.delivery_order)delivery_order,
            COALESCE(SUM(t1.netto_ton), 0) AS tonnage_split,              
            COALESCE(SUM(t1.netto_ton * t1.ni) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS ni_split,
            COALESCE(SUM(t1.netto_ton * t1.co) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.co IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS co_split,
            COALESCE(SUM(t1.netto_ton * t1.fe) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS fe_split,
            COALESCE(SUM(t1.netto_ton * t1.al2o3) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.al2o3 IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS al2o3_split,
            COALESCE(SUM(t1.netto_ton * t1.mgo) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS mgo_split,
            COALESCE(SUM(t1.netto_ton * t1.sio2) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sio2 IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS sio2_split,
            COALESCE(t3.tonnage_pulp, 0) AS tonnage_pulp,
            COALESCE(t3.ni, 0) AS ni_pulp,
            COALESCE(t3.co, 0) AS co_pulp,
            COALESCE(t3.fe, 0) AS fe_pulp,
            COALESCE(t3.al2o3, 0) AS al2o3_pulp,
            COALESCE(t3.mgo, 0) AS mgo_pulp,
            COALESCE(t3.sio2, 0) AS sio2_pulp,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.ni, 0) AS ni_official,
            COALESCE(t2.co, 0) AS co_official, 
            COALESCE(t2.fe, 0) AS fe_official, 
            COALESCE(t2.al2o3, 0) AS al2o3_official,
            COALESCE(t2.mgo, 0) AS mgo_official,
            COALESCE(t2.sio2, 0) AS sio2_official
        FROM details_selling_awk AS t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(ni), 0) AS ni,
                COALESCE(SUM(co), 0) AS co,
                COALESCE(SUM(fe), 0) AS fe,
                COALESCE(SUM(al2o3), 0) AS al2o3,
                COALESCE(SUM(mgo), 0) AS mgo,
                COALESCE(SUM(sio2), 0) AS sio2,
                type_selling
            FROM selling_official_surveyor_awk
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.delivery_order = t2.product_code
        LEFT JOIN (
            SELECT 
                delivery_order,
                COALESCE(SUM(netto_ton), 0) AS tonnage_pulp,
                COALESCE(SUM(netto_ton * ni) / SUM(CASE WHEN sample_number IS NOT NULL AND ni IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS ni,
                COALESCE(SUM(netto_ton * co) / SUM(CASE WHEN sample_number IS NOT NULL AND co IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS co,
                COALESCE(SUM(netto_ton * fe) / SUM(CASE WHEN sample_number IS NOT NULL AND fe IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS fe,
                COALESCE(SUM(netto_ton * al2o3) / SUM(CASE WHEN sample_number IS NOT NULL AND al2o3 IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS al2o3,
                COALESCE(SUM(netto_ton * mgo) / SUM(CASE WHEN sample_number IS NOT NULL AND mgo IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS mgo,
                COALESCE(SUM(netto_ton * sio2) / SUM(CASE WHEN sample_number IS NOT NULL AND sio2 IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS sio2
            FROM details_selling_awk_pulp
            WHERE 1=1
    """

    # **Filter pada subquery t3**
    filters = []
    if startDate and endDate:
        filters.append(f"date_wb BETWEEN '{startDate}' AND '{endDate}'")
    if bulanFilter and tahunFilter:
        filters.append(f"MONTH(date_wb) = {bulanFilter} AND YEAR(date_wb) = {tahunFilter}")
    elif tahunFilter:
        filters.append(f"YEAR(date_wb) = {tahunFilter}")

    if filters:
        sql_query += " AND " + " AND ".join(filters)

    sql_query += " GROUP BY delivery_order ) AS t3 ON t1.delivery_order = t3.delivery_order WHERE 1=1"

    # **Filter pada query utama t1**
    filters = []
    if startDate and endDate:
        filters.append(f"t1.date_wb BETWEEN '{startDate}' AND '{endDate}'")
    if typeFilter:
        filters.append(f"t2.type_selling = '{typeFilter}'")
    if bulanFilter and tahunFilter:
        filters.append(f"MONTH(t1.date_wb) = {bulanFilter} AND YEAR(t1.date_wb) = {tahunFilter}")
    elif tahunFilter:
        filters.append(f"YEAR(t1.date_wb) = {tahunFilter}")

    if filters:
        sql_query += " AND " + " AND ".join(filters)

    sql_query += """
        GROUP BY t1.delivery_order, t3.tonnage_pulp, t2.tonnage_official,
         t3.ni, t2.ni,t3.co, t2.co,t3.fe, t2.fe,t3.al2o3, t2.al2o3,t3.mgo, t2.mgo,t3.sio2, t2.sio2
        ORDER BY t1.delivery_order ASC
    """

    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
    # print(sql_data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})
