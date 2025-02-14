from celery import shared_task
import pandas as pd
import re
from ..models.mine_addition_factor_model import mineAdditionFactor
from ..models.task_model import taskImports
from datetime import datetime
from django.db import transaction

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
def import_truck_factors(file_path, original_file_name):
    errors = []
    duplicates = []
    list_objects = []
    update_objects = []
    successful_imports = 0
    duplicate_imports = 0
    updated_records = 0

    try:
        # Baca file excel
        df = pd.read_excel(file_path)

        # Bersihkan semua kolom numerik di DataFrame
        numeric_columns = ['bcm', 'ton']
        for col in numeric_columns:
            df[col] = df[col].apply(clean_numeric)

        # Ambil semua data yang ada untuk pengecekan duplikasi
        existing_data = mineAdditionFactor.objects.values_list("id", "validation")
        existing_dict = {val: id for id, val in existing_data}  # Dictionary {validation: id}

        # Mulai transaksi untuk memastikan rollback jika terjadi error
        with transaction.atomic():
            for index, row in df.iterrows():
                type_truck = row['type_truck']
                vendors    = row['vendors']
                sources    = row['sources']
                materials  = row['materials']
                bcm        = row['bcm']
                ton        = row['ton']
                remarks    = row['remarks']

                validate = str(type_truck) + str(vendors) + str(sources) + str(materials)

                # Cek apakah data sudah ada di database
                if validate in existing_dict:
                    # Jika sudah ada, update data
                    try:
                        update_objects.append(
                            mineAdditionFactor(
                                id=existing_dict[validate],  # Ambil ID dari data yang sudah ada
                                type_truck=type_truck,
                                vendors=vendors,
                                sources=sources,
                                materials=materials,
                                bcm=bcm,
                                ton=ton,
                                remarks=remarks
                            )
                        )
                        updated_records += 1
                    except Exception as e:
                        errors.append(f"Error updating row {index}: {str(e)}")
                        continue
                else:
                    # Jika belum ada, insert data baru
                    try:
                        data = mineAdditionFactor(
                            type_truck=type_truck,
                            vendors=vendors,
                            sources=sources,
                            materials=materials,
                            bcm=bcm,
                            ton=ton,
                            remarks=remarks
                        )
                        list_objects.append(data)
                        successful_imports += 1
                    except Exception as e:
                        errors.append(f"Error inserting row {index}: {str(e)}")
                        continue

            # Simpan semua data baru dengan bulk_create untuk efisiensi
            if list_objects:
                mineAdditionFactor.objects.bulk_create(list_objects, batch_size=200)

            # Update data yang sudah ada dengan bulk_update
            if update_objects:
                mineAdditionFactor.objects.bulk_update(update_objects, ["type_truck", "vendors", "sources", "materials", "bcm", "ton", "remarks"], batch_size=200)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Buat laporan import menggunakan task ID dari request Celery
    try:
        taskImports.objects.create(
            task_id=import_truck_factors.request.id,  # Menggunakan request.id dari task
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination='Assay mral'
        )
    except Exception as e:
        errors.append(f"Error while logging import task: {str(e)}")

    # Return hasil
    if errors or duplicates:
        return {'message': 'Import completed with some errors or duplicates', 'errors': errors, 'duplicates': duplicates}
    else:
        return {'message': 'Import successful'}