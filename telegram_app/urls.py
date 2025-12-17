from django.urls import path
from . import views

urlpatterns = [
    # Saytga birinchi kirilganda Telegram telefon-login sahifasi ochiladi
    path('', views.telegram_phone_login, name='telegram_phone_login'),
    path('add-session/', views.add_session, name='add_session'),
    path('tg-login/phone/', views.telegram_phone_login, name='telegram_phone_login'),
    path('tg-login/code/', views.telegram_phone_code, name='telegram_phone_code'),
    path('channels/', views.channels_view, name='channels'),
    path('fetch/<int:channel_id>/', views.fetch_messages_view, name='fetch_messages'),
    path('messages/', views.saved_messages_view, name='saved_messages'),
    path('stats/<int:channel_id>/', views.channel_stats_view, name='channel_stats'),
    path('stats/<int:channel_id>/export-excel/', views.channel_stats_excel, name='channel_stats_excel'),
    path('stats/<int:channel_id>/phones/', views.channel_phones_view, name='channel_phones'),
    path('stats/<int:channel_id>/phones/messages/', views.channel_phone_messages_view, name='channel_phone_messages'),
    path('stats/<int:channel_id>/phones/export-excel/', views.channel_phones_excel, name='channel_phones_excel'),
    path('stats/<int:channel_id>/route/', views.channel_route_messages_view, name='channel_route_messages'),
    path('stats/<int:channel_id>/cargo/', views.channel_cargo_messages_view, name='channel_cargo_messages'),
    path('stats/<int:channel_id>/truck/', views.channel_truck_messages_view, name='channel_truck_messages'),
    path('stats/<int:channel_id>/payment/', views.channel_payment_messages_view, name='channel_payment_messages'),
    path('export-json/', views.export_json, name='export_json'),
    path('dashboard', views.dashboard_view, name='dashboard'),
]
