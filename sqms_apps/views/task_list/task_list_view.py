from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from ...models.task_model import taskList
from ...forms.forms_task_list import TaskListForm
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from ...utils.permissions import get_dynamic_permissions

@login_required
def task_list_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions': permissions,
    }
    return render(request, 'task/list-task.html',context)

# List Table
class task_List(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        task = self._datatables(request)
        return JsonResponse(task, safe=False)

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
        records_total = taskList.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = taskList.objects.all()

        if search:
            data = taskList.objects.filter(
                Q(order_slug__icontains=search)/
                Q(type_table__icontains=search)
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
                "id"         : item.id,
                "order_slug" : item.order_slug,
                "type_table" : item.type_table,
                "status"     : item.status
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }

# Add Data
def add_task(request):
    if request.method == 'POST':
        form = TaskListForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.save()
            form.save_m2m()
            return redirect('task-table-page')  # Redirect on success
        else:
            return render(request, 'task/task_add.html', {'form': form, 'title': 'Add Task'})
    else:
        form = TaskListForm()
    return render(request, 'task/task_add.html', {'form': form, 'title': 'Add Task'})

# Edit data
def edit_task(request, pk):
    task = get_object_or_404(taskList, pk=pk)
    if request.method == 'POST':
        form = TaskListForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            return redirect('task-table-page')
    else:
        form = TaskListForm(instance=task)
    return render(request, 'task/task_edit.html', {'form': form, 'title': 'Edit Task'})

@login_required
def delete_task(request):
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = taskList.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

