from django.urls import path
from api_apps import views_api
from .views.materials_views import MaterialView
from .views.ore_production_views import OreProductionView,OreProductionYearView
from .views.ore_selling_views import OreSellingView,OreSellingYearView
from .views.ore_grade_views import hpalGradeRoaView,rkefGradeRoaView,hpalGradeMonthRoaView,rkefGradeMonthRoaView
from .views.achievements_mral_views import AchievementsMralView
from .views.achievements_roa_views import AchievementsRoaView

urlpatterns = [
    # path('materials/list/',views.material_list,name='list-materials'),  
    path('materials/list/', MaterialView.as_view(), name='materials-list'),
    path('materials/<int:pk>/', MaterialView.as_view(), name='materials-detail'),
    # Endpoint untuk membuat data Material baru (POST)
    path('materials/', MaterialView.as_view(), name='material-create'),

    # Endpoint untuk membuat data summary data Production & Selling
    path('ore-production/totals/', OreProductionView.as_view(), name='ore-production-aggregate'),
    path('ore-selling/totals/', OreSellingView.as_view(), name='ore-selling-aggregate'),
    path('ore-selling/totals/year/', OreSellingYearView.as_view(), name='ore-selling-aggregate-year'),
    path('ore-production/totals/year/', OreProductionYearView.as_view(), name='ore-production-aggregate-year'),
    path('ore-production/grade-hpal/year/', hpalGradeRoaView.as_view(), name='ore-production-grade-hpal-year'),
    path('ore-production/grade-rkef/year/', rkefGradeRoaView.as_view(), name='ore-production-grade-rkef-year'),
    path('ore-production/grade-hpal/month/', hpalGradeMonthRoaView.as_view(), name='ore-production-grade-hpal-month'),
    path('ore-production/grade-rkef/month/', rkefGradeMonthRoaView.as_view(), name='ore-production-grade-rkef-month'),

    # Endpoint Achievements
    path('ore-achievements/mral/', AchievementsMralView.as_view(), name='ore-achievements-mral'),
    path('ore-achievements/roa/', AchievementsRoaView.as_view(), name='ore-achievements-roa'),

]
