from django import template

register = template.Library()


@register.filter
def runtime_to_hours_minutes(value):
    try:
        value = int(value)
        hours = value // 60
        minutes = value % 60
        if hours > 0:
            return f"{hours} ч {minutes} мин"
        else:
            return f"{minutes} мин"
    except (ValueError, TypeError):
        return ""
