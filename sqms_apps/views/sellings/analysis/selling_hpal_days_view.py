from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
from django.shortcuts import render
from django.db import connections, DatabaseError
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database
import itertools
from ....utils.permissions import get_dynamic_permissions

@login_required
def gradeHpalMonth_page(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    permissions = get_dynamic_permissions(request.user)
    context = {
        'start_date' : last_monday.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
        'permissions': permissions,
    }
    return render(request, 'admin-mgoqa/selling/list-selling-hpal-month.html',context)

@login_required
def gradeByDays(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
     # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks = request.GET.get('filter_days') 
    # tanggal_teks = '2024-05-01' 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        # Jika tidak ada tanggal yang diberikan, gunakan tanggal hari ini
        tanggal = datetime.now().date()
    
    hari_ini = tanggal
    # hari_ini     = datetime.now().date()
    tgl_pertama  = hari_ini.replace(day=1)
    tgl_terakhir = (hari_ini.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    last_day     = tgl_terakhir.day

    query = """
               SELECT 
                    tanggal.left_date,
                    COALESCE(tonnage, 0) AS total_ore,
                    COALESCE(tonnage_plup, 0) AS total_pulp,
                    COALESCE(ni, 0) AS ni_internal,
                    COALESCE(ni_pulp, 0) AS pulp_anindya
                FROM tanggal   
                LEFT JOIN (
                            SELECT 
                                left_date
                                ,SUM(tonnage) AS tonnage
                                ,COALESCE(SUM(tonnage * ni) / NULLIF(SUM(CASE  WHEN  ni IS NOT NULL THEN tonnage ELSE 0  END ), 0),  0) AS ni
                            FROM split_sample_awk_hpal
                            WHERE date_wb BETWEEN %s AND  %s
                                GROUP BY left_date) AS subquery on tanggal.left_date = subquery.left_date
                LEFT JOIN (
                            SELECT 
                                left_date
                                ,SUM(tonnage) AS tonnage_plup
                                ,COALESCE(SUM(tonnage * ni) / NULLIF(SUM(CASE  WHEN  ni IS NOT NULL THEN tonnage ELSE 0  END ), 0),  0) AS ni_pulp
                            FROM split_pulp_awk_hpal
                            WHERE date_wb BETWEEN %s AND  %s
                            GROUP BY left_date) AS pulp on tanggal.left_date= pulp.left_date

                WHERE 
                        tanggal.left_date <= %s
                ORDER By 
                        tanggal.left_date asc
        """

    params = [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir, last_day]

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['left_date', 'total_ore', 'total_pulp', 'ni_internal', 'pulp_anindya'])

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
        
        # Loop Data
        # left_date     = [entry[0] for entry in chart_data]  
        # total_ore     = [entry[1] for entry in chart_data]  
        # total_pulp    = [entry[2] for entry in chart_data]  
        # ni_internal   = [entry[3] for entry in chart_data]  
        # pulp_anindya  = [entry[4] for entry in chart_data]  

        # Extract data dari DataFrame
        left_date     = df['left_date'].tolist()  
        total_ore     = df['total_ore'].tolist()  
        total_pulp    = df['total_pulp'].tolist()  
        ni_internal   = df['ni_internal'].tolist()  
        pulp_anindya  = df['pulp_anindya'].tolist()  

        fig=make_subplots(
            specs=[[{"secondary_y": True}]])

        # Create Plotly figure
        # fig = go.Figure()
        # Warna untuk masing-masing trace
        colors = {
            'total'    : '#feb23b',
            'plan'     : '#cfd7d9',
            'internal' : '#D37676',
            # 'surveyor' : '#5C8374',
            'surveyor' : 'rgba(92,131,116,0.7)'
            # 'surveyor' : 'rgba(99,110,250,0.4)'
        }
    

        fig.add_trace(go.Bar(
            x=left_date,
            y=total_ore,
            name='Total Ore',
            # marker = dict(color = colors['total']),
        ), secondary_y=False)

        fig.add_trace(go.Bar(
            x=left_date,
            y=total_pulp,
            name='Total Pulp',
            # yaxis='y1',
            marker = dict(color = colors['plan']),
       ), secondary_y=False)
        
        fig.add_trace(go.Scatter(
            x=left_date,
            y=ni_internal,
            mode='lines+markers+text',
            name='Internal Sample',
            # yaxis='y2',
            text=[f'{value:.2f}' for value in ni_internal], 
            textposition='top right',
            hovertemplate='%{y:.2f}<extra></extra>', 
            marker = dict( size=8,color = colors['internal']),
            line=dict(color = colors['internal'],  dash="dot", width=2),
         ), secondary_y=True)
        
        fig.add_trace(go.Scatter(
            x=left_date,
            y=pulp_anindya,
            mode='lines+markers+text',
            name='Pulp Anindya',
            # yaxis='y2',
            text=[f'{value:.2f}' for value in pulp_anindya],
            textposition='bottom right',
            hovertemplate='%{y:.2f}<extra></extra>',
            marker = dict( size=8,color = colors['surveyor']),
        ), secondary_y=True)

        fig.update_layout(
            height=360,
            title       ='Chart Daily Grade Ni - HPAL',
            yaxis_title ='Value',
            barmode     = 'group',
            xaxis_title_font=dict(size=12),
            xaxis=dict(
                tickvals=list(range(1, max(left_date)+1)), 
                ticktext=[str(day) for day in range(1, 32)],
                title='Day of the Month'
            ),
               
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=25, r=25, t=40, b=20),
            hovermode   = 'x unified',
      
        )

        # Save plot as HTML
        plot_html = pio.to_html(fig,full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        # Kirim data JSON ke template menggunakan JsonResponse
        response_data = {
            'left_date'    : left_date,
            'total_ore'    : total_ore,
            'total_pulp'   : total_pulp,
            'ni_internal'  : ni_internal,
            'pulp_anindya' : pulp_anindya,
            'plot_html'    : plot_html # Include plot HTML
        }

        return JsonResponse(response_data)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

@login_required
def achievmentByDays(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
     # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks = request.GET.get('filter_days') 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        tanggal = datetime.now().date()
    
    hari_ini = tanggal
    # hari_ini     = datetime.now().date()
    tgl_pertama  = hari_ini.replace(day=1)
    tgl_terakhir = (hari_ini.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    last_day     = tgl_terakhir.day

    query = """
               SELECT 
                    tanggal.left_date,
                    COALESCE(total_plan, 0) AS total_plan,
                    COALESCE(total_actual, 0) AS total_actual,
                    COALESCE(plan_hpal, 0) AS plan_hpal,
                    COALESCE(total_hpal, 0) AS total_hpal
                FROM tanggal   
                LEFT JOIN (
                            SELECT 
                                 left_date
                                ,SUM(tonnage) AS total_actual
                                ,COALESCE(SUM(CASE WHEN  sale_adjust='HPAL' THEN tonnage ELSE 0  END ), 0) AS total_hpal
                            FROM sale_sum_days
                            WHERE date_gwt BETWEEN %s AND  %s
                            GROUP BY left_date) AS subquery on tanggal.left_date = subquery.left_date
                LEFT JOIN (
                            SELECT 
                                 left_date
                                ,SUM(tonnage_plan) AS total_plan
                                ,COALESCE(SUM(CASE WHEN  type_ore='HPAL' THEN tonnage_plan ELSE 0  END ), 0) AS plan_hpal
                            FROM ore_sellings_plan
                            WHERE plan_date BETWEEN %s AND  %s
                            GROUP BY left_date) AS pulp on tanggal.left_date= pulp.left_date
                WHERE 
                        tanggal.left_date <= %s
                ORDER By 
                        tanggal.left_date asc
        """

    params = [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir, last_day]

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['left_date', 'total_plan', 'total_actual', 'total_hpal', 'plan_hpal'])

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

        # Loop Data
        # left_date    = [entry[0] for entry in chart_data]  
        # total_plan   = [entry[1] for entry in chart_data]  
        # total_actual = [entry[2] for entry in chart_data]  
        # plan_hpal    = [entry[3] for entry in chart_data]  
        # total_hpal   = [entry[4] for entry in chart_data]  

        # Extract data dari DataFrame
        left_date   = df['left_date'].tolist()  
        total_plan  = df['total_plan'].tolist()  
        total_actual= df['total_actual'].tolist()  
        plan_hpal   = df['plan_hpal'].tolist()  
        total_hpal  = df['total_hpal'].tolist()  
        plan_accumulated = [round(total, 2) for total in itertools.accumulate(plan_hpal)]
        hpal_accumulated = [round(total, 2) for total in itertools.accumulate(total_hpal)]

      # Zip the data into a list of dictionaries
        # response_data = [
        #     {
        #         'left_date'         : left_date[i],
        #         'total_plan'        : total_plan[i],
        #         'total_actual'      : total_actual[i],
        #         'plan_hpal'         : plan_hpal[i],
        #         'total_hpal'        : total_hpal[i],
        #         'plan_accumulated'  : plan_accumulated[i],
        #         'hpal_accumulated'  : hpal_accumulated[i],
        #     }
        #     for i in range(len(chart_data))
        # ]

        # Create Plotly figure
        fig = go.Figure()
        # Warna untuk masing-masing trace
        colors = {
            'total'    : '#feb23b',
            'plan'     : '#cfd7d9',
            'internal' : '#b4b9ba',
            'surveyor' : 'rgba(99,110,250,0.4)'
        }

        fig.add_trace(go.Bar(
            x=left_date,
            y=total_hpal,
            name='Total HPAL',
            # yaxis='y1',
            # marker = dict(color = colors['total']),
        ))
        
        fig.add_trace(go.Bar(
            x=left_date,
            y=plan_hpal,
            name='HPAL Plan',
            # yaxis='y1',
            marker = dict(color = colors['plan']),

        ))
        
        fig.add_trace(go.Scatter(
            x=left_date,
            y=plan_accumulated,
            mode='lines+markers+text',
            name='Cum.Plan',
            yaxis='y2',
            # text=[f'{value:.0f}' for value in plan_accumulated], # Format labels with 2 decimal places
            # textposition='top right',
            # hovertemplate='%{y:.0f}<extra></extra>', # Format tooltip with 2 decimal places
            # marker = dict( size=8,color = colors['internal']),
            line=dict(color = colors['internal'],  dash="dot", width=2)
            # line=dict( dash="dot", width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=left_date,
            y=hpal_accumulated,
            mode='lines+markers+text',
            name='Cum.Actual',
            yaxis='y2',
            # text=[f'{value:.2f}' for value in hpal_accumulated], # Format labels with 2 decimal places
            # textposition='bottom right',
            # hovertemplate='%{y:.2f}<extra></extra>', # Format tooltip with 2 decimal places
            marker = dict( size=8,color = colors['surveyor']),
            # marker = dict( size=8),
           
        ))

        fig.update_layout(
            title       ='Daily Achievment - DISTRIBUTION SUPPLYING HPAL',
            # yaxis_title ='DISTRIBUTION SUPPLYING HPAL',
            # barmode     = 'group',
            xaxis_title_font=dict(size=12),
            xaxis=dict(
                tickvals=list(range(1, max(left_date)+1)), 
                ticktext=[str(day) for day in range(1, 32)],
                title='Day of the Month'
            ),
            yaxis=dict(
                title='Actual (WMT)',
                showgrid=True,
                showline=True,
                zeroline=True,
                showticklabels=True,
                # range=[0, None]  # Ensure y-axis starts at 0 for bar charts
                # range=[0, max(total_hpal + total_plan) * 1.1],  # Ensure y-axis starts at 0 and extends slightly above the max value
            ),
            yaxis2=dict(
                # range=[0, 2.3],
                overlaying='y',
                side='right',
                title_font=dict(size=12),
                showgrid=False,
                showline=False,
                zeroline=False,
                showticklabels=True,
                anchor='x',
                # range=[None, None]  # Let y-axis adjust to the data range
                # dtick=max(max(ni_internal + pulp_anindya) / 5, 1)  # Set tick intervals for secondary y-axis
            ),


            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=0, r=0, t=40, b=0),
            height      = 360,
            hovermode   = 'x unified',
            # template    ='plotly_dark'
            # template  ='plotly_white'
            
        )

        plot_html = pio.to_html(fig,full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        # response_data = [
        #     {
        #         # 'left_date'       : left_date[i],
        #         # 'total_plan'      : total_plan[i],
        #         # 'total_actual'    : total_actual[i],
        #         # 'plan_hpal'       : plan_hpal[i],
        #         # 'total_hpal'      : total_hpal[i],
        #         # 'plan_accumulated': plan_accumulated[i],
        #         # 'hpal_accumulated': hpal_accumulated[i],
        #         'plot_html'       : plot_html
        #     }
        #     # for i in range(len(chart_data))
        # ]
        response_data = {
            'left_date'       : left_date,
            'total_plan'      : total_plan,
            'total_actual'    : total_actual,
            'plan_hpal'       : plan_hpal,
            'total_hpal'      : total_hpal,
            'plan_accumulated': plan_accumulated,
            'hpal_accumulated': hpal_accumulated,
            'plot_html'       : plot_html # Include plot HTML
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)


    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)


