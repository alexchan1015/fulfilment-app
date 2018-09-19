from scraper.settings import NEWEGG_AUTH, NEWEGG_KEY
import requests
import json
import datetime
from chair.models import Order, Report
from chair.order_processing.emails import send_customer_email
from chair.order_processing.bestbuy import send_tracking_bestbuy

SELLER_ID = 'AFG1'


def newegg_ship(order):
    newegg_json = get_newegg_order(order)
    headers = {'Authorization': NEWEGG_AUTH, 'SecretKey': NEWEGG_KEY,
               'Content-Type': 'application/json', 'Accept': 'application/json'}
    r = requests.post('https://api.newegg.com/marketplace/can/datafeedmgmt/feeds/submitfeed?sellerid={}&requesttype=MultiChannel_Order_DATA'.format(SELLER_ID),
                      headers=headers, data=json.dumps(newegg_json))
    try:
        feed_id = json.loads(r.content)['ResponseBody']['ResponseList'][0]['RequestId']
        order.newegg_feed = feed_id
        order.newegg_shipped = True
        order.save()
    except:
        return {'error': 'shipping failed for order {}'.format(order.order_id)}
    return {'success': 'shipping succeeded for order {}'.format(order.order_id)}


# can have multiple objects in this data feed, should probably iterate through them
def get_newegg_tracking_id(newegg_feed):
    headers = {'Authorization': NEWEGG_AUTH, 'SecretKey': NEWEGG_KEY,
               'Content-Type': 'application/json', 'Accept': 'application/json'}
    r = requests.get('https://api.newegg.com/marketplace/can/datafeedmgmt/feeds/result/{}?sellerid={}'
                     .format(newegg_feed, SELLER_ID), headers=headers)
    try:
        results = json.loads(r.content)['NeweggEnvelope']['Message']['ProcessingReport']['Result']
        for res in results:
            if res.get('AdditionalInfo') and res['AdditionalInfo'].get('TrackingNumber'):
                return res['AdditionalInfo'].get('TrackingNumber')
    except:
        return 'error in parsing feed {}'.format(newegg_feed)


def get_newegg_order(order):
    customer = order.customer_id
    today = datetime.date.today().strftime('%m/%d/%Y')
    channel = "PulseLabz"
    shipping = get_shipping_type(order)
    newegg = {
        "NeweggEnvelope": {
            "Header": {"DocumentVersion": "1.0"},
            "MessageType": "MultiChannelOrderCreation",
            "Message": {
                "MultiChannelOrder": {
                    "Order": {
                        "OrderDate": today,
                        "SalesChannel": channel,
                        "SellerOrderID": order.order_id,
                        "ShippingMethod": shipping,
                        "ShipToFirstName": customer.firstname,
                        "ShipToLastName": customer.lastname,
                        "ShipToAddressLine1": customer.street,
                        "ShipToCity": customer.city,
                        "ShipToState": customer.state,
                        "ShipToPostalCode": customer.zip,
                        "ShipToCountry": customer.country,
                        "ShipToPhoneNumber": customer.phone,
                        "ItemList": {
                            "Item": [{"SellerPartNumber": order.part_number,
                                      "Quantity": order.quantity}]
                        }
                    }
                }
            }
        }
    }
    return newegg


def get_shipping_type(order):
    if order.customer_id.country == 'Canada' or order.source == 'woocommerce':
        if 'Express' in order.shipping_type or 'Expedited' in order.shipping_type:
            shipping = "CAN Express (2-5 Business Days)"
        else:
            shipping = "CAN Ground (2-7 Business Days)"
    else:
        if 'Express' in order.shipping_type or 'Expedited' in order.shipping_type:
            shipping = "Expedited Shipping (3-5 Business Days)"
        else:
            shipping = "Standard Shipping (2-7 Business Days)"
    return shipping


# request report to get shipping id
# type should be 0 for unshipped reports (initial) or 2 for shipped reports (notice somethings wrong)
def get_report(type):
    headers = {'Authorization': NEWEGG_AUTH, 'SecretKey': NEWEGG_KEY,
               'Content-Type': 'application/json', 'Accept': 'application/json'}
    data = {
        "OperationType": "OrderListReportRequest",
        "RequestBody": {
            "OrderReportCriteria": {
                "RequestType": "ORDER_LIST_REPORT",
                "KeywordsType": "0",
                "Status": str(type),
                "Type": "0",
            }
        }
    }
    r = requests.post('https://api.newegg.com/marketplace/can/reportmgmt/report/submitrequest?sellerid=AFG1',
                      data=json.dumps(data), headers=headers)
    try:
        request_id = json.loads(r.content)['ResponseBody']['ResponseList'][0]['RequestId']
    except:
        return 'error in requesting report'
    return request_id


def parse_report(report_id):
    report = Report.objects.get(request_id=report_id)
    headers = {'Authorization': NEWEGG_AUTH, 'SecretKey': NEWEGG_KEY,
               'Content-Type': 'application/json', 'Accept': 'application/json'}
    data = {
        "OperationType": "OrderListReportRequest",
        "RequestBody": {
            "RequestID": report_id,
            "PageInfo": {
                "PageSize": "10",
                "PageIndex": "1"
            }
        }
    }
    r = requests.put('https://api.newegg.com/marketplace/can/reportmgmt/report/result?sellerid=AFG1&version=305',
                     headers=headers, data=json.dumps(data))
    if r.status_code == 400 or not int(json.loads(r.content)['ResponseBody']['PageInfo']['TotalCount']):
        report.processed = True
        report.save()
        return -1
    any_left_unparsed = False
    orders = json.loads(r.content)['ResponseBody']['OrderInfoList']
    for order in orders:
        try:
            cur_order, _ = Order.objects.get_or_create(order_id=order['SellerOrderNumber'])
            cur_order.has_report = True
            cur_order.save()
            needs_email = True if not cur_order.tracking_id else False
            tracking_id = order['PackageInfoList'][0]['TrackingNumber']
            # carrier = order['PackageInfoList'][0]['ShipCarrier']
            carrier = 'PRLA' if 'BVF' in tracking_id else 'CPCL'
            cur_order.carrier_code = carrier
            cur_order.tracking_id = tracking_id
            cur_order.save()
            if cur_order.source == 'bestbuy':
                processed = send_tracking_bestbuy(cur_order, False)
                if processed > 0:
                    cur_order.bestbuy_filled = True
                    cur_order.save()
            try:
                if needs_email and order.customer_id.email:
                    send_customer_email(order.customer_id.email, tracking_id, order.carrier_code)
            except:
                continue
        except:
            any_left_unparsed = True
    if not any_left_unparsed:
        report.processed = True
        report.save()
        return 1
    return 0
