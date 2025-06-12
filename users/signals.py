# users/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import UserGameRating, UserMovieRating, UserBookRating


@receiver(post_save, sender=UserGameRating)
@receiver(post_delete, sender=UserGameRating)
def update_game_mgb_rating_on_change(sender, instance, **kwargs):
    """
    Вызывается после сохранения или удаления UserGameRating.
    Обновляет средний рейтинг связанной игры.
    """
    # instance.game ссылается на объект Game, связанный с измененным/удаленным рейтингом
    if instance.game:
        instance.game.update_mgb_rating()


@receiver(post_save, sender=UserMovieRating)
@receiver(post_delete, sender=UserMovieRating)
def update_movie_mgb_rating_on_change(sender, instance, **kwargs):
    """Обновляет средний рейтинг связанного фильма."""
    if instance.movie:
        instance.movie.update_mgb_rating()


@receiver(post_save, sender=UserBookRating)
@receiver(post_delete, sender=UserBookRating)
def update_book_mgb_rating_on_change(sender, instance, **kwargs):
    """Обновляет средний рейтинг связанной книги."""
    if instance.book:
        instance.book.update_mgb_rating()