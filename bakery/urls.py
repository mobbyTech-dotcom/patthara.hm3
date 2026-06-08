from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('order/', views.order_page, name='order_page'),
    path('order/create/', views.create_order, name='create_order'),
    path('order/receipt/<str:order_number>/', views.order_receipt, name='order_receipt'),
    path('order/receipt/<str:order_number>/slip/', views.upload_slip, name='upload_slip'),
    path('track/', views.track_order, name='track_order'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/add/', views.product_add, name='product_add'),
    path('admin-panel/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('admin-panel/delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('admin-panel/toggle/<int:pk>/', views.product_toggle, name='product_toggle'),
    path('admin-panel/order/<int:order_id>/status/', views.order_update_status, name='order_update_status'),
    path('admin-panel/payment/update/', views.payment_update, name='payment_update'),
    path('admin-panel/payment/delete-qr/', views.payment_delete_qr, name='payment_delete_qr'),
]
