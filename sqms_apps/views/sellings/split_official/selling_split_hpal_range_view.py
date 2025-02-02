from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections, DatabaseError
from ....utils.permissions import get_dynamic_permissions

@login_required
def splitRange_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/selling/list-selling-split-range.html',context)

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

