from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from core.sitemaps import StaticViewSitemap
from core.views_home import home_view, trust_guarantee_view, privacy_policy_view, terms_view, robots_txt_view, free_template_view, free_template_download_view, paid_template_view, paid_template_download_view
from core.views_templates import (
    excel_templates_catalog_view, excel_template_category_view, excel_template_download_action
)
from core.views_auth import login_view, register_customer_view, register_vendor_view, logout_view
from core.views_planner import (
    planner_wizard_view, planner_results_view, unlock_planner_view, vendor_detail_view,
    export_planner_excel_view, export_planner_pdf_view, planner_deck_view
)
from core.views_savings import savings_list_view, savings_detail_view
from core.views_booking import (
    booking_checkout_view, order_detail_view, update_order_status_view
)
from core.views_dashboard import customer_dashboard_view, vendor_dashboard_view
from core.views_admin import (
    admin_dashboard_view, admin_verify_vendor_view
)

urlpatterns = [
    # General / Public
    path('', home_view, name='home'),
    path('trust-guarantee/', trust_guarantee_view, name='trust_guarantee'),
    path('kebijakan-privasi/', privacy_policy_view, name='privacy'),
    path('syarat-ketentuan/', terms_view, name='terms'),
    path('robots.txt', robots_txt_view, name='robots'),
    path('sitemap.xml', sitemap, {'sitemaps': {'static': StaticViewSitemap}}, name='sitemap'),
    # Public Excel Category Templates & Unique Code Download (Without Login)
    path('templates/', excel_templates_catalog_view, name='excel_templates_catalog'),
    path('templates/<slug:category_slug>/', excel_template_category_view, name='excel_template_category'),
    path('templates/<slug:category_slug>/unduh/', excel_template_download_action, name='excel_template_download'),
    # Hidden free-template page (NOT linked in nav/footer/sitemap; admin-gated)
    path('template-gratis/', free_template_view, name='free_template'),
    path('template-gratis/unduh/', free_template_download_view, name='free_template_download'),
    # Paid template: login + premium voucher, pick exactly ONE category (hidden too)
    path('template-premium/', paid_template_view, name='paid_template'),
    path('template-premium/unduh/', paid_template_download_view, name='paid_template_download'),

    # Authentication
    path('login/', login_view, name='login'),
    path('register/customer/', register_customer_view, name='register_customer'),
    path('register/vendor/', register_vendor_view, name='register_vendor'),
    path('logout/', logout_view, name='logout'),

    # Event Planner & Vendor Discovery
    path('wizard/', planner_wizard_view, name='planner_wizard'),
    path('planner/<int:plan_id>/', planner_results_view, name='planner_results'),
    path('planner/<int:plan_id>/unlock/', unlock_planner_view, name='unlock_planner'),
    path('planner/<int:plan_id>/vendor/<int:vendor_id>/', vendor_detail_view, name='vendor_detail'),
    path('planner/<int:plan_id>/export/excel/', export_planner_excel_view, name='export_planner_excel'),
    path('planner/<int:plan_id>/export/pdf/', export_planner_pdf_view, name='export_planner_pdf'),
    path('planner/<int:plan_id>/deck/', planner_deck_view, name='planner_deck'),

    # Event Savings Vault
    path('savings/', savings_list_view, name='savings_list'),
    path('savings/<int:vault_id>/', savings_detail_view, name='savings_detail'),

    # Direct Booking & Commission-based Orders
    path('booking/checkout/', booking_checkout_view, name='booking_checkout'),
    path('booking/order/<int:order_id>/', order_detail_view, name='order_detail'),
    path('booking/order/<int:order_id>/status/', update_order_status_view, name='update_order_status'),

    # Backward compatibility aliases for existing templates/links
    path('escrow/checkout/', booking_checkout_view, name='escrow_checkout'),

    # Role Dashboards
    path('dashboard/customer/', customer_dashboard_view, name='customer_dashboard'),
    path('dashboard/vendor/', vendor_dashboard_view, name='vendor_dashboard'),
    path('dashboard/admin/', admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/admin/vendor/<int:vendor_id>/<str:action>/', admin_verify_vendor_view, name='admin_verify_vendor'),

    # Django Admin
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
