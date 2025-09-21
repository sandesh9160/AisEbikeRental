from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('approve-booking/<int:booking_id>/', views.approve_booking, name='approve_booking'),
    path('approve-vehicle-registration/<int:registration_id>/', views.approve_vehicle_registration, name='approve_vehicle_registration'),
    path('reject-booking/<int:booking_id>/', views.reject_booking, name='reject_booking'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('review-documents/', views.review_documents, name='review_documents'),
    path('verify-document/<int:document_id>/', views.verify_document, name='verify_document'),
    path('verify-provider/<int:provider_id>/', views.verify_provider, name='verify_provider'),
    path('edit-document-verification/<int:document_id>/', views.edit_document_verification, name='edit_document_verification'),
    path('remove-document-verification/<int:document_id>/', views.remove_document_verification, name='remove_document_verification'),
    # Bulk document actions for review documents page
    path('bulk-approve-documents/', views.bulk_approve_documents, name='bulk_approve_documents'),
    path('bulk-reject-documents/', views.bulk_reject_documents, name='bulk_reject_documents'),
    # Bulk operations
    path('bulk-approve-bookings/', views.bulk_approve_bookings, name='bulk_approve_bookings'),
    path('bulk-reject-bookings/', views.bulk_reject_bookings, name='bulk_reject_bookings'),
    path('bulk-verify-providers/', views.bulk_verify_providers, name='bulk_verify_providers'),
    # AJAX endpoints
    path('api/filtered-data/', views.get_filtered_data, name='get_filtered_data'),
]

