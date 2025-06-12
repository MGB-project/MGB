# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg
from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.apps import apps


# МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ (User)
# --------------------------------------------------------------------------
class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', default='default_profile_icon.svg')
    header = models.ImageField(upload_to='headers/', default='header/default.jpg')
    bio = models.TextField(blank=True, default="Your bio here...")
    banner_color = models.CharField(max_length=100, blank=True, null=True, help_text="CSS-совместимая строка цвета для баннера профиля, например 'linear-gradient(...)' или '#RRGGBB'")
    # --- НОВЫЙ УНИВЕРСАЛЬНЫЙ МЕХАНИЗМ ИЗБРАННОГО ---
    FAVORITE_CONFIG = {
        # Ключ: строка-идентификатор типа контента (используется в URL и JS)
        # Значение: словарь с конфигурацией
        'game': {
            'model': 'users.FavoriteGame',         # Путь к модели избранного
            'field': 'game',                      # Имя поля ForeignKey в модели избранного, указывающее на контент
            'content_model': 'users.Game',        # Путь к модели самого контента
            'id_field': 'id'                      # Имя поля ID, которое будет передаваться в URL (обычно 'id' или 'pk')
                                                  # Используем 'id' здесь, т.к. твоя старая view использовала game_id=game.id
        },
        'movie': {
            'model': 'users.FavoriteMovie',
            'field': 'movie',
            'content_model': 'users.Movie',
            'id_field': 'tmdb_id'                  # Для фильмов используем tmdb_id как идентификатор в URL
        },
        'book': {
            'model': 'users.FavoriteBook',
            'field': 'book',
            'content_model': 'users.Book',
            'id_field': 'google_id'               # Для книг используем google_id (строка!)
        },
    }

    def _get_favorite_model_and_field(self, item):
        """Вспомогательный метод для получения модели Favorite и имени поля связи."""
        item_type_name = type(item).__name__  # Получаем имя класса 'Game', 'Movie', 'Book'

        # Ищем конфиг по имени класса элемента
        for key, config in self.FAVORITE_CONFIG.items():
            # Получаем класс модели контента из строки 'users.ModelName'
            ContentModel = apps.get_model(config['content_model'])
            if isinstance(item, ContentModel):
                # Если тип совпал, получаем класс модели избранного
                FavoriteModel = apps.get_model(config['model'])
                item_field = config['field'] # Имя поля ('game', 'movie', 'book')
                return FavoriteModel, item_field

        # Если тип не найден в конфиге
        raise TypeError(f"Type {item_type_name} is not configured for favorites.")

    def toggle_favorite(self, item):
        """
        Добавляет или удаляет элемент (Game, Movie, Book) из избранного пользователя.
        Возвращает True, если элемент теперь в избранном, False - если удален.
        """
        FavoriteModel, item_field = self._get_favorite_model_and_field(item)
        filter_kwargs = {'user': self, item_field: item}
        fav_instance, created = FavoriteModel.objects.get_or_create(**filter_kwargs)

        if not created:
            fav_instance.delete()
            return False  # Теперь не в избранном
        return True  # Теперь в избранном (был создан)

    def is_item_favorite(self, item):
        """Проверяет, находится ли элемент (Game, Movie, Book) в избранном."""
        try:
            FavoriteModel, item_field = self._get_favorite_model_and_field(item)
            filter_kwargs = {'user': self, item_field: item}
            return FavoriteModel.objects.filter(**filter_kwargs).exists()
        except TypeError:
            return False  # Тип не поддерживается -> не в избранном
    # --- КОНЕЦ НОВОГО МЕХАНИЗМА ---

    # --- МЕТОДЫ СТАТУСОВ ИГР (ОСТАЮТСЯ, Т.К. СПЕЦИФИЧНЫ ДЛЯ ИГР) ---
    def add_to_played(self, game):
        if not self.played_games.filter(game=game).exists():
            PlayedGame.objects.create(user=self, game=game)

    def remove_from_played(self, game):
        self.played_games.filter(game=game).delete()

    def is_played(self, game):
        # Убедимся, что game - это объект Game
        if not isinstance(game, Game): return False
        return self.played_games.filter(game=game).exists()

    def add_to_playing(self, game):
        if not self.playing_games.filter(game=game).exists():
            PlayingGame.objects.create(user=self, game=game)

    def remove_from_playing(self, game):
        self.playing_games.filter(game=game).delete()

    def is_playing(self, game):
        if not isinstance(game, Game): return False
        return self.playing_games.filter(game=game).exists()

    def add_to_dropped(self, game):
        if not self.dropped_games.filter(game=game).exists():
            DroppedGame.objects.create(user=self, game=game)

    def remove_from_dropped(self, game):
        self.dropped_games.filter(game=game).delete()

    def is_dropped(self, game):
        if not isinstance(game, Game): return False
        return self.dropped_games.filter(game=game).exists()
    # --- КОНЕЦ МЕТОДОВ СТАТУСОВ ИГР ---

    # --- МЕТОДЫ СТАТУСОВ ФИЛЬМОВ---
    def is_watched(self, movie):
        if not isinstance(movie, Movie): return False
        return self.watched_movies.filter(movie=movie).exists()

    def is_watching(self, movie):
        if not isinstance(movie, Movie): return False
        return self.watching_movies.filter(movie=movie).exists()

    def is_movie_dropped(self, movie): # Назовем is_movie_dropped для уникальности
        if not isinstance(movie, Movie): return False
        return self.dropped_movies.filter(movie=movie).exists()
    # --- КОНЕЦ МЕТОДОВ СТАТУСОВ ФИЛЬМОВ ---

    # --- МЕТОДЫ СТАТУСОВ КНИГ---
    def is_read(self, book):
        if not isinstance(book, Book): return False
        return self.read_books.filter(book=book).exists()

    def is_reading(self, book):
        if not isinstance(book, Book): return False
        return self.reading_books.filter(book=book).exists()

    def is_book_dropped(self, book): # Назовем is_book_dropped для уникальности
        if not isinstance(book, Book): return False
        return self.dropped_books.filter(book=book).exists()
    # --- КОНЕЦ МЕТОДОВ СТАТУСОВ КНИГ ---

    class Meta:
        managed = True
        db_table = 'Users'

    def __str__(self) -> str:
        return self.username


# МОДЕЛЬ ИГР (Game)
# --------------------------------------------------------------------------
class Game(models.Model):
    game_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    summary = models.TextField(null=True, blank=True)
    first_release_date = models.IntegerField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    company = models.CharField(max_length=255, null=True, blank=True)

    cover_url = models.URLField(null=True, blank=True)
    videos = models.JSONField(null=True, blank=True)

    genres = models.JSONField(null=True, blank=True)
    platforms = models.JSONField(null=True, blank=True)
    game_modes = models.JSONField(null=True, blank=True)
    screenshots = models.JSONField(null=True, blank=True)
    similar_games = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    websites = models.JSONField(null=True, blank=True)
    multiplayer_modes = models.JSONField(default=list, blank=True, null=True)

    video_custom = models.FileField(upload_to='videos_uploaded', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])])
    custom_photo = models.URLField(null=True, blank=True)
    custom_header_photo = models.URLField(null=True, blank=True)
    youtube_trailer = models.CharField(max_length=50, blank=True, null=True)

    is_main_game = models.BooleanField(default=False)
    is_recently_trending_small = models.BooleanField(default=False)
    is_recently_trending_big = models.BooleanField(default=False)
    is_new_game = models.BooleanField(default=False)
    is_age_limit = models.BooleanField(default=False)

    rating_color = models.CharField(max_length=7, default="white")
    btn_color = models.CharField(max_length=7, default="FF003C")

    total_rating = models.FloatField(null=True, blank=True)
    total_rating_count = models.IntegerField(null=True, blank=True)

    mgb_average_rating = models.FloatField(null=True, blank=True, default=None) # <-- НАШЕ НОВОЕ ПОЛЕ
    mgb_rating_count = models.PositiveIntegerField(default=0)

    def update_mgb_rating(self):
        """Пересчитывает и сохраняет средний MGB рейтинг и количество оценок."""
        # Получаем все оценки пользователей для этой игры
        ratings = self.user_ratings.all() # Используем related_name='user_ratings' из UserGameRating
        count = ratings.count()
        # Считаем среднее, если оценки есть
        avg = ratings.aggregate(average=Avg('rating'))['average']

        # Округляем среднее до одного знака после запятой, если оно не None
        self.mgb_average_rating = round(avg, 1) if avg is not None else None
        self.mgb_rating_count = count
        self.save(update_fields=['mgb_average_rating', 'mgb_rating_count'])

    def save(self, *args, **kwargs):
        if self.total_rating is not None:
            # Упрощенная логика определения цвета
            if 8 <= self.total_rating: self.rating_color = "#15B000"
            elif 5 <= self.total_rating < 8: self.rating_color = "#FCDA17"
            elif 1 < self.total_rating < 5: self.rating_color = "#FF4949"
            else: self.rating_color = "#B7485C"  # self.total_rating <= 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# МОДЕЛИ СТАТУСОВ ИГР (PlayedGame, PlayingGame, DroppedGame)
# --------------------------------------------------------------------------
class PlayedGame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="played_games")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="played_by", null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0) # Поле quantity кажется лишним для статусов

    class Meta:
        unique_together = ("user", "game")
        verbose_name = "Played Game"
        verbose_name_plural = "Played Games"

    def __str__(self):
        game_name = self.game.name if self.game else "N/A"
        return f"{self.user.username} - Played: {game_name}"


class PlayingGame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="playing_games")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="playing_by", null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "game")
        verbose_name = "Playing Game"
        verbose_name_plural = "Playing Games"

    def __str__(self):
        game_name = self.game.name if self.game else "N/A"
        return f"{self.user.username} - Playing: {game_name}"


class DroppedGame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dropped_games")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="dropped_by", null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "game")
        verbose_name = "Dropped Game"
        verbose_name_plural = "Dropped Games"

    def __str__(self):
        game_name = self.game.name if self.game else "N/A"
        return f"{self.user.username} - Dropped: {game_name}"


# МОДЕЛИ РЕЙТИНГОВ (GameRating, MovieRating)
# --------------------------------------------------------------------------
class GameRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Связь с игрой лучше делать через ForeignKey, если ID уникальны в твоей БД
    # game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="ratings")
    # Если используешь game_id из внешнего API, то IntegerField
    game_id = models.IntegerField() # Убедись, что это тот ID, который используется для Game
    rating = models.IntegerField() # TODO: Добавить валидаторы (1-10)

    class Meta:
        unique_together = ('user', 'game_id') # Пользователь может поставить только одну оценку игре
        verbose_name = "Game Rating"
        verbose_name_plural = "Game Ratings"

    def __str__(self):
        return f"{self.user.username} rated game {self.game_id} as {self.rating}"


# МОДЕЛЬ ФИЛЬМОВ (Movie)
# --------------------------------------------------------------------------
class Movie(models.Model): # Будем использовать эту модель и для сериалов
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255) # Для сериалов это будет 'name' из TMDB
    original_title = models.CharField(max_length=255, blank=True, null=True) # 'original_name' из TMDB
    overview = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    runtime = models.IntegerField(default=0)

    # Поля для сериалов
    number_of_seasons = models.IntegerField(null=True, blank=True) # <--- НОВОЕ ПОЛЕ
    number_of_episodes = models.IntegerField(null=True, blank=True) # <--- НОВОЕ ПОЛЕ
    first_air_date = models.DateField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)

    collection_name = models.CharField(max_length=255, null=True, blank=True) # Скорее всего не актуально для сериалов
    popularity = models.FloatField(default=0.0)
    original_language = models.CharField(max_length=10, blank=True, null=True)
    adult = models.BooleanField(default=False) # TMDB не всегда предоставляет это для сериалов, но поле может остаться
    genres = models.ManyToManyField('Genre', blank=True, related_name='tv_shows') # Изменим related_name если нужно
    actors = models.ManyToManyField('Actor', blank=True, related_name='tv_shows') # Изменим related_name
    crew = models.ManyToManyField('CrewMember', related_name="tv_shows_crew") # Изменим related_name
    similar_movies = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='similar_tv_shows') # Изменим related_name

    poster_path = models.CharField(max_length=255, blank=True, null=True)
    backdrop_path = models.CharField(max_length=255, blank=True, null=True)
    video_custom = models.FileField(upload_to='videos_uploaded/tv_shows', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])])
    custom_photo = models.URLField(null=True, blank=True)
    custom_header_photo = models.URLField(null=True, blank=True)
    youtube_trailer = models.CharField(max_length=50, blank=True, null=True)
    youtube_trailer_name = models.CharField(max_length=255, blank=True, null=True) 

    is_main_movie = models.BooleanField(default=False)
    is_recently_trending_small = models.BooleanField(default=False)
    is_recently_trending_big = models.BooleanField(default=False)

    rating_color = models.CharField(max_length=10, default="white")
    btn_color = models.CharField(max_length=10, default="FF003C")

    vote_average = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    mgb_average_rating = models.FloatField(null=True, blank=True, default=None)
    mgb_rating_count = models.PositiveIntegerField(default=0)

    # Важно: тип контента, чтобы различать фильмы и сериалы в одной модели
    CONTENT_TYPE_MOVIE = 'movie'
    CONTENT_TYPE_TV = 'tv'
    CONTENT_TYPE_CHOICES = [
        (CONTENT_TYPE_MOVIE, 'Фильм'),
        (CONTENT_TYPE_TV, 'Сериал/Аниме'),
    ]
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPE_CHOICES,
        default=CONTENT_TYPE_MOVIE,
    )

    def update_mgb_rating(self):
        pass

    def save(self, *args, **kwargs):
        if self.vote_average is not None:
            if 8 <= self.vote_average: self.rating_color = "#15B000"
            elif 5 <= self.vote_average < 8: self.rating_color = "#FCDA17"
            elif 1 < self.vote_average < 5: self.rating_color = "#FF4949"
            else: self.rating_color = "#B7485C"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"

    class Meta:
        verbose_name = "Контент (Фильм/Сериал)"
        verbose_name_plural = "Контент (Фильмы/Сериалы)"


# МОДЕЛИ, СВЯЗАННЫЕ С ФИЛЬМАМИ (Genre, Actor, CrewMember)
# --------------------------------------------------------------------------
class Genre(models.Model):
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    genre_photo = models.ImageField(upload_to='genres_images', blank=True, null=True, verbose_name='Изображение Жанра')

    def __str__(self):
        return self.name


class Actor(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    profile_path = models.CharField(max_length=255, blank=True, null=True)
    biography = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class CrewMember(models.Model):
    ROLE_CHOICES = [
        ("Director", "Director"),
        ("Screenwriter", "Screenwriter"),
        ("Producer", "Producer"),
        # Добавь другие роли по необходимости
    ]
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    job = models.CharField(max_length=50, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.job})"


# МОДЕЛИ СТАТУСОВ ФИЛЬМОВ (WatchedMovie, WatchingMovie, DroppedMovie)
# --------------------------------------------------------------------------
# Аналогично статусам игр, можно создать и статусы фильмов
class WatchedMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watched_movies")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="watched_by", null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "movie")
        verbose_name = "Watched Movie"
        verbose_name_plural = "Watched Movies"

    def __str__(self):
        movie_title = self.movie.title if self.movie else "N/A"
        return f"{self.user.username} - Watched: {movie_title}"


class WatchingMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watching_movies")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="watching_by", null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "movie")
        verbose_name = "Watching Movie"
        verbose_name_plural = "Watching Movies"

    def __str__(self):
        movie_title = self.movie.title if self.movie else "N/A"
        return f"{self.user.username} - Watching: {movie_title}"


class DroppedMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dropped_movies")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="dropped_by", null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "movie")
        verbose_name = "Dropped Movie"
        verbose_name_plural = "Dropped Movies"

    def __str__(self):
        movie_title = self.movie.title if self.movie else "N/A"
        return f"{self.user.username} - Dropped: {movie_title}"


# МОДЕЛЬ РЕЙТИНГА ФИЛЬМОВ
# --------------------------------------------------------------------------
class MovieRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Аналогично GameRating, лучше ForeignKey, если Movie есть в БД
    # movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="ratings")
    # Если используешь tmdb_id из API
    movie_id = models.IntegerField() # Убедись, что это tmdb_id
    rating = models.IntegerField() # TODO: Валидаторы 1-10

    class Meta:
        unique_together = ('user', 'movie_id')
        verbose_name = "Movie Rating"
        verbose_name_plural = "Movie Ratings"

    def __str__(self):
        return f"{self.user.username} rated movie {self.movie_id} as {self.rating}"


# МОДЕЛЬ КНИГ (Book)
# --------------------------------------------------------------------------
class Book(models.Model):
    google_id = models.CharField(max_length=255, unique=True, null=True) # <-- Google ID (строка)
    title = models.CharField(max_length=512)
    authors = models.JSONField(null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)

    published_date = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    categories = models.JSONField(null=True, blank=True)
    thumbnail = models.URLField(max_length=512, null=True, blank=True)

    isbn_13 = models.CharField(max_length=20, null=True, blank=True)
    custom_photo = models.URLField(max_length=512, null=True, blank=True)
    custom_header_photo = models.URLField(max_length=512, null=True, blank=True)

    is_main_book = models.BooleanField(default=False)
    is_recently_trending_small = models.BooleanField(default=False)

    rating_color = models.CharField(max_length=10, default="white")
    btn_color = models.CharField(max_length=10, default="FF003C")

    mgb_average_rating = models.FloatField(null=True, blank=True, default=None)
    mgb_rating_count = models.PositiveIntegerField(default=0)

    average_rating = models.FloatField(null=True, blank=True)
    ratings_count = models.IntegerField(null=True, blank=True)

    def update_mgb_rating(self):
        """Пересчитывает и сохраняет средний MGB рейтинг и количество оценок."""
        ratings = self.user_ratings.all() # Используем related_name='user_ratings' из UserBookRating
        count = ratings.count()
        avg = ratings.aggregate(average=Avg('rating'))['average']
        self.mgb_average_rating = round(avg, 1) if avg is not None else None
        self.mgb_rating_count = count
        self.save(update_fields=['mgb_average_rating', 'mgb_rating_count'])

    def save(self, *args, **kwargs):
        if self.average_rating is not None:
            if 8 <= self.average_rating: self.rating_color = "#15B000"
            elif 5 <= self.average_rating < 8: self.rating_color = "#FCDA17"
            elif 1 < self.average_rating < 5: self.rating_color = "#FF4949"
            else: self.rating_color = "#B7485C" # average_rating <= 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ReadBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="read_books")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="read_by", null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "book")
        verbose_name = "Read Book"
        verbose_name_plural = "Read Books"

    def __str__(self):
        book_title = self.book.title if self.book else "N/A"
        return f"{self.user.username} - Read: {book_title}"


class ReadingBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reading_books")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reading_by", null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "book")
        verbose_name = "Reading Book"
        verbose_name_plural = "Reading Books"

    def __str__(self):
        book_title = self.book.title if self.book else "N/A"
        return f"{self.user.username} - Reading: {book_title}"


class DroppedBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dropped_books")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="dropped_by", null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "book")
        verbose_name = "Dropped Book"
        verbose_name_plural = "Dropped Books"

    def __str__(self):
        book_title = self.book.title if self.book else "N/A"
        return f"{self.user.username} - Dropped: {book_title}"


# МОДЕЛИ ИЗБРАННОГО (FavoriteGame, FavoriteMovie, FavoriteBook)
# --------------------------------------------------------------------------
class FavoriteGame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_games")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="favorited_by", null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)  # Убрал quantity

    class Meta:
        unique_together = ("user", "game")
        verbose_name = "Favorite Game"
        verbose_name_plural = "Favorite Games"

    def __str__(self):
        game_name = self.game.name if self.game else "N/A"
        return f"{self.user.username} - Favorite: {game_name}"


class FavoriteMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_movies")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="favorited_by", null=True, blank=True) # Используем related_name="favorited_by" для единообразия
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)  # Убрал quantity

    class Meta:
        unique_together = ("user", "movie")
        verbose_name = "Favorite Movie"
        verbose_name_plural = "Favorite Movies"

    def __str__(self):
        movie_title = self.movie.title if self.movie else "N/A"
        return f"{self.user.username} - Favorite: {movie_title}"


# --- НОВАЯ МОДЕЛЬ ДЛЯ ИЗБРАННЫХ КНИГ ---
class FavoriteBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_books")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="favorited_by", null=True, blank=True)  # Используем related_name="favorited_by"
    added_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "book")
        verbose_name = "Favorite Book"
        verbose_name_plural = "Favorite Books"

    def __str__(self):
        book_title = self.book.title if self.book else "N/A"
        return f"{self.user.username} - Favorite: {book_title}"
# --------------------------------------------------------------------------


# МОДЕЛЬ КОММЕНТАРИЕВ (Comment)
# --------------------------------------------------------------------------
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments") # Добавил related_name
    # Используем ForeignKey к соответствующим моделям контента
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True, related_name="comments") # Изменил related_name
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True, related_name="comments") # Изменил related_name
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True, related_name="comments") # Изменил related_name

    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    likes = models.ManyToManyField(User, related_name="liked_comments", blank=True)

    # Ограничение: комментарий должен относиться хотя бы к одному объекту
    # (Можно добавить через clean метод или constraint в Meta, если нужно)

    def like_count(self):
        return self.likes.count()

    def __str__(self):
        # Определяем, к чему относится комментарий для __str__
        related_object_str = ""
        if self.game: related_object_str = f"Game: {self.game.name[:20]}..."
        elif self.movie: related_object_str = f"Movie: {self.movie.title[:20]}..."
        elif self.book: related_object_str = f"Book: {self.book.title[:20]}..."
        return f"Comment by {self.user.username} on {related_object_str}: {self.title}"


# --- МОДЕЛИ ПЕРСОНАЛЬНОГО РЕЙТИНГА ПОЛЬЗОВАТЕЛЯ ---
# --------------------------------------------------------------------------
class UserMovieRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="movie_ratings")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="user_ratings")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        verbose_name = "User Movie Rating"
        verbose_name_plural = "User Movie Ratings"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}'s rating for {self.movie.title}: {self.rating}/10"


class UserGameRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="game_ratings")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="user_ratings")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'game')
        verbose_name = "User Game Rating"
        verbose_name_plural = "User Game Ratings"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}'s rating for {self.game.name}: {self.rating}/10"


class UserBookRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="book_ratings")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="user_ratings")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')
        verbose_name = "User Book Rating"
        verbose_name_plural = "User Book Ratings"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}'s rating for {self.book.title}: {self.rating}/10"