from django.core.management.base import BaseCommand
from users.models import Movie, Genre, Actor, CrewMember
from mgb_main.utils import get_tmdb_data
import time


class Command(BaseCommand):
    help = "Загружает до 10 000 популярных фильмов из TMDb"

    def handle(self, *args, **kwargs):
        total_pages = 500
        movies_loaded = 0

        BASE_IMAGE_URL = "https://image.tmdb.org/t/p/original"

        genres_data = get_tmdb_data("genre/movie/list", {"language": "ru-RU"})
        if genres_data and "genres" in genres_data:
            for g in genres_data["genres"]:
                Genre.objects.update_or_create(
                    tmdb_id=g["id"],
                    defaults={"name": g["name"]}
                )

        for page in range(1, total_pages + 1):
            data = get_tmdb_data("movie/popular", {"language": "ru-RU", "page": page})
            if not data:
                self.stdout.write(self.style.ERROR(f"Ошибка загрузки данных для страницы {page}"))
                break

            for item in data["results"]:
                release_date = item.get("release_date", None)

                if not release_date:
                    self.stdout.write(self.style.WARNING(f"❗ Пропущен фильм {item['title']} (ID: {item['id']}) из-за отсутствия даты выпуска"))
                    continue

                poster_path = item.get("poster_path")
                backdrop_path = item.get("backdrop_path")

                movie, created = Movie.objects.update_or_create(
                    tmdb_id=item["id"],
                    defaults={
                        "title": item["title"],
                        "original_title": item.get("original_title", ""),
                        "overview": item.get("overview", ""),
                        "release_date": release_date,
                        "poster_path": f"{BASE_IMAGE_URL}{poster_path}" if poster_path else None,
                        "backdrop_path": f"{BASE_IMAGE_URL}{backdrop_path}" if backdrop_path else None,
                        "vote_average": item.get("vote_average", 0),
                        "vote_count": item.get("vote_count", 0),
                        "popularity": item.get("popularity", 0),
                        "original_language": item.get("original_language", ""),
                        "adult": item.get("adult", False),
                        "video": item.get("video", False),
                    },
                )

                movies_loaded += 1
                action = "Добавлен" if created else "Обновлен"
                self.stdout.write(self.style.SUCCESS(f"{action} фильм: {movie.title} (ID: {movie.tmdb_id})"))

                # Обновление жанров
                if "genre_ids" in item:
                    for genre_id in item["genre_ids"]:
                        genre = Genre.objects.filter(tmdb_id=genre_id).first()
                        if genre:
                            movie.genres.add(genre)

                # Загрузка актеров и съемочной группы
                credits = get_tmdb_data(f"movie/{movie.tmdb_id}/credits")
                if credits:
                    if "cast" in credits:
                        for actor in credits["cast"][:10]:
                            actor_obj, _ = Actor.objects.get_or_create(
                                tmdb_id=actor["id"],
                                defaults={
                                    "name": actor["name"],
                                    "profile_path": actor.get("profile_path"),
                                },
                            )
                            movie.actors.add(actor_obj)

                    if "crew" in credits:
                        for crew_member in credits["crew"]:
                            if crew_member["job"] in ["Director", "Screenplay", "Producer"]:
                                member_obj, _ = CrewMember.objects.get_or_create(
                                    tmdb_id=crew_member["id"],
                                    defaults={
                                        "name": crew_member["name"],
                                        "job": crew_member["job"],
                                    },
                                )
                                movie.crew.add(member_obj)

                # Загрузка детальной информации (страна и продолжительность)
                details = get_tmdb_data(f"movie/{movie.tmdb_id}", {"language": "ru-RU"})
                if details:
                    countries = ", ".join([c["name"] for c in details.get("production_countries", [])])
                    runtime = details.get("runtime", 0)

                    movie.country = countries
                    movie.runtime = runtime
                    movie.save()

                # Загрузка похожих фильмов
                similar_movies_data = get_tmdb_data(f"movie/{movie.tmdb_id}/similar", {"language": "ru-RU"})

                if similar_movies_data and "results" in similar_movies_data:
                    for similar in similar_movies_data["results"][:5]:  # Ограничение на 5 похожих фильмов
                        release_date = similar.get("release_date")
                        if not release_date:  # Пропускаем фильмы без даты
                            continue

                        similar_movie, _ = Movie.objects.get_or_create(
                            tmdb_id=similar["id"],
                            defaults={
                                "title": similar["title"],
                                "original_title": similar.get("original_title", ""),
                                "overview": similar.get("overview", ""),
                                "release_date": release_date,
                                "content_type": Movie.CONTENT_TYPE_MOVIE,
                                "poster_path": f"{BASE_IMAGE_URL}{similar.get('poster_path')}" if similar.get("poster_path") else None,
                                "backdrop_path": f"{BASE_IMAGE_URL}{similar.get('backdrop_path')}" if similar.get("backdrop_path") else None,
                                "vote_average": similar.get("vote_average", 0),
                                "vote_count": similar.get("vote_count", 0),
                                "popularity": similar.get("popularity", 0),
                                "original_language": similar.get("original_language", ""),
                                "adult": similar.get("adult", False),
                                "video": similar.get("video", False),
                            },
                        )

                        movie.similar_movies.add(similar_movie)  # Добавляем связь

            self.stdout.write(self.style.NOTICE(f"✅ Загружено фильмов: {movies_loaded} / 10 000"))
            time.sleep(1)

            if movies_loaded >= 10_000:
                break

        self.stdout.write(self.style.SUCCESS(f"🎬 Всего загружено {movies_loaded} фильмов!"))
