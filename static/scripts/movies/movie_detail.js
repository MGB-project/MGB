document.addEventListener("DOMContentLoaded", function () {
    if (typeof Swiper !== "undefined") {
        const swiper1 = new Swiper(".sim-movies-swiper", {
            loop: true,
            speed: 500,
            slidesPerView: 6,
            slidesPerGroup: 1,
            spaceBetween: 20,
            grabCursor: true,
            loopAdditionalSlides: 1,
            navigation: {
                nextEl: ".swiper-button-next",
                prevEl: ".swiper-button-prev",
            },
            pagination: false,
        });
  
      } else {
          console.error("Swiper is not loaded");
      }
  });
  