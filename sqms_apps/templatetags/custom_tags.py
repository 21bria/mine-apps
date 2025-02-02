# your_app/templatetags/custom_tags.py

from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()

@register.filter(name='has_any_group')
def has_any_group(user, group_names):
    if not user.is_authenticated:
        return False
    group_names_list = [group.strip() for group in group_names.split(',')]
    return user.groups.filter(name__in=group_names_list).exists()
