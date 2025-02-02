from celery import shared_task
import pandas as pd
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.mine_productions_model import mineQuickProductions
from ..models.materials_model import Material
from ..models.source_model import SourceMines,SourceMinesLoading,SourceMinesDumping,SourceMinesDome

@shared_task
def import_mine_productions_quick(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_objects = []
    successful_imports = 0

    #Konversi kolom ke datetime dengan format yang sesuai
    df['Date Production'] = pd.to_datetime(df['Date Production'], format='%Y-%m-%d', errors='coerce')
    # Ambil hanya tanggal (tanpa waktu)
    df['Date Production'] = df['Date Production'].dt.date

    # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
    source_dict    = dict(SourceMines.objects.values_list('sources_area', 'id'))
    loading_dict   = dict(SourceMinesLoading.objects.values_list('loading_point', 'id'))
    dumping_dict   = dict(SourceMinesDumping.objects.values_list('dumping_point', 'id'))
    dome_dict      = dict(SourceMinesDome.objects.values_list('pile_id', 'id'))
    # block_dict     = dict(Block.objects.values_list('mine_block', 'id'))
    material_dict  = dict(Material.objects.values_list('nama_material', 'id'))

    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                date_pds        = row['Date Production']
                time            = row['Time']
                vendors         = row['Vendors']
                shift           = row['Shift']
                loader          = row['Loader']
                hauler          = row['Hauler']
                hauler_class    = row['Hauler Class']
                source          = row['Sources']
                loading_point   = row['Loading Point']
                dumping_point   = row['Dumping Point']
                dome_id         = row['Pile Id']
                nama_material   = row['Material']
                category_mine   = row['Category']
                distance        = row['Distance']
                # block           = row['Block Id']
                # rl_from         = row['From Rl']
                # rl_to           = row['To Rl']
                ritase          = row['Ritase']
                bcm             = row['Bcm']
                tonnage         = row['Tonnage']
                remarks         = row['Remarks']

                # Tambahkan leading zero untuk time jika nilainya antara 0-9
                if isinstance(time, int) and 0 <= time <= 9:
                    time = f"0{time}"

                vendors       = None if pd.isna(vendors) else vendors
                category_mine = None if pd.isna(category_mine) else category_mine
                # rl_from       = None if pd.isna(rl_from) else rl_from
                # rl_to         = None if pd.isna(rl_to) else rl_to
                distance      = None if pd.isna(distance) else distance
                remarks       = None if pd.isna(remarks) else remarks

                # Cari ID dari Model berdasarkan nama
                id_source   = source_dict.get(source, 1)  
                id_loading  = loading_dict.get(loading_point, 1)  
                id_dumping  = dumping_dict.get(dumping_point, 1)  
                id_dome     = dome_dict.get(dome_id, 1)  
                # id_block    = block_dict.get(block, None)  
                id_material = material_dict.get(nama_material, None) 

                hauler_class = str(hauler_class) if pd.notna(hauler_class) else ''

                # Modifikasi hauler
                if isinstance(hauler_class, str):
                    if 'ADT' in hauler_class:
                        type_hauler = 'ADT'
                    elif 'Dump Truck' in hauler_class:
                    # elif any(dump in hauler_class for dump in ['Dump Truck 20 Ton', 'Dump Truck 30 Ton', 'Dump Truck 40 Ton']):    
                        type_hauler = 'DT'
                    else:
                        type_hauler = None
                else:
                    type_hauler = None  # Jika hauler_class bukan string       


                # Gabungkan Kode referensi
                materials_ref = f"{date_pds}{category_mine}{source}{vendors}".replace(" ", "")
                truck_ref     = f"{date_pds}{category_mine}{source}{vendors}{type_hauler}".replace(" ", "")

                if date_pds:  # Pastikan tanggal bukan None
                    date_str  = date_pds.strftime('%Y-%m-%d')
                    date_obj  = datetime.strptime(date_str, '%Y-%m-%d')
                    left_date = date_obj.day
                else:
                    left_date = None

                try:
                    data = mineQuickProductions(
                        date_production=date_pds,
                        vendors=vendors,
                        shift=shift,
                        loader=loader,
                        hauler=hauler,
                        hauler_class=hauler_class,
                        sources=id_source,
                        loading_point=id_loading,
                        dumping_point=id_dumping,
                        dome_id=id_dome,
                        distance=distance,
                        category_mine=category_mine,
                        # block_id=id_block,
                        # from_rl =rl_from,
                        # to_rl=rl_to,
                        id_material=id_material,
                        ritase=ritase,
                        bcm=bcm,
                        tonnage=tonnage,
                        time_loading=time,
                        remarks=remarks,
                        hauler_type=type_hauler,
                        ref_materials=materials_ref,
                        ref_plan_truck=truck_ref,
                        left_date=left_date,
                        task_id=import_mine_productions_quick.request.id,
                    )
                    list_objects.append(data)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            mineQuickProductions.objects.bulk_create(list_objects, batch_size=1000)
    
    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Buat laporan import
    taskImports.objects.create(
        task_id             =import_mine_productions_quick.request.id, 
        successful_imports  =successful_imports,
        failed_imports      =len(errors),
        duplicate_imports   =0,
        errors              ="\n".join(errors) if errors else None,
        duplicates          ="\n".join(duplicates) if duplicates else None,
        file_name           =original_file_name,
        destination         ='Mine Productions Quick',
    )

    if errors or duplicates:
        return {'message': 'Import completed with some errors or duplicates', 'errors': errors, 'duplicates': duplicates}
    else:
        return {'message': 'Import successful'}
