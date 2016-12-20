from django.utils.encoding import smart_text


def get_attributes_display_map(variant, attributes):
    display = {}
    for attribute in attributes:
        value = variant.attributes.get(smart_text(attribute.pk))
        if value:
            choices = {str(a.pk): a for a in attribute.values.all()}
            attr = choices.get(value)
            if attr:
                display[attribute.pk] = attr
    return display
