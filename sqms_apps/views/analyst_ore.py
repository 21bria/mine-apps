from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections, DatabaseError
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
import numpy as np
import logging
logger = logging.getLogger(__name__)

@login_required
def analystOreData_page(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mgoqa/analyst_data.html',context)
@login_required
def analystOre(request):
        # Inisialisasi variabel untuk kueri SQL dan rentang waktu default
    query = """
        SELECT 
            tgl_production,
            ROUND(SUM(tonnage), 2) AS total
        FROM ore_production
    """
    query += " GROUP BY tgl_production ORDER BY tgl_production ASC"

    try:
        with connections['sqms_db'].cursor() as cursor:
             cursor.execute(query)
             chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['tgl_production', 'total'])

        # Extract data dari DataFrame
        Date  = df['tgl_production'].tolist()  
        total = df['total'].tolist()  

        fig = px.line(df,
                    x=Date,
                    y=total, 
                    title='Data Production')

        fig.update_xaxes(
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month",stepmode="backward"),
                    dict(count=6, label="6m", step="month",stepmode="backward"),
                    dict(count=1, label="YTD",step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        fig.update_layout(
                height=360,
                yaxis_title ='',
                xaxis_title ='Date',
                xaxis_title_font=dict(size=12),
                plot_bgcolor='rgba(201,201,201,0.08)',
                legend      = dict(x=0.5, y=1.2, orientation='h'),
                margin      = dict(l=40, r=20, t=75, b=40),
                hovermode   = 'x unified',

        
            )

        # Save plot as HTML
        plot_html = pio.to_html(fig,full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        # Format data untuk JsonResponse
        response_data = {
            'plot_html' : plot_html # Include plot HTML
            }

        return JsonResponse(response_data, safe=False)

    except DatabaseError as e:
        return JsonResponse({'error': str(e)}, status=500)   
    
@login_required
def analystSale(request):
        # Inisialisasi variabel untuk kueri SQL dan rentang waktu default
    query = """
        SELECT 
            date_wb,
            ROUND(SUM(tonnage), 2) AS total
        FROM details_selling
    """
    query += " GROUP BY date_wb ORDER BY date_wb ASC"

    try:
        with connections['sqms_db'].cursor() as cursor:
             cursor.execute(query)
             chart_data = cursor.fetchall()


        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['date_wb', 'total'])

        # Extract data dari DataFrame
        Date  = df['date_wb'].tolist()  
        total = df['total'].tolist()  

        fig = px.line(df,
                    x=Date,
                    y=total, 
                    title='Data Selling',
                    )
        # Update line color
        fig.update_traces(line=dict(color='#7fe4aa'))

        fig.update_xaxes(
            # rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month",stepmode="backward"),
                    dict(count=6, label="6m", step="month",stepmode="backward"),
                    dict(count=1, label="YTD",step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        fig.update_layout(
                height=360,
                yaxis_title ='',
                xaxis_title ='Date',
                xaxis_title_font=dict(size=12),
                plot_bgcolor='rgba(201,201,201,0.08)',
                legend      = dict(x=0.5, y=1.2, orientation='h'),
                margin      = dict(l=40, r=20, t=75, b=40),
                hovermode   = 'x unified',
            )

        # Save plot as HTML
        plot_html = pio.to_html(fig,full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        # Format data untuk JsonResponse
        response_data = {
            'plot_html' : plot_html # Include plot HTML
            }

        return JsonResponse(response_data, safe=False)

    except DatabaseError as e:
        return JsonResponse({'error': str(e)}, status=500)   
    
@login_required
def get_ore_year_data(request):
 # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)
    # filter_year = 2023

    if filter_year:
        filter_sql = "WHERE YEAR(tgl_production) = %s"
        params = [filter_year]
    else:
        current_year =  datetime.now().year
        filter_sql = "WHERE YEAR(tgl_production) = %s"
        params = [current_year]

    query = """
        SELECT
            DATE_FORMAT(tgl_production, '%%b') AS bulan,
            DATE_FORMAT(tgl_production, '%%Y') AS tahun,
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN id_material = '7' THEN tonnage ELSE 0 END), 2), 0) AS total_lim,
            COALESCE(ROUND(SUM(CASE WHEN id_material = '10' THEN tonnage ELSE 0 END), 2), 0) AS total_sap
        FROM ore_productions
        {}
        GROUP BY MONTH(tgl_production), YEAR(tgl_production)
        ORDER BY MIN(tgl_production);
    """.format(filter_sql)

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['bulan','tahun','total','total_lim','total_sap'])

        if df.empty:
            # Create Plotly figure for empty data
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                plot_bgcolor='rgba(0,0,0,0)', 
                annotations=[
                    {
                        "text"      : "No matching data found",
                        "xref"      : "paper",
                        "yref"      : "paper",
                        "showarrow" : False,
                        "font"      : {"size": 14}
                    }
                ],
                height=265,
            )
            
            plot_html = pio.to_html(fig, full_html=False)
            return JsonResponse({'plot_html': plot_html})     

        # Extract data dari DataFrame
        bulan = df['bulan'].tolist()
        tahun = df['tahun'].tolist()
        total = df['total'].tolist()
        total_lim = df['total_lim'].tolist()
        total_sap = df['total_sap'].tolist()  

        fig = go.Figure()

        # values = total
        values = total
        colors= ['aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance',
             'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg',
             'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl',
             'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric',
             'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys',
             'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet',
             'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges',
             'orrd', 'oryel', 'oxy', 'peach', 'phase', 'picnic', 'pinkyl',
             'piyg', 'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn',
             'puor', 'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu',
             'rdgy', 'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar',
             'spectral', 'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn',
             'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid',
             'turbo', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr',
             'ylorrd'],
    
        fig.add_trace(go.Bar(
            x=bulan,
            y=total,
            name='Ore Production',
            marker=dict(
                    # size=16,
                    color=values,
                    # colorbar=dict(
                    #     title="Data"
                    # ),
                    colorscale='tealgrn'
                ),
        ))

        fig.update_layout(
            title       ='Ore Productions',
            xaxis_title_font=dict(size=12),
            xaxis=dict(
                title='Data of the Month'
            ),
            yaxis=dict(
                title='Tonnage',
                showgrid=True,
                showline=True,
                zeroline=True,
                showticklabels=True,
            ),
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=0, r=0, t=40, b=0),
            height      = 360,
            hovermode   = 'x unified',

        )

        plot_html = pio.to_html(fig,full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})
           

        # Kirim data JSON ke template menggunakan JsonResponse
        response_data = {
            # 'plot_html' : plot_html # Include plot HTML
            'bulan'    :bulan,
            'tahun'    :tahun,
            'total'    :total,
            'total_lim':total_lim,
            'total_sap':total_sap,
            'plot_html':plot_html
            }

        return JsonResponse(response_data, safe=False)
    
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)  
@login_required
def get_sale_year_date(request):
 # Ambil data dari database menggunakan cursor SQL
    filter_year = request.GET.get('filter_year', None)
    # filter_year = 2023

    if filter_year:
        filter_sql = "WHERE YEAR(date_wb) = %s"
        params = [filter_year]
    else:
        current_year =  datetime.now().year
        filter_sql = "WHERE YEAR(date_wb) = %s"
        params = [current_year]

    query = """
        SELECT
            DATE_FORMAT(date_wb, '%%b') AS bulan,
            DATE_FORMAT(date_wb, '%%Y') AS tahun,
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END), 2), 0) AS total_hpal,
            COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END), 2), 0) AS total_rkef
        FROM details_selling
        {}
        GROUP BY MONTH(date_wb), YEAR(date_wb)
        ORDER BY MIN(date_wb);
    """.format(filter_sql)
    
    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['bulan','tahun','total','total_hpal','total_rkef'])

        if df.empty:
            # Create Plotly figure for empty data
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                plot_bgcolor='rgba(0,0,0,0)', 
                annotations=[
                    {
                        "text"      : "No matching data found",
                        "xref"      : "paper",
                        "yref"      : "paper",
                        "showarrow" : False,
                        "font"      : {"size": 14}
                    }
                ],
                height=265,
            )
            
            plot_html = pio.to_html(fig, full_html=False)
            return JsonResponse({'plot_html': plot_html})     

        # Extract data dari DataFrame
        bulan = df['bulan'].tolist()
        tahun = df['tahun'].tolist()
        total = df['total'].tolist()
        total_hpal = df['total_hpal'].tolist()
        total_rkef = df['total_rkef'].tolist()  

        fig = go.Figure()

        # values = total
        values = total
        colors = ['aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance',
             'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg',
             'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl',
             'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric',
             'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys',
             'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet',
             'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges',
             'orrd', 'oryel', 'oxy', 'peach', 'phase', 'picnic', 'pinkyl',
             'piyg', 'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn',
             'puor', 'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu',
             'rdgy', 'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar',
             'spectral', 'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn',
             'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid',
             'turbo', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr',
             'ylorrd'],
    
        fig.add_trace(go.Bar(
            x=bulan,
            y=total,
            name='Ore Production',
            marker=dict(
                    color=values,
                    colorscale='teal'
                ),
        ))

        fig.update_layout(
            title       ='Selling Productions',
            xaxis_title_font=dict(size=12),
            xaxis=dict(
                title='Data of the Month'
            ),
            yaxis=dict(
                title='WMT',
                showgrid=True,
                showline=True,
                zeroline=True,
                showticklabels=True,
            ),
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=0, r=0, t=40, b=0),
            height      = 360,
            hovermode   = 'x unified',

        )

        plot_html = pio.to_html(fig,full_html=False, config={
                    'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
                    'responsive': True})
           
        # Kirim data JSON ke template menggunakan JsonResponse
        response_data = {
            'bulan'     :bulan,
            'tahun'     :tahun,
            'total'     :total,
            'total_hpal':total_hpal,
            'total_rkef':total_rkef,
            'plot_html' :plot_html
            }

        return JsonResponse(response_data, safe=False)
 
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
    return JsonResponse({'error': str(e)}, status=500) 
@login_required
def pdsAllData(request):
    # Ambil parameter time_range dari GET request
    time_range = request.GET.get('time_range', None)

    # Inisialisasi variabel untuk kueri SQL dan rentang waktu default
    query = """
        SELECT 
            tgl_production,
            ROUND(SUM(tonnage), 2) AS total
        FROM ore_production
        WHERE 1=1
    """

    params = []

    # Tambahkan filter berdasarkan time_range
    if time_range == '1_week':
        start_date = datetime.now() - timedelta(days=7)
        query += " AND tgl_production >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    elif time_range == '5_weeks':
        start_date = datetime.now() - timedelta(days=35)
        query += " AND tgl_production >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    elif time_range == '1_month':
        start_date = datetime.now() - timedelta(days=30)
        query += " AND tgl_production >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    elif time_range == '6_months':
        start_date = datetime.now() - timedelta(days=180)
        query += " AND tgl_production >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    elif time_range == '1_year':
        start_date = datetime.now() - timedelta(days=365)
        query += " AND tgl_production >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    elif time_range == '5_year':
        start_date = datetime.now() - timedelta(days=1825)
        query += " AND tgl_production >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    # Tambahkan filter untuk periode dari awal sampai tanggal sekarang
    elif time_range == 'all_data':  # Periode hingga hari ini
        start_date = datetime.now().replace(day=1)
        query += " AND tgl_production >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    query += " GROUP BY tgl_production ORDER BY tgl_production ASC"

    try:
        with connections['sqms_db'].cursor() as cursor:
             cursor.execute(query, params)
             chart_data = cursor.fetchall()

        # Format data untuk JsonResponse
        data_json = [
            {
             'date_pds': entry[0].strftime('%Y-%m-%d'), 
             'total'   : entry[1]
             }
            for entry in chart_data
        ]

        return JsonResponse(data_json, safe=False)

    except DatabaseError as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def saleAllData(request):
    # Ambil parameter time_range dari GET request
    time_range = request.GET.get('time_range', None)

    # Inisialisasi variabel untuk kueri SQL dan rentang waktu default
    query = """
        SELECT 
            date_wb,
            ROUND(SUM(tonnage), 2) AS total
        FROM details_selling
        WHERE 1=1
    """

    params = []

    # Tambahkan filter berdasarkan time_range
    if time_range == '1_week':
        start_date = datetime.now() - timedelta(days=7)
        query += " AND date_wb >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    elif time_range == '5_weeks':
        start_date = datetime.now() - timedelta(days=35)
        query += " AND date_wb >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    elif time_range == '1_month':
        start_date = datetime.now() - timedelta(days=30)
        query += " AND date_wb >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    elif time_range == '6_months':
        start_date = datetime.now() - timedelta(days=180)
        query += " AND date_wb >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    elif time_range == '1_year':
        start_date = datetime.now() - timedelta(days=365)
        query += " AND date_wb >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    elif time_range == '5_year':
        start_date = datetime.now() - timedelta(days=1825)
        query += " AND date_wb >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    # Tambahkan filter untuk periode dari awal sampai tanggal sekarang
    elif time_range == 'all_data':  # Periode hingga hari ini
        start_date = datetime.now().replace(day=1)
        query += " AND date_wb >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))

    query += " GROUP BY date_wb ORDER BY date_wb ASC"

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Format data untuk JsonResponse
        data_json = [
            {'date_wb': entry[0].strftime('%Y-%m-%d'), 'total': entry[1]}
            for entry in chart_data
        ]

        return JsonResponse(data_json, safe=False)

    except DatabaseError as e:
        return JsonResponse({'error': str(e)}, status=500)


    # Retrieve date parameters from request
    tgl_pertama = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')

    # Example fixed dates (remove this if using actual request parameters)
    tgl_pertama  = '2024-06-11'
    tgl_terakhir = '2024-06-21'

    query = """
        SELECT
            pile_id AS dome,nama_material, COALESCE(SUM(tonnage), 0) AS tonnage
        FROM 
            details_roa
        WHERE 
            tgl_production BETWEEN %s AND %s
        GROUP BY 
            pile_id,nama_material
        ORDER BY 
            nama_material,pile_id ASC
    """
    params = [tgl_pertama, tgl_terakhir]

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Create DataFrame from SQL query results
        df = pd.DataFrame(chart_data, columns=['dome','nama_material','tonnage'])

        if df.empty:
            # Create Plotly figure for empty data
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                plot_bgcolor='rgba(0,0,0,0)', 
                annotations=[
                    {
                        "text": "No matching data found",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 14}
                    }
                ],
                height=380,
            )
            
            plot_html = pio.to_html(fig, full_html=False)
            return JsonResponse({'plot_html': plot_html})

        # Extract data from DataFrame
        dome    = df['dome'].tolist()
        tonnage = df['tonnage'].tolist()

        # Create Plotly figure
        fig = go.Figure()

        values = tonnage

        fig.add_trace(go.Bar(
            x=dome,
            y=tonnage,
            name='Tonnage by Dome',
            # text=tonnage,
            # hoverinfo='text',
            # opacity=0.85,
            marker=dict(
                # color='#298c9c',
                color=values,
                colorscale='teal',
                line=dict(
                    color='white',
                    width=1
                )
            )
        ))

        # Define layout
        fig.update_layout(
            title='Tonnage by Dome',
            xaxis=dict(
                title='Dome',
                # tickangle=-45
            ),
            yaxis=dict(
                title='Tonnage'
            ),
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=0, r=0, t=40, b=0),
            height      = 380,
            hovermode   = 'x unified',
            bargap=0.03  # Adjust bar gap
        )

        plot_html = pio.to_html(fig, full_html=False, config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines', 'pan', 'select', 'lasso'],
            'responsive': True
        })

        # Return the JSON response
        response_data = {
            'plot_html': plot_html
        }

        return JsonResponse(response_data, safe=False)
    
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)