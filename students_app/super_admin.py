from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import School, SchoolUser, UserRole
from .auth_views import admin_dashboard, create_school, create_user, user_list


class SuperAdminSite(admin.AdminSite):
    """Custom admin site for super admin"""
    site_header = "School ERP - Super Admin Panel"
    site_title = "Super Admin Portal"
    index_title = "Manage Schools & System"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', login_required(admin_dashboard), name='index'),
            path('create-school/', login_required(create_school), name='create_school'),
            path('create-user/', login_required(create_user), name='create_user'),
            path('user-list/', login_required(user_list), name='user_list'),
        ]
        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        """Redirect to super admin dashboard"""
        if request.user.is_authenticated:
            try:
                school_user = request.user.school_profile
                if school_user.role.name == 'super_admin':
                    return admin_dashboard(request)
            except:
                pass
        return redirect('/login/')


# Create custom admin site
super_admin_site = SuperAdminSite(name='super_admin')

# Register models with custom admin site
super_admin_site.register(School)
super_admin_site.register(SchoolUser)
super_admin_site.register(UserRole)
super_admin_site.register(User)
