from django.urls import path
from . import views
from .exports import export_to_excel, export_to_json

urlpatterns = [
    # Auth
    path('', views.telegram_phone_login, name='telegram_phone_login'),
    path('add-session/', views.add_session, name='add_session'),
    path('tg-login/phone/', views.telegram_phone_login, name='telegram_phone_login'),
    path('tg-login/code/', views.telegram_phone_code, name='telegram_phone_code'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('bot-export/', views.bot_export_view, name='bot_export'),
    
    # 2️⃣ Channels (with subscription)
    path('channels/', views.channels_view, name='channels'),
    path('channels/<int:channel_id>/toggle/', views.toggle_channel_tracking, name='toggle_channel_tracking'),
    
    # Fetch messages
    path('fetch/<int:channel_id>/', views.fetch_messages_view, name='fetch_messages'),
    
    # 1️⃣ Messages (with TAG search & highlight)
    path('messages/', views.saved_messages_view, name='saved_messages'),
    
    # 3️⃣ Message detail (full view)
    path('messages/<int:message_id>/', views.message_detail_view, name='message_detail'),
    
    # 4️⃣ Route duplicates
    path('stats/<int:channel_id>/route/duplicates/', views.route_duplicates_view, name='route_duplicates'),
    
    # Stats
    path('stats/<int:channel_id>/', views.channel_stats_view, name='channel_stats'),
    path('stats/<int:channel_id>/export-excel/', views.channel_stats_excel, name='channel_stats_excel'),
    path('stats/<int:channel_id>/phones/', views.channel_phones_view, name='channel_phones'),
    path('stats/<int:channel_id>/phones/messages/', views.channel_phone_messages_view, name='channel_phone_messages'),
    path('stats/<int:channel_id>/phones/export-excel/', views.channel_phones_excel, name='channel_phones_excel'),
    path('stats/<int:channel_id>/route/', views.channel_route_messages_view, name='channel_route_messages'),
    path('stats/<int:channel_id>/cargo/', views.channel_cargo_messages_view, name='channel_cargo_messages'),
    path('stats/<int:channel_id>/truck/', views.channel_truck_messages_view, name='channel_truck_messages'),
    path('stats/<int:channel_id>/payment/', views.channel_payment_messages_view, name='channel_payment_messages'),
    
    # Export
    path('export-json/', views.export_json, name='export_json'),
    path('excel-export/', views.excel_export_page, name='excel_export_page'),
    path('export-excel/', export_to_excel, name='export_excel'),
    path('export-json/', export_to_json, name='export_json'),
]