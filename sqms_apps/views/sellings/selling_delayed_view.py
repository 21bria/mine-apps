from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.selling_data_model import SellingProductions
from ...models.selling_details_view_model import SellingDetailsView
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.views.decorators.http import require_http_methods
from django.db import  IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime
from django.utils import timezone
from ...utils.permissions import get_dynamic_permissions

# Fungsi untuk mengubah string menjadi datetime dengan aman
def parse_datetime(datetime_str):
    if datetime_str:
        try:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None
    return None


@login_required
def sale_delayed_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions'   : permissions,
    }
    return render(request, 'admin-mgoqa/selling/list-selling-delayed.html',context)

class getDelayed(View):

    def post(self, request):
        # Ambil semua data invoice yang valid
        data_ore = self._datatables(request)
        return JsonResponse(data_ore, safe=False)

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

        # Gunakan fungsi get_joined_data
        data = SellingDetailsView.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(sampling_area__icontains=search) |
                Q(sampling_point__icontains=search) |
                Q(nama_material__icontains=search) |
                Q(delivery_order__icontains=search) |
                Q(haulage_code__icontains=search) |
                Q(factory_stock__icontains=search)
            )
       
        # Filter berdasarkan parameter dari request
        from_date       = request.POST.get('from_date')
        to_date         = request.POST.get('to_date')
        areaFilter      = request.POST.get('areaFilter')
        pointFilter     = request.POST.get('pointFilter')
        factoriesFilter = request.POST.get('factoriesFilter')
        productFilter   = request.POST.get('productFilter')

        if from_date and to_date:
            data = data.filter(timbang_isi__range=[from_date, to_date])

        if areaFilter:
            data = data.filter(sampling_area=areaFilter)

        if pointFilter:
            data = data.filter(sampling_point=pointFilter)

        if factoriesFilter:
            data = data.filter(factory_stock=factoriesFilter)

        if productFilter:
            data = data.filter(delivery_order=productFilter)
        
        data = data.filter(netto_ton=0)

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Menghitung jumlah total sebelum filter
        records_total = data.count()

        # Menerapkan pagination
        paginator   = Paginator(data, length)
        total_pages = paginator.num_pages

        # Menghitung jumlah total setelah filter
        total_records_filtered = paginator.count

        # Atur paginator
        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"             : item.id,
                "tgl_hauling"    : item.tgl_hauling,
                "shift"          : item.shift,
                "sampling_area"  : item.sampling_area,
                "sampling_point" : item.sampling_point,
                "nama_material"  : item.nama_material,
                "batch"          : item.batch,
                "new_scci_sub"   : item.new_scci_sub,
                "new_awk_sub"    : item.new_awk_sub,
                "date_wb"        : item.date_wb,
                "fill_weigth_f"  : item.fill_weigth_f,
                "empety_weigth_f": item.empety_weigth_f,
                "netto_kg"       : item.netto_kg,
                "netto_ton"      : item.netto_ton,
                "tonnage"        : item.tonnage,
                "delivery_order" : item.delivery_order,
                "factory_stock"  : item.factory_stock,
                "haulage_code"   : item.haulage_code,
                "tonnage"        : item.tonnage
                
            } for item in object_list
        ]

        return {
            'draw'           : draw,
            'recordsTotal'   : records_total,
            'recordsFiltered': total_records_filtered,
            'data'           : data,
            'start'          : start,
            'length'         : length,
            'totalPages'     : total_pages,
        }

@login_required
@require_http_methods(["POST"])
def update_sale(request, id):
    try:
        # Aturan validasi
        rules = {
            'tgl_hauling'        : ['required'],
            'id_stockpile'       : ['required'],
            'id_pile'            : ['required'],
            'id_material'        : ['required'], 
            'timbang_kosong'     : ['required'], 
            'timbang_isi'        : ['required'], 
            'id_factory'         : ['required'],
            'delivery_order'     : ['required'],
            'type'               : ['required'],
            'batch_g'            : ['required'],
            'new_scci_sub'       : ['required'],
            'new_awk_sub'        : ['required'],
            'kode_batch_g'       : ['required'],
            'new_kode_batch_scci': ['required'],
            'new_kode_batch_awk' : ['required'],
            'new_batch_awk_pulp' : ['required']
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
            'tgl_hauling.required'   : 'Date harus diisi.',
            'id_stockpile.required'  : 'Stockpile harus diisi.',
            'id_pile.required'       : 'Dome harus diisi.',
            'id_material.required'   : 'Material harus diisi.',
            'timbang_kosong.required': 'Waktu timbang kosong.',
            'timbang_isi.required'   : 'Waktu timbang isi.',
            'id_factory.required'    : 'Factry harus diisi.',
            'delivery_order.required': 'Code harus diisi.',
            'type.required'          : 'Type harus diisi.',
            'batch_g.required'       : 'Sublot Group harus diisi.', 
            'new_scci_sub.required'  : 'Sublot SCCI harus diisi.', 
            'new_awk_sub.required'   : 'Sublot AWK harus diisi.', 
            'kode_batch_g.required'       : 'Relation Group !!.', 
            'new_kode_batch_scci.required': 'Relation SCCI !!.', 
            'new_kode_batch_awk.required' : 'Relation AWK !!.', 
            'new_batch_awk_pulp.required' : 'Relation PULP !!.', 

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

        # Gabungkan nilai-nilai kolom menjadi kode batch
        type              = request.POST.get('type')
        id_material       = request.POST.get('id_material')
        id_stockpile      = request.POST.get('id_stockpile')
        id_pile           = request.POST.get('id_pile')
        KodeBatch         = f"{type}{id_material}{id_stockpile}{id_pile}"
        
        tgl_hauling    = request.POST.get('tgl_hauling')
        if tgl_hauling:
            date_obj = datetime.strptime(tgl_hauling, '%Y-%m-%d') 
            left_date = date_obj.day
        else:
            left_date = None 

        empety_weigth_f = request.POST.get('empety_weigth_f')
        fill_weigth_f   = request.POST.get('fill_weigth_f')

        # Konversi nilai yang diambil menjadi float
        empety_weigth_f = float(empety_weigth_f) if empety_weigth_f else 0.0
        fill_weigth_f   = float(fill_weigth_f) if fill_weigth_f else 0.0
        # Hitung netto_weigth_f 
        netto_weigth_f = fill_weigth_f - empety_weigth_f

        timbang_kosong  = request.POST.get('timbang_kosong')
        timbang_isi     = request.POST.get('timbang_isi')

        # Dapatkan data yang akan diupdate berdasarkan ID
        data = SellingProductions.objects.get(id=id)

        # Lakukan update data dengan nilai baru
        data.tgl_hauling     = tgl_hauling
        data.shift           = request.POST.get('shift')
        data.id_stockpile    = id_stockpile
        data.id_pile         = id_pile
        data.id_material     = id_material 
        data.id_factory      = request.POST.get('id_factory')
        data.empety_weigth_f = empety_weigth_f
        data.fill_weigth_f   = fill_weigth_f
        data.netto_weigth_f  = netto_weigth_f
        data.timbang_kosong  = timezone.make_aware(datetime.strptime(timbang_kosong, '%Y-%m-%d %H:%M:%S'), timezone=timezone.utc)
        data.timbang_isi     = timezone.make_aware(datetime.strptime(timbang_isi, '%Y-%m-%d %H:%M:%S'), timezone=timezone.utc)
        data.delivery_order  = request.POST.get('delivery_order')
        data.kode_batch      = KodeBatch
        data.left_date       = left_date
        data.remarks         = request.POST.get('remarks')
        data.batch_g         = request.POST.get('batch_g')
        data.new_scci_sub    = request.POST.get('new_scci_sub')
        data.new_awk_sub     = request.POST.get('new_awk_sub')
        data.kode_batch_g    = request.POST.get('kode_batch_g')
        data.new_kode_batch_scci= request.POST.get('new_kode_batch_scci')
        data.new_kode_batch_awk = request.POST.get('new_kode_batch_awk')
        data.new_batch_awk_pulp = request.POST.get('new_batch_awk_pulp')
        # data.id_user = request.POST.get('id_user')

        # Simpan perubahan ke dalam database
        data.save()

        # Kembalikan respons JSON sukses
        return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

    except SellingProductions.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

