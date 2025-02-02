from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections
from ....utils.permissions import get_dynamic_permissions


@login_required
def splitMralHpal_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/selling/list-selling-split-mral-hpal.html',context)

@login_required
def getSumSellingAWK(request):
    params = []
    delivery_order = request.GET.get('delivery_order')
    # delivery_order ='SCHY-00397'

    sql_query = """
            SELECT 
                    delivery_order,
                    new_awk_sub,
                    sample_number,
                    SUM(netto_ton) AS tonnage,
                    COALESCE(FORMAT(SUM(netto_ton * ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND ni  IS NOT NULL THEN netto_ton ELSE 0 END),'N2'),'0') AS Ni,
                    COALESCE(FORMAT(SUM(netto_ton * co) / SUM(CASE WHEN sample_number  IS NOT NULL AND co  IS NOT NULL THEN netto_ton ELSE 0 END),'N2'),'0') AS Co,
                    COALESCE(FORMAT(SUM(netto_ton * fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND fe  IS NOT NULL THEN netto_ton ELSE 0 END),'N2'),'0') AS Fe,
                    COALESCE(FORMAT(SUM(netto_ton * mgo) / SUM(CASE WHEN sample_number  IS NOT NULL AND mgo  IS NOT NULL THEN netto_ton ELSE 0 END),'N2'),'0') AS MgO,
                    COALESCE(FORMAT(SUM(netto_ton * sio2) / SUM(CASE WHEN sample_number  IS NOT NULL AND sio2  IS NOT NULL THEN netto_ton ELSE 0 END),'N2'),'0') AS SiO2
            FROM
            details_selling_awk_mral
            WHERE awk_order='YES'
        """

    
    if delivery_order:
        sql_query += " AND delivery_order = %s"
        params.append(delivery_order)

    sql_query += """
            GROUP BY delivery_order,new_awk_sub,sample_number
            ORDER BY delivery_order,new_awk_sub ASC
        """

    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query,params)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    # print(data)  # Cetak hasil query
    print(sql_query)
    print(delivery_order)
    return JsonResponse({'data': sql_data})

@login_required
def getSumPulpAWKMral(request):
    params = []
    delivery_order = request.GET.get('delivery_order')
    # delivery_order ='SCHY-00397'

    sql_query = """
            SELECT 
                    delivery_order,
                    new_awk_sub,
                    sample_number,
                    SUM(netto_ton) AS tonnage,
                    COALESCE(FORMAT(SUM(netto_ton * ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND ni  IS NOT NULL THEN netto_ton ELSE 0 END),'N2'),'0') AS Ni,
                    COALESCE(FORMAT(SUM(netto_ton * co) / SUM(CASE WHEN sample_number  IS NOT NULL AND co  IS NOT NULL THEN netto_ton ELSE 0 END),'N2'),'0') AS Co,
                    COALESCE(FORMAT(SUM(netto_ton * fe) / SUM(CASE WHEN sample_number  IS NOT NULL AND fe  IS NOT NULL THEN netto_ton ELSE 0 END),'N2'),'0') AS Fe,
                    COALESCE(FORMAT(SUM(netto_ton * mgo) / SUM(CASE WHEN sample_number  IS NOT NULL AND mgo  IS NOT NULL THEN netto_ton ELSE 0 END),'N2'),'0') AS MgO,
                    COALESCE(FORMAT(SUM(netto_ton * sio2) / SUM(CASE WHEN sample_number  IS NOT NULL AND sio2  IS NOT NULL THEN netto_ton ELSE 0 END),'N2'),'0') AS SiO2
            FROM
            details_selling_awk_pulp_mral
            WHERE awk_order='YES'
        """

    
    if delivery_order:
        sql_query += " AND delivery_order = %s"
        params.append(delivery_order)

    sql_query += """
            GROUP BY delivery_order,new_awk_sub,sample_number
            ORDER BY delivery_order,new_awk_sub ASC
        """

    # with connection.cursor() as cursor:
    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query,params)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    # print(data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})

@login_required
def getOfficialAwk(request):
    params = []
    delivery_order = request.GET.get('delivery_order')
    # delivery_order ='SCHY-00397'

    sql_query = """
            SELECT 
                product_code, so_number, tonnage,
                ni,co,fe,mgo,sio2,mc
            FROM
            selling_official_surveyor_awk
        """

    if delivery_order:
        sql_query += "WHERE product_code = %s"
        params.append(delivery_order)

    sql_query += """
            ORDER BY product_code ASC
        """

    with connections['sqms_db'].cursor() as cursor:
        cursor.execute(sql_query,params)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    # print(data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})

