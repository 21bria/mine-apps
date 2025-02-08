from celery import shared_task
import pandas as pd
import re
from django.db.models.functions import Trim
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.selling_data_model import SellingProductions
from ..models.materials_model import Material
from ..models.stock_factories_model import StockFactories
from ..models.source_model import SourceMinesDumping,SourceMinesDome

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
def import_selling_hpal(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_objects = []
    update_objects = []
    successful_imports = 0
    duplicate_imports = 0

    try:
        # Konversi kolom tanggal
        df['timbang_isi']    = df['waktu_timbang_isi'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['timbang_kosong'] = df['waktu_timbang_kosong'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['tanggal']        = pd.to_datetime(df['tanggal']).dt.date

        # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
        material_dict   = dict(Material.objects.annotate(trimmed_material=Trim('nama_material')).values_list('trimmed_material', 'id'))
        dome_dict       = dict(SourceMinesDome.objects.annotate(trimmed_dome=Trim('pile_id')).values_list('trimmed_dome', 'id'))
        factory_dict    = dict(StockFactories.objects.annotate(trimmed_fact=Trim('factory_stock')).values_list('trimmed_fact', 'id'))

        # Membersihkan kolom numerik
        numeric_columns = ['berat_kotor', 'berat_kosong', 'berat_bersih']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        # Kolom yang harus None jika kosong
        empty_columns = ['no_seri', 'no_unit','nama_material','lokasi_pembongkaran','discharge','shift','code_hync','type','sale_type','batch','adjust_sale']
        for col in empty_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: None if pd.isna(x) or x == '' else x)

        # Ambil semua nota yang sudah ada dalam database
        # existing_data = SellingProductions.objects.filter(nota__in=df['no_seri'].unique()).in_bulk(field_name='nota')
        existing_data = SellingProductions.objects.filter(nota__in=df['no_seri'].unique())


        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    nota = row['no_seri']
                    if pd.isna(nota) or nota == '':
                        errors.append(f"Row {index}: No Seri kosong.")
                        continue

                    # Konversi ID berdasarkan dictionary lookup
                    id_material = material_dict.get(row['adjust_sale'], None)
                    id_pile     = dome_dict.get(row['dome'], None)
                    id_factory  = factory_dict.get(row['discharge'], None)

                    # Format kode batch
                    kode_batch_g = f"{row['type'].strip()}{str(id_material) if id_material else ''}{row['code_hync'].strip()}{row['batch'].strip()}"
                    new_kode_batch_scci = f"{row['type'].strip()}Split_SCCI{str(id_material) if id_material else ''}{row['code_hync']}{row['batch'].strip()}"
                    new_kode_batch_awk  = f"{row['type'].strip()}Split_AWK{str(id_material) if id_material else ''}{row['code_hync']}{row['batch'].strip()}"
                    new_batch_awk_pulp  = f"{row['type'].strip()}Split_AWK{row['code_hync']}{row['batch'].strip()}"

                    # Konversi tanggal
                    tanggal   = row['tanggal']
                    left_date = tanggal.day if tanggal else None

                    # Jika data sudah ada, lakukan update
                    if nota in existing_data:
                        existing_entry = existing_data[nota]
                        existing_entry.unit_code = row['no_unit']
                        existing_entry.id_material = id_material
                        existing_entry.empety_weigth_f = row['berat_kosong']
                        existing_entry.fill_weigth_f = row['berat_kotor']
                        existing_entry.netto_weigth_f = row['berat_bersih']
                        existing_entry.timbang_isi    = row['timbang_isi']
                        existing_entry.timbang_kosong = row['timbang_kosong']
                        existing_entry.remarks = row['lokasi_pembongkaran']
                        existing_entry.tgl_hauling = tanggal
                        existing_entry.time_hauling = '00:00:00'
                        existing_entry.id_pile = id_pile
                        existing_entry.id_factory = id_factory
                        existing_entry.shift = row['shift']
                        existing_entry.delivery_order = row['code_hync']
                        existing_entry.type_selling = row['sale_type']
                        existing_entry.batch = row['batch']
                        existing_entry.kode_batch_g = kode_batch_g
                        existing_entry.new_scci_sub = row['batch']
                        existing_entry.new_kode_batch_scci = new_kode_batch_scci
                        existing_entry.scci_order = 'No'
                        existing_entry.new_awk_sub = row['batch']
                        existing_entry.new_kode_batch_awk = new_kode_batch_awk
                        existing_entry.new_batch_awk_pulp = new_batch_awk_pulp
                        existing_entry.awk_order = 'Yes'
                        existing_entry.date_wb = tanggal
                        existing_entry.sale_adjust = 'HPAL'
                        existing_entry.sale_dome = 'Continue'
                        existing_entry.left_date = left_date
                        
                        update_objects.append(existing_entry)
                        duplicate_imports += 1
                    else:
                        # Jika data belum ada, buat objek baru
                        data = SellingProductions(
                            nota                = nota,
                            unit_code           = row['no_unit'],
                            id_material         = id_material,
                            empety_weigth_f     = row['berat_kosong'],
                            fill_weigth_f       = row['berat_kotor'],
                            netto_weigth_f      = row['berat_bersih'],
                            timbang_isi         = row['timbang_isi'],
                            timbang_kosong      = row['timbang_kosong'],
                            remarks             = row['lokasi_pembongkaran'],
                            tgl_hauling         = tanggal,
                            time_hauling        = '00:00:00',
                            id_pile             = id_pile,
                            id_factory          = id_factory,
                            shift               = row['shift'],
                            delivery_order      = row['code_hync'],
                            type_selling        = row['sale_type'],
                            batch               = row['batch'],
                            kode_batch_g        = kode_batch_g,
                            new_scci_sub        = row['batch'],
                            new_kode_batch_scci = new_kode_batch_scci,
                            scci_order          = 'No',
                            new_awk_sub         = row['batch'],
                            new_kode_batch_awk  = new_kode_batch_awk,
                            new_batch_awk_pulp  = new_batch_awk_pulp,
                            awk_order           = 'Yes',
                            date_wb             = tanggal,
                            sale_adjust         = 'HPAL',
                            sale_dome           = 'Continue',
                            left_date           = left_date
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
                fields_to_update = ['timbang_isi', 'timbang_kosong', 'id_material', 'unit_code', 'delivery_order', 
                                    'empety_weigth_f', 'fill_weigth_f', 'netto_weigth_f', 'id_factory', 'id_pile', 
                                    'tgl_hauling', 'time_hauling', 'shift', 'left_date',
                                    'batch','kode_batch_g','new_scci_sub', 'new_kode_batch_scci', 'scci_order',
                                    'new_awk_sub', 'new_kode_batch_awk', 'new_batch_awk_pulp', 'awk_order', 'type_selling', 
                                    'load_code', 'date_wb', 'sale_adjust', 'sale_dome']
                SellingProductions.objects.bulk_update(update_objects, fields=fields_to_update, batch_size=200)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Buat laporan import
    taskImports.objects.create(
        task_id             =import_selling_hpal.request.id, 
        successful_imports  =successful_imports,
        failed_imports      =len(errors),
        duplicate_imports   =duplicate_imports,
        errors              ="\n".join(errors) if errors else None,
        duplicates          ="\n".join(duplicates) if duplicates else None,
        file_name           =original_file_name,
        destination         ='Selling HPAL'
    )

    if errors or duplicates:
        return {'message': 'Import completed with some errors or duplicates', 'errors': errors, 'duplicates': duplicates}
    else:
        return {'message': 'Import successful'}
