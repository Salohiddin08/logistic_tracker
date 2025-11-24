from django.urls import path
from . import views

urlpatterns = [
    path('', views.add_session, name='add_session'),
    path('channels/', views.channels_view, name='channels'),
    path('fetch/<int:channel_id>/', views.fetch_messages_view, name='fetch_messages'),
    path('messages/', views.saved_messages_view, name='saved_messages'),
    path('stats/<int:channel_id>/', views.channel_stats_view, name='channel_stats'),
    path('stats/<int:channel_id>/export-excel/', views.channel_stats_excel, name='channel_stats_excel'),
    path('stats/<int:channel_id>/route/', views.channel_route_messages_view, name='channel_route_messages'),
    path('stats/<int:channel_id>/cargo/', views.channel_cargo_messages_view, name='channel_cargo_messages'),
    path('export-json/', views.export_json, name='export_json'),
]
