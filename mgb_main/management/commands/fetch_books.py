import requests
import os
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from users.models import Book  # Убедись, что модель Book существует и подключена

load_dotenv()

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Количество книг, которое нужно скачать
TOTAL_BOOKS = 10000
MAX_RESULTS = 40  # Максимум книг за один запрос (в Google API ограничение — 40 книг на запрос)


# Функция для получения всех уникальных категорий
def get_unique_categories():
    categories = set()
    genres = [
        "Art", "Biography", "Business", "Children", "Comics", "Cooking", "Health", "History",
        "Literature", "Mathematics", "Music", "Philosophy", "Poetry", "Religion", "Science",
        "Self-Help", "Sports", "Technology", "Travel"
    ]

    for genre in genres:
        params = {
            "q": f"subject:{genre}",
            "key": GOOGLE_API_KEY,
            "maxResults": 40
        }
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            for item in items:
                volume_info = item.get("volumeInfo", {})
                book_categories = volume_info.get("categories", [])
                categories.update(book_categories)
        else:
            print(f"Ошибка при загрузке категории {genre}: {response.status_code}")

    return list(categories)


class Command(BaseCommand):
    help = "Fetch and store books from Google Books API"

    def handle(self, *args, **kwargs):
        total_books = 0
        max_requests = TOTAL_BOOKS // MAX_RESULTS
        if TOTAL_BOOKS % MAX_RESULTS != 0:
            max_requests += 1

        # Получаем список уникальных категорий
        all_categories = get_unique_categories()

        # Перебираем все категории
        for category in all_categories:
            if category in ["Beard", "Children", "Literature"]:  # Пример исключения неправильных категорий
                continue

            print(f"Загружаем книги для категории: {category}")  # Логирование категории

            for start_index in range(0, max_requests * MAX_RESULTS, MAX_RESULTS):
                if total_books >= TOTAL_BOOKS:
                    break

                params = {
                    "q": f"subject:{category}",
                    "startIndex": start_index,
                    "maxResults": MAX_RESULTS,
                    "key": GOOGLE_API_KEY,
                }

                response = requests.get(GOOGLE_BOOKS_API_URL, params=params)

                if response.status_code == 200:
                    data = response.json()
                    books = data.get("items", [])

                    for item in books:
                        volume_info = item.get("volumeInfo", {})
                        identifiers = volume_info.get("industryIdentifiers", [])
                        isbn_13 = next((i["identifier"] for i in identifiers if i["type"] == "ISBN_13"), None)

                        # Сохраняем или обновляем книгу
                        Book.objects.update_or_create(
                            google_id=item["id"],
                            defaults={
                                "title": volume_info.get("title"),
                                "authors": volume_info.get("authors", []),
                                "published_date": volume_info.get("publishedDate"),
                                "description": self.get_short_description(volume_info.get("description")),
                                "categories": volume_info.get("categories", []),
                                "average_rating": volume_info.get("averageRating"),
                                "ratings_count": volume_info.get("ratingsCount"),
                                "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail"),
                                "language": volume_info.get("language"),
                                "isbn_13": isbn_13,
                            }
                        )

                        total_books += 1
                        if total_books >= TOTAL_BOOKS:
                            break

                    self.stdout.write(self.style.SUCCESS(f"{len(books)} книг загружено по категории '{category}' (начиная с {start_index})"))
                else:
                    self.stderr.write(f"Ошибка API: {response.status_code}")
                    break

            if total_books >= TOTAL_BOOKS:
                break

        self.stdout.write(self.style.SUCCESS(f"Всего загружено книг: {total_books}"))

    def get_short_description(self, description):
        if not description:
            return None
        sentences = description.split(". ")
        return ". ".join(sentences[:2]) + (". " if len(sentences) > 2 else "")
