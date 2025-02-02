from celery import shared_task
import pandas as pd
import re
from django.db.models import F, Func
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.selling_data_model import SellingProductions
from ..models.materials_model import Material
from ..models.stock_factories_model import StockFactories
from ..models.mine_units_model import MineUnits
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
    successful_imports = 0
    duplicate_imports = 0

    
    # df['timbang_isi']  = pd.to_datetime(df['timbang_isi'], format='%H:%M:%S').dt.time

    df['timbang_isi']    = df['waktu_timbang_kosong'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['timbang_kosong'] = df['waktu_timbang_isi'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['tanggal']        = pd.to_datetime(df['tanggal']).dt.date


    # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
    # material_dict  = dict(Material.objects.values_list('nama_material', 'id'))
    # stockpile_dict = dict(SourceMinesDumping.objects.values_list('dumping_point', 'id'))
    # dome_dict      = dict(SourceMinesDome.objects.values_list('pile_id', 'id'))
    # factory_dict   = dict(StockFactories.objects.values_list('factory_stock', 'id'))
    # truck_dict     = dict(MineUnits.objects.values_list('unit_code', 'id'))

    material_dict = dict(
        (material.strip(), id) for material, id in Material.objects.values_list('nama_material', 'id')
    )

    stockpile_dict = dict(
        (stockpile.strip(), id) for stockpile, id in SourceMinesDumping.objects.values_list('dumping_point', 'id')
    )

    dome_dict = dict(
        (dome.strip(), id) for dome, id in SourceMinesDome.objects.values_list('pile_id', 'id')
    )

    factory_dict = dict(
        (factory.strip(), id) for factory, id in StockFactories.objects.values_list('factory_stock', 'id')
    )

    truck_dict = dict(
        (truck.strip(), id) for truck, id in MineUnits.objects.values_list('unit_code', 'id')
    )


    # Menentukan kolom yang perlu dibersihkan
    numeric_columns = [
        'berat_kotor', 'berat_kosong', 'berat_bersih',
       ]
        
    # Kolom yang diinginkan tetap kosong jika kosong
    empty_columns = [
            'no_seri', 'no_unit','nama_material','lokasi_pembongkaran','discharge','shift',
            'code_hync','type','sale_type','batch','adjust_sale'
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric)

     # Untuk kolom yang perlu tetap kosong jika kosong
    for col in empty_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: None if pd.isna(x) or x == '' else x)


    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                nota            = row['no_seri']
                truck           = row['no_unit']  
                nama_material   = row['adjust_sale']  
                empety_weigth_f = row['berat_kosong']          
                fill_weigth_f   = row['berat_kotor']  
                netto_weigth_f  = row['berat_bersih']    
                timbang_isi     = row['timbang_isi']
                timbang_kosong  = row['timbang_kosong']
                tujuan          = row['lokasi_pembongkaran']
                tanggal         = row['tanggal']
                dome            = row['dome']
                stockpile       = row['stockpile']
                discharge       = row['discharge']
                shift           = row['shift']
                delivery_order  = row['code_hync']   
                type            = row['type']   
                sale_type       = row['sale_type']   
                batch           = row['batch']  

                # Cari ID dari Product berdasarkan nama
                id_material  = material_dict.get(nama_material, None) 
                id_pile      = dome_dict.get(dome, None) 
                id_stockpile = stockpile_dict.get(stockpile, None)  
                id_factory   = factory_dict.get(discharge, None)  
                id_truck     = truck_dict.get(truck, None)  

                # Gabungkan Kode
                kode_batch_g        = type + str(id_material) + delivery_order + batch
                new_kode_batch_scci = type + 'Split_SCCI' + str(id_material) + delivery_order + batch
                new_kode_batch_awk  = type + 'Split_AWK' + str(id_material) + delivery_order + batch
                new_batch_awk_pulp  = type + 'Split_AWK' + delivery_order + batch
                scci_order   = 'No'
                awk_order    = 'Yes'
                sale_dome    = 'Continue'
                time_hauling = '00:00:00'
                batch_g      = '' 
                new_scci     = '' 
                new_awk      = '' 
               

                if tanggal:  # Pastikan tanggal bukan None
                    date_str  = tanggal.strftime('%Y-%m-%d')
                    date_obj  = datetime.strptime(date_str, '%Y-%m-%d')
                    left_date = date_obj.day
                else:
                    left_date = None

                # Cek duplikat berdasarkan kriteria
                if SellingProductions.objects.filter(nota=nota).exists():
                    duplicates.append(f"Duplicate at row {index}: {nota}")
                    duplicate_imports += 1
                    continue

                try:
                    data = SellingProductions(
                        nota=nota,
                        timbang_isi=timbang_isi,
                        timbang_kosong=timbang_kosong,
                        id_material=id_material,
                        remarks=tujuan,
                        id_truck=id_truck,
                        empety_weigth_f=empety_weigth_f,
                        fill_weigth_f=fill_weigth_f,
                        netto_weigth_f=netto_weigth_f,
                        id_factory=id_factory,
                        id_stockpile=id_stockpile,
                        id_pile=id_pile,
                        batch=batch,
                        delivery_order =delivery_order,
                        tgl_hauling=tanggal,
                        time_hauling=time_hauling,
                        shift=shift,
                        batch_g=batch_g,
                        kode_batch_g=kode_batch_g,
                        left_date=left_date,
                        new_scci=new_scci,
                        new_scci_sub=batch,
                        new_kode_batch_scci=new_kode_batch_scci,
                        scci_order=scci_order,
                        new_awk=new_awk,
                        new_awk_sub=batch,
                        new_kode_batch_awk=new_kode_batch_awk,
                        new_batch_awk_pulp=new_batch_awk_pulp,
                        awk_order=awk_order,
                        type_selling=sale_type,
                        date_wb=tanggal,
                        sale_adjust='HPAL',
                        sale_dome=sale_dome,
                    )
                    list_objects.append(data)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            SellingProductions.objects.bulk_create(list_objects, batch_size=200)
    
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
