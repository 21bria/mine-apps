from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections, DatabaseError
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from ....utils.permissions import get_dynamic_permissions
import logging
logger = logging.getLogger(__name__)

@login_required
def gradeHpalPlan_page(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    permissions = get_dynamic_permissions(request.user)
    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
        'permissions': permissions,
    }
    return render(request, 'admin-mgoqa/selling/list-selling-hpal-plan.html',context)

@login_required
def planByDays(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
    tgl_pertama  =  request.GET.get('startDate') 
    tgl_terakhir =  request.GET.get('endDate') 

    query = """
                    SELECT
                        t1.plan_date,
                        COALESCE(SUM(t1.tonnage_plan), 0) AS total_plan,
                        COALESCE(SUM(CASE WHEN  type_ore='HPAL' THEN tonnage_plan ELSE 0  END ), 0) AS plan_hpal,
                        COALESCE(t2.total_hpal, 0) AS total_hpal
                    FROM ore_sellings_plan as t1 
                    LEFT JOIN(
                                SELECT 
                                    date_gwt
                                    ,ROUND(SUM(tonnage),2) AS total_actual
                                    ,COALESCE(ROUND(SUM(CASE WHEN sale_adjust='HPAL' THEN tonnage ELSE 0  END ),2), 0) AS total_hpal
                                FROM sale_sum_days
                                WHERE date_gwt BETWEEN %s AND  %s
                                GROUP BY date_gwt
                            ) AS t2 ON t1.plan_date = t2.date_gwt
                    WHERE t1.plan_date BETWEEN %s AND  %s
                    GROUP BY t1.plan_date,t2.total_hpal
                    ORDER By t1.plan_date asc
            """

    params = [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir]

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['plan_date', 'total_plan', 'plan_hpal', 'total_hpal'])

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
        plan_date  = df['plan_date'].tolist()  
        total_plan = df['total_plan'].tolist()  
        plan_hpal  = df['plan_hpal'].tolist()  
        total_hpal = df['total_hpal'].tolist()  

        # Loop Data
        # plan_date  = [entry[0] for entry in chart_data]  
        # total_plan = [entry[1] for entry in chart_data]  
        # plan_hpal  = [entry[2] for entry in chart_data]  
        # total_hpal = [entry[3] for entry in chart_data]  

        # data_json = [
        #     {
        #         'plan_date'  : plan_date[i],
        #         'total_plan' : total_plan[i],
        #         'plan_hpal'  : plan_hpal[i],
        #         'total_hpal' : total_hpal[i],
        #     }
        #     for i in range(len(chart_data))
        # ]
        fig=make_subplots(
            specs=[[{"secondary_y": True}]])
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
            x=plan_date,
            y=plan_hpal,
            name='Plan',
            # marker = dict(color = colors['total']),
        ), secondary_y=False)

        fig.add_trace(go.Bar(
            x=plan_date,
            y=total_hpal,
            name='Ore',
            # yaxis='y1',
            marker = dict(color = colors['plan']),
       ), secondary_y=False)
        
 
        fig.update_layout(
            height=360,
            title       ='Daily Plan vs Actual',
            # subtitle    ='LIMONITE SUPPLY HYNC',
            yaxis_title ='WMT',
            # barmode     = 'group',
            xaxis_title_font=dict(size=12),
            xaxis=dict(
                # tickvals=list(plan_date), 
                # ticktext=[str(day) for day in range(1, 32)],
                title='Date'
            ),
               
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=40, r=20, t=40, b=0),
            hovermode   = 'x unified',
            # template    ='plotly_dark'
      
        )

        # Save plot as HTML
        plot_html = pio.to_html(fig,full_html=False, config={
        'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        response_data = {
            'plan_date' : plan_date,
            'total_plan': total_plan,
            'plan_hpal' : plan_hpal,
            'total_hpal': total_hpal,
            'plot_html' : plot_html # Include plot HTML
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

@login_required    
def gradeByDaysMral(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
    tgl_pertama  =  request.GET.get('startDate') 
    tgl_terakhir =  request.GET.get('endDate') 

    query = """
                SELECT
                    t1.date_wb,
                    ROUND(SUM(t1.tonnage),2) AS total_split,
                    COALESCE(ROUND(t2.tonnage_plup,2), 0) AS total_pulp,
                    COALESCE(SUM(tonnage * ni) / NULLIF(SUM(CASE  WHEN  ni IS NOT NULL THEN tonnage ELSE 0  END ), 0),  0) AS ni_split,
                    COALESCE(t2.ni_pulp, 0) AS ni_pulp
                FROM split_sample_awk_hpal_mral as t1 
                LEFT JOIN(
                            SELECT
                                date_wb
                                ,SUM(tonnage) AS tonnage_plup
                                ,COALESCE(SUM(tonnage * ni) / NULLIF(SUM(CASE  WHEN  ni IS NOT NULL THEN tonnage ELSE 0  END ), 0),  0) AS ni_pulp
                            FROM split_pulp_awk_hpal_mral
                            WHERE date_wb BETWEEN  %s AND  %s
                            GROUP BY date_wb
                            ) AS t2 ON t1.date_wb = t2.date_wb
            WHERE t1.date_wb BETWEEN %s AND %s
            GROUP BY t1.date_wb,t2.tonnage_plup,t2.ni_pulp
            ORDER By t1.date_wb asc
        """

    params = [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir]

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['date_wb', 'total_split', 'total_pulp', 'ni_split','ni_pulp'])

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
        date_wb     = df['date_wb'].tolist()  
        ni_split    = df['ni_split'].tolist()      
        ni_pulp     = df['ni_pulp'].tolist()      

        # # Loop Data
        # date_wb     = [entry[0] for entry in chart_data]  
        # total_split = [entry[1] for entry in chart_data]  
        # total_pulp  = [entry[2] for entry in chart_data]  
        # ni_split    = [entry[3] for entry in chart_data]  
        # ni_pulp     = [entry[4] for entry in chart_data]  

        # data_json = [
        #     {
        #         'date_wb'     : date_wb[i],
        #         'total_split' : total_split[i],
        #         'total_pulp'  : total_pulp[i],
        #         'ni_split'    : ni_split[i],
        #         'ni_pulp'     : ni_pulp[i],
        #     }
        #     for i in range(len(chart_data))
        # ]

        # # Return the JSON response
        # return JsonResponse(data_json, safe=False)

         # Create Plotly figure
        fig = go.Figure()
        # Warna untuk masing-masing trace
        colors = {
            'total'    : '#feb23b',
            'plan'     : '#cfd7d9',
        }
    
        fig.add_trace(go.Scatter(
            x=date_wb,
            y=ni_split,
            mode='lines+markers+text',
            name='Ni Wet',
            # yaxis='y1',
            text=[f'{value:.2f}' for value in ni_split],
            textposition='top right',
            hovertemplate='%{y:.2f}<extra></extra>', 
            marker = dict(size=8),
            line=dict( dash="dot", width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=date_wb,
            y=ni_pulp,
            mode='lines+markers+text',
            name='Ni Pulp',
            # yaxis='y2',
            text=[f'{value:.2f}' for value in ni_pulp],
            textposition='bottom right',
            hovertemplate='%{y:.2f}<extra></extra>', 
            # marker = dict( size=8,color ='#cfd7d9'),
            marker = dict( size=8),
            line=dict( width=2)
           
        ))

        fig.update_layout(
            title   ='Samples Data - NI (WET & PULP)',
            barmode = 'group',
            xaxis_title_font=dict(size=12),
            xaxis=dict(
                tickvals=list(date_wb), 
                title='Date'
            ),
            yaxis=dict(
                title='Grade',
                showgrid=True,
                showline=True,
                zeroline=True,
                showticklabels=True,
                range=[-0.04, max(ni_split + ni_pulp) * 1.3],
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

        response_data = {
            'plot_html' : plot_html # Include plot HTML
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

@login_required    
def gradeByCodeMral(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
    tgl_pertama  =  request.GET.get('startDate') 
    tgl_terakhir =  request.GET.get('endDate') 

    query = """
                   SELECT
                        t1.delivery_order,
                        COALESCE(ROUND(SUM(t1.netto_ton),2), 0) AS tonnage_split,
                        COALESCE(ROUND(t3.tonnage_pulp,2), 0) AS tonnage_pulp,
                        COALESCE(ROUND(t2.tonnage_official,2), 0) AS tonnage_official,
                        COALESCE(SUM(t1.netto_ton * t1.ni) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS ni_split,
                        COALESCE(t3.ni_pulp, 0) AS ni_pulp,
                        COALESCE(t2.ni_official, 0) AS ni_official,
                        COALESCE(t1.ni_plan, 0) AS ni_plan
                    FROM details_selling_awk_mral as t1   
                    LEFT JOIN(
                                SELECT
                                    product_code,
                                    COALESCE(SUM(tonnage), 0) AS tonnage_official,
                                    COALESCE(SUM(ni), 0) AS ni_official,
                                    type_selling
                                FROM selling_official_surveyor_awk
                                GROUP BY product_code, type_selling
                            ) AS t2 ON t1.delivery_order = t2.product_code
                    LEFT JOIN(
                                SELECT 
                                    delivery_order,
                                    COALESCE(SUM(netto_ton),0) AS tonnage_pulp,
                                    COALESCE(SUM(netto_ton * ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND ni  IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS ni_pulp
                                FROM details_selling_awk_pulp_mral
                                WHERE date_wb BETWEEN %s AND %s
                                GROUP BY delivery_order
                            ) AS t3 ON t1.delivery_order = t3.delivery_order
                WHERE t1.date_wb BETWEEN %s AND  %s AND t2.type_selling = 'HOS'
                GROUP BY t1.delivery_order,t3.tonnage_pulp,t3.ni_pulp,t2.tonnage_official,t2.ni_official,t1.ni_plan
                ORDER By t1.delivery_order asc
        """

    params = [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir]

    try:
        with connections['sqms_db'].cursor() as cursor:
             cursor.execute(query, params)
             chart_data = cursor.fetchall()

         # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['delivery_order', 'tonnage_split', 'tonnage_pulp', 'tonnage_official','ni_split','ni_pulp','ni_official','ni_plan'])

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
        # delivery_order   = [entry[0] for entry in chart_data]
        # tonnage_split    = [entry[1] for entry in chart_data]
        # tonnage_pulp     = [entry[2] for entry in chart_data]
        # tonnage_official = [entry[3] for entry in chart_data]
        # ni_split         = [entry[4] for entry in chart_data]
        # ni_pulp          = [entry[5] for entry in chart_data]
        # ni_official      = [entry[6] for entry in chart_data]
        # ni_plan          = [entry[7] for entry in chart_data]

        # data_json = [
        #     {
        #         'delivery_order'  : delivery_order[i],
        #         'tonnage_split'   : tonnage_split[i],
        #         'tonnage_pulp'    : tonnage_pulp[i],
        #         'tonnage_official': tonnage_official[i],
        #         'ni_split'        : ni_split[i],
        #         'ni_pulp'         : ni_pulp[i],
        #         'ni_official'     : ni_official[i],
        #         'ni_plan'         : ni_plan[i],
        #     }
        #     for i in range(len(chart_data))
        # ]

         # Create Plotly figure
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df['delivery_order'].tolist(),
            y=df['tonnage_split'].tolist(),
            name='Tonnage',
            marker = dict(color ='#cfd7d9'),
        ))

        fig.add_trace(go.Scatter(
            x=df['delivery_order'].tolist(),
            y=df['ni_split'].tolist(),
            mode='lines+markers',
            name='Ni Wet',
            text=[f'{value:.2f}' for value in df['ni_split'].tolist()],
            textposition='top right',
            hovertemplate='%{y:.2f}<extra></extra>',
            marker=dict(size=4),
            line=dict(width=2),
            yaxis='y2',
        ))

        fig.add_trace(go.Scatter(
            x=df['delivery_order'].tolist(),
            y=df['ni_pulp'].tolist(),
            mode='lines+markers',
            name='Ni Pulp',
            text=[f'{value:.2f}' for value in df['ni_pulp'].tolist()],
            textposition='bottom center',
            hovertemplate='%{y:.2f}<extra></extra>',
            marker=dict(size=4),
            line=dict(width=2),
            yaxis='y2',
        ))

        fig.add_trace(go.Scatter(
            x=df['delivery_order'].tolist(),
            y=df['ni_plan'].tolist(),
            mode='lines+markers',
            name='Ni Plan',
            text=[f'{value:.2f}' for value in df['ni_official'].tolist()],
            textposition='bottom right',
            hovertemplate='%{y:.2f}<extra></extra>',
            marker=dict(size=4),
            yaxis='y2',
        ))

        fig.add_trace(go.Scatter(
            x=df['delivery_order'].tolist(),
            y=df['ni_official'].tolist(),
            mode='lines+markers',
            name='Ni Coa',
            text=[f'{value:.2f}' for value in df['ni_official'].tolist()],
            textposition='bottom right',
            hovertemplate='%{y:.2f}<extra></extra>',
            marker=dict(size=4),
            yaxis='y2',
        ))

        fig.update_layout(
            barmode='group',
            title='Chart Daily Grade Ni - HPAL',
            yaxis_title='Tonnage',
            yaxis=dict(
                title='Ore (WMT)',
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

        )

        # Save plot as HTML
        plot_html = pio.to_html(fig, full_html=False, config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines', 'pan', 'select', 'lasso'],
            'responsive': True
        })

        data_json = {
            'delivery_order'  : df['delivery_order'].tolist(),
            'tonnage_split'   : df['tonnage_split'].tolist(),
            'tonnage_pulp'    : df['tonnage_pulp'].tolist(),
            'tonnage_official': df['tonnage_official'].tolist(),
            'ni_split'        : df['ni_split'].tolist(),
            'ni_pulp'         : df['ni_pulp'].tolist(),
            'ni_official'     : df['ni_official'].tolist(),
            'ni_plan'         : df['ni_plan'].tolist(),
            'plot_html'       : plot_html,
        }

        # Return the JSON response
        return JsonResponse(data_json, safe=False)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)
