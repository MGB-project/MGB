from django.urls import path
from .views import games, game_detail

urlpatterns = [
    path("", games, name="games"),
    path("<int:game_id>/", game_detail, name="game_detail"),
]
