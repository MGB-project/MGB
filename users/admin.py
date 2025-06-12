from django.contrib import admin
from users.models import (
    User, Game, FavoriteGame, PlayedGame, PlayingGame, DroppedGame, Comment, Movie, Genre, Actor, Book
)


# USER
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'date_joined', 'is_staff')  # Поля, отображаемые в списке
    list_filter = ('is_staff', 'is_superuser', 'date_joined')  # Фильтры
    search_fields = ('username', 'email')  # Поиск по полям
    readonly_fields = ('date_joined', 'last_login')  # Только для чтения
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Profile', {'fields': ('avatar', 'header', 'bio')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


# GAME
@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_rating', 'first_release_date', 'is_main_game', 'is_new_game')
    list_filter = ('is_main_game', 'is_new_game', 'is_recently_trending_small', 'is_recently_trending_big')
    search_fields = ('name', 'summary')
    readonly_fields = ('rating_color',)  # Автоматически вычисляемое поле
    fieldsets = (
        (None, {'fields': ('name', 'summary', 'first_release_date', 'company')}),
        ('Ratings', {'fields': ('total_rating', 'total_rating_count', 'rating_color')}),
        ('Media', {'fields': ('cover_url', 'custom_photo', 'custom_header_photo', 'video_custom', 'youtube_trailer')}),
        ('Details', {'fields': ('platforms', 'genres', 'game_modes', 'screenshots', 'similar_games', 'status', 'websites', 'multiplayer_modes', 'btn_color')}),
        ('Flags', {'fields': ('is_main_game', 'is_recently_trending_small', 'is_recently_trending_big', 'is_new_game', 'is_age_limit')}),
    )


# FAVORITE GAME
@admin.register(FavoriteGame)
class FavoriteGameAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'game__name')
    raw_id_fields = ('user', 'game')


# PLAYED GAME
@admin.register(PlayedGame)
class PlayedGameAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'game__name')
    raw_id_fields = ('user', 'game')


# PLAYING GAME
@admin.register(PlayingGame)
class PlayingGameAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'game__name')
    raw_id_fields = ('user', 'game')


# DROPPED GAME
@admin.register(DroppedGame)
class DroppedGameAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'game__name')
    raw_id_fields = ('user', 'game')


# COMMENTS
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "game", "created_at", "like_count")
    list_filter = ("created_at", "game")
    search_fields = ("title", "content", "user__username", "game__name")
    ordering = ("-created_at",)

# MOVIES
# --------------------------------------------------------------


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date', 'vote_average', 'popularity', 'number_of_seasons')
    list_filter = ('release_date', 'vote_average', 'genres')
    search_fields = ('title', 'original_title', 'tmdb_id')
    filter_horizontal = ('genres', 'actors')  # Удобное управление ManyToMany
    readonly_fields = ('tmdb_id',)  # ID TMDb лучше не редактировать вручную


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'tmdb_id')
    search_fields = ('name',)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name', 'tmdb_id')
    search_fields = ('name',)


# BOOKS
# --------------------------------------------------------------


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_date', 'average_rating', 'is_main_book')
    list_filter = ('published_date', 'average_rating', 'categories')
    search_fields = ('title', 'google_id')
    readonly_fields = ('google_id',)
