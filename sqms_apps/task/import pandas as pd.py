from celery import shared_task
import pandas as pd
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.mine_productions_model import mineProductions
from ..models.materials_model import Material
from ..models.source_model import SourceMines,SourceMinesDumping
from ..models.block_model import Block

def transpose_and_import_data(file_path):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_objects = []
    successful_imports = 0

    # Konversi kolom ke datetime dengan format yang sesuai
    df['Date Production'] = pd.to_datetime(df['Date Production'], format='%Y-%m-%d', errors='coerce')

    # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
    source_dict = dict(SourceMines.objects.values_list('sources_area', 'id'))
    dumping_dict = dict(SourceMinesDumping.objects.values_list('dumping_point', 'id'))
    block_dict = dict(Block.objects.values_list('mine_block', 'id'))
    material_dict = dict(Material.objects.values_list('nama_material', 'id'))

    # Kolom non-waktu (kolom tetap yang tidak perlu ditranspose)
    non_time_columns = ['Date Production', 'Vendors', 'Shift', 'Loader', 'Hauler', 'Hauler Class', 
                        'Sources', 'Loading Point', 'Dumping Point', 'Pile Id', 'Material', 
                        'Category', 'Distance', 'Block Id', 'From Rl', 'To Rl', 'Bcm', 'Tonnage', 'Remarks']

    # Kolom waktu dimulai dari kolom yang mengandung jam (dalam hal ini: 07:00, 08:00, dst.)
    time_columns = df.columns[len(non_time_columns):]  # Mulai dari kolom waktu
    
    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            # Loop untuk setiap baris di DataFrame
            for index, row in df.iterrows():
                # Transpose setiap kolom waktu dan masukkan ke dalam database
                for time_col in time_columns:
                    time_value = row[time_col]
                    if pd.notna(time_value):  # Jika ada data ritase
                        date_pds = row['Date Production']
                        shift = row['Shift']
                        loader = row['Loader']
                        hauler = row['Hauler']
                        hauler_class = row['Hauler Class']
                        source = row['Loading Point']
                        dumping = row['Dumping Point']
                        nama_material = row['Material']
                        category_mine = row['Category']
                        distance = row['Distance']
                        block = row['Block Id']
                        rl_from = row['From Rl']
                        rl_to = row['To Rl']
                        bcm = row['Bcm']
                        tonnage = row['Tonnage']
                        remarks = row['Remarks']

                        rl_from = None if pd.isna(rl_from) else rl_from
                        rl_to = None if pd.isna(rl_to) else rl_from
                        remarks = None if pd.isna(remarks) else remarks

                        # Cari ID dari Model berdasarkan nama
                        id_source = source_dict.get(source, None)
                        id_dumping = dumping_dict.get(dumping, None)
                        id_block = block_dict.get(block, None)
                        id_material = material_dict.get(nama_material, None)

                        try:
                            data = mineProductions(
                                date_production=date_pds,
                                shift=shift,
                                loader=loader,
                                hauler=hauler,
                                hauler_class=hauler_class,
                                loading_point=id_source,
                                dumping_point=id_dumping,
                                category_mine=category_mine,
                                time_loading=pd.to_datetime(time_col).time(),  # Hanya ambil waktu
                                block_id=id_block,
                                from_rl=rl_from,
                                to_rl=rl_to,
                                id_material=id_material,
                                ritase=1,  # Tetap 1 untuk setiap baris
                                bcm=bcm,
                                tonnage=tonnage,
                                remarks=remarks,
                                ref_materials='',
                                left_date=date_pds.day if date_pds else None,
                                # task_id=import_mine_productions.request.id,
                            )
                            list_objects.append(data)
                            successful_imports += 1
                        except Exception as e:
                            errors.append(f"Error at row {index}: {str(e)}")
                            continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            mineProductions.objects.bulk_create(list_objects, batch_size=1000)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")



import pandas as pd
from datetime import datetime
from django.db import transaction

def transpose_and_import_data(file_path):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_objects = []
    successful_imports = 0

    # Konversi kolom ke datetime dengan format yang sesuai
    df['Date Production'] = pd.to_datetime(df['Date Production'], format='%Y-%m-%d', errors='coerce')

    # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
    source_dict =  dict(SourceMines.objects.values_list('sources_area', 'id'))
    dumping_dict = dict(SourceMinesDumping.objects.values_list('dumping_point', 'id'))
    block_dict = dict(Block.objects.values_list('mine_block', 'id'))
    material_dict = dict(Material.objects.values_list('nama_material', 'id'))

    # Kolom non-waktu (kolom tetap yang tidak perlu ditranspose)
    non_time_columns = ['Date Production', 'Vendors', 'Shift', 'Loader', 'Hauler', 'Hauler Class', 
                        'Sources', 'Loading Point', 'Dumping Point', 'Pile Id', 'Material', 
                        'Category', 'Distance', 'Block Id', 'From Rl', 'To Rl', 'Bcm', 'Tonnage', 'Remarks']

    # Kolom waktu dimulai dari kolom yang mengandung jam (seperti 07:00, 08:00, dst.)
    time_columns = df.columns[len(non_time_columns):]  # Mulai dari kolom waktu
    
    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            # Loop untuk setiap baris di DataFrame
            for index, row in df.iterrows():
                # Transpose setiap kolom waktu dan masukkan ke dalam database
                for time_col in time_columns:
                    time_value = row[time_col]
                    if pd.notna(time_value):  # Jika ada data ritase
                        date_pds = row['Date Production']
                        shift = row['Shift']
                        loader = row['Loader']
                        hauler = row['Hauler']
                        hauler_class = row['Hauler Class']
                        source = row['Loading Point']
                        dumping = row['Dumping Point']
                        nama_material = row['Material']
                        category_mine = row['Category']
                        distance = row['Distance']
                        block = row['Block Id']
                        rl_from = row['From Rl']
                        rl_to = row['To Rl']
                        bcm = row['Bcm']
                        tonnage = row['Tonnage']
                        remarks = row['Remarks']

                        rl_from = None if pd.isna(rl_from) else rl_from
                        rl_to = None if pd.isna(rl_to) else rl_from
                        remarks = None if pd.isna(remarks) else remarks

                        # Cari ID dari Model berdasarkan nama
                        id_source = source_dict.get(source, None)
                        id_dumping = dumping_dict.get(dumping, None)
                        id_block = block_dict.get(block, None)
                        id_material = material_dict.get(nama_material, None)

                        # Ambil waktu dari header (misal: 07:00) dan buat datetime
                        time_loading = pd.to_datetime(time_col).time()  # Hanya ambil waktu dari header
                        
                        try:
                            data = mineProductions(
                                date_production=date_pds,
                                shift=shift,
                                loader=loader,
                                hauler=hauler,
                                hauler_class=hauler_class,
                                loading_point=id_source,
                                dumping_point=id_dumping,
                                category_mine=category_mine,
                                time_loading=time_loading,  # Set Time sesuai header
                                block_id=id_block,
                                from_rl=rl_from,
                                to_rl=rl_to,
                                id_material=id_material,
                                ritase=1,  # Tetap 1 untuk setiap baris
                                bcm=bcm,
                                tonnage=tonnage,
                                remarks=remarks,
                                ref_materials='',
                                left_date=date_pds.day if date_pds else None,
                                # task_id=import_mine_productions.request.id,
                            )
                            list_objects.append(data)
                            successful_imports += 1
                        except Exception as e:
                            errors.append(f"Error at row {index}: {str(e)}")
                            continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            mineProductions.objects.bulk_create(list_objects, batch_size=1000)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

# 
def transpose_and_import_data(file_path):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_objects = []
    successful_imports = 0

    # Konversi kolom ke datetime dengan format yang sesuai
    df['Date Production'] = pd.to_datetime(df['Date Production'], format='%Y-%m-%d', errors='coerce')

    # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
    source_dict = dict(SourceMines.objects.values_list('sources_area', 'id'))
    dumping_dict = dict(SourceMinesDumping.objects.values_list('dumping_point', 'id'))
    block_dict = dict(Block.objects.values_list('mine_block', 'id'))
    material_dict = dict(Material.objects.values_list('nama_material', 'id'))

    # Kolom non-waktu (kolom tetap yang tidak perlu ditranspose)
    non_time_columns = ['Date Production', 'Vendors', 'Shift', 'Loader', 'Hauler', 'Hauler Class', 
                        'Sources', 'Loading Point', 'Dumping Point', 'Pile Id', 'Material', 
                        'Category', 'Distance', 'Block Id', 'From Rl', 'To Rl', 'Bcm', 'Tonnage', 'Remarks']

    # Kolom waktu dimulai dari kolom yang mengandung jam (seperti 07:00, 08:00, dst.)
    time_columns = df.columns[len(non_time_columns):]  # Mulai dari kolom waktu
    
    # Filter valid time columns
    valid_time_columns = [col for col in time_columns if pd.to_datetime(df[col], format='%H:%M', errors='coerce').notna().all()]

    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            # Loop untuk setiap baris di DataFrame
            for index, row in df.iterrows():
                # Transpose setiap kolom waktu dan masukkan ke dalam database
                for time_col in valid_time_columns:
                    time_value = row[time_col]
                    if pd.notna(time_value):  # Jika ada data ritase
                        date_pds = row['Date Production']
                        shift = row['Shift']
                        loader = row['Loader']
                        hauler = row['Hauler']
                        hauler_class = row['Hauler Class']
                        source = row['Loading Point']
                        dumping = row['Dumping Point']
                        nama_material = row['Material']
                        category_mine = row['Category']
                        distance = row['Distance']
                        block = row['Block Id']
                        rl_from = row['From Rl']
                        rl_to = row['To Rl']
                        bcm = row['Bcm']
                        tonnage = row['Tonnage']
                        remarks = row['Remarks']

                        rl_from = None if pd.isna(rl_from) else rl_from
                        rl_to = None if pd.isna(rl_to) else rl_from
                        remarks = None if pd.isna(remarks) else remarks

                        # Cari ID dari Model berdasarkan nama
                        id_source = source_dict.get(source, None)
                        id_dumping = dumping_dict.get(dumping, None)
                        id_block = block_dict.get(block, None)
                        id_material = material_dict.get(nama_material, None)

                        # Ambil waktu dari header (misal: 07:00) dan buat datetime
                        time_loading = pd.to_datetime(time_col).time()  # Hanya ambil waktu dari header
                        
                        try:
                            data = mineProductions(
                                date_production=date_pds,
                                shift=shift,
                                loader=loader,
                                hauler=hauler,
                                hauler_class=hauler_class,
                                loading_point=id_source,
                                dumping_point=id_dumping,
                                category_mine=category_mine,
                                time_loading=time_loading,  # Set Time sesuai header
                                block_id=id_block,
                                from_rl=rl_from,
                                to_rl=rl_to,
                                id_material=id_material,
                                ritase=1,  # Tetap 1 untuk setiap baris
                                bcm=bcm,
                                tonnage=tonnage,
                                remarks=remarks,
                                ref_materials='',
                                left_date=date_pds.day if date_pds else None,
                                # task_id=import_mine_productions.request.id,
                            )
                            list_objects.append(data)
                            successful_imports += 1
                        except Exception as e:
                            errors.append(f"Error at row {index}: {str(e)}")
                            continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            mineProductions.objects.bulk_create(list_objects, batch_size=1000)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")


import pandas as pd
from datetime import datetime, timedelta
from django.db import transaction

import pandas as pd

from django.db import transaction

def transpose_and_import_data(file_path):
    df = pd.read_excel(file_path)
    errors = []
    list_objects = []
    successful_imports = 0

    # Convert date column to datetime format
    df['Date Production'] = pd.to_datetime(df['Date Production'], format='%Y-%m-%d', errors='coerce')

    # Create dictionaries for ID lookup
    source_dict = dict(SourceMines.objects.values_list('sources_area', 'id'))
    dumping_dict = dict(SourceMinesDumping.objects.values_list('dumping_point', 'id'))
    block_dict = dict(Block.objects.values_list('mine_block', 'id'))
    material_dict = dict(Material.objects.values_list('nama_material', 'id'))

    # Non-time columns
    non_time_columns = ['Date Production', 'Vendors', 'Shift', 'Loader', 'Hauler', 'Hauler Class', 
                        'Sources', 'Loading Point', 'Dumping Point', 'Pile Id', 'Material', 
                        'Category', 'Distance', 'Block Id', 'From Rl', 'To Rl', 'Bcm', 'Tonnage', 'Remarks']

    # Time columns starting after non-time columns
    time_columns = df.columns[len(non_time_columns):]  
    
    # Filter valid time columns
    valid_time_columns = [col for col in time_columns if pd.to_datetime(col, format='%H:%M', errors='coerce').notna().all()]

    # Start transaction
    try:
        with transaction.atomic():
            # Loop through each row
            for index, row in df.iterrows():
                # Retrieve non-time data
                date_pds = row['Date Production']
                shift = row['Shift']
                loader = row['Loader']
                hauler = row['Hauler']
                hauler_class = row['Hauler Class']
                source = row['Loading Point']
                dumping = row['Dumping Point']
                nama_material = row['Material']
                category_mine = row['Category']
                distance = row['Distance']
                block = row['Block Id']
                rl_from = row['From Rl'] if not pd.isna(row['From Rl']) else None
                rl_to = row['To Rl'] if not pd.isna(row['To Rl']) else None
                bcm = row['Bcm']
                tonnage = row['Tonnage']
                remarks = row['Remarks'] if not pd.isna(row['Remarks']) else None

                # Get IDs from dictionaries
                id_source = source_dict.get(source)
                id_dumping = dumping_dict.get(dumping)
                id_block = block_dict.get(block)
                id_material = material_dict.get(nama_material)

                # Process each valid time column
                for time_col in valid_time_columns:
                    base_time = pd.to_datetime(time_col, format='%H:%M:%S').time()  # Get the base time from the header

                    # Iterate through the remaining columns in the same row for minutes
                    for idx, minute_value in enumerate(row[time_columns.get_loc(time_col):]):
                        if pd.notna(minute_value):  # If there's a value in the minute cell
                            # Calculate final time
                            final_time = (datetime.combine(date_pds, base_time) + timedelta(minutes=minute_value)).time()

                            try:
                                data = mineProductions(
                                    date_production=date_pds,
                                    shift=shift,
                                    loader=loader,
                                    hauler=hauler,
                                    hauler_class=hauler_class,
                                    loading_point=id_source,
                                    dumping_point=id_dumping,
                                    category_mine=category_mine,
                                    time_loading=final_time,
                                    block_id=id_block,
                                    from_rl=rl_from,
                                    to_rl=rl_to,
                                    id_material=id_material,
                                    ritase=1,
                                    bcm=bcm,
                                    tonnage=tonnage,
                                    remarks=remarks,
                                    ref_materials='',
                                    left_date=date_pds.day if date_pds else None,
                                    # task_id=import_mine_productions.request.id,
                                )
                                list_objects.append(data)
                                successful_imports += 1
                            except Exception as e:
                                errors.append(f"Error at row {index}, minute index {idx}: {str(e)}")
                                continue

            # Use bulk_create to save objects in batch
            mineProductions.objects.bulk_create(list_objects, batch_size=1000)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

