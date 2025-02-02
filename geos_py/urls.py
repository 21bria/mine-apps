from django.urls import path
from .views import login_page,configure_database

urlpatterns = [
    path('', configure_database, name='configure_database'),
    # path('configure-database/', configure_database, name='configure_database'),
    path('login/', login_page, name='login_page'),  # URL untuk halaman server
]
