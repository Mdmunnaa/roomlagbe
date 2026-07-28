from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('search/', views.search_results, name='search_results'),
    path('property/<slug:slug>/', views.property_detail, name='property_detail'),
    path('property/<slug:slug>/book/', views.booking_inquiry, name='booking_inquiry'),
    path('property/<slug:slug>/chat/', views.start_conversation, name='start_conversation'),

    # In-app chat
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('inbox/<int:conversation_id>/messages.json', views.conversation_messages_json, name='conversation_messages_json'),

    # Auth
    path('register/', views.register_guest, name='register'),
    path('register/host/', views.register_host, name='register_host'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Host Dashboard
    path('dashboard/', views.host_dashboard, name='host_dashboard'),
    path('dashboard/add-property/', views.add_property, name='add_property'),
    path('dashboard/edit/<slug:slug>/', views.edit_property, name='edit_property'),
    path('dashboard/delete/<slug:slug>/', views.delete_property, name='delete_property'),
]
