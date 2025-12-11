from django.contrib import admin
from django.urls import path, include

from telegram_app import views as app_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Login sahifasi o'rniga Telegram telefon-login dan foydalanamiz
    path('login/', app_views.telegram_phone_login, name='login'),
    path('logout/', app_views.logout_view, name='logout'),
    path('', include('telegram_app.urls')),
]
