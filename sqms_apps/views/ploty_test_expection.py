import plotly.graph_objects as go
import pandas as pd
import warnings
from django.db import connections, DatabaseError
from django.http import JsonResponse
from plotly.io import to_html
import logging

# Setup logger
logger = logging.getLogger(__name__)

def line_plot_sample_exmral(request):
    startDate = request.GET.get('startDate')
    endDate = request.GET.get('endDate')
    material = request.GET.get('material')
    source = request.GET.get('source')

    query = """
        SELECT
            t3.sample_number,
            COALESCE(SUM(t1.tonnage * t1.grade_expect) / NULLIF(
                        SUM(CASE WHEN t3.sample_number IS NOT NULL AND t1.grade_expect IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                    AS ex_ni,
            COALESCE(SUM(t1.tonnage * t4.ni) / NULLIF (
                    SUM(CASE WHEN t3.sample_number IS NOT NULL AND t4.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                    AS ni_act
        FROM ore_productions AS t1
        LEFT JOIN materials AS t2 ON t2.id=t1.id_material
        LEFT JOIN samples_productions as t3 ON t3.kode_batch=t1.kode_batch
        LEFT JOIN assay_mrals as t4 ON t4.sample_id=t3.sample_number
        LEFT JOIN prospect_areas AS t5 ON t5.id=t1.id_prospect_area
        WHERE 
        t1.grade_expect IS NOT NULL
            AND t3.sample_number IS NOT NULL 
            AND t4.ni IS NOT NULL  
            AND t1.tgl_production >= %s 
            AND t1.tgl_production <= %s 
            AND t2.nama_material = %s
    """
   
    filters = []
    params = [startDate, endDate, material]

    if source:
        filters.append("prospect_area = %s")
        params.append(source)

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " GROUP BY t3.sample_number"

    try:
        # Handle warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Use the correct database connection
            df = pd.read_sql_query(query, connections['sqms_db'], params=params)
        
        if df.empty:
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
                height=360,
            )
            plot_div = fig.to_html(full_html=False)
            return JsonResponse({'plot_div': plot_div})

        # Prepare data for Plotly
        sample_numbers = df['sample_number'].tolist()
        ex_ni = df['ex_ni'].tolist()
        ni_act = df['ni_act'].tolist()
        accuration = [
            round(
                (1 - abs((row['ni_act'] - row['ex_ni']) / ((row['ni_act'] + row['ex_ni']) / 2) * 100)) * 100, 2
            ) for _, row in df.iterrows()
        ]

        # Create Plotly figure
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=sample_numbers,
            y=ex_ni,
            mode='lines+markers',
            name='Expectation'
        ))

        fig.add_trace(go.Scatter(
            x=sample_numbers,
            y=ni_act,
            mode='lines+markers',
            name='Actual'
        ))

        fig.add_trace(go.Scatter(
            x=sample_numbers,
            y=accuration,
            mode='lines+markers',
            name='Accuration'
        ))

        fig.update_layout(
            title='Sample Data',
            xaxis_title='Sample Number',
            yaxis_title='Values',
        )

        # Convert Plotly figure to HTML
        plot_div = to_html(fig, full_html=False)

        return JsonResponse({'plot_div': plot_div})

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)
