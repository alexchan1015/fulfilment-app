"""scraper URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf.urls import url
from django.views.generic import RedirectView

from chair.views import *

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='dashboard/', permanent=False)),
    url(r'^dashboard/$', dashboard, name='dashboard'),
    url(r'^orders/grab_latest/$', grab_latest_orders, name='grab_latest_orders'),
    url(r'^orders/mark_fulfilled/(?P<order_id>[-_a-zA-Z0-9]+)/$', mark_fulfilled, name='mark_fulfilled'),
    url(r'^orders/walmart_refund/$', walmart_refund, name='walmart_refund'),
    url(r'^orders/accept/(?P<order_id>[-_a-zA-Z0-9]+)/$',
        accept_order, name='accept_order'),
    url(r'^orders/reject/(?P<order_id>[-_a-zA-Z0-9]+)/$',
        reject_order, name='reject_order'),
    url(r'^orders/newegg_fulfill/(?P<order_id>[-_a-zA-Z0-9]+)/$',
        newegg_fulfill, name='newegg_fulfill'),
    url(r'^orders/get_report/$', get_newegg_report, name='get_newegg_report'),
    url(r'^orders/parse_report/(?P<report_id>[-_a-zA-Z0-9]+)/$',
        process_report, name='process_report'),
    url(r'^orders/update_tracking/(?P<order_id>[-_a-zA-Z0-9]+)/$',
        update_tracking, name='update_tracking'),
    url(r'^orders/upload/(?P<order_id>[-_a-zA-Z0-9]+)/(?P<sheets_key>[-_a-zA-Z0-9]+)$', post_gsheets, name='post_gsheets'),
    url(r'^orders/fulfill/(?P<product_name>[-_a-zA-Z0-9]+)/off$', disable_autofill, name='disable_autofill'),
    url(r'^orders/fulfill/(?P<product_name>[-_a-zA-Z0-9]+)/on$', enable_autofill, name='enable_autofill'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
]
