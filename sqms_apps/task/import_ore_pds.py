from celery import shared_task
import pandas as pd
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.ore_productions_model import OreProductions
from ..models.materials_model import Material
from ..models.block_model import Block
from ..models.source_model import SourceMinesLoading,SourceMinesDumping,SourceMinesDome

@shared_task
def import_ore_productions(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_objects = []
    successful_imports = 0

    #Konversi kolom ke datetime dengan format yang sesuai
    df['Date_Production'] = pd.to_datetime(df['Date_Production'], format='%Y-%m-%d', errors='coerce')

    # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
    source_dict     = dict(SourceMinesLoading.objects.values_list('loading_point', 'id'))
    block_dict      = dict(Block.objects.values_list('mine_block', 'id'))
    material_dict   = dict(Material.objects.values_list('nama_material', 'id'))
    stockpile_dict  = dict(SourceMinesDumping.objects.values_list('dumping_point', 'id'))
    dome_dict       = dict(SourceMinesDome.objects.values_list('pile_id', 'id'))
      

    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                date_pds        = row['Date_Production']
                shift           = row['Shift']
                source          = row['Prospect_Area']
                block           = row['Mine_Block']
                rl_from         = row['From']
                rl_to           = row['To']
                nama_material   = row['Layer']
                grade           = row['Ni_GradeEx']
                grade_control   = row['Grade_Control']
                truck           = row['Unit_Truck']
                stockpile       = row['Stockpile']
                dome            = row['Pile_ID']
                batch           = row['Batch_Code']
                increment       = row['Incerment']
                status_batch    = row['Batch_Status']
                ritase          = row['Ritase']
                tonnage         = row['Tonnage']
                status_pile     = row['Pile_Status']
                remarks         = row['Remarks']
                class_ore       = row['Ore_Class']

                remarks = None if pd.isna(remarks) else remarks
                
                # Cari ID dari Model berdasarkan nama
                id_source         = source_dict.get(source, None)  
                id_block          = block_dict.get(block, None)  
                id_material       = material_dict.get(nama_material, None) 
                id_pile           = dome_dict.get(dome, None) 
                id_stockpile      = stockpile_dict.get(stockpile, None)  
               
                # Gabungkan Kode
                kode_batch   = 'PDS' + str(id_material) + truck + str(id_stockpile) + str(id_pile) + batch
                status_dome  = 'Continue'

                if date_pds:  # Pastikan tanggal bukan None
                    date_str  = date_pds.strftime('%Y-%m-%d')
                    date_obj  = datetime.strptime(date_str, '%Y-%m-%d')
                    left_date = date_obj.day
                else:
                    left_date = None

                # Menentukan nilai sale_adjust berdasarkan nilai Layer
                if nama_material == 'LIM':
                    sale_adjust = 'HPAL'
                elif nama_material == 'SAP':
                    sale_adjust = 'RKEF'
                else:
                    sale_adjust = None  # Atau bisa set default value lainnya    

                try:
                    data = OreProductions(
                        tgl_production=date_pds,
                        shift=shift,
                        id_prospect_area=id_source,
                        id_block=id_block,
                        from_rl =rl_from,
                        to_rl=rl_to,
                        id_material=id_material,
                        grade_expect=grade,
                        grade_control=grade_control,
                        unit_truck=truck,
                        id_stockpile=id_stockpile,
                        id_pile=id_pile,
                        batch_code=batch,
                        increment=increment,
                        batch_status=status_batch,
                        ritase=ritase,
                        tonnage=tonnage,
                        pile_status=status_pile,
                        remarks=remarks,
                        kode_batch=kode_batch,
                        pile_original=id_pile,
                        stockpile_ori=id_stockpile,
                        left_date=left_date,
                        truck_factor=truck,
                        ore_class=class_ore,
                        status_dome=status_dome,
                        sale_adjust=sale_adjust,
                    )
                    list_objects.append(data)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            OreProductions.objects.bulk_create(list_objects, batch_size=1000)
    
    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Buat laporan import
    taskImports.objects.create(
        task_id             =import_ore_productions.request.id, 
        successful_imports  =successful_imports,
        failed_imports      =len(errors),
        duplicate_imports   =0,
        errors              ="\n".join(errors) if errors else None,
        duplicates          ="\n".join(duplicates) if duplicates else None,
        file_name           =original_file_name,
        destination         ='Ore Productions',
    )

    if errors or duplicates:
        return {'message': 'Import completed with some errors or duplicates', 'errors': errors, 'duplicates': duplicates}
    else:
        return {'message': 'Import successful'}
