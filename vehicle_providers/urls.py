from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.vehicle_provider_dashboard, name='vehicle_provider_dashboard'),
    path('add-ebike/', views.add_ebike, name='add_ebike'),
    path('register-vehicle/', views.register_vehicle, name='register_vehicle'),
    path('upload-documents/', views.upload_documents, name='upload_documents'),
    path('view-documents/', views.view_documents, name='view_documents'),
    path('request-withdrawal/', views.request_withdrawal, name='request_withdrawal'),
    path('withdrawal-history/', views.withdrawal_history, name='withdrawal_history'),
    path('download-withdrawal-receipt/<int:withdrawal_id>/', views.download_withdrawal_receipt, name='download_withdrawal_receipt'),
    path('download-withdrawal-slip/<int:withdrawal_id>/', views.download_withdrawal_slip, name='download_withdrawal_slip'),
    path('download-statement/', views.download_statement, name='download_statement'),
]
