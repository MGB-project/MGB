from django.core.management.base import BaseCommand
from users.models import Movie, Genre, Actor, CrewMember # Убедись, что пути к моделям верные
from mgb_main.utils import get_tmdb_data # Твоя утилита для TMDB
import time
from datetime import datetime

class Command(BaseCommand):
    help = "Загружает до N популярных сериалов (включая аниме) из TMDb"

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=50, # По умолчанию 50 страниц (50 * 20 = 1000 сериалов)
            help='Количество страниц для загрузки с TMDb (20 сериалов на страницу)',
        )
        parser.add_argument(
            '--start-page',
            type=int,
            default=1,
            help='Номер страницы, с которой начать загрузку',
        )

    def handle(self, *args, **kwargs):
        total_pages_to_fetch = kwargs['pages']
        start_page = kwargs['start_page']
        tv_shows_loaded_count = 0
        MAX_TV_SHOWS_PER_RUN = total_pages_to_fetch * 20 # Примерно

        BASE_IMAGE_URL = "https://image.tmdb.org/t/p/original"

        # Загрузка жанров для TV
        # TMDB использует разные ID жанров для фильмов и сериалов
        genres_data = get_tmdb_data("genre/tv/list", {"language": "ru-RU"})
        if genres_data and "genres" in genres_data:
            for g_data in genres_data["genres"]:
                genre, created = Genre.objects.update_or_create(
                    tmdb_id=g_data["id"], # Используем TMDB ID как уникальный идентификатор
                    defaults={"name": g_data["name"]}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Добавлен жанр TV: {genre.name}"))
            self.stdout.write(self.style.SUCCESS("Жанры TV обновлены/загружены."))
        else:
            self.stdout.write(self.style.WARNING("Не удалось загрузить жанры TV."))


        self.stdout.write(f"Начинаем загрузку сериалов с TMDb, со страницы {start_page} по {start_page + total_pages_to_fetch -1}...")

        for page_num in range(start_page, start_page + total_pages_to_fetch):
            self.stdout.write(f"--- Загрузка страницы {page_num} ---")
            # Используем эндпоинт для популярных TV шоу
            data = get_tmdb_data("tv/popular", {"language": "ru-RU", "page": page_num})

            if not data or "results" not in data:
                self.stdout.write(self.style.ERROR(f"Ошибка загрузки данных для страницы {page_num} или нет результатов."))
                continue # или break, если хочешь остановить при первой ошибке

            for tv_item in data["results"]:
                tmdb_id = tv_item.get("id")
                if not tmdb_id:
                    self.stdout.write(self.style.WARNING("❗ Пропущен сериал без TMDB ID"))
                    continue

                first_air_date_str = tv_item.get("first_air_date")
                first_air_date_obj = None
                if first_air_date_str:
                    try:
                        first_air_date_obj = datetime.strptime(first_air_date_str, "%Y-%m-%d").date()
                    except ValueError:
                        self.stdout.write(self.style.WARNING(f"❗ Неверный формат даты '{first_air_date_str}' для {tv_item.get('name')} (ID: {tmdb_id})"))
                        # Можно пропустить или сохранить без даты
                        # continue

                # Проверка на дубликат по tmdb_id перед запросом деталей, если нужно экономить запросы
                # if Movie.objects.filter(tmdb_id=tmdb_id, content_type=Movie.CONTENT_TYPE_TV).exists():
                #     self.stdout.write(self.style.NOTICE(f"Сериал {tv_item.get('name')} (ID: {tmdb_id}) уже существует. Пропускаем."))
                #     continue

                # Получаем детальную информацию для количества сезонов/серий и др.
                tv_details = get_tmdb_data(f"tv/{tmdb_id}", {"language": "ru-RU", "append_to_response": "credits,similar,videos"})
                if not tv_details:
                    self.stdout.write(self.style.WARNING(f"❗ Не удалось загрузить детали для {tv_item.get('name')} (ID: {tmdb_id}). Пропускаем."))
                    continue

                poster_path = tv_details.get("poster_path")
                backdrop_path = tv_details.get("backdrop_path")

                defaults = {
                    "title": tv_details.get("name", "Без названия"),
                    "original_title": tv_details.get("original_name", ""),
                    "overview": tv_details.get("overview", ""),
                    "first_air_date": first_air_date_obj, # Используем сконвертированную дату
                    # "release_date": first_air_date_obj, # Если используешь поле release_date
                    "poster_path": f"{BASE_IMAGE_URL}{poster_path}" if poster_path else None,
                    "backdrop_path": f"{BASE_IMAGE_URL}{backdrop_path}" if backdrop_path else None,
                    "vote_average": tv_details.get("vote_average", 0),
                    "vote_count": tv_details.get("vote_count", 0),
                    "popularity": tv_details.get("popularity", 0),
                    "original_language": tv_details.get("original_language", ""),
                    "adult": tv_details.get("adult", False), # Редко используется для TV в TMDB API, но можно оставить
                    "number_of_seasons": tv_details.get("number_of_seasons"),
                    "number_of_episodes": tv_details.get("number_of_episodes"),
                    "country": ", ".join([c["name"] for c in tv_details.get("production_countries", [])]),
                    "runtime": tv_details.get("episode_run_time")[0] if tv_details.get("episode_run_time") else 0,
                    "content_type": Movie.CONTENT_TYPE_TV, # Явно указываем тип контента
                }

                tv_show_obj, created = Movie.objects.update_or_create(
                    tmdb_id=tmdb_id,
                    defaults=defaults
                )

                tv_shows_loaded_count += 1
                action = "📺 Добавлен" if created else "🔄 Обновлен"
                self.stdout.write(self.style.SUCCESS(f"{action} сериал: {tv_show_obj.title} (TMDB ID: {tv_show_obj.tmdb_id})"))

                # Обновление жанров для сериала
                if "genres" in tv_details: # Жанры берем из деталей
                    tv_show_obj.genres.clear() # Очищаем старые, если обновляем
                    for genre_data in tv_details["genres"]:
                        genre = Genre.objects.filter(tmdb_id=genre_data["id"]).first()
                        if genre:
                            tv_show_obj.genres.add(genre)
                        else:
                            self.stdout.write(self.style.WARNING(f"Жанр с TMDB ID {genre_data['id']} ({genre_data['name']}) не найден в БД."))


                # Загрузка актеров (из credits)
                if tv_details.get("credits") and "cast" in tv_details["credits"]:
                    tv_show_obj.actors.clear()
                    for actor_data in tv_details["credits"]["cast"][:15]: # Например, топ-15 актеров
                        actor_profile_path = actor_data.get("profile_path")
                        actor_obj, _ = Actor.objects.update_or_create(
                            tmdb_id=actor_data["id"],
                            defaults={
                                "name": actor_data["name"],
                                "profile_path": f"{BASE_IMAGE_URL}{actor_profile_path}" if actor_profile_path else None,
                            },
                        )
                        tv_show_obj.actors.add(actor_obj)

                # Загрузка съемочной группы (создатели, режиссеры и т.д. - job: "Creator", "Executive Producer")
                # TMDB для сериалов часто использует поле 'created_by' на верхнем уровне деталей
                # А также 'crew' в 'credits'
                tv_show_obj.crew.clear()
                creators_added = set()

                if "created_by" in tv_details:
                    for creator_data in tv_details["created_by"]:
                        if creator_data["id"] not in creators_added:
                            member_obj, _ = CrewMember.objects.update_or_create(
                                tmdb_id=creator_data["id"],
                                defaults={
                                    "name": creator_data["name"],
                                    "job": "Creator", # Явно указываем роль
                                },
                            )
                            tv_show_obj.crew.add(member_obj)
                            creators_added.add(creator_data["id"])
                
                if tv_details.get("credits") and "crew" in tv_details["credits"]:
                    for crew_data in tv_details["credits"]["crew"]:
                        # Добавляем режиссеров, сценаристов, продюсеров, если они еще не добавлены как создатели
                        if crew_data["job"] in ["Director", "Screenplay", "Producer", "Executive Producer"] and crew_data["id"] not in creators_added:
                             member_obj, _ = CrewMember.objects.update_or_create(
                                tmdb_id=crew_data["id"],
                                defaults={
                                    "name": crew_data["name"],
                                    "job": crew_data["job"],
                                },
                            )
                             tv_show_obj.crew.add(member_obj)


                # Загрузка похожих сериалов (из similar)
                if tv_details.get("similar") and "results" in tv_details["similar"]:
                    tv_show_obj.similar_movies.clear() # или similar_tv_shows, если изменил related_name
                    for similar_item in tv_details["similar"]["results"][:5]: # Топ-5 похожих
                        similar_tmdb_id = similar_item.get("id")
                        if not similar_tmdb_id: continue

                        s_first_air_date_str = similar_item.get("first_air_date")
                        s_first_air_date_obj = None
                        if s_first_air_date_str:
                            try:
                                s_first_air_date_obj = datetime.strptime(s_first_air_date_str, "%Y-%m-%d").date()
                            except ValueError:
                                pass # Пропускаем, если дата неверная у похожего

                        s_poster_path = similar_item.get("poster_path")
                        s_backdrop_path = similar_item.get("backdrop_path")

                        # Здесь мы создаем "заглушки" для похожих сериалов, если их еще нет.
                        # Полноценно они загрузятся, когда до них дойдет очередь в основном цикле.
                        similar_obj, _ = Movie.objects.update_or_create(
                            tmdb_id=similar_tmdb_id,
                            defaults={
                                "title": similar_item.get("name", "Без названия"),
                                "original_title": similar_item.get("original_name", ""),
                                "overview": similar_item.get("overview", ""), # Можно не заполнять для заглушек
                                "first_air_date": s_first_air_date_obj,
                                "poster_path": f"{BASE_IMAGE_URL}{s_poster_path}" if s_poster_path else None,
                                "backdrop_path": f"{BASE_IMAGE_URL}{s_backdrop_path}" if s_backdrop_path else None,
                                "vote_average": similar_item.get("vote_average", 0),
                                "popularity": similar_item.get("popularity", 0),
                                "content_type": Movie.CONTENT_TYPE_TV,
                                "country": ",".join(tv_details.get("origin_country", [])),
                            }
                        )
                        tv_show_obj.similar_movies.add(similar_obj)

                # Загрузка трейлеров из videos
                if tv_details.get("videos") and "results" in tv_details["videos"]:
                    # Ищем официальный трейлер на русском или английском
                    trailer_key = None
                    trailer_name = None
                    for video in tv_details["videos"]["results"]:
                        is_trailer = video.get("type") == "Trailer"
                        is_official = video.get("official") is True
                        site_is_youtube = video.get("site") == "YouTube"
                        lang_ru = video.get("iso_639_1") == "ru"
                        lang_en = video.get("iso_639_1") == "en"

                        if site_is_youtube and is_trailer:
                            if is_official and (lang_ru or lang_en): # Приоритет официальным
                                trailer_key = video.get("key")
                                trailer_name = video.get("name")
                                if lang_ru: break
                            elif trailer_key is None and (lang_ru or lang_en): # Если нет официального, берем любой подходящий
                                trailer_key = video.get("key")
                                trailer_name = video.get("name")
                    
                    if trailer_key:
                        tv_show_obj.youtube_trailer = trailer_key
                        tv_show_obj.youtube_trailer_name = trailer_name
                        tv_show_obj.save(update_fields=['youtube_trailer', 'youtube_trailer_name'])


                if tv_shows_loaded_count >= MAX_TV_SHOWS_PER_RUN and total_pages_to_fetch * 20 == MAX_TV_SHOWS_PER_RUN : # Если лимит был задан через --pages
                    self.stdout.write(self.style.SUCCESS(f"Достигнут лимит в {MAX_TV_SHOWS_PER_RUN} сериалов за запуск."))
                    # break # Раскомментируй, если хочешь прервать внешний цикл
                    return # Лучше так, чтобы выйти из handle

                time.sleep(0.3) # Небольшая задержка, чтобы не перегружать API TMDB (1-3 запроса на сериал)

            self.stdout.write(self.style.NOTICE(f"✅ Обработано сериалов на странице {page_num}: {len(data['results'])}. Всего загружено/обновлено: {tv_shows_loaded_count}"))
            # time.sleep(1) # Задержка между страницами, если нужна

        self.stdout.write(self.style.SUCCESS(f"🎬 Всего загружено/обновлено {tv_shows_loaded_count} сериалов!"))