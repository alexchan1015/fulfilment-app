import base64
import uuid
from decimal import Decimal, ROUND_HALF_UP

import requests
from django.conf import settings


DEFAULT_API_URL = 'https://marketplace.walmartapis.com'
DEFAULT_MARKET = 'ca'
DEFAULT_REASON = 'CustomerReturn'

REFUND_REASONS = [
    ('BillingError', 'Billing Error'),
    ('TaxExemptCustomer', 'Tax Exempt Customer'),
    ('ItemNotAsAdvertised', 'Item Not As Advertised'),
    ('IncorrectItemReceived', 'Incorrect Item Received'),
    ('CancelledYetShipped', 'Cancelled Yet Shipped'),
    ('ItemNotReceivedByCustomer', 'Item Not Received By Customer'),
    ('IncorrectShippingPrice', 'Incorrect Shipping Price'),
    (DEFAULT_REASON, 'Customer Return'),
]


class WalmartApiError(Exception):
    pass


def _money(value):
    if value is None or value == '':
        return Decimal('0.00')
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _as_cents(value):
    return int((_money(value) * 100).to_integral_value(rounding=ROUND_HALF_UP))


def _from_cents(value):
    return (Decimal(int(value)) / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _config():
    client_id = getattr(settings, 'WALMART_CLIENT_ID', None)
    client_secret = getattr(settings, 'WALMART_CLIENT_SECRET', None)
    if not client_id or not client_secret:
        raise WalmartApiError('Walmart API credentials are not configured')
    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'market': getattr(settings, 'WALMART_MARKET', None) or DEFAULT_MARKET,
        'base_url': (getattr(settings, 'WALMART_API_URL', None) or DEFAULT_API_URL).rstrip('/'),
        'channel_type': getattr(settings, 'WALMART_CHANNEL_TYPE', None),
        'partner_id': getattr(settings, 'WALMART_PARTNER_ID', None),
    }


def _token(config):
    raw = '{}:{}'.format(config['client_id'], config['client_secret']).encode('utf-8')
    auth = base64.b64encode(raw).decode('ascii')
    headers = {
        'Authorization': 'Basic {}'.format(auth),
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'WM_MARKET': config['market'],
        'WM_QOS.CORRELATION_ID': str(uuid.uuid4()),
        'WM_SVC.NAME': 'Walmart Marketplace',
    }
    r = requests.post('{}/v3/token'.format(config['base_url']), headers=headers, data={'grant_type': 'client_credentials'}, timeout=30)
    if r.status_code >= 400:
        raise WalmartApiError('Walmart token request failed: {} {}'.format(r.status_code, r.text[:250]))
    data = r.json()
    access_token = data.get('access_token')
    if not access_token:
        raise WalmartApiError('Walmart token response did not include an access token')
    return access_token


def _headers(config, token):
    headers = {
        'WM_SEC.ACCESS_TOKEN': token,
        'WM_MARKET': config['market'],
        'WM_QOS.CORRELATION_ID': str(uuid.uuid4()),
        'WM_SVC.NAME': 'Walmart Marketplace',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    if config.get('channel_type'):
        headers['WM_CONSUMER.CHANNEL.TYPE'] = config['channel_type']
    if config.get('partner_id'):
        headers['WM_PARTNER.ID'] = config['partner_id']
    return headers


def _walmart_request(method, path, json_body=None):
    config = _config()
    token = _token(config)
    url = '{}/v3/{}'.format(config['base_url'], path.lstrip('/'))
    r = requests.request(method, url, headers=_headers(config, token), json=json_body, timeout=45)
    if r.status_code >= 400:
        raise WalmartApiError('Walmart {} {} failed: {} {}'.format(method, path, r.status_code, r.text[:500]))
    if not r.text:
        return {}
    return r.json()


def _order_from_response(data):
    if data.get('order'):
        return data['order']
    try:
        return data['list']['elements']['order'][0]
    except (KeyError, IndexError, TypeError):
        return None


def get_walmart_order(purchase_order_id):
    data = _walmart_request('GET', 'orders/{}'.format(purchase_order_id))
    order = _order_from_response(data)
    if not order:
        raise WalmartApiError('No Walmart order matching {}'.format(purchase_order_id))
    return order


def _charge_component(charge):
    raw = '{} {}'.format(charge.get('chargeType', ''), charge.get('chargeName', '')).lower()
    if 'ship' in raw or 'delivery' in raw or 'freight' in raw:
        return 'shipping'
    return 'product'


def _line_charges(line, component):
    charges = ((line.get('charges') or {}).get('charge') or [])
    if component == 'both':
        return charges
    return [c for c in charges if _charge_component(c) == component]


def refundable_summary(order, component='both'):
    lines = ((order.get('orderLines') or {}).get('orderLine') or [])
    product = Decimal('0.00')
    shipping = Decimal('0.00')
    tax = Decimal('0.00')
    for line in lines:
        for charge in ((line.get('charges') or {}).get('charge') or []):
            amount = _money(((charge.get('chargeAmount') or {}).get('amount')))
            if _charge_component(charge) == 'shipping':
                shipping += amount
            else:
                product += amount
            tax += _money((((charge.get('tax') or {}).get('taxAmount') or {}).get('amount')))
    selected = product + shipping if component == 'both' else (shipping if component == 'shipping' else product)
    return {
        'product': product,
        'shipping': shipping,
        'tax': tax,
        'selected_before_tax': selected,
        'gross': product + shipping + tax,
    }


def _refund_charge_payload(charge, ratio, reason):
    amount = (_money(((charge.get('chargeAmount') or {}).get('amount'))) * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if amount <= 0:
        return None
    currency = ((charge.get('chargeAmount') or {}).get('currency')) or 'CAD'
    tax_amount = (_money((((charge.get('tax') or {}).get('taxAmount') or {}).get('amount'))) * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    payload = {
        'refundReason': reason,
        'charge': {
            'chargeType': charge.get('chargeType') or 'PRODUCT',
            'chargeName': charge.get('chargeName') or ('Shipping' if _charge_component(charge) == 'shipping' else 'Item Price'),
            'chargeAmount': {'currency': currency, 'amount': float(amount)},
        },
    }
    if tax_amount > 0:
        payload['charge']['tax'] = {
            'taxName': ((charge.get('tax') or {}).get('taxName')) or 'Tax',
            'taxAmount': {'currency': (((charge.get('tax') or {}).get('taxAmount') or {}).get('currency')) or currency, 'amount': float(tax_amount)},
        }
    return payload


def build_refund_payload(order, amount_cents, component='both', reason=DEFAULT_REASON):
    if amount_cents <= 0:
        raise WalmartApiError('Refund amount must be greater than zero')
    lines = ((order.get('orderLines') or {}).get('orderLine') or [])
    selected = []
    order_amount = Decimal('0.00')
    for line in lines:
        charges = _line_charges(line, component)
        basis = sum([_money(((c.get('chargeAmount') or {}).get('amount'))) for c in charges], Decimal('0.00'))
        selected.append((line, charges, basis))
        order_amount += basis
    if order_amount <= 0:
        raise WalmartApiError('Walmart order has no refundable amount for the selected type')
    ratio = min(Decimal('1'), _from_cents(amount_cents) / order_amount)
    order_lines = []
    for line, charges, basis in selected:
        refund_charges = [_refund_charge_payload(c, ratio, reason) for c in charges]
        refund_charges = [c for c in refund_charges if c]
        if not line.get('lineNumber') or not refund_charges:
            continue
        order_lines.append({
            'lineNumber': line.get('lineNumber'),
            'refunds': {
                'refund': [{
                    'refundType': 'Refund',
                    'refundComments': 'Refund issued from MotionApp',
                    'refundCharges': {'refundCharge': refund_charges},
                }],
            },
        })
    if not order_lines:
        raise WalmartApiError('Requested Walmart refund amount was too small to allocate')
    return {
        'orderRefund': {
            'purchaseOrderId': order.get('purchaseOrderId'),
            'orderLines': {'orderLine': order_lines},
        },
    }


def is_wfs_order(order):
    lines = ((order.get('orderLines') or {}).get('orderLine') or [])
    for line in lines:
        if str(line.get('shipNodeType') or '').lower() == 'wfsfulfilled':
            return True
    return False


def push_walmart_refund(purchase_order_id, amount, component='both', reason=DEFAULT_REASON, allow_wfs=False):
    order = get_walmart_order(purchase_order_id)
    if is_wfs_order(order) and not allow_wfs:
        raise WalmartApiError('This appears to be a WFS/Walmart-fulfilled order. Refund from Seller Center unless explicitly approved.')
    payload = build_refund_payload(order, _as_cents(amount), component=component, reason=reason or DEFAULT_REASON)
    data = _walmart_request('POST', 'orders/{}/refund'.format(order.get('purchaseOrderId') or purchase_order_id), json_body=payload)
    refund_id = (((data.get('orderRefund') or {}).get('refundId')) or data.get('refundId'))
    return {'order': order, 'payload': payload, 'response': data, 'refund_id': refund_id}
