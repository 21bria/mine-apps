from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings  # Import the settings module
import tempfile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.generic import View
from django.db.models import Q
from .models.task_model import taskImports
from .task.imports_assay_mral import import_assay_mral
from .task.imports_assay_roa import import_assay_roa
from .task.import_selling_hpal import import_selling_hpal
from .task.import_selling_rkef import import_selling_rkef
from .task.import_ore_pds import import_ore_productions
from .task.import_samples_pds import import_sample_GcQa
from .task.import_mines_productions import import_mine_productions
from .task.import_plan_mine_productions import import_plan_mine_productions
from .task.import_mines_productions_quick import import_mine_productions_quick
from .utils.permissions import get_dynamic_permissions

@login_required
def imports_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions': permissions,
    }
    return render(request, 'imports-page.html',context)

class TaskImportsList(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        material = self._datatables(request)
        return JsonResponse(material, safe=False)

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
        records_total = taskImports.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = taskImports.objects.all()
        

        if search:
            data = taskImports.objects.filter(
                Q(created_at__icontains=search) |
                Q(file_name__icontains=search)
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
                "id"                : item.id,
                "task_id"           : item.task_id,
                "successful_imports": item.successful_imports,
                "failed_imports"    : item.failed_imports,
                "duplicate_imports" : item.duplicate_imports,
                "errors"            : item.errors,
                "duplicates"        : item.duplicates,
                "file_name"         : item.file_name,
                "destination"       : item.destination,
                "created_at"        : item.created_at.strftime("%a, %d %b %Y %H:%M:%S")
            } for item in object_list
        ]

        return {
            'draw'           : draw,
            'recordsTotal'   : records_total,
            'recordsFiltered': records_filtered,
            'data'           : data
        }
    
@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        import_type = request.POST.get('import_type')

        if file:
            original_file_name = file.name  # Dapatkan nama asli file
            # Simpan file ke disk sementara
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                file_path = temp_file.name

            if import_type == 'assay_mral':
                task = import_assay_mral.delay(file_path,original_file_name)
            elif import_type == 'assay_roa':
                task = import_assay_roa.delay(file_path,original_file_name)
            elif import_type == 'selling_hpal':
                task = import_selling_hpal.delay(file_path,original_file_name)
            elif import_type == 'selling_rkef':
                task = import_selling_rkef.delay(file_path,original_file_name)
            elif import_type == 'ore_productions':
                task = import_ore_productions.delay(file_path,original_file_name)
            elif import_type == 'samples_productions':
                task = import_sample_GcQa.delay(file_path,original_file_name)
            elif import_type == 'mine_productions':
                task = import_mine_productions.delay(file_path,original_file_name)
            elif import_type == 'mine_plan_productions':
                task = import_plan_mine_productions.delay(file_path,original_file_name)
            elif import_type == 'mine_productions_qiuck':
                task = import_mine_productions_quick.delay(file_path,original_file_name)
            else:
                return JsonResponse({'message': 'Invalid import type'}, status=400)

            return JsonResponse({'message': 'Import started', 'task_id': task.id})

    return JsonResponse({'message': 'Invalid request method'}, status=405)




# def upload_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        column_mapping = json.loads(request.POST.get('column_mapping', '{}'))
        if file:
            # file_path = os.path.join(settings.MEDIA_ROOT, file.name)
            # file_path =os.path.join(settings.BASE_DIR, "sqms_apps/static/import", file.name)
            # with open(file_path, 'wb+') as destination:
            #     for chunk in file.chunks():
            #         destination.write(chunk)

            # Simpan file ke disk sementara
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                file_path = temp_file.name

            if column_mapping:
                result = import_mahasiswa.delay(file_path, column_mapping)
                return JsonResponse(result)
            else:
                df = pd.read_excel(file_path)
                columns_in_file = df.columns.tolist()
                return JsonResponse({'columns': columns_in_file})

    return JsonResponse({'message': 'Invalid request method'}, status=405)