from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return ['home', 'planner_wizard', 'savings_list',
                'trust_guarantee', 'privacy', 'terms',
                'login', 'register_customer', 'register_vendor']

    def location(self, item):
        return reverse(item)
