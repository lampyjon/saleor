from django.conf import settings
from templated_email import send_templated_mail, InlineImage
from saleor.account.models import User

# get list of people to email
def who_to_email():
    return User.objects.filter(groups__name='EmailRecipients').values_list('email', flat=True)


# wrapper around the mail email function, primarily to give consistency on sender email address
def send_bullet_mail(template_name, recipient_list, context, extra_headers={}, from_email=None):
    if from_email == None:
        from_email = settings.DEFAULT_FROM_EMAIL

    with open('bullets.png', 'rb') as bulletpic:
        image = bulletpic.read()
    inline_image = InlineImage(filename="bullets.png", content=image)
    context['bullet_pic'] = inline_image

    return send_templated_mail(
         template_name=template_name,
         from_email=from_email,
         recipient_list=recipient_list,
         context=context,
         headers=extra_headers)


# A wrapper to send managers emails when required
def send_manager_email(template_name, context={}, extra_headers={}):
#    print(str(context))
#    print(str(template_name))
#    print(str(who_to_email()))
    return send_bullet_mail(template_name=template_name,
        recipient_list=who_to_email(),
        context=context,
        extra_headers=extra_headers)

 	
