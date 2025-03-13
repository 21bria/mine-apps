from celery import shared_task
import pandas as pd
from django.db import transaction
from ..models.task_model import taskImports
from celery import shared_task
import re
from django.db.models.functions import Trim
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.vendors_model import Vendors
from ..models.mine_units_model import unitsCategories,MineUnits

# Fungsi untuk membersihkan data numerik
def clean_numeric(value):
    try:
        if pd.isna(value):  # Cek jika NaN atau None
            return 0
        if isinstance(value, str):
            value = value.strip()  # Menghapus spasi di awal dan akhir
            if value == '':  # Jika string kosong
                return None
            # Menghapus karakter selain angka dan titik desimal
            value = re.sub(r"[^0-9.<>]", "", value)
            if value.startswith('<') or value.startswith('>'):
                value = value[1:]  # Menghapus tanda '<' atau '>'
            if re.match(r"^\d+(\.\d+)?$", value):  # Cek jika angka valid
                return float(value)
            return 0  # Jika tidak valid, kembalikan 0
        return value if isinstance(value, (int, float)) else 0
    except Exception as e:
        print(f"Error processing value: {value}, Error: {e}")
        return 0  # Kembalikan 0 jika terjadi error

@shared_task
def import_mine_equipments(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_objects = []
    update_objects = []
    successful_imports = 0
    duplicate_imports = 0

    # Konversi kolom ke datetime dengan format yang sesuai
    df['commisioning_date']=pd.to_datetime(df['commisioning_date'], format='%Y-%m-%d', errors='coerce')
    df['on_hire']=pd.to_datetime(df['on_hire'], format='%Y-%m-%d', errors='coerce')
    df['off_hire']=pd.to_datetime(df['off_hire'], format='%Y-%m-%d', errors='coerce')
    df['commisioning_date']=df['commisioning_date'].dt.date
    df['on_hire']=df['on_hire'].dt.date
    df['off_hire']=df['off_hire'].dt.date 

    vendors_dict  = dict(Vendors.objects.annotate(trim_vendor=Trim('vendor_name')).values_list('trim_vendor', 'id'))
    category_dict = dict(unitsCategories.objects.annotate(trim_category=Trim('category')).values_list('trim_category', 'id'))

    # Ambil semua unit_code yang sudah ada di database
    existing_data = MineUnits.objects.values_list("id", "unit_code")
    existing_dict = {val: record_id for record_id, val in existing_data}  # Dictionary 

    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                code_vendors      = row['code_vendors']
                unit_code         = row['unit_code']
                unit_model        = row['unit_model']
                unit_type         = row['unit_type']
                merk              = row['merk']
                category          = row['category']
                vendors           = row['vendors']
                commisioning_date = row['commisioning_date']
                on_hire           = row['on_hire']
                off_hire          = row['off_hire']
                description       = row['description']

                id_category = category_dict.get(category, None) 
                id_vendor   = vendors_dict.get(vendors, None)  

                # Gabungkan Refrensi
                duplikat = f"{unit_code}".replace(" ", "")

                if duplikat in existing_dict:
                    # Jika sudah ada, tambahkan ke daftar update
                    update_objects.append(
                        MineUnits(
                            id=existing_dict[duplikat],  # ID dari database
                            unit_code=unit_code,
                            unit_model=unit_model,
                            unit_type=unit_type,
                            id_category=id_category,
                            id_vendor=id_vendor,
                            status=1,
                            merk=merk,
                            commisioning_date=commisioning_date,
                            on_hire=on_hire,
                            off_hire=off_hire,
                            code_vendors=code_vendors,
                            description=description,
                            task_id=import_mine_equipments.request.id,
                        )
                    )
                    duplicate_imports += 1
                    duplicates.append(f"Updated at row {index}: {duplikat}")
                else:
                    # Jika belum ada, tambahkan ke daftar insert
                    list_objects.append(
                        MineUnits(
                            unit_code=unit_code,
                            unit_model=unit_model,
                            unit_type=unit_type,
                            id_category=id_category,
                            id_vendor=id_vendor,
                            status=1,
                            merk=merk,
                            commisioning_date=commisioning_date,
                            on_hire=on_hire,
                            off_hire=off_hire,
                            code_vendors=code_vendors,
                            description=description,
                            task_id=import_mine_equipments.request.id,
                        )
                    )
                    successful_imports += 1

            # Simpan semua insert dengan bulk_create
            if list_objects:
                MineUnits.objects.bulk_create(list_objects, batch_size=200)

            # Simpan semua update dengan bulk_update
            if update_objects:
                MineUnits.objects.bulk_update(update_objects, [
                    "unit_model", "unit_type", "id_category", "id_vendor","supports", "status",   
                    "description","merk","commisioning_date","on_hire","off_hire","code_vendors"
                ], batch_size=200)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Buat laporan import
    taskImports.objects.create(
        task_id             =import_mine_equipments.request.id, 
        successful_imports  =successful_imports,
        failed_imports      =len(errors),
        duplicate_imports   =duplicate_imports,
        errors              ="\n".join(errors) if errors else None,
        duplicates          ="\n".join(duplicates) if duplicates else None,
        file_name           =original_file_name,
        destination         ='Mine Equipments',
    )

    if errors or duplicates:
        return {'message': 'Import completed with some errors or duplicates', 'errors': errors, 'duplicates': duplicates}
    else:
        return {'message': 'Import successful'}
