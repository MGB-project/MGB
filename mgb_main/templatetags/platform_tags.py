from django import template
import json
from ..utils import get_platform_icon_path, format_runtime

register = template.Library()


@register.simple_tag
def get_platform_icon_for(platform_name_from_db):
    if not platform_name_from_db:
        return None
    return get_platform_icon_path(platform_name_from_db)


@register.filter
def runtime_format(minutes):
    return format_runtime(minutes)


@register.filter(name="parse_json") # <-- НОВЫЙ ФИЛЬТР
def parse_json(json_data):
    """
    Пытается распарсить JSON-строку.
    Возвращает распарсенный объект (обычно list) или пустой список, если не удалось.
    Также работает, если данные УЖЕ являются списком/словарем, а не строкой.
    """
    if not json_data:
        return []
    try:
        if isinstance(json_data, str):
            parsed = json.loads(json_data)
        else:
            parsed = json_data

        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
