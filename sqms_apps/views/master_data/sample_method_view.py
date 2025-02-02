from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.sample_method_model import SampleMethod
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from ...utils.utils import clean_string
from ...utils.permissions import get_dynamic_permissions

@login_required
def sample_method_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/master/list-sample-method.html',context)


class SampleMethod_List(View):

    def post(self, request):
        # Ambil semua data invoice yang valid
        matehod = self._datatables(request)
        return JsonResponse(matehod, safe=False)

    def _datatables(self, request):
        datatables = request.POST
        # Ambil draw
        draw = int(datatables.get('draw'))
        # Ambil start
        start = int(datatables.get('start'))
        # Ambil length (limit)
        length = int(datatables.get('length'))
        # Ambil data search
        search = datatables.get('search[value]')
        # Ambil order column
        order_column = int(datatables.get('order[0][column]'))
        # Ambil order direction
        order_dir = datatables.get('order[0][dir]')

        # Set record total
        records_total = SampleMethod.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = SampleMethod.objects.all()

        if search:
            data = SampleMethod.objects.filter(
                Q(sample_method__icontains=search) |
                Q(keterangan__icontains=search)
            )
            records_total = data.count()
            records_filtered = records_total

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Atur paginator
        paginator = Paginator(data, length)

        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"            : item.id,
                "sample_method" : item.sample_method,
                "keterangan"    : item.keterangan,
                "status"        : item.status,
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }

@login_required
@csrf_exempt
def get_method(request, id):
    allowed_groups = ['superadmin','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'GET':
        try:
            job = SampleMethod.objects.get(id=id)
            data = {
                'id'            : job.id,
                'sample_method' : clean_string(job.sample_method), 
                'keterangan'    : clean_string(job.keterangan),
                'created_at'    : job.created_at
            }
            return JsonResponse(data)
        except SampleMethod.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_method(request):
    allowed_groups = ['superadmin','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'POST':
        sample_method = request.POST.get('sample_method')
        keterangan    = request.POST.get('keterangan')
        status        = 1

        try:
            new_job = SampleMethod.objects.create(
                    sample_method=sample_method,
                    keterangan=keterangan,
                    status=status)
            return JsonResponse({
                'status' : 'success',
                'message': 'Data berhasil disimpan.',
                'data': {
                    'id'            : new_job.id,
                    'sample_method' : new_job.sample_method,
                    'keterangan'    : new_job.keterangan,
                    'status'        : new_job.status,
                    'created_at'    : new_job.created_at
                }
            })
        except IntegrityError as e:
                return JsonResponse({'status': 'error', 'message': 'The data already exists'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)

@login_required
def update_method(request, id):
    allowed_groups = ['superadmin','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'POST':
        try:
            job = SampleMethod.objects.get(id=id)
            job.sample_method  = request.POST.get('sample_method')
            job.keterangan     = request.POST.get('keterangan')
            job.save()

            return JsonResponse({
                'id'            : job.id,
                'sample_method' : job.sample_method,
                'keterangan'    : job.keterangan,
                'created_at'    : job.created_at,
                'updated_at'    : job.updated_at
            })
        
        except SampleMethod.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        except IntegrityError as e:
            error_message = str(e)
            return JsonResponse({'error': 'The data already exists', 'message': error_message}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

@login_required
def delete_method(request):
    allowed_groups = ['superadmin']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            try:
                data = SampleMethod.objects.get(id=int(job_id))
                data.delete()
                return JsonResponse({'status': 'deleted'})
            except SampleMethod.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Data not found'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
