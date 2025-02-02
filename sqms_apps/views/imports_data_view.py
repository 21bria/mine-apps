# views.py
from django.shortcuts import render
from django.apps import apps  # Tambahkan impor ini
from ..forms.forms_imports import ImportForm  # Sesuaikan dengan path yang benar
import pandas as pd
from django.http import JsonResponse
# def import_data(request):
#     if request.method == 'POST':
#         form = ImportForm(request.POST, request.FILES)
#         if form.is_valid():
#             model_label = form.cleaned_data['table_choice']
#             app_label, model_name = model_label.split('.')
#             table_choice = apps.get_model(app_label, model_name)
#             columns = form.cleaned_data['columns']
#             excel_file = request.FILES['excel_file']
#             excel_data = pd.read_excel(excel_file)

#             # Ambil nama kolom yang dipilih
#             selected_columns = list(columns)

#             # Simpan data ke tabel yang dipilih
#             for index, row in excel_data.iterrows():
#                 model_instance = table_choice()
#                 for col in selected_columns:
#                     setattr(model_instance, col, row[col])
#                 model_instance.save()

#             return render(request, 'import_success.html')
#              # Return JSON response indicating success
#             # return JsonResponse({'message': 'Data imported successfully'}, status=200)
#     else:
#         form = ImportForm()
#     return render(request, 'imports-data/imports_temp.html', {'form': form})
#     # Return JSON response indicating form errors
#     # return JsonResponse({'errors': form.errors}, status=400)



# def import_data(request):
#     if request.method == 'POST':
#         form = ImportForm(request.POST, request.FILES)
#         if form.is_valid():
#             excel_file = request.FILES['excel_file']
#             excel_data = pd.read_excel(excel_file)
#             columns = list(excel_data.columns)
#             if 'ID' in columns:
#                 columns.remove('ID')  # Jika ID dianggap tidak perlu, dapat dihapus
#             return render(request, 'imports-data/imports_temp.html', {'columns': columns})
#     else:
#         form = ImportForm()
#     return render(request, 'imports-data/imports_temp.html', {'form': form})

# def save_data(request):
#     if request.method == 'POST':
#         table_name = request.POST.get('table_name')
#         selected_columns = request.POST.getlist('selected_columns')
#         excel_file = request.FILES['excel_file']
        
#         excel_data = pd.read_excel(excel_file)
#         selected_data = excel_data[selected_columns]
        
#         # Simpan data ke tabel yang dipilih
#         # Implementasi disesuaikan dengan struktur tabel dan kebutuhan aplikasi Anda
#         # Misalnya:
#         # for index, row in selected_data.iterrows():
#         #     table_instance = TableName(**{column: row[column] for column in selected_columns})
#         #     table_instance.save()
        
#         return render(request, 'import_success.html')

#     return render(request, 'imports-data/imports_temp.htm', {})




def import_data(request):
    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            start_cell = form.cleaned_data['start_cell']
            end_cell = form.cleaned_data['end_cell']
            table_choice = form.cleaned_data['table_choice']
            columns = form.cleaned_data['columns']

            app_label, model_name = table_choice.split('.')
            table_choice = apps.get_model(app_label, model_name)
            excel_data = pd.read_excel(excel_file, header=None)
            selected_data = excel_data.loc[start_cell:end_cell]

            for index, row in selected_data.iterrows():
                model_instance = table_choice()
                for col in columns:
                    setattr(model_instance, col, row[col])
                model_instance.save()

            return render(request, 'import_success.html')
    else:
        form = ImportForm()
    return render(request, 'imports-data/imports_temp.html', {'form': form})

def load_columns(request):
    if request.method == 'POST' and 'excel_file' in request.FILES:
        excel_file = request.FILES['excel_file']
        excel_data = pd.read_excel(excel_file)
        columns = list(excel_data.columns)
        return JsonResponse({'columns': columns})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def imports_page_view(request):
    return render(request, 'imports-data/imports_temp.html')

