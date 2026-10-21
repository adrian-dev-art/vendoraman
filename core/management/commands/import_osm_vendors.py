"""Import vendor seeds from OpenStreetMap (Overpass API) — FREE, no API key.

Source: OpenStreetMap contributors (ODbL licence). Every imported profile
keeps an attribution note and starts as PENDING + not vetted, so an admin
must verify it before it ever appears publicly.

Usage:
    python manage.py import_osm_vendors --city Yogyakarta --dry-run
    python manage.py import_osm_vendors --city Bandung --category wedding
    python manage.py import_osm_vendors --all-cities --dry-run
"""
import json
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from core.models import CustomUser, EventCategory, VendorProfile

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'

CITY_COORDS = {
    # slug-ish name: (display, lat, lon, radius_meters)
    'jakarta': ('Jakarta', -6.2088, 106.8456, 25000),
    'bandung': ('Bandung', -6.9175, 107.6191, 15000),
    'surabaya': ('Surabaya', -7.2575, 112.7521, 15000),
    'yogyakarta': ('Yogyakarta', -7.7956, 110.3695, 12000),
    'semarang': ('Semarang', -6.9667, 110.4167, 12000),
    'bali': ('Bali', -8.6705, 115.2126, 20000),
}

# (osm_key, osm_value_regex) pairs worth importing as event vendors.
TAG_FILTERS = [
    ('craft', 'caterer|photographer'),
    ('shop', 'florist|bridal|party'),
    ('office', 'event_management'),
    ('amenity', 'events_venue'),
]


def build_overpass_query(lat, lon, radius):
    parts = [f'nwr["{k}"~"^({v})$"](around:{radius},{lat},{lon});' for k, v in TAG_FILTERS]
    return '[out:json][timeout:60];(' + ''.join(parts) + ');out center tags;'


def fetch_osm_elements(lat, lon, radius):
    query = build_overpass_query(lat, lon, radius)
    data = urllib.parse.urlencode({'data': query}).encode()
    req = urllib.request.Request(OVERPASS_URL, data=data, method='POST',
                                 headers={'User-Agent': 'Vendoraman/1.0 (vendor seed import)'})
    with urllib.request.urlopen(req, timeout=90) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    return payload.get('elements', [])


def osm_element_to_vendor(element, fallback_city):
    """Pure mapping: OSM element -> vendor dict (None if unusable). No DB here."""
    tags = element.get('tags') or {}
    name = (tags.get('name') or '').strip()
    if not name:
        return None
    city = (tags.get('addr:city') or fallback_city).strip() or fallback_city
    phone = (tags.get('contact:phone') or tags.get('phone') or '').strip()
    website = (tags.get('contact:website') or tags.get('website') or '').strip()
    return {
        'business_name': name,
        'city': city,
        'contact_phone': phone,
        'website': website,
        'description': (
            f"Profil import awal untuk {name} ({city}). "
            f"Belum diklaim & belum diverifikasi — hubungi vendor untuk konfirmasi layanan. "
            f"Sumber data awal: OpenStreetMap contributors (ODbL)."
        ),
    }


def import_city(city_key, category, dry_run):
    city_display, lat, lon, radius = CITY_COORDS[city_key]
    elements = fetch_osm_elements(lat, lon, radius)
    created, skipped_no_name, skipped_dup = 0, 0, []
    for el in elements:
        mapped = osm_element_to_vendor(el, city_display)
        if mapped is None:
            skipped_no_name += 1
            continue
        name, city = mapped['business_name'], mapped['city']
        dupe = VendorProfile.objects.filter(business_name__iexact=name, city__iexact=city).exists()
        if dupe:
            skipped_dup.append(f'{name} ({city})')
            continue
        if dry_run:
            created += 1  # counted as "would create"
            continue
        base = slugify(name)[:30] or 'osm-vendor'
        username = f'osm_{base}'
        i, candidate = 1, username
        while CustomUser.objects.filter(username=candidate).exists():
            i += 1
            candidate = f'{username}-{i}'
        user = CustomUser(username=candidate, email='', role='VENDOR', is_active=False)
        user.set_unusable_password()
        user.save()
        VendorProfile.objects.create(
            user=user,
            business_name=name,
            category=category,
            city=city,
            pic_name='Belum ada PIC (profil import)',
            contact_phone=mapped['contact_phone'][:30],
            contact_email='',
            description=mapped['description'],
            verification_status='PENDING',
            is_vetted=False,
        )
        created += 1
    return {'fetched': len(elements), 'created': created,
            'skipped_no_name': skipped_no_name, 'skipped_dup': skipped_dup}


class Command(BaseCommand):
    help = 'Import vendor seeds from OpenStreetMap (free, no API key) as PENDING profiles.'

    def add_arguments(self, parser):
        parser.add_argument('--city', default='yogyakarta',
                            help=f"City key. Choices: {', '.join(CITY_COORDS)}")
        parser.add_argument('--all-cities', action='store_true')
        parser.add_argument('--category', default='wedding',
                            help='EventCategory slug to assign (admin can reassign later)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Fetch + report only, save nothing')

    def handle(self, *args, **opts):
        try:
            category = EventCategory.objects.get(slug=opts['category'])
        except EventCategory.DoesNotExist:
            raise CommandError(f"EventCategory slug '{opts['category']}' not found.")
        cities = list(CITY_COORDS) if opts['all_cities'] else [opts['city'].lower()]
        for c in cities:
            if c not in CITY_COORDS:
                raise CommandError(f"Unknown city '{c}'. Choices: {', '.join(CITY_COORDS)}")
        for c in cities:
            self.stdout.write(f'--- {CITY_COORDS[c][0]} ---')
            try:
                res = import_city(c, category, dry_run=opts['dry_run'])
            except Exception as exc:  # network etc: report, continue other cities
                self.stderr.write(f'  FAILED: {exc}')
                continue
            mode = 'DRY-RUN would create' if opts['dry_run'] else 'Created'
            self.stdout.write(f"  fetched={res['fetched']} {mode}={res['created']} "
                              f"no_name={res['skipped_no_name']} dupes={len(res['skipped_dup'])}")
            for d in res['skipped_dup'][:10]:
                self.stdout.write(f'    dupe: {d}')
        self.stdout.write(self.style.SUCCESS('Done. Imported profiles are PENDING — verify in Django Admin.'))
