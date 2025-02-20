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
from ..models.stock_factories_model import StockFactories
from ..models.selling_official_model import SellingOfficial,SellingSurveyor

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
def import_selling_official(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_objects = []
    update_objects = []
    successful_imports = 0
    duplicate_imports = 0

    # Konversi kolom ke datetime dengan format yang sesuai
    df['Start']  = pd.to_datetime(df['Start'], format='%Y-%m-%d', errors='coerce')
    df['Finish'] = pd.to_datetime(df['Finish'], format='%Y-%m-%d', errors='coerce')
    df['Start']  = df['Start'].dt.date  # Ambil hanya tanggal
    df['Finish'] = df['Finish'].dt.date  # Ambil hanya tanggal

    factory_dict  = dict(StockFactories.objects.annotate(trimmed_fact=Trim('factory_stock')).values_list('trimmed_fact', 'id'))
    surveyor_dict = dict(SellingSurveyor.objects.annotate(trim_code=Trim('code_surveyor')).values_list('trim_code', 'id'))

    # Ambil semua ref_plan yang sudah ada di database
    existing_data = SellingOfficial.objects.values_list("id", "check_duplicated")
    existing_dict = {val: record_id for record_id, val in existing_data}  # Dictionary 

    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                code        = row['Code']
                start       = row['Start']
                finish      = row['Finish']
                tonnage     = row['Tonnage']
                ni          = row['Ni']
                co          = row['Co']
                fe          = row['Fe']
                al2o3       = row['Al2O3']
                cao         = row['CaO']
                cr2o3       = row['Cr2O3']
                mno         = row['MnO']
                mgo         = row['MgO']
                p           = row['P']
                sio2        = row['SiO2']
                s           = row['S']
                mc          = row['MC']
                sm          = row['SM']
                so_number   = row['SO Number']
                surveyor    = row['Surveyor']
                type_sale   = row['Type Sale']
                distance    = row['Distance']

                id_surveyor = surveyor_dict.get(surveyor, None) 
                id_factory  = factory_dict.get(distance, None)  

                # Gabungkan Refrensi
                duplikat = f"{code}{id_surveyor}".replace(" ", "")

                if duplikat in existing_dict:
                    # Jika sudah ada, tambahkan ke daftar update
                    update_objects.append(
                        SellingOfficial(
                            id=existing_dict[duplikat],  # ID dari database
                            id_surveyor=id_surveyor,
                            type_selling=type_sale,
                            id_factory=id_factory,
                            so_number=so_number,
                            product_code=code,
                            tonnage=tonnage,
                            ni=ni,
                            co=co,
                            fe=fe,
                            al2o3=al2o3,
                            cao=cao,
                            cr2o3=cr2o3,
                            mno=mno,
                            mgo=mgo,
                            p=p,
                            sio2=sio2,
                            s=s,
                            mc=mc,
                            sm=sm,
                            start_date=start,
                            end_date=finish,
                            check_duplicated=duplicates,
                            task_id=import_selling_official.request.id,
                        )
                    )
                    duplicate_imports += 1
                    duplicates.append(f"Updated at row {index}: {duplikat}")
                else:
                    # Jika belum ada, tambahkan ke daftar insert
                    list_objects.append(
                        SellingOfficial(
                            id_surveyor=id_surveyor,
                            type_selling=type_sale,
                            id_factory=id_factory,
                            so_number=so_number,
                            product_code=code,
                            tonnage=tonnage,
                            ni=ni,
                            co=co,
                            fe=fe,
                            al2o3=al2o3,
                            cao=cao,
                            cr2o3=cr2o3,
                            mno=mno,
                            mgo=mgo,
                            p=p,
                            sio2=sio2,
                            s=s,
                            mc=mc,
                            sm=sm,
                            start_date=start,
                            end_date=finish,
                            check_duplicated=duplicates,
                            task_id=import_selling_official.request.id,
                        )
                    )
                    successful_imports += 1

            # Simpan semua insert dengan bulk_create
            if list_objects:
                SellingOfficial.objects.bulk_create(list_objects, batch_size=200)

            # Simpan semua update dengan bulk_update
            if update_objects:
                SellingOfficial.objects.bulk_update(update_objects, [
                    "id_surveyor", "type_selling", "id_factory", "so_number",
                    "product_code", "tonnage",   
                    "ni","co","fe","al2o3","cao","cr2o3","mno","mgo","p" ,"sio2","s","mc","sm"
                ], batch_size=200)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Buat laporan import
    taskImports.objects.create(
        task_id             =import_selling_official.request.id, 
        successful_imports  =successful_imports,
        failed_imports      =len(errors),
        duplicate_imports   =duplicate_imports,
        errors              ="\n".join(errors) if errors else None,
        duplicates          ="\n".join(duplicates) if duplicates else None,
        file_name           =original_file_name,
        destination         ='Selling Official',
    )

    if errors or duplicates:
        return {'message': 'Import completed with some errors or duplicates', 'errors': errors, 'duplicates': duplicates}
    else:
        return {'message': 'Import successful'}
