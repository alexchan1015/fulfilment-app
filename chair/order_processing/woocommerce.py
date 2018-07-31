from woocommerce import API
from chair.product_info import PRODUCT_INFO
from chair.models import Order, Customer


def grab_orders_woocommerce():
    wcapi = API(
        url="https://pulselabz.com",
        consumer_key="ck_a14883eff094abe7652196f03533c18b9c05eb0b",
        consumer_secret="cs_47027dbf997bd9f53155f7251ed5b2cab27ac323",
        wp_api=True,
        version="wc/v1"
    )
    orders = wcapi.get("orders?status=processing&per_page=100")
    for order in orders.json():
        load_order_wc(order)


# fill in information needed for an order
def load_order_wc(order_info):
    customer_id = order_info.get('customer')[0].split('/customers/')[1]
    customer = update_customer_info_wc(customer_id, order_info.get('billing'), order_info.get('shipping'))
    for i in range(len(order_info.get('line_items'))):
        item = order_info.get('line_items')[i]
        product_name = item.get('name')
        order, created = Order.objects.get_or_create(
            order_id=order_info.get('order_key'), product_name=product_name)
        if not created:
            order.customer_id = customer
            order.status = "SHIPPING"
            order.quantity = item.get('quantity')
            order.received = order_info.get('date_created')
            order.shipping_type = order_info.get('shipping_lines')[i].get('method_title')
            order.total_price = order_info.get('total')
            order.source = "woocommerce"
            try:
                order.part_number = PRODUCT_INFO.get(product_name)[1]
            except:
                pass
            order.save()


def update_customer_info_wc(customer_id, billing_info, customer_info):
    customer, created = Customer.objects.get_or_create(
        customer_id=customer_id)
    customer.firstname = customer_info.get('first_name')
    customer.lastname = customer_info.get('last_name')
    try:
        customer.country = customer_info.get('country')
        customer.city = customer_info.get('city')
        customer.phone = billing_info.get('phone')
        customer.state = customer_info.get('state')
        customer.street = customer_info.get('address_1')
        customer.zip = customer_info.get('postcode')
    except AttributeError:
        print('could not parse customer {}, {}'.format(
            customer.customer_id, customer_info))
    customer.save()
    return customer
