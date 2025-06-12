# users/views.py
import os
import json
import random
import string
import calendar

from mgb_main.utils import get_platform_icon_path
from django.utils import timezone
from datetime import timedelta, datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.urls import reverse
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.apps import apps
from django.db.models import (
    Q, F, OuterRef, Subquery, Min, Max, Count,
    Exists, CharField, Value, Case, When,
    IntegerField, DateField, DateTimeField
)
from django.template.loader import render_to_string
from django.db.models.functions import Greatest, Coalesce, TruncDate

# Импортируем нужные формы и модели
from users.forms import (
    UserLoginForm, UserRegistrationForm, ProfileForm,
    CustomPasswordChangeForm, EmailChangeForm
)
# Импортируем User напрямую, остальные модели можно через apps.get_model
from .models import (
    User, Game, Movie, Book,
    FavoriteGame, FavoriteMovie, FavoriteBook,
    PlayedGame, PlayingGame, DroppedGame,
    WatchedMovie, WatchingMovie, DroppedMovie,
    ReadBook, ReadingBook, DroppedBook,
    Comment,
    UserGameRating, UserMovieRating, UserBookRating
)


from dotenv import load_dotenv

load_dotenv()


# --- АУТЕНТИФИКАЦИЯ И ПРОФИЛЬ ---
def login(request):
    # Остается без изменений
    if request.user.is_authenticated:
        # Лучше редиректить на 'users:profile' или 'index', если есть
        # return HttpResponseRedirect(reverse('index')) # Убедись что 'index' определен глобально
        return HttpResponseRedirect(reverse('users:profile'))  # Пример

    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']  # Лучше брать из cleaned_data
            password = form.cleaned_data['password']
            user = auth.authenticate(request, username=username, password=password) # Передаем request
            if user:
                auth.login(request, user)
                remember_me = request.POST.get("remember_me")
                if not remember_me:
                    request.session.set_expiry(0)
                # return HttpResponseRedirect(reverse('index'))
                return HttpResponseRedirect(reverse('users:profile')) # Пример
            # else: # Добавить обработку неверного логина/пароля
            #     form.add_error(None, "Invalid username or password.")
    else:
        form = UserLoginForm()

    context = {
        'title': 'Login',
        'form': form
    }
    return render(request, 'login.html', context)  # Укажи правильный путь к шаблону


def register(request):
    # Остается без изменений
    if request.user.is_authenticated:
        # return HttpResponseRedirect(reverse('index'))
        return HttpResponseRedirect(reverse('users:profile'))  # Пример

    if request.method == 'POST':
        form = UserRegistrationForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            return HttpResponseRedirect(reverse('users:profile'))
    else:
        form = UserRegistrationForm()
    context = {
        'title': 'Register',
        'form': form,
    }
    return render(request, 'register.html', context)  # Укажи правильный путь


def logout(request):
    # Остается без изменений
    auth.logout(request)
    return redirect(reverse('users:login'))  # Редирект на логин после выхода


def get_user_activity_heatmap_data(user, year):
    """
    Собирает данные об активности пользователя для тепловой карты за указанный год.
    Возвращает словарь: { 'YYYY-MM-DD': count, ... }
    """
    activity_data = {}
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # 1. Оценки (User...Rating модели)
    game_ratings_dates = UserGameRating.objects.filter(
        user=user, updated_at__year=year
    ).annotate(
        activity_date=TruncDate('updated_at', output_field=DateField())
    ).values('activity_date').annotate(count=Count('id')).values('activity_date', 'count')

    movie_ratings_dates = UserMovieRating.objects.filter(
        user=user, updated_at__year=year
    ).annotate(
        activity_date=TruncDate('updated_at', output_field=DateField())
    ).values('activity_date').annotate(count=Count('id')).values('activity_date', 'count')

    book_ratings_dates = UserBookRating.objects.filter(
        user=user, updated_at__year=year
    ).annotate(
        activity_date=TruncDate('updated_at', output_field=DateField())
    ).values('activity_date').annotate(count=Count('id')).values('activity_date', 'count')

    # 2. Отзывы (Comment модель)
    review_dates = user.comments.filter(
        created_at__year=year
    ).annotate(
        activity_date=TruncDate('created_at', output_field=DateField())
    ).values('activity_date').annotate(count=Count('id')).values('activity_date', 'count')

    # 3. Добавление в избранное
    fav_game_dates = FavoriteGame.objects.filter(
        user=user, added_at__year=year
    ).annotate(
        activity_date=TruncDate('added_at', output_field=DateField())
    ).values('activity_date').annotate(count=Count('id')).values('activity_date', 'count')

    fav_movie_dates = FavoriteMovie.objects.filter(
        user=user, added_at__year=year
    ).annotate(
        activity_date=TruncDate('added_at', output_field=DateField())
    ).values('activity_date').annotate(count=Count('id')).values('activity_date', 'count')

    fav_book_dates = FavoriteBook.objects.filter(
        user=user, added_at__year=year
    ).annotate(
        activity_date=TruncDate('added_at', output_field=DateField())
    ).values('activity_date').annotate(count=Count('id')).values('activity_date', 'count')

    all_activities_by_date = {}

    def aggregate_dates(queryset):
        for item in queryset:
            day_str = item['activity_date'].isoformat()
            all_activities_by_date[day_str] = all_activities_by_date.get(day_str, 0) + item['count']

    aggregate_dates(game_ratings_dates)
    aggregate_dates(movie_ratings_dates)
    aggregate_dates(book_ratings_dates)
    aggregate_dates(review_dates)
    aggregate_dates(fav_game_dates)
    aggregate_dates(fav_movie_dates)
    aggregate_dates(fav_book_dates)

    return all_activities_by_date


@login_required
def profile(request):
    user = request.user

    # --- Обработка POST-запроса для обновления профиля ---
    if request.method == "POST":
        new_username_from_post = request.POST.get('username')
        username_changed = False
        if new_username_from_post and new_username_from_post != user.username:
            if not User.objects.filter(username=new_username_from_post).exclude(pk=user.pk).exists():
                user.username = new_username_from_post
                username_changed = True
            else:
                return JsonResponse({
                    "success": False,
                    "errors": {"username": [{"message": "This username is already taken."}]}
                }, status=400)

        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            updated_user_instance = form.save(commit=False)

            if username_changed:
                updated_user_instance.save()
            else:
                updated_user_instance.save()

            response_data = {
                "success": True,
                "username": updated_user_instance.username,
                "bio": updated_user_instance.bio,
                "new_avatar_url": updated_user_instance.avatar.url if 'avatar' in form.changed_data and updated_user_instance.avatar else None,
                "updated_banner_color": updated_user_instance.banner_color or "" 
            }
            return JsonResponse(response_data)
        else:
            errors_json = form.errors.get_json_data()
            if username_changed:
                pass

            return JsonResponse({"success": False, "errors": errors_json}, status=400)

    # --- Логика для GET-запроса (загрузка страницы) ---

    user_movie_rating_subquery = UserMovieRating.objects.filter(
        movie_id=OuterRef('pk'),
        user=user
    ).values('rating')[:1]

    user_game_rating_subquery = UserGameRating.objects.filter(
        game_id=OuterRef('pk'),
        user=user
    ).values('rating')[:1]

    user_book_rating_subquery = UserBookRating.objects.filter(
        book_id=OuterRef('pk'),
        user=user
    ).values('rating')[:1]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.GET.get('fetch_reviews') == 'true':
        review_filter_param = request.GET.get('review_filter', 'all')
        review_sort_param = request.GET.get('review_sort', 'date_added')
        review_search_param = request.GET.get('review_search', '')

        reviews_qs = user.comments.select_related('movie', 'game', 'book').annotate(
            sortable_item_title=Coalesce(
                'movie__title', 'game__name', 'book__title', Value(''), output_field=CharField()
            ),
            item_user_rating=Case(
                When(movie_id__isnull=False, then=Subquery(user_movie_rating_subquery, output_field=IntegerField(null=True))),
                When(game_id__isnull=False, then=Subquery(user_game_rating_subquery, output_field=IntegerField(null=True))),
                When(book_id__isnull=False, then=Subquery(user_book_rating_subquery, output_field=IntegerField(null=True))),
                default=Value(None, output_field=IntegerField(null=True)),
                output_field=IntegerField(null=True)
            )
        )
        if review_filter_param == 'movies': reviews_qs = reviews_qs.filter(movie__isnull=False)
        elif review_filter_param == 'games': reviews_qs = reviews_qs.filter(game__isnull=False)
        elif review_filter_param == 'books': reviews_qs = reviews_qs.filter(book__isnull=False)
        if review_search_param:
            reviews_qs = reviews_qs.filter(
                Q(text__icontains=review_search_param) |
                Q(title__icontains=review_search_param) |
                Q(movie__title__icontains=review_search_param) |
                Q(game__name__icontains=review_search_param) |
                Q(book__title__icontains=review_search_param)
            )
        if review_sort_param == 'title': reviews_qs = reviews_qs.order_by('sortable_item_title')
        elif review_sort_param == 'rating': reviews_qs = reviews_qs.order_by(F('rating').desc(nulls_last=True))
        else: reviews_qs = reviews_qs.order_by('-created_at')
        html_reviews = render_to_string('partials/review_list_items.html', {'reviews': reviews_qs, 'user': request.user})
        return JsonResponse({'html_reviews': html_reviews})

    initial_review_filter = request.GET.get('review_filter', 'all')
    initial_review_sort = request.GET.get('review_sort', 'date_added')
    initial_review_search = request.GET.get('review_search', '')
    user_reviews_initial = user.comments.select_related('movie', 'game', 'book').annotate(
        sortable_item_title=Coalesce('movie__title', 'game__name', 'book__title', Value(''), output_field=CharField()),
        item_user_rating=Case(
            When(movie_id__isnull=False, then=Subquery(user_movie_rating_subquery, output_field=IntegerField(null=True))),
            When(game_id__isnull=False, then=Subquery(user_game_rating_subquery, output_field=IntegerField(null=True))),
            When(book_id__isnull=False, then=Subquery(user_book_rating_subquery, output_field=IntegerField(null=True))),
            default=Value(None, output_field=IntegerField(null=True)),
            output_field=IntegerField(null=True)
        )
    )
    if initial_review_filter == 'movies': user_reviews_initial = user_reviews_initial.filter(movie__isnull=False)
    elif initial_review_filter == 'games': user_reviews_initial = user_reviews_initial.filter(game__isnull=False)
    elif initial_review_filter == 'books': user_reviews_initial = user_reviews_initial.filter(book__isnull=False)
    if initial_review_search:
        user_reviews_initial = user_reviews_initial.filter(
            Q(text__icontains=initial_review_search) | Q(title__icontains=initial_review_search) |
            Q(movie__title__icontains=initial_review_search) | Q(game__name__icontains=initial_review_search) |
            Q(book__title__icontains=initial_review_search)
        )
    if initial_review_sort == 'title': user_reviews_initial = user_reviews_initial.order_by('sortable_item_title')
    elif initial_review_sort == 'rating': user_reviews_initial = user_reviews_initial.order_by(F('rating').desc(nulls_last=True))
    else: user_reviews_initial = user_reviews_initial.order_by('-created_at')

    all_user_reviews_for_stats = user.comments.all()
    total_reviews_count_stat = all_user_reviews_for_stats.count()
    first_review_date_stat, last_review_date_stat, reviews_per_month_stat = None, None, 0
    if total_reviews_count_stat > 0:
        review_dates_agg = all_user_reviews_for_stats.aggregate(first_created=Min('created_at'), last_created=Max('created_at'))
        first_review_date_stat, last_review_date_stat = review_dates_agg['first_created'], review_dates_agg['last_created']
        if first_review_date_stat:
            start_period, end_period = first_review_date_stat, timezone.now()
            num_months_active = (end_period.year - start_period.year) * 12 + (end_period.month - start_period.month) + 1
            num_months_active = max(1, num_months_active)
            average_reviews = total_reviews_count_stat / num_months_active
            reviews_per_month_stat = round(average_reviews)
            if reviews_per_month_stat == 0 and total_reviews_count_stat > 0: reviews_per_month_stat = 1
            elif reviews_per_month_stat < 0: reviews_per_month_stat = 0

    current_year = date.today().year
    selected_year_str = request.GET.get('activity_year', str(current_year))
    try: selected_year = int(selected_year_str)
    except ValueError: selected_year = current_year
    user_activity_heatmap = get_user_activity_heatmap_data(user, selected_year)
    min_year_activity = user.date_joined.year if user.date_joined else current_year - 5
    available_years = list(range(min_year_activity, current_year + 1))
    available_years.reverse()

    total_rates = UserGameRating.objects.filter(user=user).count() + UserMovieRating.objects.filter(user=user).count() + UserBookRating.objects.filter(user=user).count()
    total_reviews = user.comments.count()
    total_favorites = FavoriteGame.objects.filter(user=user).count() + FavoriteMovie.objects.filter(user=user).count() + FavoriteBook.objects.filter(user=user).count()
    game_count, movie_count, book_count = len(get_combined_user_game_ids(user)), len(get_combined_user_movie_ids(user)), len(get_combined_user_book_ids(user))

    latest_favorite_items_overview = []
    fav_games_qs = FavoriteGame.objects.filter(user=user).select_related('game').annotate(item_user_rating=Subquery(UserGameRating.objects.filter(game=OuterRef('game_id'), user=user).values('rating')[:1], output_field=IntegerField(null=True))).order_by('-added_at')
    fav_movies_qs = FavoriteMovie.objects.filter(user=user).select_related('movie').prefetch_related('movie__genres').annotate(item_user_rating=Subquery(UserMovieRating.objects.filter(movie=OuterRef('movie_id'), user=user).values('rating')[:1], output_field=IntegerField(null=True))).order_by('-added_at')
    fav_books_qs = FavoriteBook.objects.filter(user=user).select_related('book').annotate(item_user_rating=Subquery(UserBookRating.objects.filter(book=OuterRef('book_id'), user=user).values('rating')[:1], output_field=IntegerField(null=True))).order_by('-added_at')

    def get_item_detail_url(item_type, item_obj_id, item_obj=None): # item_obj опционален, если ID уже известен
        if item_type == 'game': return reverse('game_detail', kwargs={'game_id': item_obj_id})
        elif item_type == 'movie': return reverse('movie_detail', kwargs={'tmdb_id': item_obj_id})
        elif item_type == 'book': return reverse('book_detail', kwargs={'google_id': item_obj_id})
        return "#"

    for fg in fav_games_qs:
        game_obj = fg.game
        genres_list = [genre for genre in (game_obj.genres if isinstance(game_obj.genres, list) else []) if isinstance(genre, str)][:2]
        release_year = None
        if game_obj.first_release_date:
            try:
                ts = game_obj.first_release_date
                if isinstance(ts, (int, float)) and ts > 4000000000: ts /= 1000
                if isinstance(ts, (int, float)): release_year = str(datetime.fromtimestamp(ts).year)
                elif isinstance(ts, str) and ts.isdigit() and len(ts) == 4: release_year = ts
            except: pass
        latest_favorite_items_overview.append({'id': f"game-{game_obj.id}", 'type': 'game', 'added_at': fg.added_at, 'title': game_obj.name, 'image_url': game_obj.cover_url, 'detail_url': get_item_detail_url('game', game_obj.id), 'user_rating': fg.item_user_rating, 'info_line_1': ", ".join(genres_list), 'info_line_2': release_year})

    for fm in fav_movies_qs:
        movie_obj = fm.movie
        genres_list = [genre.name for genre in movie_obj.genres.all()[:2]]
        release_year_val = movie_obj.release_date.year if movie_obj.release_date else None
        latest_favorite_items_overview.append({'id': f"movie-{movie_obj.id}", 'type': 'movie', 'added_at': fm.added_at, 'title': movie_obj.title, 'image_url': movie_obj.poster_path, 'detail_url': get_item_detail_url('movie', movie_obj.tmdb_id), 'user_rating': fm.item_user_rating, 'info_line_1': ", ".join(genres_list), 'info_line_2': str(release_year_val) if release_year_val else None})

    for fb in fav_books_qs:
        book_obj = fb.book
        authors_list = (book_obj.authors if isinstance(book_obj.authors, list) else [])[:2]
        release_year_val = None
        if book_obj.published_date:
            try:
                temp_year = str(book_obj.published_date).split('-')[0]
                if len(temp_year) == 4 and temp_year.isdigit(): release_year_val = temp_year
            except: pass
        latest_favorite_items_overview.append({'id': f"book-{book_obj.id}", 'type': 'book', 'added_at': fb.added_at, 'title': book_obj.title, 'image_url': book_obj.thumbnail, 'detail_url': get_item_detail_url('book', book_obj.google_id), 'user_rating': fb.item_user_rating, 'info_line_1': ", ".join(authors_list), 'info_line_2': release_year_val})

    latest_favorite_items_overview.sort(key=lambda x: x['added_at'], reverse=True)
    total_favorite_count = len(latest_favorite_items_overview)

    form = ProfileForm(instance=user)
    profile_form_for_template = ProfileForm(instance=user)

    latest_games, latest_movies, latest_books = get_sorted_user_games(user)[:3], get_sorted_user_movies(user)[:3], get_sorted_user_books(user)[:3] # Сократил до 3 для Library

    latest_activity_item = None
    all_potential_activities = []

    def add_activity(item_obj, type_str, verb, timestamp, image_attr, title_attr, id_for_url, id_field_name):
        if item_obj and timestamp:
            image_url_val = getattr(item_obj, image_attr, None)
            title_val = getattr(item_obj, title_attr, 'N/A')
            all_potential_activities.append({
                'type': type_str, 'activity_verb': verb, 'timestamp': timestamp,
                'image_url': image_url_val, 'title': title_val,
                'detail_url': get_item_detail_url(type_str, getattr(item_obj, id_field_name))
            })

    activity_models_config = [
        (FavoriteGame, 'game', 'Added to favorites', 'added_at', 'cover_url', 'name', 'id'),
        (FavoriteMovie, 'movie', 'Added to favorites', 'added_at', 'poster_path', 'title', 'tmdb_id'),
        (FavoriteBook, 'book', 'Added to favorites', 'added_at', 'thumbnail', 'title', 'google_id'),

        (PlayedGame, 'game', 'Started played', 'added_at', 'cover_url', 'name', 'id'),
        (WatchedMovie, 'movie', 'Started watched', 'added_at', 'poster_path', 'title', 'tmdb_id'),
        (ReadBook, 'movie', 'Started readed', 'added_at', 'thumbnail', 'title', 'google_id'),

        (PlayingGame, 'game', 'Started playing', 'added_at', 'cover_url', 'name', 'id'),
        (WatchingMovie, 'movie', 'Started watching', 'added_at', 'poster_path', 'title', 'tmdb_id'),
        (ReadingBook, 'movie', 'Started reading', 'added_at', 'thumbnail', 'title', 'google_id'),

        (DroppedGame, 'game', 'Dropped playing', 'added_at', 'cover_url', 'name', 'id'),
        (DroppedMovie, 'movie', 'Dropped watching', 'added_at', 'poster_path', 'title', 'tmdb_id'),
        (DroppedBook, 'movie', 'Dropped reading', 'added_at', 'thumbnail', 'title', 'google_id'),
    ]

    for Model, type_str, verb, time_field, img_attr, title_attr, id_field in activity_models_config:
        latest_item_rel = Model.objects.filter(user=user).select_related(type_str).order_by(f'-{time_field}').first()
        if latest_item_rel:
            item_obj = getattr(latest_item_rel, type_str)
            add_activity(item_obj, type_str, verb, getattr(latest_item_rel, time_field), img_attr, title_attr, getattr(item_obj, id_field), id_field)

    # Отдельно для отзывов и рейтингов, т.к. структура немного другая
    latest_review = user.comments.select_related('movie', 'game', 'book').order_by('-created_at').first()
    if latest_review:
        item_for_review = latest_review.movie or latest_review.game or latest_review.book
        if item_for_review:
            type_name = 'movie' if latest_review.movie else 'game' if latest_review.game else 'book'
            img_attr = 'poster_path' if type_name == 'movie' else 'cover_url' if type_name == 'game' else 'thumbnail'
            title_attr = 'title' if type_name in ['movie', 'book'] else 'name'
            id_field = 'tmdb_id' if type_name == 'movie' else 'id' if type_name == 'game' else 'google_id'
            add_activity(item_for_review, type_name, 'Reviewed', latest_review.created_at, img_attr, title_attr, getattr(item_for_review, id_field), id_field)
    
    # Рейтинги (по одному примеру, остальные аналогично)
    latest_game_rating = UserGameRating.objects.filter(user=user).select_related('game').order_by('-updated_at').first()
    if latest_game_rating:
        add_activity(latest_game_rating.game, 'game', f'Rated {latest_game_rating.rating}/10', latest_game_rating.updated_at, 'cover_url', 'name', latest_game_rating.game.id, 'id')
    latest_movie_rating = UserMovieRating.objects.filter(user=user).select_related('movie').order_by('-updated_at').first()
    if latest_movie_rating:
         add_activity(latest_movie_rating.movie, 'movie', f'Rated {latest_movie_rating.rating}/10', latest_movie_rating.updated_at, 'poster_path', 'title', latest_movie_rating.movie.tmdb_id, 'tmdb_id')
    latest_book_rating = UserBookRating.objects.filter(user=user).select_related('book').order_by('-updated_at').first()
    if latest_book_rating:
         add_activity(latest_book_rating.book, 'book', f'Rated {latest_book_rating.rating}/10', latest_book_rating.updated_at, 'thumbnail', 'title', latest_book_rating.book.google_id, 'google_id')


    if all_potential_activities:
        all_potential_activities.sort(key=lambda x: x['timestamp'] or timezone.make_aware(datetime.min, timezone.utc), reverse=True) # Убедимся, что None обрабатывается
        latest_activity_item = all_potential_activities[0] if all_potential_activities else None

    context = {
        "profile": user, # Передаем инстанс User как 'profile' для шаблона
        'user_reviews': user_reviews_initial,
        'current_review_filter': initial_review_filter,
        'current_review_sort': initial_review_sort,
        'current_review_search': initial_review_search, # Добавил для поля поиска в Reviews
        "latest_movies": latest_movies,
        "latest_games": latest_games,
        "latest_books": latest_books,
        'stats_total_rates': total_rates,
        'stats_total_favorites': total_favorites,
        "movie_count": movie_count,
        "game_count": game_count,
        "book_count": book_count,
        'total_reviews_count_stat': total_reviews_count_stat,
        'first_review_date_stat': first_review_date_stat,
        'last_review_date_stat': last_review_date_stat,
        'reviews_per_month_stat': reviews_per_month_stat,
        'latest_activity_item': latest_activity_item,
        'user_activity_heatmap_data': json.dumps(user_activity_heatmap),
        'selected_activity_year': selected_year,
        'available_activity_years': available_years,
        'current_year_for_activity': current_year,
        'latest_favorite_items_overview': latest_favorite_items_overview,
        'total_favorite_count': total_favorite_count,
        'form': profile_form_for_template,
    }
    return render(request, "profile.html", context)


@login_required
def profile_settings(request):
    password_form = CustomPasswordChangeForm(user=request.user)
    email_form = EmailChangeForm(instance=request.user)

    if request.method == 'POST':
        # Определяем, какая форма была отправлена, по имени кнопки
        if 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('profile_settings')
            else:
                messages.error(request, 'Please correct the errors below in the password form.')

        elif 'change_email' in request.POST:
            email_form = EmailChangeForm(data=request.POST, instance=request.user)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, 'Your email address was successfully updated!')
                return redirect('profile_settings')
            else:
                messages.error(request, 'Please correct the errors below in the email form.')

        if 'change_password' in request.POST and not password_form.is_valid():
            email_form = EmailChangeForm(instance=request.user)
        elif 'change_email' in request.POST and not email_form.is_valid():
            password_form = CustomPasswordChangeForm(user=request.user)
    context = {
        'password_form': password_form,
        'email_form': email_form,
        'profile': request.user
    }
    return render(request, 'settings.html', context)


@login_required
def profile_history(request):
    user = request.user
    all_activities = []

    # 1. Собираем оценки
    game_ratings = UserGameRating.objects.filter(user=user).select_related('game').order_by('-updated_at')
    for gr in game_ratings:
        all_activities.append({
            'timestamp': gr.updated_at,
            'type': 'rated',
            'verb': f'Rated {gr.rating}',
            'content_object': gr.game,
            'content_type_str': 'game',
            'title': gr.game.name,
            'image_url': gr.game.cover_url, # Или custom_photo
            'detail_url': reverse('game_detail', args=[gr.game.id]), # Убедись, что game_detail использует id/pk
        })

    movie_ratings = UserMovieRating.objects.filter(user=user).select_related('movie').order_by('-updated_at')
    for mr in movie_ratings:
        all_activities.append({
            'timestamp': mr.updated_at,
            'type': 'rated',
            'verb': f'Rated {mr.rating}',
            'content_object': mr.movie,
            'content_type_str': 'movie',
            'title': mr.movie.title,
            'image_url': mr.movie.poster_path, # Это относительный путь, нужно будет добавить префикс TMDB
            'detail_url': reverse('movie_detail', args=[mr.movie.tmdb_id]), # Использует tmdb_id
        })

    book_ratings = UserBookRating.objects.filter(user=user).select_related('book').order_by('-updated_at')
    for br in book_ratings:
        all_activities.append({
            'timestamp': br.updated_at,
            'type': 'rated',
            'verb': f'Rated {br.rating}',
            'content_object': br.book,
            'content_type_str': 'book',
            'title': br.book.title,
            'image_url': br.book.thumbnail, # Или custom_photo
            'detail_url': reverse('book_detail', args=[br.book.google_id]), # Использует google_id
        })

    # 2. Собираем добавление в избранное
    fav_games = FavoriteGame.objects.filter(user=user).select_related('game').order_by('-added_at')
    for fg in fav_games:
        all_activities.append({
            'timestamp': fg.added_at,
            'type': 'favorited',
            'verb': 'Added to favorites',
            'content_object': fg.game,
            'content_type_str': 'game',
            'title': fg.game.name,
            'image_url': fg.game.cover_url,
            'detail_url': reverse('game_detail', args=[fg.game.id]),
        })
    # Аналогично для FavoriteMovie и FavoriteBook
    fav_movies = FavoriteMovie.objects.filter(user=user).select_related('movie').order_by('-added_at')
    for fm in fav_movies:
        all_activities.append({
            'timestamp': fm.added_at,
            'type': 'favorited',
            'verb': 'Added to favorites',
            'content_object': fm.movie,
            'content_type_str': 'movie',
            'title': fm.movie.title,
            'image_url': fm.movie.poster_path,
            'detail_url': reverse('movie_detail', args=[fm.movie.tmdb_id]),
        })
    fav_books = FavoriteBook.objects.filter(user=user).select_related('book').order_by('-added_at')
    for fb in fav_books:
        all_activities.append({
            'timestamp': fb.added_at,
            'type': 'favorited',
            'verb': 'Added to favorites',
            'content_object': fb.book,
            'content_type_str': 'book',
            'title': fb.book.title,
            'image_url': fb.book.thumbnail,
            'detail_url': reverse('book_detail', args=[fb.book.google_id]),
        })


    # 3. Собираем статусы (Played, Watched, Read и т.д.)
    played_games = PlayedGame.objects.filter(user=user).select_related('game').order_by('-added_at')
    for pg in played_games:
        all_activities.append({
            'timestamp': pg.added_at,
            'type': 'status_changed',
            'verb': 'Finished playing', # Или "Marked as Played"
            'content_object': pg.game,
            'content_type_str': 'game',
            'title': pg.game.name,
            'image_url': pg.game.cover_url,
            'detail_url': reverse('game_detail', args=[pg.game.id]),
        })

    reading_books = ReadingBook.objects.filter(user=user).select_related('book').order_by('-added_at')
    for rb_reading in reading_books:
        all_activities.append({
            'timestamp': rb_reading.added_at,
            'type': 'status_changed',
            'verb': 'Started reading',
            'content_object': rb_reading.book,
            'content_type_str': 'book',
            'title': rb_reading.book.title,
            'image_url': rb_reading.book.thumbnail,
            'detail_url': reverse('book_detail', args=[rb_reading.book.google_id]),
        })

    # 4. Собираем комментарии/отзывы
    comments = Comment.objects.filter(user=user).select_related('game', 'movie', 'book').order_by('-created_at')
    for comment in comments:
        item = comment.game or comment.movie or comment.book
        item_title = "Unknown Item"
        item_image_url = None
        item_detail_url = "#"
        item_content_type = "unknown"

        if comment.game:
            item_title = comment.game.name
            item_image_url = comment.game.cover_url
            item_detail_url = reverse('game_detail', args=[comment.game.id])
            item_content_type = "game"
        elif comment.movie:
            item_title = comment.movie.title
            item_image_url = comment.movie.poster_path
            item_detail_url = reverse('movie_detail', args=[comment.movie.tmdb_id])
            item_content_type = "movie"
        elif comment.book:
            item_title = comment.book.title
            item_image_url = comment.book.thumbnail
            item_detail_url = reverse('book_detail', args=[comment.book.google_id])
            item_content_type = "book"

        all_activities.append({
            'timestamp': comment.created_at,
            'type': 'commented',
            'verb': f'Commented on "{comment.title}"',
            'content_object': item,
            'content_type_str': item_content_type,
            'title': item_title,
            'image_url': item_image_url,
            'detail_url': item_detail_url,
            'comment_content': comment.content[:150] + '...' if len(comment.content) > 150 else comment.content, # Превью комментария
        })

    # Сортируем все активности по дате/времени в обратном хронологическом порядке
    all_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    total_activities_count = len(all_activities)

    # Пагинация
    paginator = Paginator(all_activities, 20)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'profile_user': user,
        'activities_page': page_obj,
        'page_title': f"{user.username}'s History",
        'total_activities_count': total_activities_count,
        'TMDB_IMAGE_BASE_URL': "https://image.tmdb.org/t/p/",
        'POSTER_SIZE_FOR_HISTORY': "w92"
    }
    return render(request, 'users/profile_history.html', context)


# --- УНИВЕРСАЛЬНОЕ ИЗБРАННОЕ ---
# -----------------------------------------------------------------------------------------------------------------------------
@login_required
def toggle_favorite_item(request, content_type, object_id):
    """
    Универсальная view для добавления/удаления любого типа контента в/из избранного.
    """
    user = request.user

    # 1. Получаем конфигурацию для данного типа контента из модели User
    config = User.FAVORITE_CONFIG.get(content_type)
    if not config:
        return JsonResponse({'error': 'Invalid content type'}, status=400)

    try:
        # 2. Получаем класс модели контента (Game, Movie, Book)
        ContentModel = apps.get_model(config['content_model'])
        id_field = config['id_field'] # Поле, по которому ищем ('id', 'tmdb_id', 'google_id')

        # 3. Находим сам объект контента по его уникальному ID
        # Используем **kwargs для динамической передачи имени поля ID
        lookup_kwargs = {id_field: object_id}
        item = get_object_or_404(ContentModel, **lookup_kwargs)

    except LookupError: # Ошибка, если модель не найдена в apps.get_model
        return JsonResponse({'error': f"Model '{config['content_model']}' not found."}, status=500)
    except Http404: # Ошибка, если get_object_or_404 не нашел объект
        return JsonResponse({'error': f'{content_type.capitalize()} with {id_field} {object_id} not found.'}, status=404)
    except ValueError: # Ошибка, если object_id не может быть приведен к типу поля id_field (например, строка для int)
        return JsonResponse({'error': f'Invalid ID format for {id_field}: {object_id}'}, status=400)


# 4. Вызываем универсальный метод пользователя toggle_favorite
    try:
        is_now_favorite = user.toggle_favorite(item)
    except TypeError as e:
        # Ошибка, если тип item не настроен в FAVORITE_CONFIG (не должно случиться здесь)
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        # Другие возможные ошибки БД
        return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)


# 5. Возвращаем новое состояние в JSON
    return JsonResponse({
        'is_favorite': is_now_favorite,
        'content_type': content_type,
        'object_id': object_id  # Возвращаем исходный ID
    })


def get_combined_user_movie_ids(user):
    """Возвращает множество ID фильмов, добавленных пользователем в избранное или любой статус."""
    favorite_ids = set(FavoriteMovie.objects.filter(user=user).values_list('movie_id', flat=True))
    watched_ids = set(WatchedMovie.objects.filter(user=user).values_list('movie_id', flat=True))
    watching_ids = set(WatchingMovie.objects.filter(user=user).values_list('movie_id', flat=True))
    dropped_ids = set(DroppedMovie.objects.filter(user=user).values_list('movie_id', flat=True))
    return favorite_ids.union(watched_ids, watching_ids, dropped_ids)


def get_combined_user_game_ids(user):
    """Возвращает множество ID игр, добавленных пользователем в избранное или любой статус."""
    favorite_ids = set(FavoriteGame.objects.filter(user=user).values_list('game_id', flat=True))
    played_ids = set(PlayedGame.objects.filter(user=user).values_list('game_id', flat=True))
    playing_ids = set(PlayingGame.objects.filter(user=user).values_list('game_id', flat=True))
    dropped_ids = set(DroppedGame.objects.filter(user=user).values_list('game_id', flat=True))
    # Объединяем все ID
    return favorite_ids.union(played_ids, playing_ids, dropped_ids)


def get_combined_user_book_ids(user):
    """Возвращает множество ID книг, добавленных пользователем в избранное или любой статус."""
    favorite_ids = set(FavoriteBook.objects.filter(user=user).values_list('book_id', flat=True))
    read_ids = set(ReadBook.objects.filter(user=user).values_list('book_id', flat=True))
    reading_ids = set(ReadingBook.objects.filter(user=user).values_list('book_id', flat=True))
    dropped_ids = set(DroppedBook.objects.filter(user=user).values_list('book_id', flat=True))
    return favorite_ids.union(read_ids, reading_ids, dropped_ids)


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ ОТСОРТИРОВАННЫХ СПИСКОВ ---
# -----------------------------------------------------------------------------------------------------------------------------
def get_sorted_user_movies(user):
    combined_movie_ids = get_combined_user_movie_ids(user)
    if not combined_movie_ids:
        return Movie.objects.none()

    latest_fav = FavoriteMovie.objects.filter(movie=OuterRef('pk'), user=user).order_by('-added_at')
    latest_watched = WatchedMovie.objects.filter(movie=OuterRef('pk'), user=user).order_by('-added_at')
    latest_watching = WatchingMovie.objects.filter(movie=OuterRef('pk'), user=user).order_by('-added_at')
    latest_dropped = DroppedMovie.objects.filter(movie=OuterRef('pk'), user=user).order_by('-added_at')

    user_rating_subquery = UserMovieRating.objects.filter(
        movie=OuterRef('pk'), user=user
    ).values('rating')[:1]

    return Movie.objects.filter(pk__in=list(combined_movie_ids)).annotate(
        fav_date=Subquery(latest_fav.values('added_at')[:1]),
        watched_date=Subquery(latest_watched.values('added_at')[:1]),
        watching_date=Subquery(latest_watching.values('added_at')[:1]),
        dropped_date=Subquery(latest_dropped.values('added_at')[:1]),
        latest_interaction_date=Greatest(
            F('fav_date'), F('watched_date'), F('watching_date'), F('dropped_date'),
            output_field=DateTimeField(null=True)
        ),
        user_rating=Subquery(user_rating_subquery), # Если есть рейтинг для фильмов
        is_favorite_for_user=Exists(FavoriteMovie.objects.filter(movie=OuterRef('pk'), user=user)),
        is_watched_for_user=Exists(WatchedMovie.objects.filter(movie=OuterRef('pk'), user=user)),
        is_watching_for_user=Exists(WatchingMovie.objects.filter(movie=OuterRef('pk'), user=user)),
        is_dropped_for_user=Exists(DroppedMovie.objects.filter(movie=OuterRef('pk'), user=user)),
            ).prefetch_related(
            'genres'
    ).order_by(F('latest_interaction_date').desc(nulls_last=True), '-pk')


def get_sorted_user_games(user):
    """
    Возвращает QuerySet игр пользователя, отсортированный по последней дате взаимодействия,
    с аннотациями для каждого статуса.
    """
    combined_game_ids = get_combined_user_game_ids(user)
    if not combined_game_ids:
        return Game.objects.none()

    

    latest_fav = FavoriteGame.objects.filter(game=OuterRef('pk'), user=user).order_by('-added_at')
    latest_played = PlayedGame.objects.filter(game=OuterRef('pk'), user=user).order_by('-added_at')
    latest_playing = PlayingGame.objects.filter(game=OuterRef('pk'), user=user).order_by('-added_at')
    latest_dropped = DroppedGame.objects.filter(game=OuterRef('pk'), user=user).order_by('-added_at')

    user_rating_subquery = UserGameRating.objects.filter(
        game=OuterRef('pk'),
        user=user
    ).values('rating')[:1]

    return Game.objects.filter(pk__in=list(combined_game_ids)).annotate(
        fav_date=Subquery(latest_fav.values('added_at')[:1]),
        played_date=Subquery(latest_played.values('added_at')[:1]),
        playing_date=Subquery(latest_playing.values('added_at')[:1]),
        dropped_date=Subquery(latest_dropped.values('added_at')[:1]),
        latest_interaction_date=Greatest(
            F('fav_date'), F('played_date'), F('playing_date'), F('dropped_date'),
            output_field=DateTimeField(null=True)
        ),
        user_rating=Subquery(user_rating_subquery),
        # --- НОВЫЕ АННОТАЦИИ ДЛЯ СТАТУСОВ ---
        is_favorite_for_user=Exists(FavoriteGame.objects.filter(game=OuterRef('pk'), user=user)),
        is_played_for_user=Exists(PlayedGame.objects.filter(game=OuterRef('pk'), user=user)),
        is_playing_for_user=Exists(PlayingGame.objects.filter(game=OuterRef('pk'), user=user)),
        is_dropped_for_user=Exists(DroppedGame.objects.filter(game=OuterRef('pk'), user=user)),
    ).order_by(F('latest_interaction_date').desc(nulls_last=True), '-pk')


def get_sorted_user_books(user):
    combined_book_ids = get_combined_user_book_ids(user)
    if not combined_book_ids:
        return Book.objects.none()

    latest_fav = FavoriteBook.objects.filter(book=OuterRef('pk'), user=user).order_by('-added_at')
    latest_read = ReadBook.objects.filter(book=OuterRef('pk'), user=user).order_by('-added_at')
    latest_reading = ReadingBook.objects.filter(book=OuterRef('pk'), user=user).order_by('-added_at')
    latest_dropped = DroppedBook.objects.filter(book=OuterRef('pk'), user=user).order_by('-added_at')

    user_rating_subquery = UserBookRating.objects.filter(
        book=OuterRef('pk'), user=user
    ).values('rating')[:1]

    return Book.objects.filter(pk__in=list(combined_book_ids)).annotate(
        fav_date=Subquery(latest_fav.values('added_at')[:1]),
        read_date=Subquery(latest_read.values('added_at')[:1]),
        reading_date=Subquery(latest_reading.values('added_at')[:1]),
        dropped_date=Subquery(latest_dropped.values('added_at')[:1]),
        latest_interaction_date=Greatest(
            F('fav_date'), F('read_date'), F('reading_date'), F('dropped_date'),
            output_field=DateTimeField(null=True)
        ),
        user_rating=Subquery(user_rating_subquery), # Если есть рейтинг для книг
        is_favorite_for_user=Exists(FavoriteBook.objects.filter(book=OuterRef('pk'), user=user)),
        is_read_for_user=Exists(ReadBook.objects.filter(book=OuterRef('pk'), user=user)),
        is_reading_for_user=Exists(ReadingBook.objects.filter(book=OuterRef('pk'), user=user)),
        is_dropped_for_user=Exists(DroppedBook.objects.filter(book=OuterRef('pk'), user=user)),
    ).order_by(F('latest_interaction_date').desc(nulls_last=True), '-pk')


# --- VIEWS ДЛЯ ОТОБРАЖЕНИЯ ОБЪЕДИНЕННЫХ СПИСКОВ ---
# -----------------------------------------------------------------------------------------------------------------------
def apply_sorting_to_queryset(queryset, sort_by_param_str, field_map):
    """
    Применяет сортировку к QuerySet на основе строки параметра и карты полей.
    field_map: {'ключ_сортировки_из_dropdown': 'поле_в_модели'}
    """
    sort_key = sort_by_param_str
    direction = '' # desc по умолчанию для date_added и rating, asc для title

    if '_asc' in sort_by_param_str:
        sort_key = sort_by_param_str.replace('_asc', '')
        direction = 'asc'
    elif '_desc' in sort_by_param_str:
        sort_key = sort_by_param_str.replace('_desc', '')
        direction = 'desc'

    # Устанавливаем направление по умолчанию, если оно не задано явно
    if not direction:
        if sort_key == 'title' or sort_key == 'name': # 'name' для игр
            direction = 'asc'
        else:
            direction = 'desc'

    if sort_key in field_map:
        actual_sort_field = field_map[sort_key]
        if direction == 'asc':
            # Для текстовых полей F() не нужен, для остальных nulls_last/first полезно
            if actual_sort_field in ['title', 'name']:
                return queryset.order_by(actual_sort_field)
            else:
                return queryset.order_by(F(actual_sort_field).asc(nulls_last=True))
        elif direction == 'desc':
            if actual_sort_field in ['title', 'name']:
                return queryset.order_by(f'-{actual_sort_field}')
            else:
                return queryset.order_by(F(actual_sort_field).desc(nulls_last=True))

    # Сортировка по умолчанию, если sort_key не найден (например, 'date_added')
    default_sort_field = field_map.get('date_added', 'latest_interaction_date') # Фоллбэк, если 'date_added' нет
    return queryset.order_by(F(default_sort_field).desc(nulls_last=True))


@login_required
def favorite_movies_list(request):
    user = request.user
    base_queryset = get_sorted_user_movies(user)

    status_filter_key = request.GET.get('status_filter', 'all')
    sort_by_param = request.GET.get('sort_by', 'date_added_desc') 
    current_view_mode_id = request.GET.get('view_mode', 'view-grid')

    current_content_type_slug = 'movies'
    content_type_name_display = 'Movies'
    default_item_card_template = 'partials/movie_card.html'
    tierlist_item_card_template = 'partials/tierlist_item_card.html'
    showcase_item_template_path = 'partials/showcase_movie_cell.html'

    # Подготовка данных для тирлиста
    unrated_items_for_tierlist = []
    rated_items_by_tier = {i: [] for i in range(1, 11)}
    for item in base_queryset:
        rating = getattr(item, 'user_rating', None)
        if rating is not None and 1 <= rating <= 10:
            rated_items_by_tier[int(rating)].append(item)
        else:
            unrated_items_for_tierlist.append(item)

    # Модели статусов для фильмов
    status_models_map = {
        'status1': WatchedMovie, 'status2': WatchingMovie,
        'status3': DroppedMovie, 'wishlist': FavoriteMovie,
    }
    status_model_id_field = 'movie_id'

    # Фильтрация
    items_processed = base_queryset
    items_to_render_for_list_detailed = base_queryset

    if current_view_mode_id == 'view-grid' and status_filter_key != 'all' and status_filter_key in status_models_map:
        StatusModel = status_models_map[status_filter_key]
        status_item_ids = StatusModel.objects.filter(user=user).values_list(status_model_id_field, flat=True)
        items_processed = base_queryset.filter(pk__in=list(status_item_ids))

    if current_view_mode_id != 'view-grid':
        if status_filter_key != 'all' and status_filter_key in status_models_map:
            StatusModel = status_models_map[status_filter_key]
            status_item_ids = StatusModel.objects.filter(user=user).values_list(status_model_id_field, flat=True)
            items_to_render_for_list_detailed = base_queryset.filter(pk__in=list(status_item_ids))

    # Сортировка
    sort_field_map = {
        'date_added': 'latest_interaction_date',
        'rating': 'user_rating',
        'title': 'title', 
    }
    if base_queryset.exists():
        items_processed = apply_sorting_to_queryset(items_processed, sort_by_param, sort_field_map)
        items_to_render_for_list_detailed = apply_sorting_to_queryset(items_to_render_for_list_detailed, sort_by_param, sort_field_map)

    # Статистика
    stats = {
        'total': base_queryset.count(),
        'favourite': FavoriteMovie.objects.filter(user=user).count(),
        'status1_label': 'Watched', 'status1_count': WatchedMovie.objects.filter(user=user).count(),
        'status2_label': 'Watching', 'status2_count': WatchingMovie.objects.filter(user=user).count(),
        'status3_label': 'Dropped', 'status3_count': DroppedMovie.objects.filter(user=user).count(),
        'wishlist_label': 'Wishlist',
    }
    stats['wishlist_count'] = stats['favourite']

    grid_status_config = [
        {'key': 'status1', 'label': stats['status1_label'], 'annotation_field': 'is_watched_for_user', 'chip_class': 'watched-chip'},
        {'key': 'status2', 'label': stats['status2_label'], 'annotation_field': 'is_watching_for_user', 'chip_class': 'watching-chip'},
        {'key': 'status3', 'label': stats['status3_label'], 'annotation_field': 'is_dropped_for_user', 'chip_class': 'dropped-chip'},
        {'key': 'wishlist', 'label': stats['wishlist_label'], 'annotation_field': 'is_favorite_for_user', 'chip_class': 'wishlist-chip'},
    ]
    status_labels_map = {key: stats[f"{key_}_label"] for key_, key in [('status1','status1'), ('status2','status2'), ('status3','status3'), ('wishlist','wishlist')]}

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        list_template_name = ''
        context_for_ajax = {
            'content_type_name': content_type_name_display,
            'user': request.user,
            'status_filter_key': status_filter_key,
            'status_labels': status_labels_map,
            'grid_status_config': grid_status_config,
            'content_type_slug': current_content_type_slug,
        }
        if current_view_mode_id == 'view-grid':
            list_template_name = 'includes/items_list_content_grid.html'
            context_for_ajax['library_items'] = items_processed
            context_for_ajax['status_filter_from_toolbar'] = status_filter_key
            context_for_ajax['item_template_name'] = default_item_card_template
        elif current_view_mode_id == 'view-list':
            list_template_name = 'includes/items_list_content_list.html'
            context_for_ajax['library_items'] = items_to_render_for_list_detailed
        elif current_view_mode_id == 'view-detailed-list':
            list_template_name = 'includes/items_list_content_detailed.html'
            context_for_ajax['library_items'] = items_to_render_for_list_detailed
        elif current_view_mode_id == 'view-tierlist':
            list_template_name = 'includes/items_list_content_tierlist.html'
            context_for_ajax.update({
                'unrated_items': unrated_items_for_tierlist,
                'rated_items_by_tier': rated_items_by_tier,
                'tier_item_template_name': tierlist_item_card_template,
                'tier_rating_values': list(range(10, 0, -1)),
            })
        else:
            list_template_name = 'includes/items_list_content_grid.html'
            context_for_ajax['library_items'] = items_processed
            context_for_ajax['status_filter_from_toolbar'] = status_filter_key
            context_for_ajax['item_template_name'] = default_item_card_template

        html_items = render_to_string(list_template_name, context_for_ajax)
        return JsonResponse({'html_items': html_items})

    library_items_for_initial_load = items_processed 
    item_template_name_for_initial_load = default_item_card_template
    initial_list_template_to_include = 'includes/items_list_content_grid.html'

    if current_view_mode_id == 'view-list':
        initial_list_template_to_include = 'includes/items_list_content_list.html'
        library_items_for_initial_load = items_to_render_for_list_detailed
    elif current_view_mode_id == 'view-detailed-list':
        initial_list_template_to_include = 'includes/items_list_content_detailed.html'
        library_items_for_initial_load = items_to_render_for_list_detailed
    elif current_view_mode_id == 'view-tierlist':
        initial_list_template_to_include = 'includes/items_list_content_tierlist.html'

    initial_sort_dropdown_value = 'date_added'
    if sort_by_param.startswith('date_added'): initial_sort_dropdown_value = 'date_added'
    elif sort_by_param.startswith('rating'): initial_sort_dropdown_value = 'rating'
    elif sort_by_param.startswith('title'): initial_sort_dropdown_value = 'title'

    context = {
        'profile': user,
        'library_items': library_items_for_initial_load if current_view_mode_id != 'view-tierlist' else None,
        'item_template_name': item_template_name_for_initial_load if current_view_mode_id != 'view-tierlist' else None,

        'unrated_items': unrated_items_for_tierlist if current_view_mode_id == 'view-tierlist' else None,
        'rated_items_by_tier': rated_items_by_tier if current_view_mode_id == 'view-tierlist' else None,
        'tier_item_template_name': tierlist_item_card_template if current_view_mode_id == 'view-tierlist' else None,
        'tier_rating_values': list(range(10, 0, -1)) if current_view_mode_id == 'view-tierlist' else None,

        'content_type_name': content_type_name_display,
        'status_filter_key': status_filter_key,
        'grid_status_config': grid_status_config,
        'content_type_slug': current_content_type_slug,
        'sorted_items': base_queryset[:4],
        'content_type_name_page_title': content_type_name_display,
        'showcase_item_template': showcase_item_template_path,
        'stats': stats,
        'initial_view_id': current_view_mode_id,
        'initial_filter': status_filter_key,
        'initial_sort': initial_sort_dropdown_value,
        'status_labels': status_labels_map,
        'initial_list_template_to_include': initial_list_template_to_include,
    }
    return render(request, 'users/favorite_list.html', context)


@login_required
def favorite_games_list(request):
    user = request.user
    base_queryset = get_sorted_user_games(user)

    status_filter_key = request.GET.get('status_filter', 'all')
    sort_by_param = request.GET.get('sort_by', 'date_added_desc')
    current_view_mode_id = request.GET.get('view_mode', 'view-grid')

    current_content_type_slug = 'games'
    content_type_name_display = 'Games'
    default_item_card_template = 'partials/game_card.html'
    tierlist_item_card_template = 'partials/tierlist_item_card.html'
    showcase_item_template_path = 'partials/showcase_game_cell.html'

    # Подготовка данных для тирлиста
    unrated_items_for_tierlist = []
    rated_items_by_tier = {i: [] for i in range(1, 11)}
    for item in base_queryset:
        rating = getattr(item, 'user_rating', None)
        if rating is not None and 1 <= rating <= 10:
            rated_items_by_tier[int(rating)].append(item)
        else:
            unrated_items_for_tierlist.append(item)

        if item.platforms:
            game_platforms = json.loads(item.platforms) if isinstance(item.platforms, str) else item.platforms
        else:
            game_platforms = []

        item.platform_icons = list(set(get_platform_icon_path(p["name"]) for p in game_platforms if p and "name" in p))

    sorted_rated_tiers_for_template = sorted(
        [(r_val, r_items) for r_val, r_items in rated_items_by_tier.items()],
        key=lambda x: x[0],
        reverse=True
    )

    # Модели статусов для игр
    status_models_map = {
        'status1': PlayedGame, 'status2': PlayingGame,
        'status3': DroppedGame, 'wishlist': FavoriteGame,
    }
    status_model_id_field = 'game_id'

    # Фильтрация
    items_processed = base_queryset
    items_to_render_for_list_detailed = base_queryset

    if current_view_mode_id == 'view-grid' and status_filter_key != 'all' and status_filter_key in status_models_map:
        StatusModel = status_models_map[status_filter_key]
        status_item_ids = StatusModel.objects.filter(user=user).values_list(status_model_id_field, flat=True)
        items_processed = base_queryset.filter(pk__in=list(status_item_ids))

    if current_view_mode_id != 'view-grid': 
        if status_filter_key != 'all' and status_filter_key in status_models_map:
            StatusModel = status_models_map[status_filter_key]
            status_item_ids = StatusModel.objects.filter(user=user).values_list(status_model_id_field, flat=True)
            items_to_render_for_list_detailed = base_queryset.filter(pk__in=list(status_item_ids))

    # Сортировка
    sort_field_map = {
        'date_added': 'latest_interaction_date',
        'rating': 'user_rating',
        'title': 'name',
    }
    if base_queryset.exists():
        items_processed = apply_sorting_to_queryset(items_processed, sort_by_param, sort_field_map)
        items_to_render_for_list_detailed = apply_sorting_to_queryset(items_to_render_for_list_detailed, sort_by_param, sort_field_map)

    # Статистика
    stats = {
        'total': base_queryset.count(),
        'favourite': FavoriteGame.objects.filter(user=user).count(),
        'status1_label': 'Played', 'status1_count': PlayedGame.objects.filter(user=user).count(),
        'status2_label': 'Playing', 'status2_count': PlayingGame.objects.filter(user=user).count(),
        'status3_label': 'Dropped', 'status3_count': DroppedGame.objects.filter(user=user).count(),
        'wishlist_label': 'Favourite', 
    }
    stats['wishlist_count'] = stats['favourite']

    grid_status_config = [
        {'key': 'wishlist', 'label': stats['wishlist_label'], 'annotation_field': 'is_favorite_for_user', 'chip_class': 'wishlist-chip'},
        {'key': 'status1', 'label': stats['status1_label'], 'annotation_field': 'is_played_for_user', 'chip_class': 'played-chip'},
        {'key': 'status2', 'label': stats['status2_label'], 'annotation_field': 'is_playing_for_user', 'chip_class': 'playing-chip'},
        {'key': 'status3', 'label': stats['status3_label'], 'annotation_field': 'is_dropped_for_user', 'chip_class': 'dropped-chip'},
    ]
    status_labels_map = {key: stats[f"{key_}_label"] for key_, key in [('status1','status1'), ('status2','status2'), ('status3','status3'), ('wishlist','wishlist')]}

    # AJAX и полная загрузка (аналогично movies, с заменой имен шаблонов и контекста)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        list_template_name = ''
        context_for_ajax = {
            'content_type_name': content_type_name_display, # 'Games'
            'user': request.user,
            'status_filter_key': status_filter_key,
            'status_labels': status_labels_map,
            'grid_status_config': grid_status_config,
            'content_type_slug': current_content_type_slug, # 'games'
        }
        if current_view_mode_id == 'view-grid':
            list_template_name = 'includes/items_list_content_grid.html'
            context_for_ajax['library_items'] = items_processed
            context_for_ajax['status_filter_from_toolbar'] = status_filter_key
            context_for_ajax['item_template_name'] = default_item_card_template 
        elif current_view_mode_id == 'view-list':
            list_template_name = 'includes/items_list_content_list.html'
            context_for_ajax['library_items'] = items_to_render_for_list_detailed
        elif current_view_mode_id == 'view-tierlist':
            list_template_name = 'includes/items_list_content_tierlist.html'
            context_for_ajax.update({
                'unrated_items': unrated_items_for_tierlist,
                'rated_items_by_tier': rated_items_by_tier,
                'tier_item_template_name': tierlist_item_card_template,
                'tier_rating_values': list(range(10, 0, -1)),
            })
        else:
            list_template_name = 'includes/items_list_content_grid.html'
            context_for_ajax['library_items'] = items_processed
            context_for_ajax['status_filter_from_toolbar'] = status_filter_key
            context_for_ajax['item_template_name'] = default_item_card_template

        html_items = render_to_string(list_template_name, context_for_ajax)
        return JsonResponse({'html_items': html_items})

    library_items_for_initial_load = items_processed
    item_template_name_for_initial_load = default_item_card_template
    initial_list_template_to_include = 'includes/items_list_content_grid.html'

    if current_view_mode_id == 'view-list':
        initial_list_template_to_include = 'includes/items_list_content_list.html'
        library_items_for_initial_load = items_to_render_for_list_detailed
    elif current_view_mode_id == 'view-detailed-list':
        initial_list_template_to_include = 'includes/items_list_content_detailed.html'
        library_items_for_initial_load = items_to_render_for_list_detailed
    elif current_view_mode_id == 'view-tierlist':
        initial_list_template_to_include = 'includes/items_list_content_tierlist.html'

    initial_sort_dropdown_value = 'date_added'
    if sort_by_param.startswith('date_added'): initial_sort_dropdown_value = 'date_added'
    elif sort_by_param.startswith('rating'): initial_sort_dropdown_value = 'rating'
    elif sort_by_param.startswith('title') or sort_by_param.startswith('name'): initial_sort_dropdown_value = 'title'

    context = {
        'profile': user,
        'sorted_rated_tiers': sorted_rated_tiers_for_template,
        'library_items': library_items_for_initial_load if current_view_mode_id != 'view-tierlist' else None,
        'item_template_name': item_template_name_for_initial_load if current_view_mode_id != 'view-tierlist' else None,
        'unrated_items': unrated_items_for_tierlist if current_view_mode_id == 'view-tierlist' else None,
        'tier_rating_values': list(range(10, 0, -1)) if current_view_mode_id == 'view-tierlist' else None,
        'rated_items_by_tier': rated_items_by_tier,
        'tier_item_template_name': tierlist_item_card_template if current_view_mode_id == 'view-tierlist' else None,
        'content_type_name': content_type_name_display,
        'status_filter_key': status_filter_key,
        'grid_status_config': grid_status_config,
        'content_type_slug': current_content_type_slug,
        'sorted_items': base_queryset[:4],
        'content_type_name_page_title': content_type_name_display,
        'showcase_item_template': showcase_item_template_path,
        'stats': stats,
        'initial_view_id': current_view_mode_id,
        'initial_filter': status_filter_key,
        'initial_sort': initial_sort_dropdown_value,
        'status_labels': status_labels_map,
        'initial_list_template_to_include': initial_list_template_to_include,
    }
    return render(request, 'users/favorite_list.html', context)


@login_required
def favorite_books_list(request):
    user = request.user
    base_queryset = get_sorted_user_books(user)

    status_filter_key = request.GET.get('status_filter', 'all')
    sort_by_param = request.GET.get('sort_by', 'date_added_desc')
    current_view_mode_id = request.GET.get('view_mode', 'view-grid')

    current_content_type_slug = 'books'
    content_type_name_display = 'Books'
    default_item_card_template = 'partials/book_card.html'
    tierlist_item_card_template = 'partials/tierlist_item_card.html'
    showcase_item_template_path = 'partials/showcase_book_cell.html'

    # Подготовка данных для тирлиста
    unrated_items_for_tierlist = []
    rated_items_by_tier = {i: [] for i in range(1, 11)}
    for item in base_queryset:
        rating = getattr(item, 'user_rating', None)
        if rating is not None and 1 <= rating <= 10:
            rated_items_by_tier[int(rating)].append(item)
        else:
            unrated_items_for_tierlist.append(item)

    # Модели статусов для книг
    status_models_map = {
        'status1': ReadBook, 'status2': ReadingBook,
        'status3': DroppedBook, 'wishlist': FavoriteBook,
    }
    status_model_id_field = 'book_id'

    # Фильтрация
    items_processed = base_queryset
    items_to_render_for_list_detailed = base_queryset

    if current_view_mode_id == 'view-grid' and status_filter_key != 'all' and status_filter_key in status_models_map:
        StatusModel = status_models_map[status_filter_key]
        status_item_ids = StatusModel.objects.filter(user=user).values_list(status_model_id_field, flat=True)
        items_processed = base_queryset.filter(pk__in=list(status_item_ids))

    if current_view_mode_id != 'view-grid':
        if status_filter_key != 'all' and status_filter_key in status_models_map:
            StatusModel = status_models_map[status_filter_key]
            status_item_ids = StatusModel.objects.filter(user=user).values_list(status_model_id_field, flat=True)
            items_to_render_for_list_detailed = base_queryset.filter(pk__in=list(status_item_ids))

    # Сортировка
    sort_field_map = {
        'date_added': 'latest_interaction_date',
        'rating': 'user_rating',
        'title': 'title',
    }
    if base_queryset.exists():
        items_processed = apply_sorting_to_queryset(items_processed, sort_by_param, sort_field_map)
        items_to_render_for_list_detailed = apply_sorting_to_queryset(items_to_render_for_list_detailed, sort_by_param, sort_field_map)

    # Статистика
    stats = {
        'total': base_queryset.count(),
        'favourite': FavoriteBook.objects.filter(user=user).count(),
        'status1_label': 'Read', 'status1_count': ReadBook.objects.filter(user=user).count(),
        'status2_label': 'Reading', 'status2_count': ReadingBook.objects.filter(user=user).count(),
        'status3_label': 'Dropped', 'status3_count': DroppedBook.objects.filter(user=user).count(),
        'wishlist_label': 'Wishlist',
    }
    stats['wishlist_count'] = stats['favourite']

    grid_status_config = [
        {'key': 'status1', 'label': stats['status1_label'], 'annotation_field': 'is_read_for_user', 'chip_class': 'read-chip'},
        {'key': 'status2', 'label': stats['status2_label'], 'annotation_field': 'is_reading_for_user', 'chip_class': 'reading-chip'},
        {'key': 'status3', 'label': stats['status3_label'], 'annotation_field': 'is_dropped_for_user', 'chip_class': 'dropped-chip'},
        {'key': 'wishlist', 'label': stats['wishlist_label'], 'annotation_field': 'is_favorite_for_user', 'chip_class': 'wishlist-chip'},
    ]
    status_labels_map = {key: stats[f"{key_}_label"] for key_, key in [('status1','status1'), ('status2','status2'), ('status3','status3'), ('wishlist','wishlist')]}

    # AJAX и полная загрузка (аналогично)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        list_template_name = ''
        context_for_ajax = {
            'content_type_name': content_type_name_display, # 'Books'
            'user': request.user,
            'status_filter_key': status_filter_key,
            'status_labels': status_labels_map,
            'grid_status_config': grid_status_config,
            'content_type_slug': current_content_type_slug, # 'books'
        }
        if current_view_mode_id == 'view-grid':
            list_template_name = 'includes/items_list_content_grid.html'
            context_for_ajax['library_items'] = items_processed
            context_for_ajax['status_filter_from_toolbar'] = status_filter_key
            context_for_ajax['item_template_name'] = default_item_card_template
        elif current_view_mode_id == 'view-list':
            list_template_name = 'includes/items_list_content_list.html'
            context_for_ajax['library_items'] = items_to_render_for_list_detailed
        elif current_view_mode_id == 'view-detailed-list':
            list_template_name = 'includes/items_list_content_detailed.html'
            context_for_ajax['library_items'] = items_to_render_for_list_detailed
        elif current_view_mode_id == 'view-tierlist':
            list_template_name = 'includes/items_list_content_tierlist.html'
            context_for_ajax.update({
                'unrated_items': unrated_items_for_tierlist,
                'rated_items_by_tier': rated_items_by_tier,
                'tier_item_template_name': tierlist_item_card_template,
                'tier_rating_values': list(range(10, 0, -1)),
            })
        else:
            list_template_name = 'includes/items_list_content_grid.html'
            context_for_ajax['library_items'] = items_processed
            context_for_ajax['status_filter_from_toolbar'] = status_filter_key
            context_for_ajax['item_template_name'] = default_item_card_template

        html_items = render_to_string(list_template_name, context_for_ajax)
        return JsonResponse({'html_items': html_items})

    library_items_for_initial_load = items_processed
    item_template_name_for_initial_load = default_item_card_template
    initial_list_template_to_include = 'includes/items_list_content_grid.html'

    if current_view_mode_id == 'view-list':
        initial_list_template_to_include = 'includes/items_list_content_list.html'
        library_items_for_initial_load = items_to_render_for_list_detailed
    elif current_view_mode_id == 'view-detailed-list':
        initial_list_template_to_include = 'includes/items_list_content_detailed.html'
        library_items_for_initial_load = items_to_render_for_list_detailed
    elif current_view_mode_id == 'view-tierlist':
        initial_list_template_to_include = 'includes/items_list_content_tierlist.html'

    initial_sort_dropdown_value = 'date_added'
    if sort_by_param.startswith('date_added'): initial_sort_dropdown_value = 'date_added'
    elif sort_by_param.startswith('rating'): initial_sort_dropdown_value = 'rating'
    elif sort_by_param.startswith('title'): initial_sort_dropdown_value = 'title'

    context = {
        'profile': user,
        'library_items': library_items_for_initial_load if current_view_mode_id != 'view-tierlist' else None,
        'item_template_name': item_template_name_for_initial_load if current_view_mode_id != 'view-tierlist' else None,
        'unrated_items': unrated_items_for_tierlist if current_view_mode_id == 'view-tierlist' else None,
        'rated_items_by_tier': rated_items_by_tier if current_view_mode_id == 'view-tierlist' else None,
        'tier_rating_values': list(range(10, 0, -1)) if current_view_mode_id == 'view-tierlist' else None,

        'tier_item_template_name': tierlist_item_card_template if current_view_mode_id == 'view-tierlist' else None,
        'content_type_name': content_type_name_display,
        'status_filter_key': status_filter_key,
        'grid_status_config': grid_status_config,
        'content_type_slug': current_content_type_slug,
        'sorted_items': base_queryset[:4],
        'content_type_name_page_title': content_type_name_display,
        'showcase_item_template': showcase_item_template_path,
        'stats': stats,
        'initial_view_id': current_view_mode_id,
        'initial_filter': status_filter_key,
        'initial_sort': initial_sort_dropdown_value,
        'status_labels': status_labels_map,
        'initial_list_template_to_include': initial_list_template_to_include,
    }
    return render(request, 'users/favorite_list.html', context)


def generate_verification_code(length=6):
    """Генерирует случайный цифровой код указанной длины."""
    return "".join(random.choice(string.digits) for i in range(length))


@login_required
@require_POST
def send_email_verification(request):
    new_email = request.POST.get('new_email')
    if not new_email:
        return JsonResponse({'status': 'error', 'message': 'New email address is required.'}, status=400)

    try:
        validate_email(new_email)
    except ValidationError:
        return JsonResponse({'status': 'error', 'message': 'Invalid email format.'}, status=400)

    if User.objects.filter(email__iexact=new_email).exclude(pk=request.user.pk).exists():
        return JsonResponse({'status': 'error', 'message': 'This email address is already in use.'}, status=400)

    if request.user.email.lower() == new_email.lower():
        return JsonResponse({'status': 'error', 'message': 'This is already your current email address.'}, status=400)

    verification_code = generate_verification_code()

    # Сохраняем код и новую почту в сессии пользователя
    # Код будет действителен, пока сессия жива, или можно добавить время жизни
    request.session['email_verification_code'] = verification_code
    request.session['pending_new_email'] = new_email
    request.session['email_verification_code_sent_at'] = timezone.now().isoformat() # Для проверки срока действия

    subject = 'Your Email Verification Code'
    site_name = getattr(settings, 'SITE_NAME_DISPLAY', "Site Team") # Безопасно получаем значение
    message = f'Hello {request.user.username},\n\nYour verification code to change your email address is: {verification_code}\n\nThis code is valid for 10 minutes.\n\nIf you did not request this change, please ignore this email.\n\nThanks,\nThe {site_name}'

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [new_email],
            fail_silently=False,
        )
        return JsonResponse({'status': 'success', 'message': f'Verification code sent to {new_email}.'})
    except Exception as e:
        # Логирование ошибки e
        print(f"Error sending verification email: {e}")
        return JsonResponse({'status': 'error', 'message': 'Could not send verification email. Please try again later.'}, status=500)


@login_required
@require_POST
def verify_and_change_email(request):
    submitted_code = request.POST.get('verification_code')
    # Получаем новую почту, которая была передана в hidden input
    # Это важно для безопасности, чтобы убедиться, что мы меняем на ту почту, на которую отсылали код
    pending_new_email_from_form = request.POST.get('new_email') 

    if not submitted_code or not pending_new_email_from_form:
        return JsonResponse({'status': 'error', 'message': 'Verification code and email are required.'}, status=400)

    stored_code = request.session.get('email_verification_code')
    stored_pending_email = request.session.get('pending_new_email')
    code_sent_at_str = request.session.get('email_verification_code_sent_at')

    if not stored_code or not stored_pending_email or not code_sent_at_str:
        return JsonResponse({'status': 'error', 'message': 'Verification process not initiated or session expired. Please start over.'}, status=400)

    if stored_pending_email.lower() != pending_new_email_from_form.lower():
        return JsonResponse({'status': 'error', 'message': 'Email mismatch. Please start over.'}, status=400)

    # Проверка срока действия кода (например, 10 минут)
    code_sent_at = timezone.datetime.fromisoformat(code_sent_at_str)
    if timezone.now() > code_sent_at + timedelta(minutes=10):
        # Очищаем сессию, чтобы заставить пользователя начать заново
        del request.session['email_verification_code']
        del request.session['pending_new_email']
        del request.session['email_verification_code_sent_at']
        return JsonResponse({'status': 'error', 'message': 'Verification code has expired. Please request a new one.'}, status=400)

    if submitted_code == stored_code:
        user = request.user
        user.email = stored_pending_email
        user.save()

        # Очищаем сессию после успешной смены
        del request.session['email_verification_code']
        del request.session['pending_new_email']
        del request.session['email_verification_code_sent_at']

        return JsonResponse({'status': 'success', 'message': 'Email address updated successfully!', 'new_email': user.email})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid verification code.'}, status=400)


@login_required
@require_POST # Эта view должна принимать только POST запросы
def update_item_rating(request, content_type_slug, item_pk_str): # item_pk_str потому что ID книги может быть строкой
    user = request.user

    try:
        data = json.loads(request.body)
        new_rating_input = data.get('rating') # Ожидаем число (1-10) или null/0 для сброса
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)

    # Определяем модели на основе content_type_slug
    if content_type_slug == 'games':
        ContentModel = Game
        UserRatingModel = UserGameRating
        item_field_name = 'game'
        try:
            item_pk = int(item_pk_str) # Для игр ID это int
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid game ID format.'}, status=400)
    elif content_type_slug == 'movies':
        ContentModel = Movie
        UserRatingModel = UserMovieRating
        item_field_name = 'movie'
        try:
            item_pk = int(item_pk_str) # Для фильмов ID (PK) это int, tmdb_id тоже int
        except ValueError: # Если вдруг захочешь использовать tmdb_id как pk_str, но лучше pk
            return JsonResponse({'status': 'error', 'message': 'Invalid movie ID format.'}, status=400)
    elif content_type_slug == 'books':
        ContentModel = Book
        UserRatingModel = UserBookRating
        item_field_name = 'book'
        item_pk = item_pk_str
        try:
            item_pk = int(item_pk_str)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid book ID format for internal PK.'}, status=400)

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid content type.'}, status=400)

    try:
        # Ищем объект по его PK
        item = get_object_or_404(ContentModel, pk=item_pk)
    except Http404:
        return JsonResponse({'status': 'error', 'message': f'{content_type_slug.capitalize()} not found.'}, status=404)

    current_rating_value = None

    if new_rating_input is not None:
        try:
            new_rating = int(new_rating_input)
            if 1 <= new_rating <= 10:
                rating_obj, created = UserRatingModel.objects.update_or_create(
                    user=user,
                    **{item_field_name: item},
                    defaults={'rating': new_rating}
                )
                current_rating_value = rating_obj.rating
                action_message = f'Rating {"set" if created else "updated"} to {current_rating_value}.'

                # Обновим MGB рейтинг для самого объекта Game/Movie/Book
                if hasattr(item, 'update_mgb_rating'):
                    item.update_mgb_rating()

            else:
                return JsonResponse({'status': 'error', 'message': 'Rating must be between 1 and 10.'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'status': 'error', 'message': 'Invalid rating value. Expected number or null.'}, status=400)
    else:
        deleted_count, _ = UserRatingModel.objects.filter(
            user=user,
            **{item_field_name: item}
        ).delete()
        action_message = 'Rating removed.' if deleted_count > 0 else 'No rating to remove.'
        current_rating_value = None

        if hasattr(item, 'update_mgb_rating'):
            item.update_mgb_rating()

    return JsonResponse({
        'status': 'success',
        'message': action_message,
        'current_rating': current_rating_value,
        'item_id': item.pk,
        'content_type': content_type_slug
    })
    

# --- СТАТУСЫ ИГР ---
# --------------------------------------------------------------------------------------------------------------------------------------------
@login_required
def played_add(request, game_id):
    # Используем стандартный pk/id для поиска Game в БД
    game = get_object_or_404(Game, pk=game_id)

    # Удаляем игру из других категорий
    PlayingGame.objects.filter(user=request.user, game=game).delete()
    DroppedGame.objects.filter(user=request.user, game=game).delete()

    played_game, created = PlayedGame.objects.get_or_create(user=request.user, game=game)

    if not created:
        played_game.delete()
        is_played = False
    else:
        is_played = True

    return JsonResponse({"is_played": is_played})


@login_required
def playing_add(request, game_id):
    game = get_object_or_404(Game, pk=game_id)

    # Удаляем игру из других категорий
    PlayedGame.objects.filter(user=request.user, game=game).delete()
    DroppedGame.objects.filter(user=request.user, game=game).delete()

    playing_game, created = PlayingGame.objects.get_or_create(user=request.user, game=game)

    if not created:
        playing_game.delete()
        is_playing = False
    else:
        is_playing = True

    return JsonResponse({"is_playing": is_playing})


@login_required
def dropped_add(request, game_id):
    game = get_object_or_404(Game, pk=game_id)

    # Удаляем игру из других категорий
    PlayedGame.objects.filter(user=request.user, game=game).delete()
    PlayingGame.objects.filter(user=request.user, game=game).delete()

    dropped_game, created = DroppedGame.objects.get_or_create(user=request.user, game=game)

    if not created:
        dropped_game.delete()
        is_dropped = False
    else:
        is_dropped = True

    return JsonResponse({"is_dropped": is_dropped})


# --- СТАТУСЫ ФИЛЬМОВ ---
@login_required
def watched_add(request, movie_id): # Используем movie_id (tmdb_id)
    movie = get_object_or_404(Movie, tmdb_id=movie_id)
    user = request.user
    # Удаляем из других статусов фильмов
    WatchingMovie.objects.filter(user=user, movie=movie).delete()
    DroppedMovie.objects.filter(user=user, movie=movie).delete()
    # Добавляем/удаляем из просмотренных
    watched_obj, created = WatchedMovie.objects.get_or_create(user=user, movie=movie)
    if not created:
        watched_obj.delete()
        is_watched = False
    else:
        is_watched = True
    return JsonResponse({"is_watched": is_watched}) # Возвращаем правильный ключ


@login_required
def watching_add(request, movie_id):
    movie = get_object_or_404(Movie, tmdb_id=movie_id)
    user = request.user
    WatchedMovie.objects.filter(user=user, movie=movie).delete()
    DroppedMovie.objects.filter(user=user, movie=movie).delete()
    watching_obj, created = WatchingMovie.objects.get_or_create(user=user, movie=movie)
    if not created:
        watching_obj.delete()
        is_watching = False
    else:
        is_watching = True
    return JsonResponse({"is_watching": is_watching})


@login_required
def movie_dropped_add(request, movie_id): # Назвали movie_dropped_add
    movie = get_object_or_404(Movie, tmdb_id=movie_id)
    user = request.user
    WatchedMovie.objects.filter(user=user, movie=movie).delete()
    WatchingMovie.objects.filter(user=user, movie=movie).delete()
    dropped_obj, created = DroppedMovie.objects.get_or_create(user=user, movie=movie)
    if not created:
        dropped_obj.delete()
        is_dropped = False
    else:
        is_dropped = True
    return JsonResponse({"is_dropped": is_dropped})


# --- СТАТУСЫ КНИГ ---
@login_required
def read_add(request, book_id): # Используем book_id (google_id)
    book = get_object_or_404(Book, google_id=book_id)
    user = request.user
    ReadingBook.objects.filter(user=user, book=book).delete()
    DroppedBook.objects.filter(user=user, book=book).delete()
    read_obj, created = ReadBook.objects.get_or_create(user=user, book=book)
    if not created:
        read_obj.delete()
        is_read = False
    else:
        is_read = True
    return JsonResponse({"is_read": is_read})


@login_required
def reading_add(request, book_id):
    book = get_object_or_404(Book, google_id=book_id)
    user = request.user
    ReadBook.objects.filter(user=user, book=book).delete()
    DroppedBook.objects.filter(user=user, book=book).delete()
    reading_obj, created = ReadingBook.objects.get_or_create(user=user, book=book)
    if not created:
        reading_obj.delete()
        is_reading = False
    else:
        is_reading = True
    return JsonResponse({"is_reading": is_reading})


@login_required
def book_dropped_add(request, book_id): # Назвали book_dropped_add
    book = get_object_or_404(Book, google_id=book_id)
    user = request.user
    ReadBook.objects.filter(user=user, book=book).delete()
    ReadingBook.objects.filter(user=user, book=book).delete()
    dropped_obj, created = DroppedBook.objects.get_or_create(user=user, book=book)
    if not created:
        dropped_obj.delete()
        is_dropped = False
    else:
        is_dropped = True
    return JsonResponse({"is_dropped": is_dropped})

# --- КОММЕНТАРИИ И ЛАЙКИ (В основном без изменений) ---
# TODO: Адаптировать add_comment и add_reply для работы с Book
# (Сейчас работают только с Game и Movie)


@login_required  # Добавил декоратор, т.к. комментировать могут только авторизованные
def add_comment(request, content_type, object_id):
    if request.method == "POST":
        user = request.user

        try:
            data = json.loads(request.body.decode('utf-8'))
            title = data.get("title", "").strip() # Убираем пробелы по краям
            content = data.get("content", "").strip()
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"}, status=400)

        if not title or not content:
            return JsonResponse({"success": False, "error": "Title and content cannot be empty"}, status=400)

        comment = Comment(user=user, title=title, content=content)
        item = None # Инициализируем переменную для объекта контента

        # Определяем объект, к которому относится комментарий
        try:
            if content_type == "game":
                item = get_object_or_404(Game, pk=object_id) # Используем pk
                comment.game = item
            elif content_type == "movie":
                item = get_object_or_404(Movie, pk=object_id) # Используем pk
                comment.movie = item
            elif content_type == "book": # --- ДОБАВЛЕНА ПРОВЕРКА ДЛЯ КНИГ ---
                item = get_object_or_404(Book, pk=object_id) # Используем pk
                comment.book = item
            else:
                return JsonResponse({"success": False, "error": "Invalid content type for comment"}, status=400)
        except Http404:
             return JsonResponse({"success": False, "error": f"{content_type.capitalize()} not found"}, status=404)

        comment.save()

        # Возвращаем данные о созданном комментарии
        return JsonResponse({
            "success": True,
            "comment": {
                "id": comment.id,
                "title": comment.title,
                "content": comment.content,
                "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S"), # Формат можно настроить
                "user": {
                    "username": user.username,
                    "avatar_url": user.avatar.url if user.avatar else None, # Переименовал в avatar_url
                },
                "like_count": 0, # Новый коммент - 0 лайков
                "liked": False, # Текущий юзер его еще не лайкнул
                "reply_count": 0, # Новый коммент - 0 ответов
            }
        }, status=201) # Статус 201 Created

    return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)


@login_required  # Добавил декоратор
def add_reply(request, comment_id):
    if request.method == "POST":
        parent_comment = get_object_or_404(Comment, id=comment_id)
        user = request.user

        try:
            data = json.loads(request.body.decode('utf-8'))
            title = data.get("title", "").strip()
            content = data.get("content", "").strip()
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"}, status=400)

        if not title or not content:
            return JsonResponse({"success": False, "error": "Title and content cannot be empty"}, status=400)

        # Создаем ответ, связывая его с родительским комментом
        # и копируя связь с контентом (game/movie/book)
        reply = Comment.objects.create(
            user=user,
            title=title,
            content=content,
            parent=parent_comment,
            game=parent_comment.game, # Копируем связь
            movie=parent_comment.movie, # Копируем связь
            book=parent_comment.book   # Копируем связь
            )

        return JsonResponse({
            "success": True,
            "reply": {
                "id": reply.id,
                "title": reply.title,
                "content": reply.content,
                "created_at": reply.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "user": {
                    "username": user.username,
                    "avatar_url": user.avatar.url if user.avatar else None,
                },
                "like_count": 0,
                "liked": False,
                "parent_id": parent_comment.id # Добавил ID родителя
            }
        }, status=201)

    return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)


@login_required
def like_comment(request, comment_id):
    if request.method == "POST": # Лайк - это изменение данных, лучше POST
        comment = get_object_or_404(Comment, id=comment_id)
        user = request.user

        if user in comment.likes.all():
            # Если лайк уже есть - убираем
            comment.likes.remove(user)
            liked = False
        else:
            # Если лайка нет - добавляем
            comment.likes.add(user)
            liked = True

        like_count = comment.likes.count() # Получаем актуальное количество

        return JsonResponse({
            "success": True,
            "like_count": like_count,
            "liked": liked,  # Возвращаем текущее состояние лайка для пользователя
        })

    # Возвращаем ошибку, если метод не POST
    return JsonResponse({"success": False, "error": "Method not allowed, use POST"}, status=405)


# РЕЙТИНГ ПОЛЬЗОВАТЕЛЕЙ MGB
# -------------------------------------------------------------------------------------------------------
@login_required
@require_POST  # Принимаем только POST запросы
def set_user_rating(request, content_type, item_pk):
    user = request.user

    # --- Определяем модели контента и рейтинга ---
    rating_config = {
        'game': {'content_model': Game, 'rating_model': UserGameRating, 'content_field': 'game'},
        'movie': {'content_model': Movie, 'rating_model': UserMovieRating, 'content_field': 'movie'},
        'book': {'content_model': Book, 'rating_model': UserBookRating, 'content_field': 'book'}
    }

    config = rating_config.get(content_type)
    if not config:
        return JsonResponse({'status': 'error', 'message': 'Invalid content type'}, status=400)

    ContentModel = config['content_model']
    RatingModel = config['rating_model']
    content_field = config['content_field']

    # --- Получаем объект контента ---
    try:
        item = get_object_or_404(ContentModel, pk=item_pk)
    except Http404:
        return JsonResponse({'status': 'error', 'message': f'{content_type.capitalize()} not found'}, status=404)

    # --- Получаем и валидируем рейтинг из POST данных ---
    try:
        data = json.loads(request.body.decode('utf-8'))
        rating_value = data.get('rating') # Ожидаем ключ 'rating' в JSON
        # Рейтинг 0 означает удаление
        if rating_value is not None:
            rating_value = int(rating_value)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid rating data format'}, status=400)

    # --- Обновляем или удаляем рейтинг ---
    current_rating = None
    try:
        if rating_value is not None and 1 <= rating_value <= 10:
            rating_obj, created = RatingModel.objects.update_or_create(
                user=user,
                **{content_field: item},
                defaults={'rating': rating_value}
            )
            current_rating = rating_obj.rating
            message = 'Rating saved successfully'
            status = 'success'
        elif rating_value == 0:
            deleted_count, _ = RatingModel.objects.filter(
                user=user,
                **{content_field: item}
            ).delete()
            current_rating = None
            message = 'Rating removed successfully' if deleted_count > 0 else 'Rating not found to remove'
            status = 'success'
        else:
            return JsonResponse({'status': 'error', 'message': 'Rating must be between 1 and 10, or 0 to remove'}, status=400)

    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': ', '.join(e.messages)}, status=400)
    except Exception as e:
        print(f"Error saving rating: {e}")
        return JsonResponse({'status': 'error', 'message': 'Error saving rating'}, status=500)

    # --- Возвращаем успешный ответ ---
    return JsonResponse({
        'status': status,
        'message': message,
        'current_rating': current_rating
    })
