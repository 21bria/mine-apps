import re
import pandas as pd
from django.http import JsonResponse
from django.conf import settings
import os
from datetime import datetime

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

def clean_data_view(request):
    # Tentukan path file yang ada di dalam folder static
    file_path = os.path.join(settings.BASE_DIR, 'static', 'format-upload', 'import_sellings_rkef.xlsx')

    if os.path.exists(file_path):
        # Membaca file Excel
        df = pd.read_excel(file_path)

        
        df['date_gwt']      = df['date_gwt'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['date_ewt']      = df['date_ewt'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['load_date']     = pd.to_datetime(df['load_date']).dt.date
        df['weighing_date'] = pd.to_datetime(df['weighing_date']).dt.date

        # Menentukan kolom yang perlu dibersihkan
    #     numeric_columns = [
    #     'berat_kotor', 'berat_kosong', 'berat_bersih',
    #    ]
        
    #     # Kolom yang diinginkan tetap kosong jika kosong
    #     empty_columns = [
    #         'no_seri', 'no_unit','nama_material','lokasi_pembongkaran','discharge','shift',
    #         'code_hync','type','sale_type','batch','adjust_sale'
    #     ]
        numeric_columns = [
            'netto', 'gross', 'empty'
        ]
        # Kolom yang diinginkan tetap kosong jika kosong
        empty_columns = [
                'stockpile_temp','dome_temp','buyer','product_code','scci_gps', 'scci_sl','awk_inc','awk_sl','nota',
                'date_gwt','date_ewt','load_date','weighing_date'
            ]

        # Bersihkan data numerik di setiap kolom
        # for col in numeric_columns:
        #     if col in df.columns:
        #         df[col] = df[col].apply(clean_numeric)
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        # Untuk kolom yang perlu tetap kosong jika kosong
        for col in empty_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: None if pd.isna(x) or x == '' else x)


        # Mengonversi DataFrame ke dictionary dan kirim sebagai JsonResponse
        cleaned_data = df.to_dict(orient='list')

        return JsonResponse(cleaned_data)
    else:
        return JsonResponse({'error': 'File not found'}, status=404)
