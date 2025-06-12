import requests
import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("GOOGLE_API_KEY")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

COUNTRY_ABBREVIATIONS = {
    "United States of America": "USA",
    "United Kingdom": "UK",
}


def get_country_abbreviation(country_string):
    countries = [c.strip() for c in country_string.split(',')]
    abbreviated = [COUNTRY_ABBREVIATIONS.get(c, c) for c in countries]
    return ', '.join(abbreviated)


def format_runtime(minutes):
    if not minutes or minutes <= 0:
        return "Unknown"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}min" if hours else f"{mins}min"


def get_youtube_trailer_with_name(query):
    """Ищет трейлер на YouTube и возвращает словарь с videoId и названием."""
    search_query = f"{query} official trailer"
    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": search_query,
        "key": YOUTUBE_API_KEY,
        "maxResults": 1,
        "type": "video",
        "videoEmbeddable": "true"
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "error" in data:
        print(f"❌ Ошибка API: {data['error']['message']}")
        return None

    if "items" in data and data["items"]:
        video = data["items"][0]
        return {
            "id": video["id"]["videoId"],
            "title": video["snippet"]["title"]
        }

    print(f"❌ Трейлер не найден для {query}")
    return None


def get_tmdb_data(endpoint, params=None):
    """Функция для выполнения GET-запросов к TMDb API."""
    url = f"{TMDB_BASE_URL}/{endpoint}"
    params = params or {}
    params["api_key"] = TMDB_API_KEY

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None


def get_platform_icon_path(platform_name):
    """
    Возвращает путь к иконке платформы.
    """

    xbox = ["Xbox Series X|S", "Xbox One", "Xbox 360"]
    playstation = ["PlayStation 5", "PlayStation 4", "PlayStation 3", "PlayStation 2", "PlayStation", "PlayStation Portable"]
    mobile = ["Android", "iOS", "Google Stadia"]
    pc = ["PC (Microsoft Windows)", "Mac", "Linux", "DOS", "Family Computer"]

    nintendo_switch = ["Nintendo Switch", "Nintendo 64", "Wii", "Nintendo GameCube", "Nintendo Entertainment System", "Wii U", "Super Nintendo Entertainment System"]

    if platform_name in xbox:
        return "imgs/platforms/xbox_icon.svg"
    elif platform_name in playstation:
        return "imgs/platforms/ps_icon.svg"
    elif platform_name in mobile:
        return "imgs/platforms/mobile_icon.svg"
    elif platform_name in pc:
        return "imgs/platforms/pc_icon.svg"
    elif platform_name in nintendo_switch:
        return "imgs/platforms/nintendo_switch_icon.svg"
    return "imgs/platforms/pc_icon.svg"
