from celery import shared_task
import pandas as pd
import re
from django.db.models import F, Func
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.task_model import UploadLog
from ..models.selling_data_model import SellingProductions
from ..models.materials_model import Material
from ..models.stock_factories_model import StockFactories
from ..models.selling_dome_model import SellingDomeTemp
from ..models.selling_stock_model import SellingStockTemp
from ..models.mine_units_model import MineUnits
from ..models.source_model import SourceMinesDumping,SourceMinesDome
from django.db.models.functions import Trim

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
def import_selling_rkef(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0

    try:
        # Pastikan format tanggal sesuai
        df['date_gwt'] = df['date_gwt'].fillna(pd.Timestamp('1900-01-01')).dt.strftime('%Y-%m-%d %H:%M:%S')
        df['date_ewt'] = df['date_ewt'].fillna(pd.Timestamp('1900-01-01')).dt.strftime('%Y-%m-%d %H:%M:%S')
        df['load_date'] = pd.to_datetime(df['load_date']).dt.date
        df['weighing_date'] = pd.to_datetime(df['weighing_date']).dt.date

        # Buat dictionary untuk pencarian ID berdasarkan nama
        material_dict = dict(Material.objects.annotate(trimmed_material=Trim('nama_material')).values_list('trimmed_material', 'id'))
        dome_dict = dict(SourceMinesDome.objects.annotate(trimmed_dome=Trim('pile_id')).values_list('trimmed_dome', 'id'))
        factory_dict = dict(StockFactories.objects.annotate(trimmed_fact=Trim('factory_stock')).values_list('trimmed_fact', 'id'))
        dome_temp_dict = dict(SellingDomeTemp.objects.annotate(trim_dome=Trim('temp_dome')).values_list('trim_dome', 'id'))
        stock_temp_dict = dict(SellingStockTemp.objects.annotate(trim_stock=Trim('temp_stock')).values_list('trim_stock', 'id'))

        # Kolom angka yang perlu dibersihkan
        numeric_columns = ['netto', 'gross', 'empty']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        # Kolom yang boleh tetap kosong
        empty_columns = ['stockpile_temp', 'dome_temp', 'buyer', 'product_code', 'scci_gps', 'scci_sl', 'awk_inc', 'awk_sl', 'nota']
        for col in empty_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: None if pd.isna(x) or x == '' else x)

        existing_records = SellingProductions.objects.filter(haulage_code__in=df['haulage_code'].tolist())
        existing_dict = {record.haulage_code: record for record in existing_records}
        new_objects = []
        update_objects = []

        with transaction.atomic():
            for index, row in df.iterrows():
                haulage_code = row['haulage_code']
                data = {
                    "nota": row['nota'],
                    "timbang_isi": row['date_gwt'],
                    "timbang_kosong": row['date_ewt'],
                    "id_material": material_dict.get(row['material'], None),
                    "unit_code": row['no_truck'],
                    "delivery_order": row['product_code'],
                    "empety_weigth_f": row['empty'],
                    "fill_weigth_f": row['gross'],
                    "netto_weigth_f": row['netto'],
                    "id_factory": factory_dict.get(row['buyer'], None),
                    "id_pile": dome_dict.get(row['dome_ori'], None),
                    "id_stock_temp": stock_temp_dict.get(row['stockpile_temp'], None),
                    "id_dome_temp": dome_temp_dict.get(row['dome_temp'], None),
                    "tgl_hauling": row['load_date'],
                    "time_hauling": "00:00:00",
                    "shift": row['shift'],
                    "left_date": row['weighing_date'].day if row['weighing_date'] else None,
                    "new_scci": row['scci_gps'],
                    "new_scci_sub": row['scci_sl'],
                    "new_kode_batch_scci": f"{row['sale_code']}Split_SCCI{material_dict.get(row['material'], '')}{row['product_code']}{row['scci_sl']}",
                    "scci_order": "Yes",
                    "new_awk": row['awk_inc'],
                    "new_awk_sub": row['awk_sl'],
                    "new_kode_batch_awk": f"{row['sale_code']}Split_AWK{material_dict.get(row['material'], '')}{row['product_code']}{row['awk_sl']}",
                    "new_batch_awk_pulp": f"{row['sale_code']}Split_AWK{row['product_code']}{row['awk_sl']}",
                    "awk_order": "Yes",
                    "type_selling": row['type_sale'],
                    "load_code": row['load_code'],
                    "haulage_code": haulage_code,
                    "date_wb": row['weighing_date'],
                    "sale_adjust": "RKEF",
                    "sale_dome": "Continue",
                }

                if haulage_code in existing_dict:
                    for key, value in data.items():
                        setattr(existing_dict[haulage_code], key, value)
                    update_objects.append(existing_dict[haulage_code])
                else:
                    new_objects.append(SellingProductions(**data))

            if new_objects:
                SellingProductions.objects.bulk_create(new_objects, batch_size=200)
            if update_objects:
                SellingProductions.objects.bulk_update(update_objects, [field for field in data.keys()], batch_size=200)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")


    # Buat laporan impor
    taskImports.objects.create(
        task_id             =import_selling_rkef.request.id, 
        successful_imports  =successful_imports,
        failed_imports      =len(errors),
        duplicate_imports   =duplicate_imports,
        errors              ="\n".join(errors) if errors else None,
        duplicates          ="\n".join(duplicates) if duplicates else None,
        file_name           =original_file_name,
        destination         ='Selling RKEF',
    )

    if errors or duplicates:
        return {'message': 'Import completed with some errors or duplicates', 'errors': errors, 'duplicates': duplicates}
    else:
        return {'message': 'Import successful'}
