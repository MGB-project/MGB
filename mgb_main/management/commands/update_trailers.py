from django.core.management.base import BaseCommand
from users.models import Game, Movie
from mgb_main.utils import get_youtube_trailer_with_name


class Command(BaseCommand):
    help = "Обновляет YouTube трейлеры для всех игр и фильмов"

    def handle(self, *args, **kwargs):
        self.update_game_trailers()
        self.update_movie_trailers()

    def update_game_trailers(self):
        games = Game.objects.filter(youtube_trailer__isnull=True)

        if not games.exists():
            self.stdout.write(self.style.WARNING("⚠️ Все трейлеры для игр уже обновлены."))
        else:
            self.stdout.write(self.style.SUCCESS("🎮 Обновление трейлеров для игр:"))

        for game in games:
            video_id = get_youtube_trailer_with_name(game.name)
            if not video_id:
                self.stdout.write(self.style.WARNING(f'❌ Трейлер не найден для игры {game.name}'))
                continue

            game.youtube_trailer = video_id['id']
            game.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Обновлён трейлер для игры {game.name}: {video_id["id"]}'))

    def update_movie_trailers(self):
        movies = Movie.objects.filter(youtube_trailer__isnull=True)

        if not movies.exists():
            self.stdout.write(self.style.WARNING("⚠️ Все трейлеры для фильмов уже обновлены."))
        else:
            self.stdout.write(self.style.SUCCESS("🎬 Обновление трейлеров для фильмов:"))

        for movie in movies:
            video_data = get_youtube_trailer_with_name(movie.title)
            if not video_data:
                self.stdout.write(self.style.WARNING(f'❌ Трейлер не найден для фильма {movie.title}'))
                continue

            movie.youtube_trailer = video_data['id']
            movie.youtube_trailer_name = video_data['title']
            movie.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Обновлён трейлер для фильма {movie.title}: {video_data["id"]} | {video_data["title"]}'))
