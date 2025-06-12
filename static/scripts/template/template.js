// ui_interactions.js (или template_ui.js)
document.addEventListener("DOMContentLoaded", function () {
  // --- Логика для выпадающих меню (если они у вас есть и не связаны с поиском) ---
  // Пример: если у вас есть другие выпадающие меню, управляемые JS
  // let searchButton = document.getElementById("dropdownButtonSearch"); // Убрано, т.к. поиск отдельно
  // let searchMenu = document.getElementById("dropdownSearch"); // Убрано

  let languageButton = document.getElementById("dropdownButtonLanguage"); // Если это кнопка языка
  let languageMenu = document.getElementById("dropdownLanguage");     // Если это меню языка
  let profileButton = document.querySelector('.sign_header > a'); // Пример для кнопки профиля
  let profileMenu = document.querySelector('.profile-block');     // Пример для меню профиля

  if (languageButton && languageMenu) {
      languageButton.addEventListener("click", function (event) {
          event.stopPropagation(); // Предотвращаем всплытие, чтобы не закрыть сразу
          languageMenu.style.display = (languageMenu.style.display === "block") ? "none" : "block";
      });
  }
  
  if (profileButton && profileMenu) {
      profileButton.addEventListener('click', function(event) {
          // Если внутри .sign_header есть иконка и блок .profile-block
          // и это не переход по ссылке на другую страницу (проверяем, есть ли # в href)
          if (profileButton.getAttribute('href') === '#' || !profileButton.getAttribute('href')) {
              event.preventDefault(); // Предотвращаем переход, если это просто якорь
              profileMenu.classList.toggle('active'); // Переключаем класс active
          }
      });
  }


  // --- Логика скрытия хедера при скролле ---
  const header = document.querySelector("header.header"); // Уточняем селектор
  if (header) {
      let lastScrollTop = 0;
      const scrollThresholdToShow = 50; // Порог для показа при скролле вверх
      const scrollThresholdToHide = 200; // Порог для скрытия при скролле вниз

      window.addEventListener("scroll", () => {
          let scrollTop = window.scrollY || document.documentElement.scrollTop;

          if (scrollTop > lastScrollTop && scrollTop > scrollThresholdToHide) {
              // Скролл вниз и больше порога
              header.classList.add("header-hidden");
          } else if (scrollTop < lastScrollTop || scrollTop <= scrollThresholdToShow) {
              // Скролл вверх или в самом верху страницы (меньше порога для показа)
              header.classList.remove("header-hidden");
          }
          lastScrollTop = scrollTop <= 0 ? 0 : scrollTop; // Для Mobile Safari
      }, false);
  }

  // --- Общий обработчик кликов для закрытия открытых меню ---
  document.addEventListener("click", function (event) {
      // Закрытие меню языка
      if (languageMenu && languageMenu.style.display === "block" &&
          languageButton && !languageButton.contains(event.target) &&
          !languageMenu.contains(event.target)) {
          languageMenu.style.display = "none";
      }

      // Закрытие меню профиля
      if (profileMenu && profileMenu.classList.contains('active') &&
          profileButton && !profileButton.contains(event.target) &&
          !profileMenu.contains(event.target)) {
          profileMenu.classList.remove('active');
      }
  });
});