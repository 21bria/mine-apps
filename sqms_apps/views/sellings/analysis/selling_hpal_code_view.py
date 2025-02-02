from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections, DatabaseError
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
from ....utils.permissions import get_dynamic_permissions
import logging
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database


@login_required
def gradeHpalCode_page(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    permissions = get_dynamic_permissions(request.user)
    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
        'permissions': permissions,
    }
    return render(request, 'admin-mgoqa/selling/list-selling-hpal-code.html',context)

@login_required
def gradeByCode(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []

    # hari_ini     = datetime.now().date()
    tgl_pertama  =  request.GET.get('startDate') 
    tgl_terakhir =  request.GET.get('endDate') 

    query = """
                SELECT
                    t1.delivery_order,
                    COALESCE(SUM(t1.netto_ton), 0) AS tonnage_split,
                    COALESCE(t3.tonnage_pulp, 0) AS tonnage_pulp,
                    COALESCE(t2.tonnage_official, 0) AS tonnage_official,
                    COALESCE(SUM(t1.netto_ton * t1.ni) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.netto_ton ELSE 0 END), 0) AS ni_split,
                    COALESCE(t3.ni_pulp, 0) AS ni_pulp,
                    COALESCE(t2.ni_official, 0) AS ni_official
                FROM details_selling_awk as t1   
                LEFT JOIN (SELECT
                            product_code,
                            COALESCE(SUM(tonnage), 0) AS tonnage_official,
                            COALESCE(SUM(ni), 0) AS ni_official,
                            type_selling
                            FROM selling_official_surveyor_awk
                            GROUP BY product_code, type_selling) AS t2
                    ON t1.delivery_order = t2.product_code
                LEFT JOIN(SELECT 
                                delivery_order,
                                COALESCE(SUM(netto_ton),0) AS tonnage_pulp,
                                COALESCE(SUM(netto_ton * ni) / SUM(CASE WHEN sample_number  IS NOT NULL AND ni  IS NOT NULL THEN netto_ton ELSE 0 END), 0) AS ni_pulp
                            FROM details_selling_awk_pulp
                            WHERE date_wb BETWEEN %s AND  %s
                            GROUP BY delivery_order) AS t3
                    ON t1.delivery_order = t3.delivery_order
                WHERE t1.date_wb BETWEEN %s AND %s AND t2.type_selling = 'HOS'
                GROUP BY t1.delivery_order,t3.tonnage_pulp,t2.tonnage_official,t3.ni_pulp,t2.ni_official
                ORDER By t1.delivery_order asc
            """

    params = [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir]

    try:
        with connections['sqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['delivery_order', 'tonnage_split', 'tonnage_pulp', 'tonnage_official', 'ni_split','ni_pulp','ni_official'])


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

        # Initialize lists
        var_split_list = []
        var_pulp_list  = []

        # Calculate percentage error for each entry
        for i in range(len(df)):
            ni_official = df.loc[i, 'ni_official']
            ni_split    = df.loc[i, 'ni_split']
            ni_pulp     = df.loc[i, 'ni_pulp']

            # Calculate var_split
            if ni_official != 0:
                var_split = f"{((ni_split - ni_official) / ni_official) * 100:.0f}%"
            else:
                var_split = "0"  # or handle accordingly

            # Calculate var_pulp
            if ni_official != 0:
                var_pulp = f"{((ni_pulp - ni_official) / ni_official) * 100:.0f}%"
            else:
                var_pulp = "0"  # or handle accordingly

            var_split_list.append(var_split)
            var_pulp_list.append(var_pulp)


        # Create Plotly figure
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['delivery_order'].tolist(),
            y=df['ni_split'].tolist(),
            mode='lines+markers',
            name='Internal Sample',
            text=[f'{value:.2f}' for value in df['ni_split'].tolist()],
            textposition='top right',
            hovertemplate='%{y:.2f}<extra></extra>',
            marker=dict(size=6),
            line=dict(dash="dot", width=2),
        ))

        fig.add_trace(go.Scatter(
            x=df['delivery_order'].tolist(),
            y=df['ni_pulp'].tolist(),
            mode='lines+markers',
            name='Pulp Anindya',
            text=[f'{value:.2f}' for value in df['ni_pulp'].tolist()],
            textposition='bottom center',
            hovertemplate='%{y:.2f}<extra></extra>',
            marker=dict(size=6),
            line=dict(dash="dot", width=2),
        ))

        fig.add_trace(go.Scatter(
            x=df['delivery_order'].tolist(),
            y=df['ni_official'].tolist(),
            mode='lines+markers+text',
            name='Official Anindya',
            text=[f'{value:.2f}' for value in df['ni_official'].tolist()],
            textposition='bottom right',
            hovertemplate='%{y:.2f}<extra></extra>',
            marker=dict(size=6),
        ))

        fig.update_layout(
            height=360,
            barmode='group',
            title='Chart Daily Grade Ni - HPAL',
            yaxis_title='Grade',
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend=dict(x=0.5, y=1.2, orientation='h'),
            margin=dict(l=0, r=0, t=40, b=0),
            hovermode='x unified',

        )

        # Save plot as HTML
        plot_html = pio.to_html(fig, full_html=False, config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines', 'pan', 'select', 'lasso'],
            'responsive': True
        })

        response_data = {
            'delivery_order'  : df['delivery_order'].tolist(),
            'tonnage_split'   : df['tonnage_split'].tolist(),
            'tonnage_pulp'    : df['tonnage_pulp'].tolist(),
            'tonnage_official': df['tonnage_official'].tolist(),
            'ni_split'        : df['ni_split'].tolist(),
            'ni_pulp'         : df['ni_pulp'].tolist(),
            'ni_official'     : df['ni_official'].tolist(),
            'var_split'       : var_split_list,
            'var_pulp'        : var_pulp_list,
            'plot_html'       : plot_html,
        }

        # Return JSON response
        return JsonResponse(response_data, safe=False)


    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)


