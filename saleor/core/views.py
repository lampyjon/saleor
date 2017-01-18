from django.template.response import TemplateResponse

from ..product.utils import products_with_availability, products_with_details
from ..product.models import FeaturedProduct


def home(request):
    products = products_with_details(request.user)
    products = products.filter(featured__isnull=False).order_by('featured', 'featured__display_order')
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    return TemplateResponse(
        request, 'index.html',
        {'products': products, 'parent': None})
