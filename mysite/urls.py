"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from students_app.school_admin import school_admin_site

urlpatterns = [
    path('admin/', admin.site.urls),  # Your super admin panel
    path('ai/', include('ai_question_generator.urls')),  # AI Question Generator endpoints
    path('wa/', include('whatsapp_integration.urls')),  # WhatsApp integration endpoints
    path('teacher-demo/', include('teacher_portal_demo.urls')),  # Teacher portal demo
    path('school-admin/', school_admin_site.urls),  # School admin panel
    path('api/', include('students_app.api_urls')),  # Mobile App API
    path('', include('students_app.urls')),  # Main app URLs
]

# Media and Static files configuration for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)