document.addEventListener("DOMContentLoaded", function () {
    if (typeof Swiper !== "undefined") {
        const swiper1 = new Swiper(".main-swiper", {
            loop: true,
            speed: 800,
            grabCursor: true,
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
            speed: 700,
            slidesPerView: 3,
            slidesPerGroup: 1,
            spaceBetween: 20,
            grabCursor: true,
            loopAdditionalSlides: 1,
            navigation: {
                nextEl: ".new-releases-container .swiper-button-next",
                prevEl: ".new-releases-container .swiper-button-prev",
            },
            pagination: false,
        });

        const swiper3 = new Swiper(".top-rated-swiper", {
            loop: true,
            speed: 800,
            slidesPerView: 6,
            slidesPerGroup: 6,
            spaceBetween: 20,
            grabCursor: true,
            loopAdditionalSlides: 6,
            navigation: {
                nextEl: ".top-rated-container .swiper-button-next",
                prevEl: ".top-rated-container .swiper-button-prev",
            },
            pagination: false,
        });

        const swiper4 = new Swiper(".upcoming-games-swiper", {
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
    } else {
        console.error("Swiper is not loaded");
    }
});