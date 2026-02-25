from django import template

register = template.Library()


@register.filter
def shekels(value):
    amount = (value or 0) / 100
    return f"?{amount:,.2f}"
