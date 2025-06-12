# game_tags.py
from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from users.models import Game, UserGameRating # Убедитесь, что все нужные модели импортированы

register = template.Library()

# Иконки (оставляем как есть, убедись, что пути верны)
ICON_PATHS = {
    'star': static('imgs/icons/star_btn.svg'),
    'close': static('imgs/icons/close_btn.svg'),
    'fav_default': static('imgs/icons/fav_btn.svg'),
    'fav_active': static('imgs/icons/red_fav_btn.svg'),
    'fav_small_default': static('imgs/icons/fav_btn.svg'), # Может быть та же, что и обычная
    'fav_small_active': static('imgs/icons/red_fav_btn.svg'), # Может быть та же, что и обычная
    # --- Иконки статусов ИГР ---
    'gamepad_default': static('imgs/icons/btn_gamepad_main.svg'), # Иконка по умолчанию для игр
    'gamepad_small_default': static('imgs/icons/btn_gamepad_main.svg'), # Для маленьких кнопок
    'played': static('imgs/icons/green_btn_gamepad_main.svg'),
    'playing': static('imgs/icons/playing_icon.svg'),
    'dropped': static('imgs/item_actions_icons/dropped_icon.svg'),
    # --- Общие иконки ---
    'arrow_down': static('imgs/icons/swiper_arrownext.svg'), # Проверьте, используется ли
    'complete_check': static('imgs/icons/complete-check.svg'),
    'trash': static('imgs/icons/trash_btn.svg'),
    'star_gray': static('imgs/icons/gray_star.svg'),
    'star_yellow': static('imgs/icons/yellow_star.svg'),
    # Для маленькой кнопки рейтинга (btn-star-small)
    'star_gray_small': static('imgs/icons/star_btn.svg'),
    'star_yellow_small': static('imgs/icons/yellow_star_small.svg'),
    'star_small': static('imgs/icons/star_btn.svg'), # Эта иконка может быть не нужна, если маленькая кнопка отдельная
}


@register.inclusion_tag('includes/_item_actions.html', takes_context=True)
def game_actions(context, game, size='large', show_learn_more=True, show_rating=True):
    user = context.get('user')
    is_authenticated = user and user.is_authenticated
    is_favorite = False
    current_status_slug = 'none'
    current_status_icon = ICON_PATHS.get('gamepad_default')
    statuses_state = {'played': False, 'playing': False, 'dropped': False}
    urls = {}
    available_statuses = []
    user_rating = None

    game_status_map = {
        'played': {'display': 'Played', 'icon': ICON_PATHS.get('played'), 'url_name': 'users:played_add'},
        'playing': {'display': 'Playing', 'icon': ICON_PATHS.get('playing'), 'url_name': 'users:playing_add'},
        'dropped': {'display': 'Dropped', 'icon': ICON_PATHS.get('dropped'), 'url_name': 'users:dropped_add'},
    }

    # --- НОВЫЕ ПЕРЕМЕННЫЕ ДЛЯ МОДАЛЬНОГО ОКНА ---
    item_title_for_modal = ""
    item_image_url_for_modal = ""
    # --- КОНЕЦ НОВЫХ ПЕРЕМЕННЫХ ---

    if isinstance(game, Game): # Проверяем, что game это действительно объект Game
        # --- ЗАПОЛНЯЕМ ДАННЫЕ ДЛЯ МОДАЛЬНОГО ОКНА ---
        item_title_for_modal = game.name
        # Выбираем лучшее изображение для модалки: custom_header_photo, потом custom_photo, потом cover_url
        if game.custom_header_photo:
            item_image_url_for_modal = game.custom_header_photo
        elif game.cover_url:
            item_image_url_for_modal = game.cover_url
        # --- КОНЕЦ ЗАПОЛНЕНИЯ ДАННЫХ ДЛЯ МОДАЛЬНОГО ОКНА ---

        if is_authenticated:
            is_favorite = user.is_item_favorite(game)

            if user.is_played(game): current_status_slug = 'played'
            elif user.is_playing(game): current_status_slug = 'playing'
            elif user.is_dropped(game): current_status_slug = 'dropped'
            else: current_status_slug = 'none'

            current_status_icon = game_status_map.get(current_status_slug, {}).get('icon', ICON_PATHS.get('gamepad_default'))
            if size == 'small' and current_status_slug == 'none': # Для маленьких кнопок без статуса
                current_status_icon = ICON_PATHS.get('gamepad_small_default')

            statuses_state = {
                'played': user.is_played(game),
                'playing': user.is_playing(game),
                'dropped': user.is_dropped(game),
            }

            if show_rating:
                try:
                    rating_obj = UserGameRating.objects.get(user=user, game=game)
                    user_rating = rating_obj.rating
                except UserGameRating.DoesNotExist:
                    user_rating = None
            
            try:
                urls['favorite'] = reverse('users:favorite_toggle', args=['game', game.id])
                for slug, data in game_status_map.items():
                    urls[slug] = reverse(data['url_name'], args=[game.id])
                if show_learn_more:
                    urls['learn_more'] = reverse('game_detail', args=[game.id])

                for slug, data in game_status_map.items():
                    available_statuses.append({
                        'slug': slug,
                        'display': data['display'],
                        'icon': data['icon'],
                        'url': urls.get(slug, '#'),
                        'is_selected': statuses_state.get(slug, False)
                    })
            except NoReverseMatch as e:
                print(f"Error reversing URL in game_actions tag for game {game.id if game else 'None'}: {e}")
                # Очищаем URLs и статусы, чтобы избежать ошибок в шаблоне
                urls = {key: '#' for key in ['favorite', 'played', 'playing', 'dropped', 'learn_more']}
                available_statuses = []
        else: # Если пользователь не аутентифицирован, но game передан
             if show_learn_more and game:
                try:
                    urls['learn_more'] = reverse('game_detail', args=[game.id])
                except NoReverseMatch:
                    urls['learn_more'] = '#'


    current_status_display_name = game_status_map.get(current_status_slug, {}).get('display', 'Status')
    if size == 'small' and current_status_slug == 'none': # Для маленьких кнопок без статуса
        current_status_display_name = '' # Или можно вообще не выводить текст


    # Убедимся, что передаем item_id и item_pk даже если game=None, чтобы избежать ошибок в шаблоне
    # Хотя _item_actions.html должен быть достаточно умным, чтобы справиться с None
    _item_id = game.id if isinstance(game, Game) else None
    _item_pk = game.pk if isinstance(game, Game) else None


    return {
        # 'item': game, # _item_actions.html не использует 'item' напрямую
        'content_type': 'game',
        'item_id': _item_id, # ID для AJAX-запросов на статусы/избранное (может быть game.id или game.game_id)
        'item_pk': _item_pk,   # PK для AJAX-запросов на рейтинг (обычно game.pk)
        
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
        'default_status_icon': ICON_PATHS.get('gamepad_small_default' if size == 'small' else 'gamepad_default'),
        'default_status_text': '' if size == 'small' else 'Status',

        'urls': urls,
        'icons': ICON_PATHS,
        'rating_range': range(1, 11),
    }


# Фильтр для JSON (остается без изменений)
@register.filter(is_safe=True)
def jsonify(obj):
    import json
    return mark_safe(json.dumps(obj))
