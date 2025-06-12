from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.models import Game, FavoriteGame, Movie, Genre, Actor, Book, UserGameRating, UserMovieRating, UserBookRating
from django.http import JsonResponse
import json
import re
import time
from .utils import get_youtube_trailer_with_name, get_country_abbreviation, format_runtime, get_platform_icon_path
from datetime import date, timedelta, datetime
from django.template.loader import render_to_string
from django.utils import timezone
from django.urls import reverse
from itertools import chain
from django.templatetags.static import static


def home_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    return render(request, "index_preview.html")


@login_required
def index_view(request):
    return render(request, "index.html")


def profile(request):
    return render(request, 'profile.html')


def sign_page(request):
    return render(request, 'sign_page.html')


def search_view(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', 'all')

    if not query:
        return JsonResponse({'games': [], 'movies': [], 'books': []})

    result = {'games': [], 'movies': [], 'books': []}

    try:
        print(f"Получен запрос: q={query}, category={category}")

        if category in ['all', 'games']:
            games = Game.objects.filter(name__icontains=query).values(
                'id', 'name', 'cover_url', 'first_release_date', 'total_rating', 'rating_color', 'genres'
            )[:5]

            # Форматируем даты
            result['games'] = [
                {
                    **game,  # Распаковываем оригинальные данные
                    'first_release_date': format_date(game['first_release_date'])
                } for game in games
            ]
            print(f"Найдено игр: {len(result['games'])}")

        if category in ['all', 'movies']:
            movies_qs = Movie.objects.filter(title__icontains=query).prefetch_related('genres')[:5] # prefetch_related для оптимизации

            result['movies'] = []
            for movie in movies_qs:
                movie_data = {
                    'id': movie.id,
                    'tmdb_id': movie.tmdb_id,
                    'title': movie.title,
                    'poster_path': movie.poster_path,
                    'release_date': movie.release_date.isoformat() if movie.release_date else None,
                    'vote_average': movie.vote_average,
                    'rating_color': movie.rating_color,
                    'genres': [genre.name for genre in movie.genres.all()],
                 }
                result['movies'].append(movie_data)
            print(f"Найдено фильмов: {len(result['movies'])}")

        if category in ['all', 'books']:
            books_qs = Book.objects.filter(title__icontains=query)[:5]

            result['books'] = []
            for book in books_qs:
                book_data = {
                    'id': book.pk, # Внутренний PK, если нужен
                    'google_id': book.google_id,
                    'title': book.title,
                    'thumbnail': book.thumbnail if book.thumbnail else '/static/imgs/placeholder_thumbnail.png',
                    'published_date': book.published_date,
                    'mgb_average_rating': book.mgb_average_rating, # или book.average_rating
                    'authors': book.authors if isinstance(book.authors, list) else [], # <--- Убедись, что это список строк
                    'categories': book.categories if isinstance(book.categories, list) else [],
                }
                result['books'].append(book_data)
            print(f"Найдено Книг: {len(result['books'])}")

        return JsonResponse(result)

    except Exception as e:
        print(f"Ошибка при обработке запроса: {e}")
        return JsonResponse({'error': 'Internal Server Error'}, status=500)


# ___________________________________________________________________________________________________
# GAMES FUNCTIONS
def games(request):
    top_popular_games = Game.objects.filter(
        total_rating_count__gt=1000
    ).exclude(
        name__icontains="Mario"
    ).exclude(
        name__icontains="Zelda"
    ).order_by('-total_rating')[:50]

    main_games = Game.objects.filter(is_main_game=True)

    recently_trending_small = Game.objects.filter(is_recently_trending_small=True)
    recently_trending_big = Game.objects.filter(is_recently_trending_big=True)

    favorite_games = FavoriteGame.objects.filter(user=request.user)
    favorite_games_ids = set(favorite_games.values_list("game_id", flat=True))

    now_ts = int(timezone.now().timestamp())
    time_threshold = timezone.now() - timedelta(days=120)
    timestamp_threshold = int(time_threshold.timestamp())

    MIN_RATING_COUNT = 1
    new_games = Game.objects.filter(
        first_release_date__isnull=False,        # Исключаем игры без даты
        first_release_date__gt=0,                # Исключаем игры с датой 0 (если это проблема)
        first_release_date__gte=timestamp_threshold,  # Дата >= 60 дней назад
        first_release_date__lte=now_ts,           # Дата <= чем СЕЙЧАС (исключаем будущие)
        total_rating_count__gte=MIN_RATING_COUNT
    ).order_by('-total_rating_count', '-first_release_date')[:9]

    current_timestamp = int(time.time())
    upcoming_games = Game.objects.filter(
        first_release_date__gt=current_timestamp,
        total_rating_count__gt=500
    ).order_by('-total_rating_count')[:10]

    for game in upcoming_games:
        print(game)

    process_games(main_games)
    process_games(recently_trending_small)
    process_games(top_popular_games)
    process_games(recently_trending_big)
    process_games(upcoming_games)

    for game in new_games:
        game.summary = get_first_sentence(game.summary)

    return render(request, 'games_list.html', {
        "favorite_games_ids": favorite_games_ids,
        "new_games": new_games,
        "top_popular_games": top_popular_games,
        "main_games": main_games,
        "recently_trending_small_games": recently_trending_small,
        "recently_trending_big_games": recently_trending_big,
        "upcoming_games": upcoming_games,
    })


def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    user_personal_rating = None
    if request.user.is_authenticated:
        try:
            rating_obj = UserGameRating.objects.get(user=request.user, game=game)
            user_personal_rating = rating_obj.rating
        except UserGameRating.DoesNotExist:
            pass

    similar_games = get_similar_games(game)

    for similar_game in similar_games:
        process_games([similar_game])

    process_games([game])
    process_games(similar_games)

    if game.first_release_date:
        date_obj = datetime.fromtimestamp(game.first_release_date)
        game.release_date = date_obj.strftime('%d %B %Y').lstrip('0')

    comments = game.comments.all()
    comment_count = comments.count()

    game.mini_summary = get_first_sentence(game.summary)

    return render(request, 'game_detail.html', {
        "game": game,
        "similar_games": similar_games,
        "comment_count": comment_count,
        'user_personal_rating': user_personal_rating,
    })


def process_games(games):
    for game in games:
        if game.platforms:
            game_platforms = json.loads(game.platforms) if isinstance(game.platforms, str) else game.platforms
        else:
            game_platforms = []

        game.platform_icons = list(set(get_platform_icon_path(p["name"]) for p in game_platforms if p and "name" in p))

        if game.first_release_date:
            game.release_date = datetime.fromtimestamp(game.first_release_date).strftime('%Y')


def save_game_with_trailer(game_name):
    """Создаёт запись игры и сохраняет трейлер из YouTube API."""
    trailer_id = get_youtube_trailer_with_name(game_name)

    game = Game.objects.create(name=game_name, youtube_trailer=trailer_id)
    return game


def clean_genre_name():
    genre = "Role-playing (RPG)"
    return re.sub(r'.*\((.*?)\)', r'\1', genre)


def get_first_sentence(text):
    if not text:
        return ""
    # Разбиваем текст на предложения по точке, восклицательному и вопросительному знаку
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return sentences[0] if sentences else text


def format_date(timestamp):
    """Возвращает только год из timestamp (игры) или строки (фильмы)"""
    if isinstance(timestamp, int):
        return datetime.fromtimestamp(timestamp).strftime('%Y')
    elif isinstance(timestamp, str) and timestamp:
        try:
            return datetime.strptime(timestamp, '%Y-%m-%d').strftime('%Y')
        except ValueError:
            return timestamp
    return None


def get_similar_games(current_game):
    if hasattr(current_game, 'name') and isinstance(current_game.name, str):
        name = current_game.name
        similar_games = Game.objects.filter(name__icontains=name[:7]).exclude(id=current_game.id)

        # Если похожих фильмов нет, используем поле similar_movies
        if not similar_games.exists():
            # Проверяем, не None ли similar_games, иначе даём пустой список
            similar_games_ids = json.loads(current_game.similar_games) if isinstance(current_game.similar_games, str) else current_game.similar_games or []
            similar_games = Game.objects.filter(id__in=similar_games_ids) if similar_games_ids else Game.objects.none()
    else:
        similar_games = Game.objects.none()

    return similar_games


# ___________________________________________________________________________________________________
# MOVIES
def movies(request):
    genres = Genre.objects.all()

    main_movies = Movie.objects.filter(is_main_movie=True)
    recently_trending_small_movies = Movie.objects.filter(is_recently_trending_small=True)
    recently_trending_big_movies = Movie.objects.filter(is_recently_trending_big=True)

    two_months_ago = date.today() - timedelta(days=60)
    today = date.today()
    new_movies = Movie.objects.filter(release_date__gte=two_months_ago, release_date__lte=today).exclude(release_date__isnull=True).order_by('-release_date')

    upcoming_movies = Movie.objects.filter(release_date__gt=today).exclude(release_date__isnull=True).order_by('release_date')

    top_popular_movies = Movie.objects.filter(vote_count__gt=1000).order_by('-vote_average')[:60]
    best_movies = Movie.objects.filter(vote_average__gt=8, vote_count__gt=1000).order_by('-vote_average')[:50]

    # --- Получаем Аниме-сериалы ---
    anime_series_list = Movie.objects.filter(
        content_type=Movie.CONTENT_TYPE_TV,
        genres__tmdb_id="16",
        country__icontains="JP"
    )

    for movie in main_movies:
        movie.overview = get_first_sentence(movie.overview)

    for movie in new_movies:
        movie.overview = get_first_sentence(movie.overview)

    for movie in upcoming_movies:
        movie.overview = get_first_sentence(movie.overview)

    # Объединение всех фильмов в один список
    all_movies = list(chain(top_popular_movies, main_movies, recently_trending_small_movies,
                            recently_trending_big_movies, new_movies, upcoming_movies, best_movies, anime_series_list))

    process_movies(all_movies)

    return render(request, 'movies_list.html', {
        "top_popular_movies": top_popular_movies,
        "main_movies": main_movies,
        "recently_trending_small_movies": recently_trending_small_movies,
        "recently_trending_big_movies": recently_trending_big_movies,
        "new_movies": new_movies,
        "upcoming_movies": upcoming_movies,
        'anime_series_list': anime_series_list,
        "genres": genres,
        "best_movies": best_movies,
    })


def movie_detail(request, tmdb_id):
    genres = Genre.objects.all()
    actors = Actor.objects.all()
    movie = get_object_or_404(Movie, id=tmdb_id)
    similar_movies = get_similar_movies(movie)

    process_movies(movie)
    for similar_movie in similar_movies:
        process_movies(similar_movie)

    comments = movie.comments.all()
    comment_count = comments.count()

    user_personal_rating = None
    if request.user.is_authenticated:
        try:
            rating_obj = UserMovieRating.objects.get(user=request.user, movie=movie)
            user_personal_rating = rating_obj.rating
        except UserMovieRating.DoesNotExist:
            pass

    return render(request, 'movie_detail.html', {
        "movie": movie,
        "genres": genres,
        "actors": actors,
        "comment_count": comment_count,
        "similar_movies": similar_movies,
        'user_personal_rating': user_personal_rating,
    })


def genre_movies(request, genre_id):
    genre = get_object_or_404(Genre, pk=genre_id)
    movies_in_genre = Movie.objects.filter(genres=genre)

    return render(request, 'genre_movies.html', {'genre': genre, 'movies': movies_in_genre})


def process_movies(movies):
    if not isinstance(movies, list):
        movies = [movies]

    for movie in movies:
        if movie.poster_path:
            movie.full_poster_path = f"https://image.tmdb.org/t/p/w500{movie.poster_path}"  # Создаём новое поле

        if movie.backdrop_path:
            movie.full_backdrop_path = f"https://image.tmdb.org/t/p/w500{movie.backdrop_path}"

        if movie.country:
            movie.country = get_country_abbreviation(movie.country)

        if movie.runtime:
            movie.formatted_runtime = format_runtime(movie.runtime)


def get_similar_movies(current_movie):
    if hasattr(current_movie, 'title') and isinstance(current_movie.title, str):
        title = current_movie.title
        similar_movies = Movie.objects.filter(title__icontains=title[:4]).exclude(id=current_movie.id)

        # Если похожих фильмов нет, используем поле similar_movies
        if not similar_movies.exists():
            similar_movies = current_movie.similar_movies.all()
    else:
        similar_movies = Movie.objects.none()

    return similar_movies


# ___________________________________________________________________________________________________
# BOOKS
def books(request):
    main_books_qs = Book.objects.filter(is_main_book=True)
    recently_trending_small_books = Book.objects.filter(is_recently_trending_small=True)

    try:
        # Для new_books, published_date должно быть DateField или DateTimeField в модели
        # Если это CharField, фильтрация будет некорректной.
        # Предположим, что published_date это DateField или корректно парсится в дату.
        # Если это CharField в формате 'YYYY-MM-DD' или 'YYYY':
        # Тебе нужно будет либо изменить модель, либо использовать Cast или парсинг.
        # Сейчас оставлю как есть, но это потенциальная проблема.
        two_months_ago_str = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        today_str = datetime.now().strftime('%Y-%m-%d')

        # Если published_date это CharField 'YYYY' или 'YYYY-MM-DD'
        # Этот фильтр будет работать только если формат позволяет строковое сравнение,
        # что не всегда надежно для дат. Идеально - иметь DateField.
        new_books_qs = Book.objects.filter(
            published_date__gte=two_months_ago_str[:4], # Берем только год, если формат YYYY
            published_date__lte=today_str[:4]
        ).exclude(published_date__isnull=True).exclude(published_date__exact='').order_by('-published_date')
        # Для DateField было бы:
        # two_months_ago_dt = datetime.now().date() - timedelta(days=180)
        # today_dt = datetime.now().date()
        # new_books_qs = Book.objects.filter(
        #     published_date__gte=two_months_ago_dt,
        #     published_date__lte=today_dt
        # ).exclude(published_date__isnull=True).order_by('-published_date')

    except Exception as e:
        print(f"Error filtering new_books by date: {e}")
        new_books_qs = Book.objects.none()

    # --- ПОЛУЧЕНИЕ САМЫХ ПОПУЛЯРНЫХ КНИГ ---
    popular_books_qs = Book.objects.filter(
        ratings_count__gte=5,
        average_rating__isnull=False
    ).order_by('-ratings_count')
    # --- КОНЕЦ ПОЛУЧЕНИЯ ПОПУЛЯРНЫХ КНИГ ---

    processed_main_books = []
    for book_obj in main_books_qs:
        actions_context = {'current_book': book_obj, 'user': request.user}
        try:
            actions_html = render_to_string('partials/book_actions_for_showcase.html', actions_context)
        except Exception as e:
            actions_html = '<p class="text-danger">Error loading actions.</p>'

        authors_list = []
        if hasattr(book_obj, 'authors') and book_obj.authors:
            if isinstance(book_obj.authors, list):
                authors_list = [str(author) for author in book_obj.authors]

        published_year_val = '----'
        if book_obj.published_date:
            date_str = str(book_obj.published_date).strip()
            if len(date_str) >= 4 and date_str[:4].isdigit():
                published_year_val = date_str[:4]
            elif date_str.isdigit():
                published_year_val = date_str

        cover_url_val = static('imgs/placeholder_book_cover_large.png')
        if book_obj.thumbnail:
            cover_url_val = book_obj.thumbnail
        elif book_obj.custom_photo:
            cover_url_val = book_obj.custom_photo

        processed_main_books.append({
            'id': book_obj.id,
            'google_id': book_obj.google_id,
            'title': book_obj.title[:20] + '...' if len(book_obj.title) > 23 else book_obj.title,
            'authors': authors_list,
            'rating': str(book_obj.mgb_average_rating) if book_obj.mgb_average_rating is not None else '',
            'rating_color': getattr(book_obj, 'rating_color', '#777'),
            'year': str(published_year_val),
            'pages': getattr(book_obj, 'page_count', 0) if getattr(book_obj, 'page_count', 0) else 0, # Если есть поле page_count
            'description': book_obj.description if book_obj.description else "",
            'cover_url': cover_url_val,
            'learn_more_url': reverse('book_detail', args=[book_obj.google_id]) if book_obj.google_id else '#',
            'actions_html': actions_html,
        })

    context_to_render = {
        "recently_trending_small_books": recently_trending_small_books,
        "main_books_for_django": main_books_qs,
        "main_books_js_data": processed_main_books,
        "new_books": new_books_qs,
        "popular_books": popular_books_qs,
    }
    return render(request, 'books_list.html', context_to_render)


def book_detail(request, google_id):
    book = get_object_or_404(Book, google_id=google_id)

    comments = book.comments.all()
    comment_count = comments.count()

    return render(request, 'book_detail.html', {
        "book": book,
        "comment_count": comment_count,
    })


# АНИМЕ
# ---------------------------------------------------------------------------------
def get_anime_series():
    """
    Возвращает QuerySet с аниме-сериалами.
    Аниме-сериал - это TV-шоу с жанром 'Animation' (TMDB Genre ID 16).
    """
    try:
        # Способ 1: Найти жанр "Animation" по его TMDB ID и использовать его объект
        # Это предпочтительнее, если имя жанра может измениться, а ID стабилен.
        animation_genre_obj = Genre.objects.get(tmdb_id=16)
        anime_list = Movie.objects.filter(
            content_type=Movie.CONTENT_TYPE_TV,
            genres=animation_genre_obj
        )

        return anime_list

    except Genre.DoesNotExist:
        # Этот блок выполнится, если жанр с tmdb_id=16 (или указанным именем) не найден в твоей БД.
        # Это означает, что либо он не был загружен, либо ID другой.
        print("Внимание: Жанр 'Animation' (TMDB ID: 16) не найден в базе данных. Невозможно отфильтровать аниме.")
        return Movie.objects.none() # Возвращаем пустой QuerySet


# Чтобы вывести "обычные" сериалы (не аниме):
def get_regular_series():
    """
    Возвращает QuerySet с сериалами, которые НЕ являются аниме.
    """
    try:
        animation_genre_obj = Genre.objects.get(tmdb_id=16)
        regular_tv_list = Movie.objects.filter(
            content_type=Movie.CONTENT_TYPE_TV
        ).exclude( # ИСКЛЮЧАЕМ те, что содержат жанр "Animation"
            genres=animation_genre_obj
        )

        return regular_tv_list

    except Genre.DoesNotExist:
        print("Внимание: Жанр 'Animation' (TMDB ID: 16) не найден. Возвращаю все TV-шоу как 'обычные'.")
        return Movie.objects.filter(content_type=Movie.CONTENT_TYPE_TV)

# Чтобы вывести фильмы-аниме (анимационные фильмы):
def get_anime_movies():
    """
    Возвращает QuerySet с анимационными фильмами.
    """
    try:
        animation_genre_obj = Genre.objects.get(tmdb_id=16)
        anime_movie_list = Movie.objects.filter(
            content_type=Movie.CONTENT_TYPE_MOVIE, # Условие 1: это фильм
            genres=animation_genre_obj             # Условие 2: содержит жанр "Animation"
        )
        return anime_movie_list
    except Genre.DoesNotExist:
        print("Внимание: Жанр 'Animation' (TMDB ID: 16) не найден в базе данных. Невозможно отфильтровать анимационные фильмы.")
        return Movie.objects.none()
