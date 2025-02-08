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
    update_objects = []
    successful_imports = 0
    duplicate_imports = 0

    try:
        # Konversi kolom tanggal
        df['date_gwt']      = df['date_gwt'].fillna(pd.Timestamp('1900-01-01')).dt.strftime('%Y-%m-%d %H:%M:%S')
        df['date_ewt']      = df['date_ewt'].fillna(pd.Timestamp('1900-01-01')).dt.strftime('%Y-%m-%d %H:%M:%S')
        df['load_date']     = pd.to_datetime(df['load_date']).dt.date
        df['weighing_date'] = pd.to_datetime(df['weighing_date']).dt.date

        # Buat dictionary dari tabel referensi
        material_dict   = dict(Material.objects.annotate(trimmed_material=Trim('nama_material')).values_list('trimmed_material', 'id'))
        dome_dict       = dict(SourceMinesDome.objects.annotate(trimmed_dome=Trim('pile_id')).values_list('trimmed_dome', 'id'))
        factory_dict    = dict(StockFactories.objects.annotate(trimmed_fact=Trim('factory_stock')).values_list('trimmed_fact', 'id'))
        dome_temp_dict  = dict(SellingDomeTemp.objects.annotate(trim_dome=Trim('temp_dome')).values_list('trim_dome', 'id'))
        stock_temp_dict = dict(SellingStockTemp.objects.annotate(trim_stock=Trim('temp_stock')).values_list('trim_stock', 'id'))

        # Membersihkan kolom numerik
        numeric_columns = ['netto', 'gross', 'empty']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        # Kolom yang harus None jika kosong
        empty_columns = ['stockpile_temp', 'dome_temp', 'buyer', 'product_code', 'scci_gps', 'scci_sl', 'awk_inc', 'awk_sl', 'nota']
        for col in empty_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: None if pd.isna(x) or x == '' else x)

        # Ambil semua haulage_code yang sudah ada dalam database
        # existing_data = SellingProductions.objects.filter(haulage_code__in=df['haulage_code'].unique()).in_bulk(field_name='haulage_code')
        existing_data = SellingProductions.objects.filter(haulage_code__in=df['haulage_code'].unique())

        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    haulage_code = row['haulage_code']
                    if pd.isna(haulage_code) or haulage_code == '':
                        errors.append(f"Row {index}: No Seri kosong.")
                        continue

                    # Konversi ID berdasarkan dictionary lookup
                    id_material     = material_dict.get(row['material'], None)
                    id_pile         = dome_dict.get(row['dome_ori'], None)
                    id_stock_temp   = stock_temp_dict.get(row['stockpile_temp'], None)
                    id_dome_temp    = dome_temp_dict.get(row['dome_temp'], None)
                    id_factory      = factory_dict.get(row['buyer'], None)

                    # Format kode batch
                    new_kode_batch_scci = f"{row['sale_code']}Split_SCCI{str(id_material) if id_material else ''}{row['product_code']}{row['scci_sl'] if row['scci_sl'] else ''}"
                    new_kode_batch_awk = f"{row['sale_code']}Split_AWK{str(id_material) if id_material else ''}{row['product_code']}{row['awk_sl'] if row['awk_sl'] else ''}"
                    new_batch_awk_pulp = f"{row['sale_code']}Split_AWK{row['product_code']}{row['awk_sl'] if row['awk_sl'] else ''}"

                    # Konversi tanggal
                    weighing_date = row['weighing_date']
                    left_date = weighing_date.day if weighing_date else None

                    # Jika data sudah ada, lakukan update
                    if haulage_code in existing_data:
                        existing_entry = existing_data[haulage_code]
                        existing_entry.nota = row['nota']
                        existing_entry.timbang_isi = row['date_gwt']
                        existing_entry.timbang_kosong = row['date_ewt']
                        existing_entry.id_material = id_material
                        existing_entry.unit_code = row['no_truck']
                        existing_entry.delivery_order = row['product_code']
                        existing_entry.empety_weigth_f = row['empty']
                        existing_entry.fill_weigth_f = row['gross']
                        existing_entry.netto_weigth_f = row['netto']
                        existing_entry.id_factory = id_factory
                        existing_entry.id_pile = id_pile
                        existing_entry.id_stock_temp = id_stock_temp
                        existing_entry.id_dome_temp = id_dome_temp
                        existing_entry.tgl_hauling = row['load_date']
                        existing_entry.time_hauling = '00:00:00'
                        existing_entry.shift = row['shift']
                        existing_entry.left_date = left_date
                        existing_entry.new_scci = row['scci_gps']
                        existing_entry.new_scci_sub = row['scci_sl']
                        existing_entry.new_kode_batch_scci = new_kode_batch_scci
                        existing_entry.scci_order = 'Yes'
                        existing_entry.new_awk = row['awk_inc']
                        existing_entry.new_awk_sub = row['awk_sl']
                        existing_entry.new_kode_batch_awk = new_kode_batch_awk
                        existing_entry.new_batch_awk_pulp = new_batch_awk_pulp
                        existing_entry.awk_order = 'Yes'
                        existing_entry.type_selling = row['type_sale']
                        existing_entry.load_code = row['load_code']
                        existing_entry.date_wb = weighing_date
                        existing_entry.sale_adjust = 'RKEF'
                        existing_entry.sale_dome = 'Continue'
                        
                        update_objects.append(existing_entry)
                        duplicate_imports += 1
                    else:
                        # Jika data belum ada, buat objek baru
                        data = SellingProductions(
                            nota=row['nota'],
                            timbang_isi=row['date_gwt'],
                            timbang_kosong=row['date_ewt'],
                            id_material=id_material,
                            unit_code=row['no_truck'],
                            delivery_order=row['product_code'],
                            empety_weigth_f=row['empty'],
                            fill_weigth_f=row['gross'],
                            netto_weigth_f=row['netto'],
                            id_factory=id_factory,
                            id_pile=id_pile,
                            id_stock_temp=id_stock_temp,
                            id_dome_temp=id_dome_temp,
                            tgl_hauling=row['load_date'],
                            time_hauling='00:00:00',
                            shift=row['shift'],
                            left_date=left_date,
                            new_scci=row['scci_gps'],
                            new_scci_sub=row['scci_sl'],
                            new_kode_batch_scci=new_kode_batch_scci,
                            scci_order='Yes',
                            new_awk=row['awk_inc'],
                            new_awk_sub=row['awk_sl'],
                            new_kode_batch_awk=new_kode_batch_awk,
                            new_batch_awk_pulp=new_batch_awk_pulp,
                            awk_order='Yes',
                            type_selling=row['type_sale'],
                            load_code=row['load_code'],
                            haulage_code=haulage_code,
                            date_wb=weighing_date,
                            sale_adjust='RKEF',
                            sale_dome='Continue',
                        )
                        list_objects.append(data)
                        successful_imports += 1
                except Exception as e:
                     errors.append(f"Row {index}: {str(e)}")
            # Simpan data baru dengan bulk_create
            if list_objects:
                SellingProductions.objects.bulk_create(list_objects, batch_size=200)

            # Update data yang sudah ada dengan bulk_update
            if update_objects:
                fields_to_update = ['nota', 'timbang_isi', 'timbang_kosong', 'id_material', 'unit_code', 'delivery_order', 
                                    'empety_weigth_f', 'fill_weigth_f', 'netto_weigth_f', 'id_factory', 'id_pile', 
                                    'id_stock_temp', 'id_dome_temp', 'tgl_hauling', 'time_hauling', 'shift', 'left_date',
                                    'new_scci', 'new_scci_sub', 'new_kode_batch_scci', 'scci_order', 'new_awk', 
                                    'new_awk_sub', 'new_kode_batch_awk', 'new_batch_awk_pulp', 'awk_order', 'type_selling', 
                                    'load_code', 'date_wb', 'sale_adjust', 'sale_dome']
                SellingProductions.objects.bulk_update(update_objects, fields=fields_to_update, batch_size=200)

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
