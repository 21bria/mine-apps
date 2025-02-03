from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connections
from .....utils.permissions import get_dynamic_permissions

#List Data Tables:
class SamplesCrm(View):
    def post(self, request):
        data_ore = self._datatables(request)
        return JsonResponse(data_ore, safe=False)
    
    def _datatables(self, request):
        datatables = request.POST
        draw = int(datatables.get('draw'))
        start = int(datatables.get('start'))
        length = int(datatables.get('length'))
        search_value = datatables.get('search[value]')
        order_column_index = int(datatables.get('order[0][column]'))
        order_dir = datatables.get('order[0][dir]')

        sql_query = """
            SELECT * FROM oreas_certified
        """
        params = []

        if search_value:
            sql_query += " WHERE (oreas_name LIKE %s)"
            params.extend([f"%{search_value}%"])

        if order_dir == 'desc':
            sql_query += f" ORDER BY {order_column_index} DESC"
        else:
            sql_query += f" ORDER BY {order_column_index} ASC"

        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(sql_query, params)
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        total_records = len(sql_data)

        paginator   = Paginator(sql_data, length)
        total_pages = paginator.num_pages

        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = list(object_list)

        return {
            'draw'           : draw,
            'recordsTotal'   : total_records,
            'recordsFiltered': total_records,
            'data'           : data,
            'start'          : start,
            'length'         : length,
            'totalPages'     : total_pages,
        }

@login_required
def sampleCrmPage(request):
    allowed_groups = ['superadmin','admin-mgoqa','superintendent-mgoqa','manager-mgoqa','user-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        # Jika tidak memiliki izin, arahkan ke halaman error
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)
    
    permissions = get_dynamic_permissions(request.user)

    # Menambahkan tanggal awal dan akhir minggu ke konteks
    context = {
        'permissions' : permissions
    }
    return render(request, 'admin-mgoqa/report-qa/list-sample-crm.html')

