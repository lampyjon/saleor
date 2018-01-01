from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, reverse
from django.template.response import TemplateResponse
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django.views.decorators.http import require_POST

from . import forms
from ...core.utils import get_paginator_items
from ...discount.models import Sale
from ...product.models import (
    AttributeChoiceValue, Product, ProductAttribute, ProductImage, ProductType,
    ProductVariant)
from ...product.utils.availability import get_availability
from ...product.utils.costs import (
    get_margin_for_variant, get_product_costs_data)
from ..views import staff_member_required
from .filters import ProductAttributeFilter, ProductFilter, ProductTypeFilter


@staff_member_required
@permission_required('product.view_properties')
def product_type_list(request):
    types = ProductType.objects.all().prefetch_related(
        'product_attributes', 'variant_attributes').order_by('name')
    type_filter = ProductTypeFilter(request.GET, queryset=types)
    form = forms.ProductTypeForm(request.POST or None)
    if form.is_valid():
        return redirect('dashboard:product-type-add')
    types = get_paginator_items(
        type_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    types.object_list = [
        (pc.pk, pc.name, pc.has_variants, pc.product_attributes.all(),
         pc.variant_attributes.all())
        for pc in types.object_list]
    ctx = {
        'form': form, 'product_types': types, 'filter_set': type_filter,
        'is_empty': not type_filter.queryset.exists()}
    return TemplateResponse(
        request,
        'dashboard/product/product_type/list.html',
        ctx)


@staff_member_required
@permission_required('product.edit_properties')
def product_type_create(request):
    product_type = ProductType()
    form = forms.ProductTypeForm(
        request.POST or None, instance=product_type)
    if form.is_valid():
        product_type = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added product type %s') % (product_type,)
        messages.success(request, msg)
        return redirect('dashboard:product-type-list')
    ctx = {'form': form, 'product_type': product_type}
    return TemplateResponse(
        request,
        'dashboard/product/product_type/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_properties')
def product_type_edit(request, pk):
    product_type = get_object_or_404(ProductType, pk=pk)
    form = forms.ProductTypeForm(
        request.POST or None, instance=product_type)
    if form.is_valid():
        product_type = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated product type %s') % (product_type,)
        messages.success(request, msg)
        return redirect('dashboard:product-type-update', pk=pk)
    ctx = {'form': form, 'product_type': product_type}
    return TemplateResponse(
        request,
        'dashboard/product/product_type/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_properties')
def product_type_delete(request, pk):
    product_type = get_object_or_404(ProductType, pk=pk)
    if request.method == 'POST':
        product_type.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed product type %s') % (product_type,)
        messages.success(request, msg)
        return redirect('dashboard:product-type-list')
    ctx = {
        'product_type': product_type,
        'products': product_type.products.all()}
    return TemplateResponse(
        request,
        'dashboard/product/product_type/modal/confirm_delete.html',
        ctx)


@staff_member_required
@permission_required('product.view_product')
def product_list(request):
    products = Product.objects.prefetch_related('images')
    products = products.order_by('name')
    product_types = ProductType.objects.all()
    product_filter = ProductFilter(request.GET, queryset=products)
    products = get_paginator_items(
        product_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'bulk_action_form': forms.ProductBulkUpdate(),
        'products': products, 'product_types': product_types,
        'filter_set': product_filter,
        'is_empty': not product_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/product/list.html', ctx)


@staff_member_required
@permission_required('product.edit_product')
def product_select_type(request):
    """View for add product modal embedded in the product list view."""
    form = forms.ProductTypeSelectorForm(request.POST or None)
    status = 200
    if form.is_valid():
        redirect_url = reverse(
            'dashboard:product-add',
            kwargs={'type_pk': form.cleaned_data.get('product_type').pk})
        return (
            JsonResponse({'redirectUrl': redirect_url})
            if request.is_ajax() else redirect(redirect_url))
    elif form.errors:
        status = 400
    ctx = {'form': form}
    template = 'dashboard/product/modal/select_type.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('product.edit_product')
def product_create(request, type_pk):
    product_type = get_object_or_404(ProductType, pk=type_pk)
    create_variant = not product_type.has_variants
    product = Product()
    product.product_type = product_type
    product_form = forms.ProductForm(request.POST or None, instance=product)
    if create_variant:
        variant = ProductVariant(product=product)
        variant_form = forms.ProductVariantForm(
            request.POST or None, instance=variant, prefix='variant')
        variant_errors = not variant_form.is_valid()
    else:
        variant_form = None
        variant_errors = False

    if product_form.is_valid() and not variant_errors:
        product = product_form.save()
        if create_variant:
            variant.product = product
            variant_form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added product %s') % (product,)
        messages.success(request, msg)
        return redirect('dashboard:product-details', pk=product.pk)
    ctx = {
        'product_form': product_form, 'variant_form': variant_form,
        'product': product}
    return TemplateResponse(request, 'dashboard/product/form.html', ctx)


@staff_member_required
@permission_required('product.view_product')
def product_details(request, pk):
    products = Product.objects.prefetch_related('variants', 'images').all()
    product = get_object_or_404(products, pk=pk)
    variants = product.variants.all()
    images = product.images.all()
    availability = get_availability(
        product, discounts=request.discounts, taxes=request.taxes)
    sale_price = availability.price_range_undiscounted
    discounted_price = availability.price_range
    purchase_cost, margin = get_product_costs_data(product)

    # no_variants is True for product types that doesn't require variant.
    # In this case we're using the first variant under the hood to allow stock
    # management.
    no_variants = not product.product_type.has_variants
    only_variant = variants.first() if no_variants else None
    ctx = {
        'product': product, 'sale_price': sale_price,
        'discounted_price': discounted_price, 'variants': variants,
        'images': images, 'no_variants': no_variants,
        'only_variant': only_variant, 'purchase_cost': purchase_cost,
        'margin': margin, 'is_empty': not variants.exists()}
    return TemplateResponse(request, 'dashboard/product/detail.html', ctx)


@require_POST
@staff_member_required
@permission_required('product.edit_product')
def product_toggle_is_published(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_published = not product.is_published
    product.save(update_fields=['is_published'])
    return JsonResponse(
        {'success': True, 'is_published': product.is_published})


@staff_member_required
@permission_required('product.edit_product')
def product_edit(request, pk):
    product = get_object_or_404(
        Product.objects.prefetch_related('variants'), pk=pk)
    form = forms.ProductForm(request.POST or None, instance=product)

    edit_variant = not product.product_type.has_variants
    if edit_variant:
        variant = product.variants.first()
        variant_form = forms.ProductVariantForm(
            request.POST or None, instance=variant, prefix='variant')
        variant_errors = not variant_form.is_valid()
    else:
        variant_form = None
        variant_errors = False

    if form.is_valid() and not variant_errors:
        product = form.save()
        if edit_variant:
            variant_form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated product %s') % (product,)
        messages.success(request, msg)
        return redirect('dashboard:product-details', pk=product.pk)
    ctx = {
        'product': product, 'product_form': form, 'variant_form': variant_form}
    return TemplateResponse(request, 'dashboard/product/form.html', ctx)


@staff_member_required
@permission_required('product.edit_product')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed product %s') % (product,)
        messages.success(request, msg)
        return redirect('dashboard:product-list')
    return TemplateResponse(
        request,
        'dashboard/product/modal/confirm_delete.html',
        {'product': product})


@staff_member_required
@permission_required('product.view_product')
def product_images(request, product_pk):
    product = get_object_or_404(
        Product.objects.prefetch_related('images'), pk=product_pk)
    images = product.images.all()
    ctx = {
        'product': product, 'images': images, 'is_empty': not images.exists()}
    return TemplateResponse(
        request, 'dashboard/product/product_image/list.html', ctx)


@staff_member_required
@permission_required('product.edit_product')
def product_image_add(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    product_image = ProductImage(product=product)
    form = forms.ProductImageForm(
        request.POST or None, request.FILES or None, instance=product_image)
    if form.is_valid():
        product_image = form.save()
        msg = pgettext_lazy(
            'Dashboard message',
            'Added image %s') % (product_image.image.name,)
        messages.success(request, msg)
        return redirect('dashboard:product-image-list', product_pk=product.pk)
    ctx = {'form': form, 'product': product, 'product_image': product_image}
    return TemplateResponse(
        request,
        'dashboard/product/product_image/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_product')
def product_image_edit(request, product_pk, img_pk):
    product = get_object_or_404(Product, pk=product_pk)
    product_image = get_object_or_404(product.images, pk=img_pk)
    form = forms.ProductImageForm(
        request.POST or None, request.FILES or None, instance=product_image)
    if form.is_valid():
        product_image = form.save()
        msg = pgettext_lazy(
            'Dashboard message',
            'Updated image %s') % (product_image.image.name,)
        messages.success(request, msg)
        return redirect('dashboard:product-image-list', product_pk=product.pk)
    ctx = {'form': form, 'product': product, 'product_image': product_image}
    return TemplateResponse(
        request,
        'dashboard/product/product_image/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_product')
def product_image_delete(request, product_pk, img_pk):
    product = get_object_or_404(Product, pk=product_pk)
    image = get_object_or_404(product.images, pk=img_pk)
    if request.method == 'POST':
        image.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed image %s') % (image.image.name,)
        messages.success(request, msg)
        return redirect('dashboard:product-image-list', product_pk=product.pk)
    return TemplateResponse(
        request,
        'dashboard/product/product_image/modal/confirm_delete.html',
        {'product': product, 'image': image})


@staff_member_required
@permission_required('product.edit_product')
def variant_add(request, product_pk):
    product = get_object_or_404(Product.objects.all(), pk=product_pk)
    variant = ProductVariant(product=product)
    form = forms.ProductVariantForm(request.POST or None, instance=variant)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Saved variant %s') % (variant.name,)
        messages.success(request, msg)
        return redirect(
            'dashboard:variant-details', product_pk=product.pk,
            variant_pk=variant.pk)
    ctx = {'form': form, 'product': product, 'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/product_variant/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_product')
def variant_edit(request, product_pk, variant_pk):
    product = get_object_or_404(Product.objects.all(), pk=product_pk)
    variant = get_object_or_404(product.variants.all(), pk=variant_pk)
    form = forms.ProductVariantForm(request.POST or None, instance=variant)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Saved variant %s') % (variant.name,)
        messages.success(request, msg)
        return redirect(
            'dashboard:variant-details', product_pk=product.pk,
            variant_pk=variant.pk)
    ctx = {'form': form, 'product': product, 'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/product_variant/form.html',
        ctx)


@staff_member_required
@permission_required('product.view_product')
def variant_details(request, product_pk, variant_pk):
    product = get_object_or_404(Product, pk=product_pk)
    variant = get_object_or_404(product.variants.all(), pk=variant_pk)

    # If the product type of this product assumes no variants, redirect to
    # product details page that has special UI for products without variants.
    if not product.product_type.has_variants:
        return redirect('dashboard:product-details', pk=product.pk)

    images = variant.images.all()
    margin = get_margin_for_variant(variant)
    discounted_price = variant.get_price(discounts=Sale.objects.all()).gross
    ctx = {
        'images': images, 'product': product, 'variant': variant,
        'margin': margin, 'discounted_price': discounted_price}
    return TemplateResponse(
        request,
        'dashboard/product/product_variant/detail.html',
        ctx)


@staff_member_required
@permission_required('product.view_product')
def variant_images(request, product_pk, variant_pk):
    product = get_object_or_404(Product, pk=product_pk)
    qs = product.variants.prefetch_related('images')
    variant = get_object_or_404(qs, pk=variant_pk)
    form = forms.VariantImagesSelectForm(request.POST or None, variant=variant)
    if form.is_valid():
        form.save()
        return redirect(
            'dashboard:variant-details', product_pk=product.pk,
            variant_pk=variant.pk)
    ctx = {'form': form, 'product': product, 'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/product_variant/modal/select_images.html',
        ctx)


@staff_member_required
@permission_required('product.edit_product')
def variant_delete(request, product_pk, variant_pk):
    product = get_object_or_404(Product, pk=product_pk)
    variant = get_object_or_404(product.variants, pk=variant_pk)
    if request.method == 'POST':
        variant.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed variant %s') % (variant.name,)
        messages.success(request, msg)
        return redirect('dashboard:product-details', pk=product.pk)
    ctx = {
        'is_only_variant': product.variants.count() == 1, 'product': product,
        'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/product_variant/modal/confirm_delete.html',
        ctx)


@staff_member_required
@permission_required('product.view_properties')
def attribute_list(request):
    attributes = (ProductAttribute.objects.prefetch_related('values')
                  .order_by('name'))
    attribute_filter = ProductAttributeFilter(request.GET, queryset=attributes)
    attributes = [
        (attribute.pk, attribute.name, attribute.values.all())
        for attribute in attribute_filter.qs]
    attributes = get_paginator_items(
        attributes, settings.DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    ctx = {
        'attributes': attributes, 'filter_set': attribute_filter,
        'is_empty': not attribute_filter.queryset.exists()}
    return TemplateResponse(
        request, 'dashboard/product/product_attribute/list.html', ctx)


@staff_member_required
@permission_required('product.view_properties')
def attribute_details(request, pk):
    attributes = ProductAttribute.objects.prefetch_related('values').all()
    attribute = get_object_or_404(attributes, pk=pk)
    ctx = {
        'attribute': attribute,
        'is_empty': not attributes.exists()}
    return TemplateResponse(
        request, 'dashboard/product/product_attribute/detail.html', ctx)


@staff_member_required
@permission_required('product.edit_properties')
def attribute_add(request):
    attribute = ProductAttribute()
    form = forms.ProductAttributeForm(request.POST or None, instance=attribute)
    if form.is_valid():
        attribute = form.save()
        msg = pgettext_lazy('Dashboard message', 'Added attribute')
        messages.success(request, msg)
        return redirect('dashboard:product-attribute-details', pk=attribute.pk)
    ctx = {'attribute': attribute, 'form': form}
    return TemplateResponse(
        request,
        'dashboard/product/product_attribute/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_properties')
def attribute_edit(request, pk):
    attribute = get_object_or_404(ProductAttribute, pk=pk)
    form = forms.ProductAttributeForm(request.POST or None, instance=attribute)
    if form.is_valid():
        attribute = form.save()
        msg = pgettext_lazy('Dashboard message', 'Updated attribute')
        messages.success(request, msg)
        return redirect('dashboard:product-attribute-details', pk=attribute.pk)
    ctx = {'attribute': attribute, 'form': form}
    return TemplateResponse(
        request,
        'dashboard/product/product_attribute/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_properties')
def attribute_delete(request, pk):
    attribute = get_object_or_404(ProductAttribute, pk=pk)
    if request.method == 'POST':
        attribute.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed attribute %s') % (attribute.name,)
        messages.success(request, msg)
        return redirect('dashboard:product-attributes')
    return TemplateResponse(
        request,
        'dashboard/product/product_attribute/modal/'
        'attribute_confirm_delete.html',
        {'attribute': attribute})


@staff_member_required
@permission_required('product.edit_properties')
def attribute_choice_value_add(request, attribute_pk):
    attribute = get_object_or_404(ProductAttribute, pk=attribute_pk)
    value = AttributeChoiceValue(attribute_id=attribute_pk)
    form = forms.AttributeChoiceValueForm(request.POST or None, instance=value)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added attribute\'s value')
        messages.success(request, msg)
        return redirect('dashboard:product-attribute-details', pk=attribute_pk)
    ctx = {'attribute': attribute, 'value': value, 'form': form}
    return TemplateResponse(
        request,
        'dashboard/product/product_attribute/values/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_properties')
def attribute_choice_value_edit(request, attribute_pk, value_pk):
    attribute = get_object_or_404(ProductAttribute, pk=attribute_pk)
    value = get_object_or_404(AttributeChoiceValue, pk=value_pk)
    form = forms.AttributeChoiceValueForm(request.POST or None, instance=value)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated attribute\'s value')
        messages.success(request, msg)
        return redirect('dashboard:product-attribute-details', pk=attribute_pk)
    ctx = {'attribute': attribute, 'value': value, 'form': form}
    return TemplateResponse(
        request,
        'dashboard/product/product_attribute/values/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_properties')
def attribute_choice_value_delete(request, attribute_pk, value_pk):
    value = get_object_or_404(AttributeChoiceValue, pk=value_pk)
    if request.method == 'POST':
        value.delete()
        msg = pgettext_lazy(
            'Dashboard message',
            'Removed attribute\'s value %s') % (value.name,)
        messages.success(request, msg)
        return redirect('dashboard:product-attribute-details', pk=attribute_pk)
    return TemplateResponse(
        request,
        'dashboard/product/product_attribute/values/modal/confirm_delete.html',
        {'value': value, 'attribute_pk': attribute_pk})


@require_POST
@staff_member_required
def ajax_reorder_product_images(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    form = forms.ReorderProductImagesForm(request.POST, instance=product)
    status = 200
    ctx = {}
    if form.is_valid():
        form.save()
    elif form.errors:
        status = 400
        ctx = {'error': form.errors}
    return JsonResponse(ctx, status=status)


@require_POST
@staff_member_required
def ajax_upload_image(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    form = forms.UploadImageForm(
        request.POST or None, request.FILES or None, product=product)
    status = 200
    if form.is_valid():
        image = form.save()
        ctx = {'id': image.pk, 'image': None, 'order': image.order}
    elif form.errors:
        status = 400
        ctx = {'error': form.errors}
    return JsonResponse(ctx, status=status)


@require_POST
@staff_member_required
def product_bulk_update(request):
    form = forms.ProductBulkUpdate(request.POST)
    if form.is_valid():
        form.save()
        count = len(form.cleaned_data['products'])
        msg = npgettext_lazy(
            'Dashboard message',
            '%(count)d product has been updated',
            '%(count)d products have been updated',
            number=count) % {'count': count}
        messages.success(request, msg)
    return redirect('dashboard:product-list')


@staff_member_required
def ajax_available_variants_list(request):
    """Return variants filtered by request GET parameters.

    Response format is that of a Select2 JS widget.
    """
    available_products = Product.objects.available_products().prefetch_related(
        'category',
        'product_type__product_attributes')
    queryset = ProductVariant.objects.filter(
        product__in=available_products).prefetch_related(
            'product__category',
            'product__product_type__product_attributes')

    search_query = request.GET.get('q', '')
    if search_query:
        queryset = queryset.filter(
            Q(sku__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(product__name__icontains=search_query))

    variants = [
        {'id': variant.id, 'text': variant.get_ajax_label(request.discounts)}
        for variant in queryset]
    return JsonResponse({'results': variants})


@staff_member_required
def ajax_products_list(request):
    """Return products filtered by request GET parameters.

    Response format is that of a Select2 JS widget.
    """
    queryset = (
        Product.objects.all() if request.user.has_perm('product.view_product')
        else Product.objects.available_products())
    search_query = request.GET.get('q', '')
    if search_query:
        queryset = queryset.filter(Q(name__icontains=search_query))
    products = [
        {'id': product.id, 'text': str(product)} for product in queryset
    ]
    return JsonResponse({'results': products})

@staff_member_required
def view_allocations(request):
    # table view of all stock allocations in open orders
    stock_items = Stock.objects.filter(quantity_allocated__gt=0).order_by('location')
    ctx = {'items':stock_items}
    return TemplateResponse(request, 'dashboard/product/view_allocations.html', ctx)
