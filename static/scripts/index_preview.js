document.addEventListener('DOMContentLoaded', function () {
  const buttons = document.querySelectorAll('.tracking-lists, .ratings-reviews, .friends-social-features, .discovery-recs');

  buttons.forEach(button => {
    button.addEventListener('click', function () {
      const plusIcon = button.querySelector('.plus-icon');
      const plusIconPath = button.getAttribute('data-plus-icon');
      const minusIconPath = button.getAttribute('data-minus-icon');

      // Найти связанный контентный блок (следующий элемент)
      const contentBlock = button.nextElementSibling;

      // Переключаем класс active
      button.classList.toggle('active');
      contentBlock.classList.toggle('active'); // Показываем/скрываем блок

      // Меняем иконку после завершения анимации
      if (button.classList.contains('active')) {
        setTimeout(() => {
          plusIcon.src = minusIconPath;
        }, 500);
      } else {
        setTimeout(() => {
          plusIcon.src = plusIconPath;
        }, 500);
      }
    });
  });
});
