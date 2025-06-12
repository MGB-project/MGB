# users/urls.py
from django.urls import path
from . import views  # Используем относительный импорт '.'

app_name = 'users'

urlpatterns = [
    # --- Комментарии и Лайки ---
    # Используем <int:object_id> т.к. комментарии привязаны к pk объектов Game/Movie/Book
    path('add_comment/<str:content_type>/<int:object_id>/', views.add_comment, name='add_comment'),
    path('add_reply/<int:comment_id>/', views.add_reply, name='add_reply'),
    # Для лайка нужен только ID комментария
    path('like_comment/<int:comment_id>/', views.like_comment, name='like_comment'),

    # --- Аутентификация и Профиль ---
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout, name='logout'),

    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('profile/history/', views.profile_history, name='profile_history'),
    path('profile/send-email-verification/', views.send_email_verification, name='send_email_verification'),
    path('profile/verify-and-change-email/', views.verify_and_change_email, name='verify_and_change_email'),

    # --- СТРАНИЦЫ СПИСКОВ ИЗБРАННОГО (НУЖНО ДОБАВИТЬ!) ---
    path('profile/favorites/games/', views.favorite_games_list, name='favorite_games_list'),
    path('profile/favorites/movies/', views.favorite_movies_list, name='favorite_movies_list'),
    path('profile/favorites/books/', views.favorite_books_list, name='favorite_books_list'),
    # -------------------------------------------------------

    # --- Избранное (Универсальный URL) ---
    path('favorite-toggle/<str:content_type>/<slug:object_id>/', views.toggle_favorite_item, name='favorite_toggle'),

    # --- Статусы Игр ---
    path("played-add/<int:game_id>/", views.played_add, name="played_add"),
    path("playing-add/<int:game_id>/", views.playing_add, name="playing_add"),
    path("dropped-add/<int:game_id>/", views.dropped_add, name="dropped_add"),  # Для игр используем старое имя

    # --- Статусы Фильмов ---
    # Используем tmdb_id (число)
    path("watched-add/<int:movie_id>/", views.watched_add, name="watched_add"),
    path("watching-add/<int:movie_id>/", views.watching_add, name="watching_add"),
    path("movie-dropped-add/<int:movie_id>/", views.movie_dropped_add, name="movie_dropped_add"),  # Новое имя

    # --- Статусы Книг ---
    # Используем google_id (строка -> slug)
    path("read-add/<slug:book_id>/", views.read_add, name="read_add"),
    path("reading-add/<slug:book_id>/", views.reading_add, name="reading_add"),
    path("book-dropped-add/<slug:book_id>/", views.book_dropped_add, name="book_dropped_add"),

    # --- URL ДЛЯ УСТАНОВКИ/УДАЛЕНИЯ РЕЙТИНГА ---
    path('rate/<str:content_type>/<int:item_pk>/', views.set_user_rating, name='set_user_rating'),
    path('tierlist/rate/<slug:content_type_slug>/<str:item_pk_str>/', views.update_item_rating, name='update_item_rating_tierlist'),
]
