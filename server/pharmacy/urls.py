from django.urls import path
from . import views

app_name = 'pharmacy'

urlpatterns = [
    # Medicine URLs
    path('medicines/', views.MedicineListView.as_view(), name='medicine-list'),
    path('medicines/<int:pk>/', views.MedicineDetailView.as_view(), name='medicine-detail'),
    path('medicines/search/', views.search_medicines, name='medicine-search'),
    path('medicines/suggestions/', views.medicine_suggestions, name='medicine-suggestions'),
    
    # Category and Manufacturer URLs  
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('manufacturers/', views.ManufacturerListView.as_view(), name='manufacturer-list'),
    
    # Pharmacy URLs
    path('pharmacies/', views.PharmacyListView.as_view(), name='pharmacy-list'),
    path('pharmacies/<int:pk>/', views.PharmacyDetailView.as_view(), name='pharmacy-detail'),
    path('pharmacies/<int:pharmacy_id>/inventory/', views.pharmacy_inventory, name='pharmacy-inventory'),
    path('pharmacies/nearby/', views.pharmacy_nearby, name='pharmacy-nearby'),
    
    # Customer URLs
    path('customers/', views.CustomerCreateView.as_view(), name='customer-create'),
    path('customers/<str:phone_number>/', views.customer_profile, name='customer-profile'),
    
    # Order URLs
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/<uuid:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/quick-create/', views.create_quick_order, name='quick-order'),
    path('orders/<uuid:order_id>/status/', views.update_order_status, name='update-order-status'),
    
    # WhatsApp Session URLs
    path('whatsapp-session/<str:phone_number>/', views.whatsapp_session, name='whatsapp-session'),
]