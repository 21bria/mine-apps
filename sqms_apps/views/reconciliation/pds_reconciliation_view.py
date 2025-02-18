from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View
from ...models.production_reconciliation_model import productionReconciliation
from ...models.mine_productions_model import mineProductionsView
from ...models.ore_production_model import OreProductionsView
from django.core.cache import cache
from datetime import datetime
from django.utils.timezone import now as timezone_now
from django.db.models import Sum
from collections import defaultdict
from ...encrypt_view import  decrypt_date
from ...utils.permissions import get_dynamic_permissions

class viewReconciliationPds(View):
    def post(self, request):
        data = self._datatables(request)
        return JsonResponse(data, safe=False)

    def _datatables(self, request):
        datatables   = request.POST
        draw         = int(datatables.get('draw'))
        start        = int(datatables.get('start'))
        length       = int(datatables.get('length'))
        search       = datatables.get('search[value]')
        order_dir    = datatables.get('order[0][dir]')

        # Filter parameters
        startDate = request.POST.get('startDate')
        endDate   = request.POST.get('endDate')

        # Generate unique cache key based on filters
        cache_key      = f'reconciliation_data_{startDate}_{endDate}'
        cache_time_key = f'reconciliation_cache_time_{startDate}_{endDate}'
        records        = cache.get(cache_key)

        if records is None:
            # Fetch data from database
            records = productionReconciliation.objects.values(
                'production_date',
                'status_gc',
                'gc_status',
                'mining_status',
                'status_mining'
            ).order_by('-production_date')

            # Apply filters if provided
            if startDate and endDate:
                records = records.filter(production_date__range=[startDate, endDate])

            # Cache the filtered data
            cache.set(cache_key, list(records), timeout=60)  # Cache for 1 minute
            cache.set(cache_time_key, timezone_now(), timeout=60)

        records_total = len(records)

        # Apply search filter
        if search:
            records = [r for r in records if (
                search.lower() in r['gc_status'].lower() or
                search.lower() in r['status_mining'].lower()
            )]

        records_filtered = len(records)

        # Sorting always based on 'production_date'
        records = sorted(records, key=lambda x: x['production_date'], reverse=(order_dir == 'desc'))

        # Pagination
        paginated_records = records[start:start + length]

        data = [
            {
                "production_date" : item['production_date'],
                "status_gc"       : item['status_gc'],
                "gc_status"       : item['gc_status'],
                "mining_status"   : item['mining_status'],
                "status_mining"   : item['status_mining'],
            } for item in paginated_records
        ]

        return {
            'draw'           : draw,
            'recordsTotal'   : records_total,
            'recordsFiltered': records_filtered,
            'data'           : data
        }
    
# encrypted
def recon_gc_date(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Metode permintaan tidak valid. Gunakan GET.'}, status=405)

    try:
        encrypted_date = request.GET.get('filter_date')
        # Tentukan tanggal produksi yang ingin difilter

        # Dekripsi filter_date yang dienkripsi
        filter_date = decrypt_date(encrypted_date)

        # Query untuk data produksi GC dengan filter tanggal dan urutan
        gc_data = OreProductionsView.objects.filter(tgl_production=filter_date) \
            .values('tgl_production', 'prospect_area', 'shift', 'nama_material', 'ore_class') \
            .annotate(
                gc_total_ritase  = Sum('ritase'),
                gc_total_tonnage = Sum('tonnage')
            ) \
            .order_by('tgl_production', 'prospect_area', 'shift', 'nama_material','ore_class')

        # Query untuk data produksi Mining dengan filter tanggal dan urutan
        mining_data = mineProductionsView.objects.filter(date_production=filter_date) \
            .values('date_production', 'loading_point', 'shift', 'nama_material') \
            .annotate(
                mining_total_ritase  = Sum('ritase'),
                mining_total_tonnage = Sum('tonnage')
            ) \
            .order_by('date_production', 'loading_point', 'shift', 'nama_material')

        # Mengubah data mining ke dalam dictionary untuk pencarian lebih cepat
        mining_dict = {}
        for mining in mining_data:
            key = (mining['date_production'], mining['loading_point'], mining['shift'], mining['nama_material'])
            mining_dict[key] = {
                'mining_total_ritase' : round(mining['mining_total_ritase'], 2),
                'mining_total_tonnage': round(mining['mining_total_tonnage'], 2),
            }

        # Inisialisasi dictionary untuk summary total by material_type
        summary_total = defaultdict(lambda: {'total_gc_ritase': 0, 'total_mining_ritase': 0, 'total_ritase_diff': 0,
                                     'total_gc_tonnage': 0, 'total_mining_tonnage': 0, 'total_tonnage_diff': 0})

        # Gabungkan hasil rekonsiliasi
        reconciliation_data = []
        for gc in gc_data:
            key    = (gc['tgl_production'], gc['prospect_area'], gc['shift'], gc['ore_class'])
            mining = mining_dict.get(key)

            # Hitung dengan pembulatan
            gc_total_ritase     = round(gc['gc_total_ritase'], 2)
            mining_total_ritase = mining['mining_total_ritase'] if mining else 0
            ritase_difference   = round(gc_total_ritase - mining_total_ritase, 2)

            gc_total_tonnage     = round(gc['gc_total_tonnage'], 2)
            mining_total_tonnage = mining['mining_total_tonnage'] if mining else 0
            tonnage_difference   = round(gc_total_tonnage - mining_total_tonnage, 2)

            reconciliation_data.append({
                'date'      : gc['tgl_production'],
                'area'      : gc['prospect_area'],
                'shift'     : gc['shift'],
                'material'  : gc['nama_material'],
                'material_type'       : gc['ore_class'],
                'gc_total_ritase'     : gc_total_ritase,
                'mining_total_ritase' : mining_total_ritase,
                'ritase_difference'   : ritase_difference,
                'gc_total_tonnage'    : gc_total_tonnage,
                'mining_total_tonnage': mining_total_tonnage,
                'tonnage_difference'  : tonnage_difference,
            })

            # return JsonResponse({'data': reconciliation_data}, safe=False)

            # Tambahkan ke summary berdasarkan material_type
            material_type = gc['ore_class']
            summary_total[material_type]['total_gc_ritase'] += gc_total_ritase
            summary_total[material_type]['total_mining_ritase'] += mining_total_ritase
            summary_total[material_type]['total_ritase_diff'] += ritase_difference
            summary_total[material_type]['total_gc_tonnage'] += gc_total_tonnage
            summary_total[material_type]['total_mining_tonnage'] += mining_total_tonnage
            summary_total[material_type]['total_tonnage_diff'] += tonnage_difference

        # Konversi summary_total ke list agar bisa dikembalikan dalam JSON
        summary_list = [{'material_type': mt, **values} for mt, values in summary_total.items()]

        return JsonResponse({'data': reconciliation_data, 'summary_total': summary_list}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def recon_mine_date(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Metode permintaan tidak valid. Gunakan GET.'}, status=405)

    try:
        encrypted_date = request.GET.get('filter_date')
        # Dekripsi filter_date yang dienkripsi
        filter_date = decrypt_date(encrypted_date)
        # Query untuk data produksi GC dengan filter tanggal dan urutan
        gc_data = OreProductionsView.objects.filter(tgl_production=filter_date) \
            .values('tgl_production', 'prospect_area', 'shift', 'nama_material', 'ore_class') \
            .annotate(
                gc_total_ritase  = Sum('ritase'),
                gc_total_tonnage = Sum('tonnage')
            ) \
            .order_by('tgl_production', 'prospect_area', 'shift', 'nama_material','ore_class')

        # Query untuk data produksi Mining dengan filter tanggal dan urutan
        mining_data = mineProductionsView.objects.filter(date_production=filter_date) \
            .values('date_production', 'loading_point', 'shift', 'nama_material') \
            .annotate(
                mining_total_ritase  = Sum('ritase'),
                mining_total_tonnage = Sum('tonnage')
            ) \
            .order_by('date_production', 'loading_point', 'shift', 'nama_material')

        # Mengubah data gc ke dalam dictionary untuk pencarian lebih cepat
        gc_dict = {}
        for gc in gc_data:
            # print(f"Processing Mining: {mining}")  # Debug data mentah
            key = (
                gc['tgl_production'].strftime('%Y-%m-%d') if gc['tgl_production'] else "",
                gc['prospect_area'].strip().lower() if gc['prospect_area'] else "",
                gc['shift'].strip() if gc['shift'] else "",
                # gc['nama_material'].strip().lower() if gc['nama_material'] else "",
                gc['ore_class'].strip().lower() if gc['ore_class'] else "",
            )
            # print("Mining Key:", key)
            gc_dict[key] = {
                'gc_total_ritase' : round(gc['gc_total_ritase'], 2),
                'gc_total_tonnage': round(gc['gc_total_tonnage'], 2),
            }

        # Inisialisasi dictionary untuk summary total by material_type
        summary_total = defaultdict(lambda: {'total_gc_ritase': 0, 'total_mining_ritase': 0, 'total_ritase_diff': 0,
                                     'total_gc_tonnage': 0, 'total_mining_tonnage': 0, 'total_tonnage_diff': 0})
        # Gabungkan hasil rekonsiliasi
        reconciliation_data = []
        for mining in mining_data:
            key = (
                str(mining['date_production']).strip(),  # Konversi ke string terlebih dahulu
                mining['loading_point'].strip().lower(),
                mining['shift'].strip(),
                mining['nama_material'].strip().lower()
            )
            print("Mining Key:", key)
            gc = gc_dict.get(key)

            # Hitung dengan pembulatan
            mining_ritase = round(mining['mining_total_ritase'], 2)
            gc_ritase     = gc['gc_total_ritase'] if gc else 0
            ritase_diff   = round(mining_ritase - gc_ritase, 2)

            mining_tonnage = round(mining['mining_total_tonnage'], 2)
            gc_tonnage     = gc['gc_total_tonnage'] if gc else 0
            tonnage_diff   = round(mining_tonnage - gc_tonnage, 2)

            reconciliation_data.append({
                'date'      : mining['date_production'],
                'area'      : mining['loading_point'].strip(),
                'shift'     : mining['shift'].strip(),
                'material'  : mining['nama_material'].strip(),
                # 'material_type'       : gc['ore_class'].strip(),
                'gc_ritase'      : gc_ritase,
                'mining_ritase'  : mining_ritase,
                'ritase_diff'    : ritase_diff,
                'gc_tonnage'     : gc_tonnage,
                'mining_tonnage' : mining_tonnage,
                'tonnage_diff'   : tonnage_diff,
            })

            # Fiter MAterial yang diambil
            allowed_materials = {"MWS", "LGLO", "MGLO", "HGLO", "LGSO", "MGSO", "HGSO"}

            # Tambahkan ke summary berdasarkan material_type jika material_type ada di daftar
            material_type = mining['nama_material'].strip()
            if material_type in allowed_materials:
                summary_total[material_type]['total_gc_ritase'] += gc_ritase
                summary_total[material_type]['total_mining_ritase'] += mining_ritase
                summary_total[material_type]['total_ritase_diff'] += ritase_diff
                summary_total[material_type]['total_gc_tonnage'] += gc_tonnage
                summary_total[material_type]['total_mining_tonnage'] += mining_tonnage
                summary_total[material_type]['total_tonnage_diff'] += tonnage_diff

        summary_list = [{'material_type': mt, **values} for mt, values in summary_total.items()]

        return JsonResponse({'data': reconciliation_data, 'summary_total': summary_list}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# decrypts
def recon_gc_daily(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Metode permintaan tidak valid. Gunakan GET.'}, status=405)

    try:
        filter_date = request.GET.get('filter_date')

        # Query untuk data produksi GC dengan filter tanggal dan urutan
        gc_data = OreProductionsView.objects.filter(tgl_production=filter_date) \
            .values('tgl_production', 'prospect_area', 'shift', 'nama_material', 'ore_class') \
            .annotate(
                gc_total_ritase  = Sum('ritase'),
                gc_total_tonnage = Sum('tonnage')
            ) \
            .order_by('tgl_production', 'prospect_area', 'shift', 'nama_material','ore_class')

        # Query untuk data produksi Mining dengan filter tanggal dan urutan
        mining_data = mineProductionsView.objects.filter(date_production=filter_date) \
            .values('date_production', 'loading_point', 'shift', 'nama_material') \
            .annotate(
                mining_total_ritase  = Sum('ritase'),
                mining_total_tonnage = Sum('tonnage')
            ) \
            .order_by('date_production', 'loading_point', 'shift', 'nama_material')

        # Mengubah data mining ke dalam dictionary untuk pencarian lebih cepat
        mining_dict = {}
        for mining in mining_data:
            # print(f"Processing Mining: {mining}")  # Debug data mentah
            key = (
                mining['date_production'].strftime('%Y-%m-%d') if mining['date_production'] else "",
                mining['loading_point'].strip().lower() if mining['loading_point'] else "",
                mining['shift'].strip() if mining['shift'] else "",
                mining['nama_material'].strip().lower() if mining['nama_material'] else ""
            )
            print("Mining Key:", key)
            mining_dict[key] = {
                'mining_total_ritase' : round(mining['mining_total_ritase'], 2),
                'mining_total_tonnage': round(mining['mining_total_tonnage'], 2),
            }

        # Inisialisasi dictionary untuk summary total by material_type
        summary_total = defaultdict(lambda: {'total_gc_ritase': 0, 'total_mining_ritase': 0, 'total_ritase_diff': 0,
                                     'total_gc_tonnage': 0, 'total_mining_tonnage': 0, 'total_tonnage_diff': 0})
        # Gabungkan hasil rekonsiliasi
        reconciliation_data = []
        for gc in gc_data:
            # key    = (gc['tgl_production'], gc['prospect_area'], gc['shift'], gc['ore_class'])
            key = (
                str(gc['tgl_production']).strip(),  # Konversi ke string terlebih dahulu
                gc['prospect_area'].strip().lower(),
                gc['shift'].strip(),
                gc['ore_class'].strip().lower()
            )
            print("GC Key:", key)
            mining = mining_dict.get(key)

            # Hitung dengan pembulatan
            gc_total_ritase     = round(gc['gc_total_ritase'], 2)
            mining_total_ritase = mining['mining_total_ritase'] if mining else 0
            ritase_difference   = round(gc_total_ritase - mining_total_ritase, 2)

            gc_total_tonnage     = round(gc['gc_total_tonnage'], 2)
            mining_total_tonnage = mining['mining_total_tonnage'] if mining else 0
            tonnage_difference   = round(gc_total_tonnage - mining_total_tonnage, 2)

            reconciliation_data.append({
                'date'      : gc['tgl_production'],
                'area'      : gc['prospect_area'].strip(),
                'shift'     : gc['shift'].strip(),
                'material'  : gc['nama_material'].strip(),
                'material_type'       : gc['ore_class'].strip(),
                'gc_total_ritase'     : gc_total_ritase,
                'mining_total_ritase' : mining_total_ritase,
                'ritase_difference'   : ritase_difference,
                'gc_total_tonnage'    : gc_total_tonnage,
                'mining_total_tonnage': mining_total_tonnage,
                'tonnage_difference'  : tonnage_difference,
            })

           # return JsonResponse({'data': reconciliation_data}, safe=False)

            # Tambahkan ke summary berdasarkan material_type
            material_type = gc['ore_class']
            summary_total[material_type]['total_gc_ritase'] += gc_total_ritase
            summary_total[material_type]['total_mining_ritase'] += mining_total_ritase
            summary_total[material_type]['total_ritase_diff'] += ritase_difference
            summary_total[material_type]['total_gc_tonnage'] += gc_total_tonnage
            summary_total[material_type]['total_mining_tonnage'] += mining_total_tonnage
            summary_total[material_type]['total_tonnage_diff'] += tonnage_difference

        # Konversi summary_total ke list agar bisa dikembalikan dalam JSON
        summary_list = [{'material_type': mt, **values} for mt, values in summary_total.items()]
        
        return JsonResponse({'data': reconciliation_data, 'summary_total': summary_list}, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def recon_mine_daily(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Metode permintaan tidak valid. Gunakan GET.'}, status=405)

    try:
        filter_date = request.GET.get('filter_date')
        # Query untuk data produksi GC dengan filter tanggal dan urutan
        
        gc_data = OreProductionsView.objects.filter(tgl_production=filter_date) \
            .values('tgl_production', 'prospect_area', 'shift', 'nama_material', 'ore_class') \
            .annotate(
                gc_total_ritase  = Sum('ritase'),
                gc_total_tonnage = Sum('tonnage')
            ) \
            .order_by('tgl_production', 'prospect_area', 'shift', 'nama_material','ore_class')

        # Query untuk data produksi Mining dengan filter tanggal dan urutan
        mining_data = mineProductionsView.objects.filter(date_production=filter_date) \
            .values('date_production', 'loading_point', 'shift', 'nama_material') \
            .annotate(
                mining_total_ritase  = Sum('ritase'),
                mining_total_tonnage = Sum('tonnage')
            ) \
            .order_by('date_production', 'loading_point', 'shift', 'nama_material')

        # Mengubah data gc ke dalam dictionary untuk pencarian lebih cepat
        gc_dict = {}
        for gc in gc_data:
            # print(f"Processing Mining: {mining}")  # Debug data mentah
            key = (
                gc['tgl_production'].strftime('%Y-%m-%d') if gc['tgl_production'] else "",
                gc['prospect_area'].strip().lower() if gc['prospect_area'] else "",
                gc['shift'].strip() if gc['shift'] else "",
                # gc['nama_material'].strip().lower() if gc['nama_material'] else "",
                gc['ore_class'].strip().lower() if gc['ore_class'] else "",
            )
            # print("Mining Key:", key)
            gc_dict[key] = {
                'gc_total_ritase' : round(gc['gc_total_ritase'], 2),
                'gc_total_tonnage': round(gc['gc_total_tonnage'], 2),
            }

        # Inisialisasi dictionary untuk summary total by material_type
        summary_total = defaultdict(lambda: {'total_gc_ritase': 0, 'total_mining_ritase': 0, 'total_ritase_diff': 0,
                                     'total_gc_tonnage': 0, 'total_mining_tonnage': 0, 'total_tonnage_diff': 0})
        # Gabungkan hasil rekonsiliasi
        reconciliation_data = []
        for mining in mining_data:
            key = (
                str(mining['date_production']).strip(),  # Konversi ke string terlebih dahulu
                mining['loading_point'].strip().lower(),
                mining['shift'].strip(),
                mining['nama_material'].strip().lower()
            )
            print("Mining Key:", key)
            gc = gc_dict.get(key)

            # Hitung dengan pembulatan
            mining_ritase = round(mining['mining_total_ritase'], 2)
            gc_ritase     = gc['gc_total_ritase'] if gc else 0
            ritase_diff   = round(mining_ritase - gc_ritase, 2)

            mining_tonnage = round(mining['mining_total_tonnage'], 2)
            gc_tonnage     = gc['gc_total_tonnage'] if gc else 0
            tonnage_diff   = round(mining_tonnage - gc_tonnage, 2)

            reconciliation_data.append({
                'date'      : mining['date_production'],
                'area'      : mining['loading_point'].strip(),
                'shift'     : mining['shift'].strip(),
                'material'  : mining['nama_material'].strip(),
                # 'material_type'       : gc['ore_class'].strip(),
                'gc_ritase'      : gc_ritase,
                'mining_ritase'  : mining_ritase,
                'ritase_diff'    : ritase_diff,
                'gc_tonnage'     : gc_tonnage,
                'mining_tonnage' : mining_tonnage,
                'tonnage_diff'   : tonnage_diff,
            })

            # Fiter MAterial yang diambil
            allowed_materials = {"MWS", "LGLO", "MGLO", "HGLO", "LGSO", "MGSO", "HGSO"}

            # Tambahkan ke summary berdasarkan material_type jika material_type ada di daftar
            material_type = mining['nama_material'].strip()
            if material_type in allowed_materials:
                summary_total[material_type]['total_gc_ritase'] += gc_ritase
                summary_total[material_type]['total_mining_ritase'] += mining_ritase
                summary_total[material_type]['total_ritase_diff'] += ritase_diff
                summary_total[material_type]['total_gc_tonnage'] += gc_tonnage
                summary_total[material_type]['total_mining_tonnage'] += mining_tonnage
                summary_total[material_type]['total_tonnage_diff'] += tonnage_diff

        summary_list = [{'material_type': mt, **values} for mt, values in summary_total.items()]

        return JsonResponse({'data': reconciliation_data, 'summary_total': summary_list}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
        
def source_mine_dome(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Metode permintaan tidak valid. Gunakan GET.'}, status=405)

    try:
        filter_date = request.GET.get('filter_date')

        # Query untuk data produksi GC dengan filter tanggal dan urutan
        gc_data = OreProductionsView.objects.filter(tgl_production=filter_date) \
            .values('tgl_production', 'prospect_area', 'shift','pile_id', 'nama_material', 'ore_class') \
            .annotate(
                gc_total_ritase  = Sum('ritase'),
                gc_total_tonnage = Sum('tonnage')
            ) \
            .order_by('tgl_production', 'prospect_area', 'shift', 'pile_id','nama_material','ore_class')

        # Query untuk data produksi Mining dengan filter tanggal dan urutan
        mining_data = mineProductionsView.objects.filter(date_production=filter_date) \
            .values('date_production', 'loading_point', 'shift', 'dome_id','nama_material') \
            .annotate(
                mining_total_ritase  = Sum('ritase'),
                mining_total_tonnage = Sum('tonnage')
            ) \
            .order_by('date_production', 'loading_point', 'shift','dome_id', 'nama_material')

        # Mengubah data mining ke dalam dictionary untuk pencarian lebih cepat
        mining_dict = {}
        for mining in mining_data:
            # print(f"Processing Mining: {mining}")  # Debug data mentah
            key = (
                mining['date_production'].strftime('%Y-%m-%d') if mining['date_production'] else "",
                mining['loading_point'].strip().lower() if mining['loading_point'] else "",
                mining['shift'].strip() if mining['shift'] else "",
                mining['dome_id'].strip() if mining['dome_id'] else "",
                mining['nama_material'].strip().lower() if mining['nama_material'] else ""
            )
            print("Mining Key:", key)
            mining_dict[key] = {
                'mining_total_ritase' : round(mining['mining_total_ritase'], 2),
                'mining_total_tonnage': round(mining['mining_total_tonnage'], 2),
                # 'dome_id'             : mining['dome_id'].strip() if mining['dome_id'] else "",
            }

        # Gabungkan hasil rekonsiliasi
        reconciliation_data = []
        for gc in gc_data:
            # key    = (gc['tgl_production'], gc['prospect_area'], gc['shift'], gc['ore_class'])
            key = (
                str(gc['tgl_production']).strip(),  # Konversi ke string terlebih dahulu
                gc['prospect_area'].strip().lower(),
                gc['shift'].strip(),
                gc['pile_id'].strip(),
                gc['ore_class'].strip().lower()
            )
            print("GC Key:", key)

            mining = mining_dict.get(key)

            # Hitung dengan pembulatan
            gc_total_ritase     = round(gc['gc_total_ritase'], 2)
            mining_total_ritase = mining['mining_total_ritase'] if mining else 0
            ritase_difference   = round(gc_total_ritase - mining_total_ritase, 2)

            gc_total_tonnage     = round(gc['gc_total_tonnage'], 2)
            mining_total_tonnage = mining['mining_total_tonnage'] if mining else 0
            tonnage_difference   = round(gc_total_tonnage - mining_total_tonnage, 2)

            reconciliation_data.append({
                'date'      : gc['tgl_production'],
                'area'      : gc['prospect_area'].strip(),
                'shift'     : gc['shift'].strip(),
                'pile_id'   : gc['pile_id'].strip(),
                # 'dome_id'   : mining['dome_id'],
                'material'  : gc['nama_material'].strip(),
                'material_type'       : gc['ore_class'].strip(),
                'gc_total_ritase'     : gc_total_ritase,
                'mining_total_ritase' : mining_total_ritase,
                'ritase_difference'   : ritase_difference,
                'gc_total_tonnage'    : gc_total_tonnage,
                'mining_total_tonnage': mining_total_tonnage,
                'tonnage_difference'  : tonnage_difference,
            })

        return JsonResponse({'data': reconciliation_data}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def mine_reconciliation_page(request):
    allowed_groups = ['superadmin','admin-mining','superintendent-mining','manager-mining']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        # Jika tidak memiliki izin, arahkan ke halaman error
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)
    today = datetime.today()
    first_day_of_month = today.replace(day=1)  # Tanggal awal bulan berjalan

     # Cek permission
    permissions = get_dynamic_permissions(request.user)

    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
        'permissions':permissions
    }
    return render(request, 'reconciliation/list-reconciliation-mining.html',context)

def gc_reconciliation_page(request):
    allowed_groups = ['superadmin','admin-mgoqa','superintendent-mgoqa','manager-mgoqa','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        # Jika tidak memiliki izin, arahkan ke halaman error
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)
    today = datetime.today()
    first_day_of_month = today.replace(day=1)  # Tanggal awal bulan berjalan

     # Cek permission
    permissions = get_dynamic_permissions(request.user)

    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
        'permissions':permissions
        
    }
    return render(request, 'reconciliation/list-reconciliation-gc.html',context)

def mine_recon_day_page(request):
    # Cek permission
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions':permissions
    }
    return render(request, 'reconciliation/sum-reconciliation-mining.html',context)

def gc_recon_day_page(request):
    # Cek permission
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions':permissions
    }
    return render(request, 'reconciliation/sum-reconciliation-gc.html',context)