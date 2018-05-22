import json

from django import forms
from django.utils.encoding import smart_text
from django.utils.translation import pgettext_lazy
from django_prices.templatetags.prices_i18n import amount

from ..cart.forms import AddToCartForm
from ..core.utils.taxes import display_gross_prices

from django.db.models import F, Sum	# Bullets: needed for the future shipping line below

class VariantChoiceField(forms.ModelChoiceField):
    discounts = None
    taxes = None
    display_gross = True

    def label_from_instance(self, obj):
        if obj.future_shipping:
            s = "(*)"
        else:
            s = ""

        variant_label = smart_text(obj)
        price = obj.get_price(self.discounts, self.taxes)
        price = price.gross if self.display_gross else price.net
        label = pgettext_lazy(
            'Variant choice field label',
            '%(variant_label)s - %(price)s %(future)s') % {
                'variant_label': variant_label, 'price': amount(price),
		'future': s}	# BULLETS future shipping
        return label

    def update_field_data(self, variants, discounts, taxes, product):  # BULLETS add product
        """Initialize variant picker metadata."""
        self.queryset = variants
        self.discounts = discounts
        self.taxes = taxes
        self.empty_label = None
        self.display_gross = display_gross_prices()
        images_map = {
            variant.pk: [
                vi.image.image.url for vi in variant.variant_images.all()]
            for variant in variants.all()}
        self.widget.attrs['data-images'] = json.dumps(images_map)

	# BULLETS TWEAK, I HAVE NO RECOLLECTION WHAT THIS DOES NOW!
        qs = self.queryset
        if product.any_future_shipping():
            qs = qs.annotate(stock_left=F('quantity')-F('quantity_allocated')).filter(stock_left__gte=1) #### Remove any variants that have no stock available from the QS
        self.queryset = qs

        # Don't display select input if there is only one variant.
        if self.queryset.count() == 1:
            self.widget = forms.HiddenInput(
                {'value': variants.all()[0].pk})


class ProductForm(AddToCartForm):
    variant = VariantChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        variant_field = self.fields['variant']
        variant_field.label = "Product Option"		# BULLETS to make it a bit saner
        variant_field.update_field_data(
            self.product.variants, self.discounts, self.taxes, self.product)

    def get_variant(self, cleaned_data):
        x = cleaned_data.get('variant')
        try:
            y = int(x)
            variant = self.product.variants.get(pk=x)
            return variant
        except TypeError:
            return x
