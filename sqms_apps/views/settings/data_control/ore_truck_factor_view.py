from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import JsonResponse
from ....models.ore_truck_factor_model import OreTruckFactor
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from ....utils.db_utils import get_db_vendor
from ....utils.permissions import get_dynamic_permissions
# Memanggil fungsi utility
db_vendor = get_db_vendor('sqms_db')

@login_required
def ore_factors_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/master/list-truck-factor.html',context)

class OreFactorsList(View):

    def post(self, request):
        data = self._datatables(request)
        return JsonResponse(data, safe=False)

    def _datatables(self, request):
        datatables = request.POST
        draw    = int(datatables.get('draw'))
        start   = int(datatables.get('start'))
        length  = int(datatables.get('length'))
        search  = datatables.get('search[value]')
        order_column = int(datatables.get('order[0][column]'))
        order_dir = datatables.get('order[0][dir]')

        sql_query = """
            SELECT ore_truck_factors.id, type_tf, materials.nama_material,
            density,bcm,ton,status
            FROM ore_truck_factors
            LEFT JOIN materials ON materials.id = ore_truck_factors.material
        """

        if search:
            sql_query += """
                WHERE ore_truck_factors.type_tf LIKE %s
                OR materials.nama_material LIKE %s
            """
        #  query dengan limit Mysql & MsSQL
        if db_vendor == 'mysql':
            sql_query += " ORDER BY materials.nama_material ASC LIMIT %s OFFSET %s"
        
        elif db_vendor in ['mssql', 'microsoft']:
             sql_query += """
                            ORDER BY materials.nama_material ASC
                            OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                        """
             
        else:
            raise ValueError("Unsupported database vendor.")

        with connections['sqms_db'].cursor() as cursor:
            # When search is provided, pass the correct parameters for search and pagination
            if search:
                cursor.execute(sql_query, ['%' + search + '%', '%' + search + '%', start, length])
            else:
                cursor.execute(sql_query, [start, length])  # Correct order: start, length
            result = cursor.fetchall()
    

        data_list = [
            {
            'id': row[0], 
             'type_tf': row[1], 
             'nama_material': row[2],
             'density': row[3],
             'bcm': row[4],
             'ton': row[5], 
             'status': row[6]
             }
               for row in result
        ]

        return {
            'draw': draw,
            'recordsTotal': len(data_list),
            'recordsFiltered': len(data_list),
            'data': data_list,
        }

@login_required        
@csrf_exempt
def get_ore_factors(request, id):
    allowed_groups = ['superadmin','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'GET':
        try:
            item = OreTruckFactor.objects.get(id=id)
            data = {
                'id'           : item.id,
                'type_tf'      : item.type_tf,
                'material'     : item.material, 
                'bcm'          : item.bcm,
                'density'      : item.density,
                'ton'          : item.ton,
                'reference_tf' : item.reference_tf,
                'status'       : item.status,
                'created_at'   : item.created_at
            }
            return JsonResponse(data)
        except OreTruckFactor.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_ore_factors(request):
    allowed_groups = ['superadmin','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'type_tf': ['required'],
                'material': ['required'],
                'ton': ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'type_tf.required' : 'Type Truck is required.',
                'material.required': 'Material is required.',
                'ton.required'     : 'Tonnage is required.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
                    elif rule.startswith('min_length'):
                        min_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) < min_length:
                            return JsonResponse({'error': custom_messages[f'{field}.min_length']}, status=400)
                    elif rule.startswith('max_length'):
                        max_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) > max_length:
                            return JsonResponse({'error': custom_messages[f'{field}.max_length']}, status=400)
                    elif rule == 'regex':
                        import re
                        pattern = re.compile(r'^[a-zA-Z0-9]*$')
                        if not pattern.match(request.POST.get(field, '')):
                            return JsonResponse({'error': custom_messages[f'{field}.regex']}, status=400)

                
            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():
                # Dapatkan data dari request
                type_tf      = request.POST.get('type_tf')
                material     = request.POST.get('material')
                bcm          = request.POST.get('bcm')
                density      = request.POST.get('density')
                ton          = request.POST.get('ton')
                reference_tf = request.POST.get('reference_tf')

                if OreTruckFactor.objects.filter(reference_tf =reference_tf).exists():
                        return JsonResponse({'message': f'{reference_tf} : already exists.'}, status=422)
    
                # Simpan data baru
                OreTruckFactor.objects.create(
                    type_tf=type_tf,
                    material=int(material),
                    bcm=float(bcm),
                    density=float(density),
                    ton=float(ton),
                    reference_tf=reference_tf,
                    status=1,
                    # id_user=request.user.id  # Sesuaikan dengan cara Anda mendapatkan user ID
                )

            # Kembalikan respons JSON sukses
            return JsonResponse({'success': True, 'message': 'Data berhasil disimpan.'})

        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)

@login_required
def update_ore_factors(request, id):
    allowed_groups = ['superadmin','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'POST':
        try:
            # validasi
            rules = {
                'type_tf': ['required'],
                'material': ['required'],
                'ton': ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'type_tf.required' : 'Type Truck is required.',
                'material.required': 'Material is required.',
                'ton.required'     : 'Tonnage is required.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
                    elif rule.startswith('min_length'):
                        min_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) < min_length:
                            return JsonResponse({'error': custom_messages[f'{field}.min_length']}, status=400)
                    elif rule.startswith('max_length'):
                        max_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) > max_length:
                            return JsonResponse({'error': custom_messages[f'{field}.max_length']}, status=400)
                    elif rule == 'regex':
                        import re
                        pattern = re.compile(r'^[a-zA-Z0-9]*$')
                        if not pattern.match(request.POST.get(field, '')):
                            return JsonResponse({'error': custom_messages[f'{field}.regex']}, status=400)

            reference_tf = request.POST.get('reference_tf')
            if OreTruckFactor.objects.exclude(id=id).filter(reference_tf=reference_tf).exists():
                return JsonResponse({'error': f'Data {reference_tf} already exists.'}, status=400)

            # Dapatkan data yang akan diupdate berdasarkan ID
            data = OreTruckFactor.objects.get(id=id)

            # Lakukan update data dengan nilai baru
            data.type_tf=request.POST.get('type_tf')
            data.material=request.POST.get('material')
            data.density=request.POST.get('density')
            data.bcm=request.POST.get('bcm')
            data.ton=request.POST.get('ton')
            data.reference_tf=reference_tf
           

            # Simpan perubahan ke dalam database
            data.save()

            # Kembalikan respons JSON sukses
            return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

        except OreTruckFactor.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)
     
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)    
   
@login_required
def delete_ore_factors(request):
    allowed_groups = ['superadmin','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = OreTruckFactor.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
