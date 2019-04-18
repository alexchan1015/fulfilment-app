from django.core.management.base import BaseCommand
from chair.order_processing.newegg import parse_report, get_report
from chair.models import Report, Order


class Command(BaseCommand):
    def handle(self, *app_labels, **options):
        Report.objects.filter(processed=1).delete()
        reports = Report.objects.filter(processed=0)
        for report in reports:
            try:
                parse_report(report.request_id)
            except:
                continue
        needs_report = Order.objects.filter(newegg_shipped=True, has_report=False).exclude(status='RECEIVED')
        if needs_report.count() > 0:
            request_id = get_report(0)
            if 'error' not in request_id:
                Report.objects.create(request_id=request_id, processed=0)
