# users/templatetags/custom_filters.py
from django import template

register = template.Library()


@register.filter(name='filter_by_status')
def filter_by_status(queryset, attribute_name):
    """
    Фильтрует queryset или список объектов, оставляя только те,
    у которых заданный булев атрибут равен True.
    Используется для аннотированных полей типа Exists.
    """
    if not queryset:
        return []

    try:
        # Используем list comprehension, чтобы создать новый список
        filtered_list = [item for item in queryset if getattr(item, attribute_name, False)]
        # print(f"Filtering by {attribute_name}, found {len(filtered_list)} items.") # Для отладки
        return filtered_list
    except AttributeError:
        # Этот блок может быть избыточным, так как getattr с дефолтом уже обрабатывает отсутствие атрибута
        # print(f"Warning: Attribute '{attribute_name}' not found on some items in filter_by_status.")
        # Если мы хотим строго, чтобы атрибут был, но он может отсутствовать на некоторых объектах коллекции,
        # то можно оставить. Но getattr(item, attribute_name, False) уже вернет False, если атрибута нет.
        return [item for item in queryset if hasattr(item, attribute_name) and getattr(item, attribute_name)]
    except Exception as e:
        print(f"Error in filter_by_status with attribute {attribute_name}: {e}")
        return []


@register.filter
def get_item(dictionary, key):
    """Позволяет получить значение из словаря по ключу в шаблоне."""
    return dictionary.get(key)
