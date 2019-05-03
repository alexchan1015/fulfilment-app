from django.core.management.base import BaseCommand
from chair.order_processing.bestbuy import grab_orders, process_order
from chair.order_processing.woocommerce import grab_orders_woocommerce
from chair.models import Order, OrderStatus, Report
import datetime


class Command(BaseCommand):
    def handle(self, *app_labels, **options):
        date = (datetime.date.today() -
                datetime.timedelta(days=10)).strftime('%Y-%m-%d')
        grab_orders(date)
        grab_orders_woocommerce()
        old_reports = Report.objects.all().order_by('-id')[:10]
        Report.objects.all().exclude(request_id__in=old_reports.values_list('request_id', flat=True)).delete()
        autofulfill = OrderStatus.objects.filter(auto_fulfill=True).values_list('part_number', flat=True)
        for order in Order.objects.filter(status='WAITING_ACCEPTANCE'):
            if order.part_number in autofulfill and order.source == 'bestbuy':
                process_order(order, True)
