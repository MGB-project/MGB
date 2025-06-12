import re
import requests
import os
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from users.models import Game

load_dotenv()

client_id_games = os.getenv("CLIENT_ID")
auth_games_token = os.getenv("AUTHORIZATION_GAMES_TOKEN")

API_URL = "https://api.igdb.com/v4/games"
COMPANY_API_URL = "https://api.igdb.com/v4/involved_companies"
HEADERS = {
    "Client-ID": f"{client_id_games}",
    "Authorization": f"Bearer {auth_games_token}"
}


class Command(BaseCommand):
    help = "Fetch and store games from IGDB API"

    def handle(self, *args, **kwargs):
        total_games = []  # Список для всех загруженных игр
        batch_size = 500   # Максимальное количество игр за раз
        max_games = 10000  # Сколько всего игр нужно загрузить

        for offset in range(0, max_games, batch_size):
            query = f"""
            fields name, id, total_rating, total_rating_count, cover.url, platforms.name, summary, videos, 
                   first_release_date, involved_companies, genres.name, game_modes.name, screenshots.url, 
                   similar_games, status, websites.url, multiplayer_modes.*;
            limit {batch_size};
            offset {offset};
            """
            response = requests.post(API_URL, headers=HEADERS, data=query)

            if response.status_code == 200:
                games = response.json()
                total_games.extend(games)

                for game in games:
                    company_name = self.get_company_name(game.get("involved_companies"))

                    Game.objects.update_or_create(
                        game_id=game["id"],
                        defaults={
                            "name": game["name"],
                            "total_rating": round(game["total_rating"] / 10, 1) if game.get("total_rating") else None,
                            "total_rating_count": game.get("total_rating_count"),
                            "cover_url": self.get_high_quality_cover(game["cover"]["url"]) if "cover" in game else None,
                            "platforms": game.get("platforms"),
                            "summary": self.get_short_summary(game.get("summary")),
                            "videos": game.get("videos"),
                            "first_release_date": game.get("first_release_date"),
                            "company": company_name,
                            "genres": [
                                re.search(r"\((.*?)\)", genre["name"]).group(1) if "(" in genre["name"] else genre["name"]
                                for genre in game.get("genres", [])
                            ] if "genres" in game else [],
                            "game_modes": [mode["name"] for mode in game.get("game_modes", [])] if "game_modes" in game else [],
                            "screenshots": [self.get_high_quality_screenshot(screenshot["url"]) for screenshot in game.get("screenshots", [])] if "screenshots" in game else [],
                            "similar_games": game.get("similar_games"),
                            "status": game.get("status"),
                            "websites": [website["url"] for website in game.get("websites", [])] if "websites" in game else [],
                            "multiplayer_modes": game.get("multiplayer_modes", [])
                        }
                    )

                self.stdout.write(self.style.SUCCESS(f"Загружено {len(games)} игр (offset {offset})"))
            else:
                self.stderr.write(f"Ошибка загрузки: {response.status_code}")
                break

        self.stdout.write(self.style.SUCCESS(f"Всего загружено {len(total_games)} игр"))

    def get_company_name(self, involved_companies):
        """ Получает название компании-разработчика """
        if not involved_companies:
            return None

        company_query = f"""
        fields company.name;
        where id = ({', '.join(map(str, involved_companies))});
        limit 1;
        """
        response = requests.post(COMPANY_API_URL, headers=HEADERS, data=company_query)

        if response.status_code == 200:
            companies = response.json()
            if companies:
                return companies[0].get("company", {}).get("name")
        return None

    def get_high_quality_cover(self, cover_url):
        """ Улучшает качество обложки """
        if not cover_url:
            return None
        return cover_url.replace("t_thumb", "t_1080p")

    def get_high_quality_screenshot(self, screenshot_url):
        """ Улучшает качество скриншота """
        if not screenshot_url:
            return None
        return screenshot_url.replace("t_thumb", "t_1080p")

    def get_short_summary(self, summary):
        """ Обрезает описание до 2 предложений """
        if not summary:
            return None
        sentences = summary.split(". ")
        return ". ".join(sentences[:2]) + (". " if len(sentences) > 2 else "")
