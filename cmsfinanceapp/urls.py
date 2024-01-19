from django.contrib import admin
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('',views.index,name="index"),#working
    path('sign-in/',views.sign_in,name="sign_in"),#working
    path('show_sign-up/',views.show_sign_up,name="show_sign_up"),#working
    path('show_sign_in/',views.show_sign_in,name="show_sign_in"),#working
    path('sign-up/',views.sign_up,name="sign_up"),#working
    path('sign-out/',views.sign_out,name="sign_out"),#working
    path("forget_password/", views.forget_password, name="forget_password"),
    path("otp_validation/", views.otp_validation, name="otp_validation"),
    path("reset_password/", views.reset_password, name="reset_password"),
    path("table-data/", views.get_table_data, name=""),
    path("upload-file/", views.upload_file, name="upload-file"),
    path("submit_excel/", views.submit_excel, name="submit_excel"),
    path('show_forget_password/',views.show_forget_password,name="show_forget_password"),#working
 
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
