from django.urls import path
# Sale Ore
from ..views.sellings.selling_details_view import *
from ..views.sellings.selling_delayed_view import *
from ..views.sellings.selling_plan_view import *
from ..views.sellings.selling_official_view import *
from ..views.sellings.split_official.selling_split_hpal_mral_view import *
from ..views.sellings.split_official.selling_split_hpal_roa_view import *
from ..views.sellings.split_official.selling_split_hpal_range_view import *
from ..views.sellings.analysis.selling_hpal_days_view import *
from ..views.sellings.analysis.selling_hpal_code_view import *
from ..views.sellings.analysis.selling_hpal_days_mral_view import *



urlpatterns = [

 # Table Selling Details
    path('sale-page/', sale_details_page, name='sale-page'), 
    path('sale-list/', SellingDetails.as_view(), name='sale-list'), 
    path('export-sale-data/',export_sale_data, name='export-sale-data'),
    path('sale/get-id/<int:id>/', getIdSale, name='get-id-sale'),
    path('sale/delete/', delete_sale, name='delete-data-sale'),

    # Selling Delayed
    path('sale-delayed-page/', sale_delayed_page, name='sale-delayed-page'), 
    path('sale-delayed/list/', getDelayed.as_view(), name='sale-delayed-list'), 
    path('sale/update-data/<int:id>/', update_sale, name='update-data-sale'),

    # Plan Selling
    path('sale-plan-page/', sale_plan_page, name='sale-plan-page'), 
    path('sale-plan/list/', sellingDataPlan.as_view(), name='sale-plan-list'), 
    path('sale-plan/create/', create_plan_sale, name='create-plan-sale'),
    path('sale-plan/delete/', delete_sale_plan, name='delete-sale-plan'),
    path('sale-plan/get-id/<int:id>/', getIdPlanSale, name='get-id-sale-paln'),
    path('sale-plan/update/<int:id>/', update_sale_plan, name='update-sale-plan'),

    # Official Selling
    path('sale-official-page/', sale_official_page, name='sale-official-page'), 
    path('sale-official/list/', sellingDataOfficial.as_view(), name='sale-official-list'), 
    path('sale-official/create/', create_official_sale, name='create-official-sale'),
    path('sale-official/delete/', delete_sale_official, name='delete-sale-official'),
    path('sale-official/get-id/<int:id>/', getIdOfficial, name='get-id-sale-official'),
    path('sale-official/update/<int:id>/', update_official, name='update-sale-official'),

    # SPLIT Selling Official
    path('split-hpal/mral-index/',splitMralHpal_page, name='split-hpal-mral-page'),
    path('split-hpal/mral-awk/',getSumSellingAWK, name='get-split-hpal-mral'),
    path('split-hpal/mral-pulp/',getSumPulpAWKMral, name='get-split-hpal-pulp-mral'),
    path('split-hpal/awk-official/',getOfficialAwk, name='get-awk-official'),

    path('split-hpal/roa-index/',splitRoaHpal_page, name='split-hpal-roa-page'),
    path('split-hpal/roa-awk/',getSellingAWKRoa, name='get-split-hpal-roa'),
    path('split-hpal/roa-pulp/',getPulpAWKRoa, name='get-split-hpal-pulp-roa'),
    path('split-hpal/roa-awk-official/',getOfficialAwkRoa, name='get-awk-official-roa'),

    path('split-sale/range-index/',splitRange_page, name='split-range-page'),
    path('split-sale/range-awk/',rangeSplitAWK, name='get-split-sale-range'),
    path('split-sale/range-pulp/',rangeSplitPulpAWK, name='get-split-sale-pulp-range'),
    path('split-sale/range-awk-official/',rangeOfficialAwk, name='get-awk-official-range'),
   
    # Analys Sale
    path('sale-analysis/hpal-grade-index/',gradeHpalMonth_page, name='hpal-grade-index'),
    path('sale-analysis/hpal-grade-days/',gradeByDays, name='get-hpal-grade-days'),
    path('sale-analysis/hpal-ach-days/',achievmentByDays, name='get-hpal-ach-days'),

    path('sale-analysis/hpal-code-index/',gradeHpalCode_page, name='index-hpal-code'),
    path('sale-analysis/hpal-grade-code/',gradeByCode, name='get-grade-code'),

    path('sale-analysis/hpal-plan-index/',gradeHpalPlan_page, name='index-hpal-plan'),
    path('sale-analysis/hpal-plan-days/',planByDays, name='get-plan-hpal-days'),
    path('sale-analysis/hpal-plan-grade/',gradeByDaysMral, name='get-plan-hpal-grade'),
    path('sale-analysis/hpal-grade-code-mral/',gradeByCodeMral, name='get-plan-hpal-code'),
 

]