document.addEventListener('DOMContentLoaded', function () {
  if (typeof Swiper === 'undefined') {
      console.error("Swiper library is not loaded.");
      return;
  }

  if (typeof mainBooksData === 'undefined' || !Array.isArray(mainBooksData) || mainBooksData.length === 0) {
      return;
  }

  const infoPanel = {
      title: document.getElementById('showcaseBookTitle'),
      authors: document.getElementById('showcaseBookAuthors'),
      rating: document.getElementById('showcaseBookRating'),
      year: document.getElementById('showcaseBookYear'),
      pages: document.getElementById('showcaseBookPages'),
      description: document.getElementById('showcaseBookDescription'),
      actions: document.getElementById('showcaseBookActions')
  };

  let infoPanelElementsExist = true;
  for (const key in infoPanel) {
      if (!infoPanel[key]) {
          infoPanelElementsExist = false;
      }
  }
  if (!infoPanel.title || !infoPanel.actions) {
      console.error('Critical info panel elements (title or actions) are missing for book showcase.');
      return;
  }

  function updateInfoPanel(bookData) {
    if (!bookData) return;

    if (infoPanel.title) infoPanel.title.textContent = bookData.title || 'Заголовок отсутствует';
    
    if (infoPanel.authors) {
        infoPanel.authors.textContent = (bookData.authors && Array.isArray(bookData.authors) && bookData.authors.length > 0 && !(bookData.authors.length === 1 && bookData.authors[0] === "")) // Проверка на пустой массив авторов
                                      ? bookData.authors.join(', ') 
                                      : 'Автор неизвестен';
    }
    
    if (infoPanel.rating) {
        if (bookData.rating && bookData.rating !== '----' && bookData.rating !== '' && parseFloat(bookData.rating) >= 0) { // >= 0 для рейтинга
            infoPanel.rating.textContent = bookData.rating;
            infoPanel.rating.style.backgroundColor = bookData.rating_color || '#777'; // Используем rating_color
            infoPanel.rating.style.display = 'inline-block'; // или inline-flex
        } else {
            infoPanel.rating.style.display = 'none';
        }
    }
    
    if (infoPanel.year) infoPanel.year.textContent = bookData.year || '----';

    if (infoPanel.description) infoPanel.description.textContent = bookData.description || 'Описание отсутствует.';
    
    if (infoPanel.actions && bookData.actions_html) {
      infoPanel.actions.innerHTML = bookData.actions_html; // Перезаписываем HTML

      // ---- НОВЫЙ КОД ----
      // После перезаписи innerHTML, нам нужно заново применить updateRatingUI 
      // к контейнеру кнопок, который мы только что вставили.
      // Мы предполагаем, что actions_html содержит один .item-actions-container
      const newlyInsertedActionsContainer = infoPanel.actions.querySelector('.item-actions-container');
      if (newlyInsertedActionsContainer) {
          const initialRatingStr = newlyInsertedActionsContainer.dataset.initialRating;
          let initialRating = null;
          if (initialRatingStr && initialRatingStr !== '') {
              const parsedRating = parseInt(initialRatingStr, 10);
              if (!isNaN(parsedRating) && parsedRating >= 1 && parsedRating <= 10) {
                  initialRating = parsedRating;
              }
          }
          // Вызываем updateRatingUI из item_actions.js
          // Убедись, что функция updateRatingUI доступна глобально или передана сюда
          if (typeof updateRatingUI === 'function') { // Проверяем, доступна ли функция
              console.log("Re-applying updateRatingUI to showcase actions for rating:", initialRating);
              updateRatingUI(newlyInsertedActionsContainer, initialRating);
          } else {
              console.warn("updateRatingUI function is not globally available in books.js. Cannot re-apply to showcase actions.");
              // Альтернатива: если updateRatingUI не глобальна, 
              // можно попробовать вызвать initializeRatingUI для конкретного элемента,
              // но это может быть избыточно, если initializeRatingUI делает больше, чем просто updateRatingUI.
              // Или можно эмулировать часть initializeRatingUI здесь.
          }
          // Также, если статусы и избранное обновляются аналогично, их тоже надо "переинициализировать"
          // для newlyInsertedActionsContainer.
          // Например:
          // if (typeof updateFavoriteStatusUI === 'function' && typeof bookData.is_favorite !== 'undefined') {
          //     updateFavoriteStatusUI(newlyInsertedActionsContainer, bookData.is_favorite);
          // }
          // if (typeof updateItemStatusUI === 'function' && bookData.status_data) {
          //    updateItemStatusUI(newlyInsertedActionsContainer, bookData.status_data.slug, bookData.status_data.icon, bookData.status_data.text);
          // }
      }
      // ---- КОНЕЦ НОВОГО КОДА ----

    } else if (infoPanel.actions) {
        infoPanel.actions.innerHTML = ''; 
    }
  }

  const bookCoverSwiperElement = document.querySelector('.book-cover-swiper');

  if (bookCoverSwiperElement && mainBooksData.length > 0) {
    const bookCoverSwiper = new Swiper(bookCoverSwiperElement, {
      slidesPerView: 'auto', // <--- ИЗМЕНЕНИЕ: Swiper будет брать ширину из CSS
      spaceBetween: 20,      // Отступ между слайдами
      centeredSlides: false,   // Первый слайд будет слева
      loop: mainBooksData.length > 5, // Петля, если слайдов достаточно (например, больше чем 2*кол-во видимых + запас)
                                    // Подбери это значение аккуратно. Если мало слайдов, loop может плохо работать с 'auto'.
      
      slidesPerGroup: 1,     // <--- ВАЖНО: Прокрутка по одному слайду
      
      // slidesOffsetBefore: 10, // Небольшой отступ слева, чтобы первый слайд не прилипал к краю панели
                                // если не хочешь эффекта "вылезания" для первого слайда.
                                // Если хочешь, чтобы первый тоже был частично виден, оставь 0 или подбери.
      slidesOffsetBefore: 0,    // Для эффекта "вылезания" первого слайда

      grabCursor: true,

      navigation: {
        nextEl: '.book-cover-swiper-button-next', 
        prevEl: '.book-cover-swiper-button-prev',
      },
      // Breakpoints могут не понадобиться для slidesPerView, если ширина слайдов фиксирована в CSS,
      // но могут быть полезны для изменения spaceBetween или других опций.
      // Если breakpoints нужны, в них тоже можно использовать slidesPerView: 'auto'
      breakpoints: {
        320: { spaceBetween: 10 },
        480: { spaceBetween: 15 },
        // Для больших экранов spaceBetween из основной конфигурации (20)
      },
      on: {
        init: function (swiperInstance) {
          // Обновляем стили для видимых слайдов, чтобы применить эффект размера
          swiperInstance.slides.forEach(slide => slide.style.transition = 'transform 0.3s ease');
          updateSlideStyles(swiperInstance); 

          const initialActiveIndex = swiperInstance.realIndex !== undefined ? swiperInstance.realIndex : 0;
          if (mainBooksData[initialActiveIndex]) {
              updateInfoPanel(mainBooksData[initialActiveIndex]);
          } else if (mainBooksData.length > 0) {
              updateInfoPanel(mainBooksData[0]);
          }
        },
        slideChange: function (swiperInstance) {
          updateSlideStyles(swiperInstance); // Обновляем стили при смене слайда

          const currentActiveIndex = swiperInstance.realIndex;
          if (mainBooksData[currentActiveIndex]) {
            updateInfoPanel(mainBooksData[currentActiveIndex]);
          }
        },
      },
  });

  function updateSlideStyles(swiper) {
    swiper.slides.forEach((slide) => {
        if (slide.classList.contains('swiper-slide-active')) {
            slide.style.transform = 'scale(1)';
        } else {
            slide.style.transform = 'scale(1)';
        }
    });
  }

  } else if (mainBooksData.length > 0 && infoPanel.title) { 
    updateInfoPanel(mainBooksData[0]);
  }

  const topRatedSwipers = document.querySelectorAll('.top-rated-swiper');
  topRatedSwipers.forEach((swiperElement, index) => {
      const parentContainer = swiperElement.closest('.top-rated-container');
      let navOptions = false; 

      if (parentContainer) {
          const prevBtn = parentContainer.querySelector('.swiper-button-prev');
          const nextBtn = parentContainer.querySelector('.swiper-button-next');

          if (prevBtn && nextBtn) {
              navOptions = {
                  nextEl: nextBtn, 
                  prevEl: prevBtn,
              };
          }
      }

      if (swiperElement) {
          new Swiper(swiperElement, {
              loop: true, 
              speed: 800,
              slidesPerView: 6, 
              slidesPerGroup: 1,
              spaceBetween: 20,
              grabCursor: true,
              navigation: navOptions, 
              pagination: false, 
              breakpoints: {
                  320: { slidesPerView: 2, slidesPerGroup: 1, spaceBetween: 10 },
                  480: { slidesPerView: 3, slidesPerGroup: 1, spaceBetween: 10 },
                  768: { slidesPerView: 4, slidesPerGroup: 1, spaceBetween: 15 },
                  1024: { slidesPerView: 5, slidesPerGroup: 1, spaceBetween: 20 },
                  1200: { slidesPerView: 6, slidesPerGroup: 1, spaceBetween: 20 },
              }
          });
      }
  });

  const NewBooksSwipers = document.querySelectorAll('.new-books-swiper');
  NewBooksSwipers.forEach((swiperElement, index) => {
      const parentContainer = swiperElement.closest('.new-books-container');
      let navOptions = false; 

      if (parentContainer) {
          const prevBtn = parentContainer.querySelector('.swiper-button-prev');
          const nextBtn = parentContainer.querySelector('.swiper-button-next');
          
          if (prevBtn && nextBtn) {
              navOptions = {
                  nextEl: nextBtn, 
                  prevEl: prevBtn,
              };
          }
      }

      if (swiperElement) {
          new Swiper(swiperElement, {
              loop: true, 
              speed: 800,
              slidesPerView: 6, 
              slidesPerGroup: 1,
              spaceBetween: 20,
              grabCursor: true,
              navigation: navOptions, 
              pagination: false, 
              breakpoints: {
                  320: { slidesPerView: 2, slidesPerGroup: 1, spaceBetween: 10 },
                  480: { slidesPerView: 3, slidesPerGroup: 1, spaceBetween: 10 },
                  768: { slidesPerView: 4, slidesPerGroup: 1, spaceBetween: 15 },
                  1024: { slidesPerView: 5, slidesPerGroup: 1, spaceBetween: 20 },
                  1200: { slidesPerView: 6, slidesPerGroup: 1, spaceBetween: 20 },
              }
          });
      }
  });
});