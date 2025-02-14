from celery import shared_task
import pandas as pd
from django.db import transaction
from ..models.task_model import taskImports
from ..models.mine_plan_productions_model import planProductions

@shared_task
def import_plan_mine_productions(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_objects = []
    update_objects = []
    successful_imports = 0
    duplicate_imports = 0

    # Konversi kolom ke datetime dengan format yang sesuai
    df['Date Plan'] = pd.to_datetime(df['Date Plan'], format='%Y-%m-%d', errors='coerce')
    df['Date Plan'] = df['Date Plan'].dt.date  # Ambil hanya tanggal

    # Ambil semua ref_plan yang sudah ada di database
    existing_data = planProductions.objects.values_list("id", "ref_plan")
    existing_dict = {val: record_id for record_id, val in existing_data}  # Dictionary {ref_plan: id}

    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                date_plan = row['Date Plan']
                category  = row['Category']
                sources   = row['Sources']
                vendors   = row['Vendors']
                TopSoil   = row['Top Soil']
                OB        = row['OB']
                LGLO      = row['LGLO']
                MGLO      = row['MGLO']
                HGLO      = row['HGLO']
                Waste     = row['Waste']
                MWS       = row['MWS']
                LGSO      = row['LGSO']
                MGSO      = row['MGSO']
                HGSO      = row['HGSO']
                Quarry    = row['Quarry']
                Ballast   = row['Ballast']
                Biomass   = row['Biomass']

                category = None if pd.isna(category) else category
                sources  = None if pd.isna(sources) else sources
                vendors  = None if pd.isna(vendors) else vendors

                # Gabungkan Refrensi Plan
                ref_plan = f"{date_plan}{category}{sources}{vendors}".replace(" ", "")

                if ref_plan in existing_dict:
                    # Jika sudah ada, tambahkan ke daftar update
                    update_objects.append(
                        planProductions(
                            id=existing_dict[ref_plan],  # ID dari database
                            date_plan=date_plan,
                            category=category,
                            sources=sources,
                            vendors=vendors,
                            TopSoil=TopSoil,
                            OB=OB,
                            LGLO=LGLO,
                            MGLO=MGLO,
                            HGLO=HGLO,
                            Waste=Waste,
                            MWS=MWS,
                            LGSO=LGSO,
                            MGSO=MGSO,
                            HGSO=HGSO,
                            Quarry=Quarry,
                            Ballast=Ballast,
                            Biomass=Biomass,
                            ref_plan=ref_plan,
                            task_id=import_plan_mine_productions.request.id,
                        )
                    )
                    duplicate_imports += 1
                    duplicates.append(f"Updated at row {index}: {ref_plan}")
                else:
                    # Jika belum ada, tambahkan ke daftar insert
                    list_objects.append(
                        planProductions(
                            date_plan=date_plan,
                            category=category,
                            sources=sources,
                            vendors=vendors,
                            TopSoil=TopSoil,
                            OB=OB,
                            LGLO=LGLO,
                            MGLO=MGLO,
                            HGLO=HGLO,
                            Waste=Waste,
                            MWS=MWS,
                            LGSO=LGSO,
                            MGSO=MGSO,
                            HGSO=HGSO,
                            Quarry=Quarry,
                            Ballast=Ballast,
                            Biomass=Biomass,
                            ref_plan=ref_plan,
                            task_id=import_plan_mine_productions.request.id,
                        )
                    )
                    successful_imports += 1

            # Simpan semua insert dengan bulk_create
            if list_objects:
                planProductions.objects.bulk_create(list_objects, batch_size=200)

            # Simpan semua update dengan bulk_update
            if update_objects:
                planProductions.objects.bulk_update(update_objects, [
                    "date_plan", "category", "sources", "vendors",
                    "TopSoil", "OB", "LGLO", "MGLO", "HGLO", "Waste",
                    "MWS", "LGSO", "MGSO", "HGSO", "Quarry", "Ballast", "Biomass",
                    "task_id"
                ], batch_size=200)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Buat laporan import
    taskImports.objects.create(
        task_id             =import_plan_mine_productions.request.id, 
        successful_imports  =successful_imports,
        failed_imports      =len(errors),
        duplicate_imports   =duplicate_imports,
        errors              ="\n".join(errors) if errors else None,
        duplicates          ="\n".join(duplicates) if duplicates else None,
        file_name           =original_file_name,
        destination         ='Plan Mine Productions',
    )

    if errors or duplicates:
        return {'message': 'Import completed with some errors or duplicates', 'errors': errors, 'duplicates': duplicates}
    else:
        return {'message': 'Import successful'}
