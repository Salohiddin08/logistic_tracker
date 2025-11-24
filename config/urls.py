from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from telegram_app import views as app_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', app_views.logout_view, name='logout'),
    path('', include('telegram_app.urls')),
]
