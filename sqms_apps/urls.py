# sqms_apps/urls.py
from django.urls import path,include
from .views.auth import login_view
from .views.dashboard import *
from django.contrib.auth.views import LogoutView
# Import Dropdown List
from .views.settings.dropdown_view import *

# Ore Production Mine Geology
from .views.mgoqa.ore_pds.ore_details_view import *
from .views.mgoqa.ore_pds.ore_create_view import *

# Samples Production Mine Geology
from .views.mgoqa.samples.samples_details_view import *

# Reconciliation Productions
from .views.reconciliation.pds_reconciliation_view import *

# Workflow
from .views.approval.submit_admin_view import *
from .views.approval.approval_production_view import *


# Imports
# from .views.imports_data_view import import_data, imports_page,load_columns

# Dashboard
from  .views.dashboard.index import *
from  .views.dashboard.dashboard_selling import *
from .views.dashboard.dashboard_mgoqa import *
from .views.dashboard.dashboard_mining import *
from .views.analyst_ore import *


from .views_upload import *
from .encrypt_view import *
from .views.notification.notifications_view import get_notifications
from .views.task_list.task_list_view import *

from .template_file_views import format_downloads
from .email_views import send_test_email
from .clean_data import clean_data_view

from .views.auth_users.manage_group_view import *

urlpatterns = [
 
    path('', login_view, name='auth'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashborad/mgoqa/', home_mgoqa, name='index-mgoqa'),
    path('dashborad/mining/', home_mining, name='index-mining'),
    path('dashborad/vendors/', home_vendors, name='index-vendors'),
    path('dashborad/selling/', home_selling, name='index-selling'),
    path('clean/data/', clean_data_view, name='index-clean'),

    # Dashboard MGOQA
    path('get-ore-ptd/', get_ore_ptd, name='get-ore-ptd'),
    path('get-total-lim/', get_total_lim, name='get-total-lim'),
    path('get-total-sap/', get_total_sap, name='get-total-sap'),
    path('get-grade-ytd/hpal/', get_grade_hpal, name='get-grade-ytd-hpal'),
    path('get-grade-ytd/rkef/', get_grade_rkef, name='get-grade-ytd-rkef'),
    path('get-ytd-ore/', get_ytd_ore, name='get-ytd-ore'),
    path('get-chart-data/', get_chart_data, name='get_chart_data'),
    path('chart-ore-class/', get_chart_ore_class, name='chart-ore-class'),
    path('chart-ore-daily/', get_chart_ore_daily, name='chart-ore-daily'),
    path('chart-ore-class-daily/', get_daily_ore_class, name='chart-ore-class-daily'),
    path('get-mtd-ore/', get_mtd_ore, name='get-mtd-ore'),
    path('get-grade-mtd/hpal/', get_mtd_grade_hpal, name='get-grade-mtd-hpal'),
    path('get-grade-mtd/rkef/', get_mtd_grade_rkef, name='get-grade-mtd-rkef'),

    path('get-ytd-sample/', get_sample_ytd, name='get-ytd-sample'),
    path('get-mtd-sample/', get_sample_mtd, name='get-mtd-sample'),
    path('get-sample/this-week/', get_sample_this_week, name='get-sample-this-week'),
    path('get-sample/this-days/', get_sample_this_days, name='get-sample-this-days'),
    path('get-ore/stockpile/hpal/', get_stockpile_hpal, name='get-ore-stockpile-hpal'),
    path('get-ore/stockpile/rkef/', get_stockpile_rkef, name='get-ore-stockpile-rkef'),

    path('get-ore/production/forecast/', forecast_production, name='get-ore-forecast-production'),

    
    # Dashboard Selling
    path('get-sale-ptd/', get_sale_ptd, name='get-sale-ptd'),
    path('get-sale-ytd/', get_ytd_sale, name='get-sale-ytd'),
    path('get-chart-sale-ytd/', get_chart_sale_ytd, name='get-chart-sale-ytd'),
    path('get-pie-sale-ytd/', get_pie_sale_ytd, name='get-pie-sale-ytd'),
    path('get-sale/grade-hpal-ytd/', getGradeHpalbyYtd, name='get-sale-grade-hpal-ytd'),
    path('get-sale/grade-rkef-ytd/', getGradeRkefbyYtd, name='get-sale-grade-rkef-ytd'),
    path('get-sale/type-selling-ytd/', getTypeSellingYtd, name='get-sale-type-selling-ytd'),

    path('get-daily-sale-discharge/', get_daily_sale_discharge, name='get-daily-sale-discharge'),
    path('get-daily-sale/', get_chart_sale_daily, name='get-daily-sale'),
    path('get-time-sale/', get_chart_sale_time, name='get-daily-time'),
    path('get-mtd-sale/', get_mtd_sale, name='get-mtd-sale'),
    path('get-week-sale/', getTotalbyWeekSelling, name='get-week-sale'),
    path('get-sale-daily/grade-hpal/', gradeByDaysHpal, name='get-sale-daily-grade-hpal'),
    path('get-sale-daily/grade-rkef/', gradeByDaysRkef, name='get-sale-daily-grade-rkef'),

    path('get-ytd/sample/selling/', get_sample_selling_ytd, name='get-ytd-sample-selling'),
    path('get-mtd/sample/selling/', get_sample_selling_mtd, name='get-mtd-sample-selling'),
    path('get-sample/this-week/selling/', get_sample_selling_this_week, name='get-sample-this-week-selling'),
    path('get-sample/this-days/selling/', get_sample_selling_this_days, name='get-sample-this-days-selling'),
    
    #By Year Summary
    path('get-total-ore-year/', getTotalOreByYear, name='get-total-ore-year'),
    path('get-total-sale-year/', getTotalSaleByYear, name='get-total-sale-year'),

    # Stokcpile Ore
    path('get-total-hpal/', getOreHPAL, name='get-total-hpal'),
    path('get-total-rkef/', getOreRKEF, name='get-total-rkef'),

    # Dashboard Mining
    path('get-mine/ptd/', get_mine_category_ptd, name='get-mine-category-ptd'),
    path('get-mine/ytd/', get_mine_category_ytd, name='get-mine-category-ytd'),
    path('get-mine/mtd/', get_mine_category_mtd, name='get-mine-category-mtd'),
    path('get-mine/wtd/', get_mine_category_wtd, name='get-mine-category-wtd'),
    path('get-mine/ytd/card/', get_ytd_card_mine, name='get-mine-card-ytd'),
    path('get-mine/ytd/chart/', get_mine_chart_ytd, name='get-mine-chart-ytd'),
    path('get-mine/chart/mtd/', get_chart_mine_daily, name='get-mine-chart-mtd'),
    path('get-mine/material/mtd/', get_chart_material_daily, name='get-mine-material-mtd'),
    path('get-mine/hours/daily/', get_MineByHours, name='get-mine-hours-daily'),
    path('get-mine/material/days/', get_MineByDays, name='get-mine-material-days'),
    path('get-mine/analysis/weeks/', get_mine_chart_weeks, name='get-mine-weeks-analysis'),
    path('get-mine/analysis/on-weeks/', get_material_on_week, name='get-mine-on-weeks-analysis'),


    # Get Dropdown dinamyc
    path('method_dropdown/', method_dropdown, name='method-dropdown'), 
    path('material_dropdown/', material_dropdown, name='material-dropdown'), 
    path('get-details-point/', get_details_point, name='get-details-point'), 
    path('get-details-source/', get_details_sources, name='get-details-source'), 
    path('get-details-truck/', get_details_truck, name='get-details-truck'), 
    path('get-year-ore/', get_year_ore, name='get-year-ore'), 
    path('get-year-sale/', get_year_sale, name='get-year-sale'), 
    path('get-year-sample/', get_year_sample, name='get-year-sample'), 
    path('get-sale-stockpile/', get_sale_stockpile, name='get-sale-stockpile'), 
    path('get-sale-dome/', get_sale_dome, name='get-sale-dome'), 
    path('get-sale-discharge/', get_sale_discharge, name='get-sale-discharge'), 
    path('get-sale-product/', get_sale_product, name='get-sale-product'), 
    path('get-materials-factors/', getMaterialsFactors, name='get-materials-factors'), 

    # For Insert & edit Ore
    path('block-id-dropdown/', dropdownBlockId, name='block-id-dropdown'), 
    path('material-id-dropdown/', dropdownMaterialId, name='material-id-dropdown'), 
    path('stockpile-id-dropdown/', dropdownStockpileId, name='stockpile-id-dropdown'), 
    path('dome-id-dropdown/', dropdownDomeId, name='dome-id-dropdown'), 
    path('mine-geos-dropdown/', dropdownMineGoes, name='mine-geos-dropdown'), 
    path('ore-class-dropdown/<int:id>/', dropdownOreClass, name='ore-class-dropdown'), 
    path('ore-class-get/', dropdownOreClassGet, name='ore-class-get'), 
    path('get-ore-classes/', get_ore_classes, name='get-ore-classes'),
    path('get-ore-factors/', get_truck_factors, name='get-ore-factors'),
    path('ore-ton/get-id/<str:id>/', getOreTonnage, name='get-ton-ore'),
   
    #  For Samples Production
    path('samples-material/',  get_sample_material, name='samples-material'), 
    path('samples-product/',  get_product_code, name='samples-product'), 
    path('samples-discharge/',  get_discharge, name='samples-discharge'), 
    path('samples-type/',  sample_type_dropdown, name='samples-type'), 
    path('samples-type/pds/',  sampleTypeId, name='samples-type-pds'), 
    path('samples-type/sale/',  sampleTypeSaleId, name='samples-type-sale'), 
    path('method/get-id/<int:id>/', method_detail, name='get-method-detail'),
    path('method/id-get/', get_methodSample, name='get-method-id'),
    path('sample/get-material/', sampleMaterialId, name='get-sample-material'),
    path('sample/get-area/', sampleAreaId, name='get-sample-area'),
    path('sample/get-point/', samplePointId, name='get-sample-point'),
    path('sample/get-product/', codeProductId, name='get-sample-product'),
    path('sample/get-factory/', stockFactoryId, name='get-sample-factory'),
    path('sample/get-material-sale/', material_sale, name='get-material-sale'),
    path('sale/get-surveyor/', saleSurveyor, name='get-surveyor'),
    
    path('sample/get-crm/', get_sample_crm, name='get-crm'),
    path('sample/get-dome-pds-active/', get_dome_pds_active, name='get-dome-pds-active'),

    path('get-units-categories/', get_units_categories, name='get-units-categories'),
    path('get-units-vendor/', get_units_vendors, name='get-units-vendor'),
    path('get-dome-merge-dropdown/', get_merge_dome, name='get-dome-merge-dropdown'),
    path('get-stockpile-merge-dropdown/', get_merge_stockpile, name='get-stockpile-merge-dropdown'),

    # For Production Dropdown
    path('get-mine/source/', get_mine_sources, name='get-mine-source'),
    path('get-mine/block/', get_blockMine, name='get-block-mine'),
    path('get-mine/materials/', get_materials, name='get-mine-materials'),
    path('get-mine/loading-point/', get_mine_loading_points, name='get-mine-loading-point'),
    path('get-mine/dumping-point/', get_mine_dumping_points, name='get-mine-dumping-point'),
    path('get-mine/dome/', get_mine_dome, name='get-mine-dome'),
    path('get-mine/units/', get_mine_units, name='get-mine-units-entry'),
    path('get-mine/vendors/', get_mine_vendors, name='get-mine-vendors'),
    path('get-mine/plan-category/', get_category_mine, name='get-mine-plan-category'),
    path('get-mine/materials/all/', get_mineMaterials, name='get-materials-mine'),
    path('get-mine/geos/', get_mine_geos, name='get-mine-geos'),
    
    # Get All
    path('get-mine/category/', get_mine_category, name='get-mine-category'),
    path('get-mine/source/all', get_sources_mine, name='get-mine-source-all'),

    # Samples
    path('get-mine/sample/type/', get_sample_type, name='get-mine-sample-type'),
    path('get-mine/sample/type/sale/', get_sampleTypeSale, name='get-sale-sample-type'),
    path('get-mine/stock/factories/sale/', get_stockFactories, name='get-sale-stock-factories'),
    path('get-mine/code/product/sale/', get_codeProduct, name='get-sale-code-product'),
    # END Drop Down

    # Analisis Sale
    path('sale-analysis/sale-all/',saleAllData, name='get-sale-all'),
    path('pds-analysis/pds-all/',pdsAllData, name='get-pds-all'),

    # Reconciliation Productions
    path('mine-reconciliation/page/', mine_reconciliation_page, name='mine-reconciliation-page'), 
    path('gc-reconciliation/page/', gc_reconciliation_page, name='gc-reconciliation-page'), 
    path('mine-reconciliation/list/', viewReconciliationPds.as_view(), name='mine-reconciliation-list'),
    # Sum date
    path('mine-reconciliation/get/page', mine_recon_day_page, name='mine-reconciliation-get-page'),
    path('mine-reconciliation/get/day', recon_mine_day, name='mine-reconciliation-get-day'),
    path('mine-reconciliation/get/date', recon_mine_date, name='mine-reconciliation-get-date'),
    path('mine-reconciliation/get/date/dome', source_mine_dome, name='mine-reconciliation-get-date-dome'),

    # Create Approval Production :
    # Form create Approval
    path('approval/create/', create_approval, name='create-approval'),
    path('approval/asisten/review/', review_asisten, name='approval-asisten-review'),
    path('approval/manager/review/', review_manager, name='approval-manager-review'),
    path('approval/submit/list/', submitApprovalProduction.as_view(), name='submit-approval-list'),

    path('approval/submit/page/gc', submit_approval_gc_page, name='submit-approval-page-gc'),
    path('approval/submit/gc-get/<int:approval_id>/', get_approval_log, name='get-submit-approval-gc'),
    path('approval/submit/page/review', review_approval_page, name='submit-approval-page-review'),
    path('approval/submit/get/gc', get_approval_gc, name='submit-approval-get-gc'),
    path('approval/submit/get/mining', get_approval_mining, name='submit-approval-get-mining'),

    # from submited to Assisten and Manager
    path('approval/create/page/gc', create_approval_page, name='create-approval-page-gc'), 
    path('approval/create/page/mining', createApproval_page, name='create-approval-page-mining'), 

    path('approval/review/page/asisten/gc', review_asisten_page, name='review-approval-page-asisten-gc'),
    path('approval/asisten/page/gc', asisten_approval_page, name='approval-asisten-page-gc'),

    path('approval/review/page/manager/gc', review_manager_page, name='review-approval-page-manager-gc'),
    path('approval/manager/page/gc', manager_approval_page, name='approval-manager-page-gc'),
   

    # For Mining Approval
    path('approval/submit/page/mining', submitApproval_page, name='submit-approval-page-mining'),
    path('approval/submit/page/review/mining', reviewApproval_page, name='submit-approval-page-review-mining'),
    path('approval/create/asisten/page/mining', asistenApproval_page, name='create-asisten-page-mining'),
    path('approval/create/manager/page/mining', managerApproval_page, name='create-manager-page-mining'),

    path('approval/asisten/review/mining', reviewAsisten_page, name='approval-asisten-page-mining'),
    path('approval/manager/review/mining', reviewManager_page, name='approval-manager-page-mining'),
    path('encrypt-date/', encrypt_date_view, name='encrypt-date'),  # URL untuk enkripsi
    
    #  Imports Data
    # path('import-data/', import_data, name='import-data'),
    # path('load-columns/', load_columns, name='load_columns'),

    path('analyst/data-ore/', analystOreData_page, name='analyst-data-ore'),
    path('data-analyst/ore/', analystOre, name='get-data-analyst-ore'),
    path('data-analyst/selling/', analystSale, name='get-data-analyst-selling'),
    path('data-analyst/ore-year/', get_ore_year_data, name='get-ore-year-data-analyst'),
    path('data-analyst/sale-year/', get_sale_year_date, name='get-sale-year-data-analyst'),
    
    #Data Import Excel 
    path('import-excel-page/', imports_page, name='import-excel-page'),
    path('get-task-import/', get_task_import, name='get-task-import'),
    path('upload-file/', upload_file, name='upload-file'),
    path('task-import/list/', TaskImportsList.as_view(), name='task-list-imports'), 
        
    # URL sub
    path('mgoqa/', include('sqms_apps.urls_path.mgoqa_urls')),
    path('selling/', include('sqms_apps.urls_path.selling_urls')),
    path('mining/', include('sqms_apps.urls_path.mining_urls')),
    path('master/', include('sqms_apps.urls_path.master_urls')),
    path('report/', include('sqms_apps.urls_path.report_urls')),
    path('auth/', include('sqms_apps.urls_path.auth_urls')),
    path('config/', include('sqms_apps.urls_path.config_urls')),

    # URL lainnya di sini
    path('get-notifications/', get_notifications, name='get-notifications'),

    # Task list
    path('task/table/', task_list_page, name='task-table-page'),
    path('task-table/list/', task_List.as_view(), name='task-list-table'),
    path('task/table/add/', add_task, name='task-table-add'),
    path('task/table/<int:pk>/edit/', edit_task, name='task-table-edit'),
    path('task/table/delete/', delete_task, name='task-table-delete'),

    # tempalte format import
    path('format-downloads/', format_downloads, name='format_downloads'),
    path('send-email/', send_test_email, name='send_test_email'),


    # permission role
    path('permission/group/', permission_group_page, name='permission-group-page'),
    path('permission/list/group/', group_permissionList.as_view(), name='permission-list-group'),
    path('groups/permission/create', group_permission_create, name='group-permission-create'),
    path('groups/permission/<int:pk>/edit/', group_permission_edit, name='group-permission-edit'),

]
