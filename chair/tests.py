from decimal import Decimal
from unittest import TestCase

from chair.order_processing.walmart import build_refund_payload, refundable_summary, is_wfs_order


SAMPLE_ORDER = {
    'purchaseOrderId': '309116957252162',
    'customerOrderId': '600000100996860',
    'orderLines': {
        'orderLine': [
            {
                'lineNumber': '1',
                'shipNodeType': 'SellerFulfilled',
                'charges': {
                    'charge': [
                        {
                            'chargeType': 'PRODUCT',
                            'chargeName': 'ItemPrice',
                            'chargeAmount': {'currency': 'CAD', 'amount': '508.49'},
                            'tax': {'taxName': 'Tax', 'taxAmount': {'currency': 'CAD', 'amount': '60.00'}},
                        },
                        {
                            'chargeType': 'SHIPPING',
                            'chargeName': 'Shipping',
                            'chargeAmount': {'currency': 'CAD', 'amount': '10.00'},
                            'tax': {'taxName': 'Tax', 'taxAmount': {'currency': 'CAD', 'amount': '1.20'}},
                        },
                    ],
                },
            },
        ],
    },
}


class WalmartRefundTests(TestCase):
    def test_refundable_summary_splits_product_shipping_and_tax(self):
        summary = refundable_summary(SAMPLE_ORDER)
        self.assertEqual(summary['product'], Decimal('508.49'))
        self.assertEqual(summary['shipping'], Decimal('10.00'))
        self.assertEqual(summary['tax'], Decimal('61.20'))
        self.assertEqual(summary['selected_before_tax'], Decimal('518.49'))

    def test_build_refund_payload_allocates_partial_item_refund(self):
        payload = build_refund_payload(SAMPLE_ORDER, 25425, component='product', reason='BillingError')
        refund_charge = payload['orderRefund']['orderLines']['orderLine'][0]['refunds']['refund'][0]['refundCharges']['refundCharge'][0]
        self.assertEqual(payload['orderRefund']['purchaseOrderId'], '309116957252162')
        self.assertEqual(refund_charge['refundReason'], 'BillingError')
        self.assertEqual(refund_charge['charge']['chargeType'], 'PRODUCT')
        self.assertEqual(refund_charge['charge']['chargeAmount']['amount'], 254.25)
        self.assertEqual(refund_charge['charge']['tax']['taxAmount']['amount'], 30.0)

    def test_wfs_detection(self):
        order = dict(SAMPLE_ORDER)
        order['orderLines'] = {'orderLine': [dict(SAMPLE_ORDER['orderLines']['orderLine'][0], shipNodeType='WFSFulfilled')]}
        self.assertTrue(is_wfs_order(order))
        self.assertFalse(is_wfs_order(SAMPLE_ORDER))
