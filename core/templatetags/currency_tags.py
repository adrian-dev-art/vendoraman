from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name='intdot')
def intdot(value):
    """
    Formats a numeric value using a period (.) as the thousands separator.
    Examples:
        100000 -> "100.000"
        4500000 -> "4.500.000"
        120000000 -> "120.000.000"
    """
    if value is None or value == '':
        return ''
    try:
        if isinstance(value, str):
            value = value.strip().replace(',', '')
        num = int(round(float(value)))
        return f"{num:,}".replace(',', '.')
    except (ValueError, TypeError):
        return value


@register.filter(name='rupiah')
def rupiah(value):
    """
    Formats a numeric value as Indonesian Rupiah with period thousands separator:
    Example:
        100000 -> "Rp 100.000"
        4500000 -> "Rp 4.500.000"
    """
    if value is None or value == '':
        return ''
    return f"Rp {intdot(value)}"
