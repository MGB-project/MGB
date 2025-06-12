document.addEventListener("DOMContentLoaded", function () {
  if (typeof Swiper !== "undefined") {
    const swiper1 = new Swiper(".main-swiper", {
        loop: true,
        speed: 800,
        grabCursor: true,
        centeredSlides: true,
        slidesPerView: 1.2,
        spaceBetween: 20,
        pagination: {
            el: ".swiper-pagination",
            clickable: true,
        },
        navigation: {
            nextEl: ".swiper-button-next",
            prevEl: ".swiper-button-prev",
        },
    });

    const swiper2 = new Swiper(".new-releases-swiper", {
        loop: true,
        speed: 800,
        slidesPerView: 6,
        slidesPerGroup: 6,
        spaceBetween: 20,
        grabCursor: true,
        loopAdditionalSlides: 6,
        navigation: {
            nextEl: ".swiper-button-next",
            prevEl: ".swiper-button-prev",
        },
        pagination: false,
    });

    const swiper3 = new Swiper(".upcoming-movies-swiper", {
        loop: true,
        speed: 800,
        grabCursor: true,
        centeredSlides: true,
        spaceBetween: 20,
        pagination: {
            el: ".swiper-pagination",
            clickable: true,
        },
        navigation: {
            nextEl: ".swiper-button-next",
            prevEl: ".swiper-button-prev",
        },
    });

    const swiper4 = new Swiper(".best-movies-swiper", {
        loop: true,
        speed: 800,
        slidesPerView: 6,
        slidesPerGroup: 6,
        spaceBetween: 20,
        grabCursor: true,
        loopAdditionalSlides: 6,
        navigation: {
            nextEl: ".swiper-button-next",
            prevEl: ".swiper-button-prev",
        },
        pagination: false,
    });

    const swiper5 = new Swiper(".categories-swiper", {
        loop: false,
        speed: 800,
        slidesPerView: "auto",
        spaceBetween: 10,
        grabCursor: true,
        pagination: false,
    });

    } else {
        console.error("Swiper is not loaded");
    }
    swiper1.on("slideChangeTransitionStart", function () {
        gsap.fromTo(".movie-info", { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: 0.5 });
    });
});
