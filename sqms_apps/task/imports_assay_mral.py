from celery import shared_task
import pandas as pd
import re
from ..models.assay_mral_model import AssayMral
from ..models.task_model import UploadLog
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
def import_assay_mral(file_path, original_file_name):
    errors = []
    duplicates = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0

    try:
        # Baca file excel
        df = pd.read_excel(file_path)

        # Pastikan format 'Release Date' dan 'Release Time'
        df['Release Date'] = pd.to_datetime(df['Release Date']).dt.date
        df['Release Time'] = pd.to_datetime(df['Release Time'], format='%H:%M:%S').dt.time

        # Gabungkan kolom Release Date dan Release Time menjadi datetime tanpa timezone
        df['release_mral'] = df.apply(lambda row: datetime.combine(row['Release Date'], row['Release Time']), axis=1)
        df['release_mral'] = df['release_mral'].apply(lambda x: x.replace(tzinfo=None))

        # Bersihkan semua kolom numerik di DataFrame
        numeric_columns = ['Ni-mral', 'Co-mral', 'Fe2O3-mral', 'Fe-mral', 'Mgo-mral', 'SiO2-mral']
        for col in numeric_columns:
            df[col] = df[col].apply(clean_numeric)

        # Mulai transaksi untuk memastikan rollback jika terjadi error
        with transaction.atomic():
            for index, row in df.iterrows():
                release_mral = row['release_mral']
                job_number = row['Job Number']
                sample_id = row['Samples Id']
                ni = row['Ni-mral']
                co = row['Co-mral']
                fe2o3 = row['Fe2O3-mral']
                fe = row['Fe-mral']
                mgo = row['Mgo-mral']
                sio2 = row['SiO2-mral']

                # Cek duplikat berdasarkan kriteria
                if AssayMral.objects.filter(sample_id=sample_id).exists():
                    duplicates.append(f"Duplicate at row {index}: {sample_id}")
                    duplicate_imports += 1
                    continue

                try:
                    # Siapkan data untuk disimpan
                    data = AssayMral(
                        release_mral=release_mral,
                        job_number=job_number,
                        sample_id=sample_id,
                        ni=ni,
                        co=co,
                        fe2o3=fe2o3,
                        fe=fe,
                        mgo=mgo,
                        sio2=sio2
                    )
                    list_objects.append(data)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue

            # Simpan semua data dengan bulk_create untuk efisiensi
            if list_objects:
                AssayMral.objects.bulk_create(list_objects, batch_size=200)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Buat laporan import menggunakan task ID dari request Celery
    try:
        taskImports.objects.create(
            task_id=import_assay_mral.request.id,  # Menggunakan request.id dari task
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