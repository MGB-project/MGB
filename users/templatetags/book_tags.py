# users/templatetags/book_tags.py
from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from users.models import Book, UserBookRating

register = template.Library()

# --- ИКОНКИ ДЛЯ КНИГ ---
BOOK_ICON_PATHS = {
    'star': static('imgs/icons/star_btn.svg'),
    'close': static('imgs/icons/close_btn.svg'),
    'fav_default': static('imgs/icons/fav_btn.svg'),
    'fav_active': static('imgs/icons/red_fav_btn.svg'),
    'fav_small_default': static('imgs/icons/fav_btn.svg'),
    'fav_small_active': static('imgs/icons/red_fav_btn.svg'),
    # --- Иконки статусов КНИГ ---
    'status_default': static('imgs/item_actions_icons/book_status_default.svg'),
    'status_small_default': static('imgs/item_actions_icons/book_status_default.svg'),
    'read': static('imgs/item_actions_icons/book_read_icon.svg'),
    'reading': static('imgs/item_actions_icons/book_reading_icon.svg'),
    'dropped': static('imgs/item_actions_icons/dropped_icon.svg'),
    # --- Общие иконки ---
    'arrow_down': static('imgs/icons/swiper_arrownext.svg'),
    'complete_check': static('imgs/icons/complete-check.svg'),
    'trash': static('imgs/icons/trash_btn.svg'),
    'star_gray': static('imgs/icons/gray_star.svg'),
    'star_yellow': static('imgs/icons/yellow_star.svg'),
    # Для маленькой кнопки рейтинга (btn-star-small)
    'star_gray_small': static('imgs/icons/star_btn.svg'),
    'star_yellow_small': static('imgs/icons/yellow_star_small.svg'),
}


@register.inclusion_tag('includes/_item_actions.html', takes_context=True)
def book_actions(context, book, size='large', show_learn_more=True, show_rating=True):
    user = context.get('user')
    is_authenticated = user and user.is_authenticated
    is_favorite = False
    current_status_slug = 'none'
    current_status_icon = BOOK_ICON_PATHS.get('status_default')
    statuses_state = {'read': False, 'reading': False, 'dropped': False}
    urls = {}
    available_statuses = []
    user_rating = None

    book_status_map = {
        'read':    {'display': 'Read',    'icon': BOOK_ICON_PATHS.get('read'),    'url_name': 'users:read_add'},
        'reading': {'display': 'Reading', 'icon': BOOK_ICON_PATHS.get('reading'), 'url_name': 'users:reading_add'},
        'dropped': {'display': 'Dropped', 'icon': BOOK_ICON_PATHS.get('dropped'), 'url_name': 'users:book_dropped_add'},
    }

    # --- НОВЫЕ ПЕРЕМЕННЫЕ ДЛЯ МОДАЛЬНОГО ОКНА ---
    item_title_for_modal = ""
    item_image_url_for_modal = ""
    # --- КОНЕЦ НОВЫХ ПЕРЕМЕННЫХ ---

    if isinstance(book, Book): # Проверяем, что book это действительно объект Book
        # --- ЗАПОЛНЯЕМ ДАННЫЕ ДЛЯ МОДАЛЬНОГО ОКНА ---
        item_title_for_modal = book.title
        if book.custom_header_photo:
            item_image_url_for_modal = book.custom_header_photo
        elif book.thumbnail:
            item_image_url_for_modal = book.thumbnail
        # Убедитесь, что эти поля содержат ПОЛНЫЕ URL изображений
        # --- КОНЕЦ ЗАПОЛНЕНИЯ ДАННЫХ ДЛЯ МОДАЛЬНОГО ОКНА ---

        if is_authenticated:
            is_favorite = user.is_item_favorite(book)

            if user.is_read(book): current_status_slug = 'read'
            elif user.is_reading(book): current_status_slug = 'reading'
            elif user.is_book_dropped(book): current_status_slug = 'dropped'
            else: current_status_slug = 'none'

            current_status_icon = book_status_map.get(current_status_slug, {}).get('icon', BOOK_ICON_PATHS.get('status_default'))
            if size == 'small' and current_status_slug == 'none':
                current_status_icon = BOOK_ICON_PATHS.get('status_small_default')

            statuses_state = {
                'read': user.is_read(book),
                'reading': user.is_reading(book),
                'dropped': user.is_book_dropped(book),
            }

            if show_rating:
                user_pk_val = user.pk if user else None
                book_pk_val = book.pk if book else None
                print(f"Querying UserBookRating with user_pk={user_pk_val}, book_pk={book_pk_val}")

                if user_pk_val is not None and book_pk_val is not None:
                    try:
                        # Используем _id для ForeignKey полей для прямого запроса по PK
                        rating_obj = UserBookRating.objects.get(user_id=user_pk_val, book_id=book_pk_val)
                        user_rating = rating_obj.rating
                        print(f"SUCCESS (by _id fields): Found rating: {user_rating}")
                    except UserBookRating.DoesNotExist:
                        user_rating = None
                        print(f"INFO (by _id fields): UserBookRating.DoesNotExist.")
                    # ... остальные except ...
                else:
                    user_rating = None
                    print(f"INFO (by _id fields): user_pk or book_pk is None.")
                if user and user.is_authenticated:
                    rating_exists_by_id = UserBookRating.objects.filter(user_id=user.pk, book_id=book.pk).exists()

                    if rating_exists_by_id:
                        try:
                            rating_obj_by_id = UserBookRating.objects.get(user_id=user.pk, book_id=book.pk)
                            user_rating = rating_obj_by_id.rating

                        except UserBookRating.DoesNotExist:

                            user_rating = None
                        except UserBookRating.MultipleObjectsReturned:
                            # Попробуем взять первый, но это указывает на проблему с данными
                            rating_obj_by_id = UserBookRating.objects.filter(user_id=user.pk, book_id={book.pk}).first()
                            if rating_obj_by_id:
                                user_rating = rating_obj_by_id.rating
                            else:
                                user_rating = None
                        except Exception as e_get_id:
                            user_rating = None
                    else:
                        user_rating = None
                else:
                    user_rating = None

            try:
                # Используем google_id для книг в URL
                urls['favorite'] = reverse('users:favorite_toggle', args=['book', book.google_id])
                for slug, data in book_status_map.items():
                    urls[slug] = reverse(data['url_name'], args=[book.google_id])
                if show_learn_more:
                    # Для book_detail может использоваться google_id или pk. Сейчас стоит pk (book.id)
                    # Если используется google_id, то args=[book.google_id]
                    urls['learn_more'] = reverse('book_detail', args=[book.id])

                for slug, data in book_status_map.items():
                    available_statuses.append({
                        'slug': slug,
                        'display': data['display'],
                        'icon': data['icon'],
                        'url': urls.get(slug, '#'),
                        'is_selected': statuses_state.get(slug, False)
                    })
            except NoReverseMatch as e:
                print(f"Error reversing URL in book_actions tag for book {book.google_id if book else 'None'}: {e}")
                urls = {key: '#' for key in ['favorite', 'read', 'reading', 'dropped', 'learn_more']}
                available_statuses = []
        else: # Если пользователь не аутентифицирован, но book передан
            if show_learn_more and book:
                try:
                    urls['learn_more'] = reverse('book_detail', args=[book.id])
                except NoReverseMatch:
                    urls['learn_more'] = '#'

    print(f"FINAL user_rating being passed to template for '{book.title if book else 'N/A'}': {user_rating}\n")
    current_status_display_name = book_status_map.get(current_status_slug, {}).get('display', 'Status')
    if size == 'small' and current_status_slug == 'none':
        current_status_display_name = ''

    # Убедимся, что google_id и pk передаются корректно
    _item_id_for_actions = book.google_id if isinstance(book, Book) else None
    _item_pk_for_rating = book.pk if isinstance(book, Book) else None

    return {
        # 'item': book, # _item_actions.html не использует 'item' напрямую
        'content_type': 'book',
        'item_id': _item_id_for_actions,   # google_id для внешних действий
        'item_pk': _item_pk_for_rating,      # Внутренний PK для рейтинга
        
        # --- ДАННЫЕ ДЛЯ МОДАЛЬНОГО ОКНА ---
        'item_title': item_title_for_modal,
        'item_image_url': item_image_url_for_modal,
        # --- КОНЕЦ ДАННЫХ ДЛЯ МОДАЛЬНОГО ОКНА ---

        'user_rating': user_rating,
        'size': size,
        'show_learn_more': show_learn_more,
        'show_rating': show_rating,
        'is_authenticated': is_authenticated,
        'is_favorite': is_favorite,

        'current_status_slug': current_status_slug,
        'current_status_display_name': current_status_display_name,
        'current_status_icon': current_status_icon,
        'available_statuses': available_statuses,
        'clear_status_url': urls.get(current_status_slug, '#'),
        'default_status_icon': BOOK_ICON_PATHS.get('status_small_default' if size == 'small' else 'status_default'),
        'default_status_text': '' if size == 'small' else 'Status',

        'urls': urls,
        'icons': BOOK_ICON_PATHS,
        'rating_range': range(1, 11),
    }


# Фильтр jsonify
@register.filter(is_safe=True)
def jsonify(obj):
    import json
    return mark_safe(json.dumps(obj))
