from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin
from . import views

copy_id_prefix = getattr(settings, 'COPY_ID_PREFIX', 'censusnumber').lower()

urlpatterns = [

    # --- Main site ---

    path('', views.homepage, name='homepage'),
    path('homepage/', views.homepage, name='homepage'),
    path('title/<int:id>/', views.issue_list, name='issue_list'),
    path('issue/<int:id>/', views.copy_list, name='copy_list'),
    path('copy/<str:census_id>/', views.single_copy, name='single_copy'),
    path(f'{copy_id_prefix}/<str:census_id>/', views.single_copy, name='single_copy_by_prefix'),
    path('copydata/<int:pk>/', views.copy_data, name='copy_data'),
    path('search/', views.search, name='search'),
    path('info/<str:viewname>/', views.info, name='info'),


    # --- Search autofill ---

    path('autofill/location/<str:query>/', views.autofill_location, name='autofill_location'),
    path('autofill/geography/<str:query>/', views.autofill_geography, name='autofill_geography'),
    path('autofill/provenance/<str:query>/', views.autofill_provenance, name='autofill_provenance'),
    path('autofill/collection/<str:query>/', views.autofill_collection, name='autofill_collection'),


    # --- Data export ---

    path('export/location_copy_count/', views.location_copy_count_csv_export, name='location_copy_count'),
    path('export/title_copy_count/', views.title_copy_count_csv_export, name='title_copy_count'),
    path('export/edition_copy_count/', views.edition_copy_count_csv_export, name='edition_copy_count'),
    path('export/issue_copy_count/', views.issue_copy_count_csv_export, name='issue_copy_count'),
    path('export/provenance_name_copy_count/', views.provenance_name_copy_count_csv_export, name='provenance_name_copy_count'),


    # --- User account management ---

    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),


    # --- Admin panel ---

    path(settings.ADMIN_URL, admin.site.urls),
]


# --- Serve static and media files in development ---

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# Static files will be served even when DEBUG = False, allowing layout and styling to be tested locally.

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# However, media files (title icons) will *not* be served when DEBUG = False unless configured via a separate web server.
