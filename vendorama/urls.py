from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from core.views_home import home_view, trust_guarantee_view
from core.views_auth import login_view, register_customer_view, register_vendor_view, logout_view
from core.views_planner import (
    planner_wizard_view, planner_results_view, unlock_planner_view, vendor_detail_view
)
from core.views_savings import savings_list_view, savings_detail_view
from core.views_escrow import (
    escrow_checkout_view, order_detail_view,
    request_milestone_payout_view, approve_milestone_payout_view
)
from core.views_dispute import file_dispute_view
from core.views_dashboard import customer_dashboard_view, vendor_dashboard_view
from core.views_admin import (
    admin_dashboard_view, admin_dispute_detail_view, admin_verify_vendor_view
)

urlpatterns = [
    # General / Public
    path('', home_view, name='home'),
    path('trust-guarantee/', trust_guarantee_view, name='trust_guarantee'),

    # Authentication
    path('login/', login_view, name='login'),
    path('register/customer/', register_customer_view, name='register_customer'),
    path('register/vendor/', register_vendor_view, name='register_vendor'),
    path('logout/', logout_view, name='logout'),

    # Event Planner & Vendor Discovery (Free vs Paid Planner)
    path('wizard/', planner_wizard_view, name='planner_wizard'),
    path('planner/<int:plan_id>/', planner_results_view, name='planner_results'),
    path('planner/<int:plan_id>/unlock/', unlock_planner_view, name='unlock_planner'),
    path('planner/<int:plan_id>/vendor/<int:vendor_id>/', vendor_detail_view, name='vendor_detail'),

    # Event Savings Vault
    path('savings/', savings_list_view, name='savings_list'),
    path('savings/<int:vault_id>/', savings_detail_view, name='savings_detail'),

    # Escrow Booking & Milestone Payouts
    path('escrow/checkout/', escrow_checkout_view, name='escrow_checkout'),
    path('escrow/order/<int:order_id>/', order_detail_view, name='order_detail'),
    path('escrow/order/<int:order_id>/milestone/<int:milestone_id>/request/', request_milestone_payout_view, name='request_milestone_payout'),
    path('escrow/order/<int:order_id>/milestone/<int:milestone_id>/approve/', approve_milestone_payout_view, name='approve_milestone_payout'),

    # Disputes & Financial Guarantee
    path('escrow/order/<int:order_id>/dispute/', file_dispute_view, name='file_dispute'),

    # Role Dashboards
    path('dashboard/customer/', customer_dashboard_view, name='customer_dashboard'),
    path('dashboard/vendor/', vendor_dashboard_view, name='vendor_dashboard'),
    path('dashboard/admin/', admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/admin/dispute/<int:dispute_id>/', admin_dispute_detail_view, name='admin_dispute_detail'),
    path('dashboard/admin/vendor/<int:vendor_id>/<str:action>/', admin_verify_vendor_view, name='admin_verify_vendor'),

    # Django Admin
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
