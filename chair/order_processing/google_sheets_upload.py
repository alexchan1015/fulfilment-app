import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from chair.models import Order
from scraper.settings import GOOGLE_CREDS
import json


def post_order_info(order_id, sheets_key):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(GOOGLE_CREDS), scope)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(sheets_key)
    worksheet = sheet.get_worksheet(0)
    next_free = len(worksheet.col_values(2)) + 1
    order = Order.objects.get(order_id=order_id)
    today = datetime.datetime.today().strftime('%B %d')
    worksheet.update_acell('B{}'.format(next_free), today)
    worksheet.update_acell('D{}'.format(next_free), order.part_number)
    if order.source == 'woocommerce':
        worksheet.update_acell('E{}'.format(next_free), order.total_price)
    else:
        worksheet.update_acell('L{}'.format(next_free), order.total_price)
    if order.customer_id.state == 'BC':
        worksheet.update_acell('F{}'.format(next_free), 'BC Retail')
    elif order.customer_id.country == 'USA' and order.source == 'woocommerce':
        worksheet.update_acell('F{}'.format(next_free), 'USA')
    else:
        worksheet.update_acell('F{}'.format(next_free), order.customer_id.state)
    if order.source == 'bestbuy':
        worksheet.update_acell('N{}'.format(next_free), 'Bestbuy')
    elif order.customer_id.country == 'US':
        worksheet.update_acell('N{}'.format(next_free), 'Website-US')
    else:
        worksheet.update_acell('N{}'.format(next_free), 'Website')
    worksheet.update_acell('O{}'.format(next_free), order.bestbuy_commission)
    if order.customer_id.country == 'USA' and order.source == 'woocommerce':
        worksheet.update_acell('Q{}'.format(next_free), 'UPS')
    else:
        worksheet.update_acell('Q{}'.format(next_free), 'Ground-Newegg')
    worksheet.update_acell('T{}'.format(next_free), order.tracking_id)
    worksheet.update_acell('Y{}'.format(next_free),
                           order.customer_id.firstname)
    worksheet.update_acell('Z{}'.format(next_free), order.customer_id.lastname)
    worksheet.update_acell('AA{}'.format(next_free), order.customer_id.phone)
    worksheet.update_acell('AB{}'.format(next_free), order.customer_id.street)
    worksheet.update_acell('AC{}'.format(next_free), order.customer_id.zip)
    worksheet.update_acell('AD{}'.format(next_free), order.customer_id.city)
    worksheet.update_acell('AE{}'.format(next_free), order.customer_id.state)
    worksheet.update_acell('X{}'.format(next_free), order.order_id)
    worksheet.update_acell('AF{}'.format(next_free), order.customer_id.email)
