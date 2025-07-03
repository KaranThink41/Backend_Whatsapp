
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('pharmacy.urls')),  # Include pharmacy app URLs with 'api/' prefix
]
