from django.conf import settings
from templated_email import send_templated_mail


# wrapper around the mail email function, primarily to give consistency on sender email address
def send_bullet_mail(template_name, recipient_list, context, extra_headers={}, from_email=None):
    if from_email == None:
        from_email = settings.DEFAULT_FROM_EMAIL

    send_templated_mail(
         template_name=template_name,
         from_email=from_email,
         recipient_list=recipient_list,
         context=context,
         headers=extra_headers)

