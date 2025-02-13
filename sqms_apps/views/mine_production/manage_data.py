from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.mine_productions_model import mineProductions
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Sum
from django.shortcuts import render
from ...utils.permissions import get_dynamic_permissions

@login_required
def get_vendor_production(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Metode permintaan tidak valid. Gunakan GET.'}, status=405)

    try:
        startDate = request.GET.get('startDate',None)
        endDate   = request.GET.get('endDate',None)

        if not startDate or not endDate:
            return JsonResponse({'error': 'Parameter startDate dan endDate wajib diisi.'}, status=400)

        # Query data produksi berdasarkan rentang tanggal
        production_data = mineProductions.objects.filter(
            date_production__range=[startDate, endDate]
        ).values('vendors').annotate(
            ritase=Count('ritase'),
            bcm=Sum('bcm'),
            tonnage=Sum('tonnage')
        ).order_by('vendors')

        return JsonResponse(
            {'data': list(production_data)}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def delete_range(request):
    if request.method == 'DELETE':
        vendor      = request.GET.get('id')  # vendors
        start_date  = request.GET.get('startDate')
        end_date    = request.GET.get('endDate')

        if vendor and start_date and end_date:
            deleted_rows, _ = mineProductions.objects.filter(
                vendors=vendor,
                date_production__range=[start_date, end_date]
            ).delete()

            if deleted_rows > 0:
                return JsonResponse({'status': 'deleted', 'deleted_count': deleted_rows})
            else:
                return JsonResponse({'status': 'error', 'message': 'No data found to delete'})

        return JsonResponse({'status': 'error', 'message': 'Missing parameters'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def vendors_production_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions': permissions,
    }
    return render(request, 'admin-mine/master/list-manage-data.html',context)
