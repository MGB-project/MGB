document.addEventListener("DOMContentLoaded", function () {
    const mainPhoto = document.querySelector(".main-photo");
    const gameCover = document.querySelector(".game-cover");
    const screenshots = document.querySelectorAll(".others-photo img");

    let videoElement = document.querySelector(".main-photo video");
    let videoUrl = videoElement ? videoElement.querySelector("source").src : null;
    let videoCurrentTime = 0;

    let iframeElement = document.querySelector(".main-photo iframe");
    let youtubeTrailerId = iframeElement ? iframeElement.src.split("/embed/")[1].split("?")[0] : null;

    let defaultCoverBg = gameCover.style.backgroundImage || null;
    let defaultMainBg = mainPhoto.style.backgroundImage || null;
    let defaultMainContent = mainPhoto.innerHTML;
    let isVideoMoved = false;
    let activeScreenshot = null;

    function setVideoAsCover() {
        if (videoUrl) {
            gameCover.innerHTML = "";
            gameCover.style.background = "none";

            let newVideo = document.createElement("video");
            newVideo.autoplay = true;
            newVideo.muted = true;
            newVideo.loop = true;

            let source = document.createElement("source");
            source.src = videoUrl;
            source.type = "video/mp4";

            newVideo.appendChild(source);
            gameCover.appendChild(newVideo);
            newVideo.currentTime = videoCurrentTime;
            isVideoMoved = true;
        }
    }

    function setYouTubeTrailerAsCover() {
        if (youtubeTrailerId) {
            gameCover.innerHTML = `<iframe src="https://www.youtube.com/embed/${youtubeTrailerId}?autoplay=1&mute=1"
                frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
            gameCover.style.background = "none";
            isVideoMoved = true;
        }
    }

    screenshots.forEach(screenshot => {
        screenshot.addEventListener("click", function () {
            const imageUrl = this.getAttribute("src");

            if (videoElement || iframeElement) {
                setVideoAsCover();
                setYouTubeTrailerAsCover();
            }

            mainPhoto.style.transition = "opacity 0.2s ease-in-out";
            mainPhoto.style.opacity = "1";

            setTimeout(() => {
                mainPhoto.style.background = `url('${imageUrl}') center/cover no-repeat`;
                mainPhoto.style.opacity = "1";
                mainPhoto.innerHTML = "";
            }, 200);

            // Снимаем обводку у предыдущего активного скриншота
            if (activeScreenshot) {
                activeScreenshot.classList.remove("selected-screenshot");
            }

            // Добавляем обводку у текущего
            this.classList.add("selected-screenshot");
            activeScreenshot = this;
        });
    });

    gameCover.addEventListener("click", function () {
        if (isVideoMoved) {
            gameCover.innerHTML = "";
            gameCover.style.background = defaultCoverBg || "";
            mainPhoto.style.background = defaultMainBg || "";
            mainPhoto.innerHTML = defaultMainContent;
            videoElement = document.querySelector(".main-photo video");
            if (videoElement) videoElement.currentTime = videoCurrentTime;
            isVideoMoved = false;
        }
    });

    if (typeof Swiper !== "undefined") {
        const swiper1 = new Swiper(".sim-games-swiper", {
            loop: true,
            speed: 800,
            slidesPerView: 6,
            slidesPerGroup: 1,
            spaceBetween: 15,
            grabCursor: true,
            loopAdditionalSlides: 1,
            navigation: {
                nextEl: ".sim-games-swiper-button-next",
                prevEl: ".sim-games-swiper-button-prev",
            },
            pagination: false,
        });

    } else {
        console.error("Swiper is not loaded");
    }
});