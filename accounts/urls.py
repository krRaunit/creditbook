from django.urls import path
from . import views
from .views import health_check  # or use the appropriate path


urlpatterns = [
    path('', views.home, name='home'),
    path('customer-login/', views.customer_login, name='customer-login'),
    path('help/', views.help, name='help'),
    path('about/', views.about, name='about'),
    path('customer-registration/', views.customer_register, name='customer-registration'),
    path('merchant-login/', views.merchant_login, name='merchant-login'),
    path('merchant-registration/', views.merchant_register, name='merchant-registration'),
    path('customer-dashboard/', views.customer_dashboard, name='customer-dashboard'),
    path('merchant-dashboard/', views.merchant_dashboard, name='merchant-dashboard'),
    path('process-payment/', views.process_payment, name='process-payment'),
    path('logout/', views.logout_view, name='logout'),
    path('export-customer/<str:username>/', views.export_customer_profile_excel, name='export_customer_profile_excel'),
    path('mark-as-paid/<int:payment_id>/', views.mark_as_paid, name='mark_as_paid'),
    path('merchant-dashboard/mark-as-paid/', views.mark_as_paid, name='mark_as_paid'),
    path('merchant-dashboard/customers/', views.merchant_customers, name='merchant-customers'),
    path('customer-profile/<str:username>/', views.customer_profile, name='customer-profile'),  # Keep this one
    path('customer-analytics/', views.customer_analytics, name='customer-analytics'),
    path('accept-payment/<int:payment_id>/', views.accept_payment, name='accept_payment'),
    path('reject-payment/<int:payment_id>/', views.reject_payment, name='reject_payment'),
    path('delete-payment/<int:payment_id>/', views.delete_payment, name='delete_payment'),
    path('generate-qr/', views.generate_qr_code, name='generate-qr'),
    path('myqr/', views.my_qr_code, name='my-qr'),
    path("healthz", health_check),
    path('scan-qr/', views.scan_qr, name='scan-qr'),
    path('export-customers-excel/', views.export_customers_excel, name='export-customers-excel'),
    

]
