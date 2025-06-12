# users/templatetags/movie_tags.py
from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from users.models import Movie, UserMovieRating

register = template.Library()

# --- ИКОНКИ ДЛЯ ФИЛЬМОВ ---
MOVIE_ICON_PATHS = {
    'star': static('imgs/icons/star_btn.svg'),
    'close': static('imgs/icons/close_btn.svg'),
    'fav_default': static('imgs/icons/fav_btn.svg'),
    'fav_active': static('imgs/icons/red_fav_btn.svg'),
    'fav_small_default': static('imgs/icons/fav_btn.svg'),
    'fav_small_active': static('imgs/icons/red_fav_btn.svg'),
    # Иконки статусов фильмов
    'status_default': static('imgs/item_actions_icons/movie_status_default.svg'),
    'status_small_default': static('imgs/item_actions_icons/movie_status_default.svg'),
    'watched': static('imgs/item_actions_icons/watched_icon.svg'),
    'watching': static('imgs/item_actions_icons/watching_icon.svg'),
    'dropped': static('imgs/item_actions_icons/dropped_icon.svg'),
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
def movie_actions(context, movie, size='large', show_learn_more=True, show_rating=True):
    user = context.get('user')
    is_authenticated = user and user.is_authenticated
    is_favorite = False
    current_status_slug = 'none'
    current_status_icon = MOVIE_ICON_PATHS.get('status_default')
    statuses_state = {'watched': False, 'watching': False, 'dropped': False}
    urls = {}
    available_statuses = []
    user_rating = None

    status_map = {
        'watched': {'display': 'Watched', 'icon': MOVIE_ICON_PATHS.get('watched'), 'url_name': 'users:watched_add'},
        'watching': {'display': 'Watching', 'icon': MOVIE_ICON_PATHS.get('watching'), 'url_name': 'users:watching_add'},
        'dropped': {'display': 'Dropped', 'icon': MOVIE_ICON_PATHS.get('dropped'), 'url_name': 'users:movie_dropped_add'}, # Убедитесь, что это имя URL правильное
    }

    # --- НОВЫЕ ПЕРЕМЕННЫЕ ДЛЯ МОДАЛЬНОГО ОКНА ---
    item_title_for_modal = ""
    item_image_url_for_modal = ""
    # --- КОНЕЦ НОВЫХ ПЕРЕМЕННЫХ ---

    if isinstance(movie, Movie):
        # --- ЗАПОЛНЯЕМ ДАННЫЕ ДЛЯ МОДАЛЬНОГО ОКНА ---
        item_title_for_modal = movie.title

        TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/"
        POSTER_SIZE_FOR_MODAL = "w342"

        if movie.custom_header_photo:
            item_image_url_for_modal = movie.custom_header_photo
        elif movie.poster_path:
            item_image_url_for_modal = f"{TMDB_IMAGE_BASE_URL}{POSTER_SIZE_FOR_MODAL}{movie.poster_path}"

        # Можно добавить URL для заглушки, если совсем нет изображения
        # else:
        #    item_image_url_for_modal = static('imgs/placeholder_movie.png')
        # --- КОНЕЦ ЗАПОЛНЕНИЯ ДАННЫХ ДЛЯ МОДАЛЬНОГО ОКНА ---

        if is_authenticated:
            is_favorite = user.is_item_favorite(movie)

            if user.is_watched(movie): current_status_slug = 'watched'
            elif user.is_watching(movie): current_status_slug = 'watching'
            elif user.is_movie_dropped(movie): current_status_slug = 'dropped'
            else: current_status_slug = 'none'

            current_status_icon = status_map.get(current_status_slug, {}).get('icon', MOVIE_ICON_PATHS.get('status_default'))
            if size == 'small' and current_status_slug == 'none':
                current_status_icon = MOVIE_ICON_PATHS.get('status_small_default')

            statuses_state = {
                'watched': user.is_watched(movie),
                'watching': user.is_watching(movie),
                'dropped': user.is_movie_dropped(movie),
            }
            
            if show_rating:
                try:
                    rating_obj = UserMovieRating.objects.get(user=user, movie=movie)
                    user_rating = rating_obj.rating
                except UserMovieRating.DoesNotExist:
                    user_rating = None
            
            try:
                urls['favorite'] = reverse('users:favorite_toggle', args=['movie', movie.tmdb_id])
                for slug, data in status_map.items():
                    urls[slug] = reverse(data['url_name'], args=[movie.tmdb_id])
                if show_learn_more:
                     urls['learn_more'] = reverse('movie_detail', args=[movie.tmdb_id])

                for slug, data in status_map.items():
                    available_statuses.append({
                        'slug': slug,
                        'display': data['display'],
                        'icon': data['icon'],
                        'url': urls.get(slug, '#'),
                        'is_selected': statuses_state.get(slug, False)
                    })
            except NoReverseMatch as e:
                print(f"Error reversing URL in movie_actions tag for movie {movie.tmdb_id if movie else 'None'}: {e}")
                urls = {key: '#' for key in ['favorite', 'watched', 'watching', 'dropped', 'learn_more']}
                available_statuses = []
        else: # Если пользователь не аутентифицирован, но movie передан
            if show_learn_more and movie:
                try:
                    urls['learn_more'] = reverse('movie_detail', args=[movie.tmdb_id])
                except NoReverseMatch:
                    urls['learn_more'] = '#'

    current_status_display_name = status_map.get(current_status_slug, {}).get('display', 'Status')
    if size == 'small' and current_status_slug == 'none':
        current_status_display_name = ''

    _item_id = movie.tmdb_id if isinstance(movie, Movie) else None
    _item_pk = movie.pk if isinstance(movie, Movie) else None

    return {
        # 'item': movie, # _item_actions.html не использует 'item' напрямую
        'content_type': 'movie',
        'item_id': _item_id,    # tmdb_id для внешних действий
        'item_pk': _item_pk,      # Внутренний PK для рейтинга

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
        'default_status_icon': MOVIE_ICON_PATHS.get('status_small_default' if size == 'small' else 'status_default'),
        'default_status_text': '' if size == 'small' else 'Status',

        'urls': urls,
        'icons': MOVIE_ICON_PATHS,
        'rating_range': range(1, 11),
    }
