from scraper.settings import BESTBUY_KEY
from chair.product_info import PRODUCT_INFO
from chair.models import Order, Customer, OrderStatus

import requests
import json


# date should be in format yyyy-MM-dd
def grab_orders(date=None):
    headers = {'Authorization': BESTBUY_KEY}
    r = requests.get('https://marketplace.bestbuy.ca/api/orders',
                     {"start_date": date, "paginate": False}, headers=headers)
    r_data = json.loads(r.content)
    orders = r_data.get('orders')
    if not orders:
        return 0
    for order in orders:
        # grab necessary fields for newegg stuff and enter them into the db
        load_order(order)
    return len(orders)


# fill in information needed for an order
def load_order(order_info):
    autofulfill = OrderStatus.objects.filter(auto_fulfill=True).values_list('part_number', flat=True)
    customer = update_customer_info(order_info.get('customer'))
    for item in order_info.get('order_lines'):
        product_name = item.get('product_title')
        order, created = Order.objects.get_or_create(
            order_id=order_info.get('order_id'), product_name=product_name)
        order.customer_id = customer
        order.status = order_info.get('order_state')
        if order_info.get('shipping_tracking'):
            order.tracking_id = order_info.get('shipping_tracking')
        order.quantity = item.get('quantity')
        order.received = order_info.get('created_date')
        order.order_line_id = item.get('order_line_id')
        order.shipping_type = order_info.get('shipping_type_label')
        order.total_price = order_info.get('total_price')
        order.bestbuy_commission = order_info.get('total_commission')
        order.source = "bestbuy"
        try:
            order.part_number = PRODUCT_INFO.get(product_name)[1]
        except:
            pass
        order.save()
        if order.status == 'WAITING_ACCEPTANCE' and order.part_number in autofulfill:
            process_order(order, True)


def update_customer_info(customer_info):
    customer, created = Customer.objects.get_or_create(
        customer_id=customer_info.get('customer_id'))
    customer.firstname = customer_info.get('firstname')
    customer.lastname = customer_info.get('lastname')
    try:
        customer.country = customer_info['shipping_address'].get('country')
        customer.city = customer_info['shipping_address'].get('city')
        customer.phone = customer_info['shipping_address'].get('phone')
        customer.state = customer_info['shipping_address'].get('state')
        customer.street = customer_info['shipping_address'].get('street_1')
        if customer_info.get('address_2'):
            customer.street = '{} - {}'.format(customer_info['shipping_address'].get('street_2'), customer_info['shipping_address'].get('street_1'))
        customer.zip = customer_info['shipping_address'].get('zip_code')
    except AttributeError:
        print('could not parse customer {}, {}'.format(
            customer.customer_id, customer_info))
    customer.save()
    return customer


def process_order(order, accept):
    headers = {'Authorization': BESTBUY_KEY, 'Content-Type': 'application/json'}
    data = {
        "order_lines": [{
            "accepted": accept,
            "id": order.order_line_id,
        }]
    }
    r = requests.put('https://marketplace.bestbuy.ca/api/orders/{}/accept'.format(order.order_id),
                     headers=headers, data=json.dumps(data))
    return r


def send_tracking_bestbuy(order):
    headers = {'Authorization': BESTBUY_KEY, 'Content-Type': 'application/json'}
    if order.customer_id.state == 'BC':
        tracking_data = {'carrier_code': 'Other',
                         'carrier_name': 'Pulselabz',
                         'carrier_url': 'https://www.bestbuy.ca/profile/checkorderstatus.aspx',
                         'tracking_number': 'Order coming by Pulselabz Local Delivery within 2 business days.'}
    else:
        tracking_data = {'carrier_code': order.carrier_code,
                         'tracking_number': order.tracking_id}
    r1 = requests.put('https://marketplace.bestbuy.ca/api/orders/{}/tracking'.format(order.order_id),
                      data=json.dumps(tracking_data), headers=headers)
    r2 = requests.put('https://marketplace.bestbuy.ca/api/orders/{}/ship'.format(order.order_id), headers=headers)
    if r1.status_code != 204 or r2.status_code != 204:
        return -1
    return 1
