from django.urls import path
from .views import *  # Import all your views from your app
# Or you can import only what you need:
# from .views import voter_id_view, otp_view, voter_info, parties_view, receipt_view, receipt_pdf, resend_otp, results_view, logout_view, profile_view, profile_edit_view, change_password_view, election_page, voting_booth
from . import views
urlpatterns = [
    path('', voter_id_view, name='home'),
    path('about/', about_view, name='about'),
    path('otp/', otp_view, name='otp'),
    path('info/', voter_info, name='voter-info'),
    path('parties/', parties_view, name='parties'),
    path('receipt/', receipt_view, name='receipt'),
    path('receipt/pdf/', receipt_pdf, name='receipt-pdf'),
    path('resend-otp/', resend_otp, name='resend-otp'),
    path('results/', results_view, name='results-api'),
    path('logout/', logout_view, name='logout'),
    # path('login/', views.voter_login, name='voter_login'), 
    path('login/', views.voter_id_view, name='voter_id'),
    path('verify-otp/', views.otp_view, name='verify_otp'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('profile/change-password/', change_password_view, name='change_password'),
    path('election/', election_page, name='election'),        # ✅ Use app view, not django.views
    path('voting-booth/', voting_booth, name='voting_booth'), # ✅ Use app view, not django.views
]

