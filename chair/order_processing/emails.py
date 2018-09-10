from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template


def send_customer_email(email_address, tracking, shipping):
    mail_context = {'tracking': tracking, 'shipping': shipping}
    mail_template = get_template('dashboard/order_sent_mail.html')
    html_content = mail_template.render(mail_context)
    subject, from_email = 'Your Order from Pulselabz has been shipped', 'noreply@pulselabz.com'
    text_content = ("Thank you for supporting Pulselabz! \n\n"
                    " Your item has been shipped out and the tracking number is as follows: {} \n\n"
                    "Please feel free to contact us at any time and we will be happy to assist you. \n\n"
                    "Thank you,\n"
                    "Pulselabz Team\n")
    msg = EmailMultiAlternatives(subject, text_content, from_email, [email_address])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
