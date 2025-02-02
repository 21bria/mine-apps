from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from ...models import PermissionGroup
from ...forms.forms_permission_group import PermissionGroupForm
from django.contrib import messages
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from ...utils.permissions import get_dynamic_permissions

class group_permissionList(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        groups = self._datatables(request)
        return JsonResponse(groups, safe=False)

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
        records_total = PermissionGroup.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = PermissionGroup.objects.all()

        if search:
            data = PermissionGroup.objects.filter(
                Q(name__icontains=search) 
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
                "id": item.id,
                "name": item.name,
                "groups": ", ".join([group.name for group in item.groups.all()])  # Join group names as a string
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }


@login_required
def group_permission_create(request, pk=None):
    allowed_groups = ['superadmin']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse({'status': 'error', 'message': 'You do not have permission'}, status=403)

    if pk:
        group = get_object_or_404(PermissionGroup, pk=pk)
        form = PermissionGroupForm(request.POST or None, instance=group)
    else:
        form = PermissionGroupForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('permission-group-page')
        else:
            # Debugging error form
            return JsonResponse({'status': 'error', 'message': 'Form is not valid', 'errors': form.errors}, status=400)

    return render(request, 'permission/group-form.html', {'form': form, 'is_edit': bool(pk)})

@login_required
def group_permission_edit(request, pk):
    allowed_groups = ['superadmin']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )

    group = get_object_or_404(PermissionGroup, pk=pk)
    if request.method == 'POST':
        form = PermissionGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('permission-group-page')
        else:
             print(f"Form errors: {form.errors}")  # Menampilkan error jika form tidak valid 
    else:
        form = PermissionGroupForm(instance=group)
    return render(request, 'permission/group-form.html', {'form': form})


@login_required
def permission_group_page(request):
    allowed_groups = ['superadmin']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        # Jika tidak memiliki izin, arahkan ke halaman error
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)
    # Ambil permissions dinamis dari database
    permissions = get_dynamic_permissions(request.user)

    context = {
     'permissions': permissions,

    }

    return render(request, 'permission/list-group.html',context)