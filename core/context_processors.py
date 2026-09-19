from django.conf import settings


def site_config(request):
    """Expose non-secret public config (site URL, analytics ID) to all templates."""
    return {
        'SITE_URL': getattr(settings, 'SITE_URL', ''),
        'ANALYTICS_ID': getattr(settings, 'ANALYTICS_ID', ''),
        'SHOPEE_VOUCHER_URL': getattr(settings, 'SHOPEE_VOUCHER_URL', ''),
    }
