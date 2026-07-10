from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q

from chair.models import Order, OrderStatus, Report
from chair.order_processing.bestbuy import grab_orders, process_order, send_tracking_bestbuy
from chair.order_processing.newegg import newegg_ship, get_report, parse_report
from chair.order_processing.google_sheets_upload import post_order_info
from chair.order_processing.woocommerce import grab_orders_woocommerce
from chair.order_processing.walmart import (
    REFUND_REASONS,
    WalmartApiError,
    get_walmart_order,
    is_wfs_order,
    push_walmart_refund,
    refundable_summary,
)
import datetime


# workflow: load bestbuy orders from last date, grab unshipped orders, display.
# have option to fulfill order - user clicks fulfill = send newegg shipment -> returns newegg_feed
# have to parse newegg_feed to get tracking_id -> update tracking_id on bestbuy side
@login_required()
def dashboard(request):
    # date = (datetime.date.today() -
    #         datetime.timedelta(weeks=4)).strftime('%Y-%m-%d')
    # grab_orders(date)
    # grab_orders_woocommerce()
    completed = Order.objects.filter(
        Q(status='RECEIVED') | Q(status='CANCELLED') | Q(status='REFUSED') | Q(status='CLOSED') | Q(uploaded=True)).order_by('-received')[:50]
    pending = Order.objects.filter(
        (Q(status='WAITING_ACCEPTANCE') | Q(status='WAITING_DEBIT_PAYMENT') | Q(status='SHIPPING') | Q(status='SHIPPED')) & Q(uploaded=False)).order_by('-received')
    list_of_products = OrderStatus.objects.all()
    reports = Report.objects.filter(processed=False)
    # print(pending)
    return render(request, "dashboard/dashboard.html", context={'completed': completed, 'pending': pending,
                                                                'reports': reversed(reports), 'completed_len': len(completed),
                                                                'list_of_products': list_of_products})


@login_required()
def grab_latest_orders(request):
    settings = OrderStatus.objects.first()
    date = (datetime.date.today() -
            datetime.timedelta(weeks=4)).strftime('%Y-%m-%d')
    updated = grab_orders(date)
    grab_orders_woocommerce()
    settings.last_update = datetime.date.today().strftime('%Y-%m-%d')
    settings.save()
    if updated > 0:
        return JsonResponse({'status': 'success', 'message': 'orders have been updated'})
    return JsonResponse({'status': 'failure', 'message': 'no new orders'})


@login_required()
def newegg_fulfill(request, order_id):
    order = Order.objects.filter(order_id=order_id)
    for o in order:
        newegg_ship(o)
    order.update(newegg_shipped=True)
    return JsonResponse(
        {'status': 'success', 'message': 'shipment for order {} has been created'.format(order_id)})


@login_required()
def accept_order(request, order_id):
    order = Order.objects.get(order_id=order_id)
    r = process_order(order, True)
    if not r.status_code == 204:
        return JsonResponse({'status': 'error', 'message': 'error in accepting order {}'.format(order_id)})
    # sync db with orders
    # date = (datetime.date.today() - datetime.timedelta(weeks=4)).strftime('%Y-%m-%d')
    # grab_orders(date)
    order = Order.objects.filter(order_id=order_id)
    order.update(status='WAITING_DEBIT_PAYMENT')
    return JsonResponse({'status': 'success', 'message': 'order {} has been accepted'.format(order_id)})


@login_required()
def reject_order(request, order_id):
    order = Order.objects.get(order_id=order_id)
    r = process_order(order, False)
    if not r.status_code == 204:
        return JsonResponse({'status': 'error', 'message': 'error in accepting order {}'.format(order_id)})
    # date = (datetime.date.today() - datetime.timedelta(weeks=4)).strftime('%Y-%m-%d')
    # sync db with orders
    # grab_orders(date)
    order = Order.objects.filter(order_id=order_id)
    order.update(status='REFUSED')
    return JsonResponse({'status': 'success', 'message': 'order {} has been rejected'.format(order_id)})


# update tracking information for an order - can't call this before shipping the order via newegg
# and parsing the tracking_id from the newegg feed
@login_required()
def update_tracking(request, order_id):
    local = request.GET.get('local')
    order = Order.objects.get(order_id=order_id)
    send_tracking_bestbuy(order, local)
    order.bestbuy_filled = True
    order.save()
    return JsonResponse({'status': 'success', 'message': 'tracking number for order {} has been updated'.format(order_id)})


@login_required()
def get_newegg_report(request):
    report_id = get_report(0)
    report, _ = Report.objects.get_or_create(request_id=report_id)
    report_id = get_report(2)
    report, _ = Report.objects.get_or_create(request_id=report_id)
    return JsonResponse({'status': 'success', 'message': 'Report successfully requested'})


@login_required()
def process_report(request, report_id):
    parsed = parse_report(report_id)
    if parsed > 0:
        return JsonResponse({'status': 'success', 'message': 'Report {} successfully parsed'.format(report_id)})
    elif parsed < 0:
        return JsonResponse({'status': 'error', 'message': 'Empty report, try requesting another'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Report {} did not contain the necessary info at this time, try again later'.format(report_id)})


@login_required()
def post_gsheets(request, order_id, sheets_key):
    try:
        post_order_info(order_id, sheets_key)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'Error in uploading order {} with error {}'.format(order_id, e)})
    order = Order.objects.get(order_id=order_id)
    order.uploaded = True
    order.save()
    return JsonResponse({'status': 'success', 'message': 'Order {} uploaded'.format(order_id)})


@login_required()
def enable_autofill(request, product_name):
    product = OrderStatus.objects.get(part_number=product_name)
    product.auto_fulfill = True
    product.save()
    return JsonResponse({'status': 'success', 'message': 'Autofulfil updated for {}'.format(product_name)})


@login_required()
def disable_autofill(request, product_name):
    product = OrderStatus.objects.get(part_number=product_name)
    product.auto_fulfill = False
    product.save()
    return JsonResponse({'status': 'success', 'message': 'Autofulfil updated for {}'.format(product_name)})


@login_required()
def mark_fulfilled(request, order_id):
    try:
        order = Order.objects.get(order_id=order_id)
        order.bestbuy_filled = True
        order.status = 'SHIPPED'
        order.save()
        return JsonResponse({'status': 'success', 'message': 'Order {} marked as fulfilled'.format(order_id)})
    except:
        return JsonResponse({'status': 'failure', 'message': 'Order {} does not exist'.format(order_id)})


@login_required()
def walmart_refund(request):
    context = {
        'reasons': REFUND_REASONS,
        'component': 'both',
        'reason': 'CustomerReturn',
        'allow_wfs': False,
    }
    if request.method == 'GET' and request.GET.get('purchase_order_id'):
        purchase_order_id = request.GET.get('purchase_order_id').strip()
        component = request.GET.get('component') or 'both'
        context.update({'purchase_order_id': purchase_order_id, 'component': component})
        try:
            order = get_walmart_order(purchase_order_id)
            context.update({
                'order': order,
                'summary': refundable_summary(order, component=component),
                'is_wfs': is_wfs_order(order),
            })
        except WalmartApiError as e:
            context['error'] = str(e)
        return render(request, 'dashboard/walmart_refund.html', context=context)

    if request.method == 'POST':
        purchase_order_id = (request.POST.get('purchase_order_id') or '').strip()
        amount = (request.POST.get('amount') or '').strip()
        component = request.POST.get('component') or 'both'
        reason = request.POST.get('reason') or 'CustomerReturn'
        allow_wfs = request.POST.get('allow_wfs') == 'on'
        confirmed = request.POST.get('confirm') == 'on'
        context.update({
            'purchase_order_id': purchase_order_id,
            'amount': amount,
            'component': component,
            'reason': reason,
            'allow_wfs': allow_wfs,
        })
        if not confirmed:
            context['error'] = 'Confirm the refund before submitting.'
        elif not purchase_order_id or not amount:
            context['error'] = 'Purchase order ID and amount are required.'
        else:
            try:
                result = push_walmart_refund(
                    purchase_order_id,
                    amount,
                    component=component,
                    reason=reason,
                    allow_wfs=allow_wfs,
                )
                context.update({
                    'success': True,
                    'order': result['order'],
                    'refund_id': result.get('refund_id'),
                    'response': result.get('response'),
                    'summary': refundable_summary(result['order'], component=component),
                    'is_wfs': is_wfs_order(result['order']),
                })
            except WalmartApiError as e:
                context['error'] = str(e)
        return render(request, 'dashboard/walmart_refund.html', context=context)

    return render(request, 'dashboard/walmart_refund.html', context=context)
