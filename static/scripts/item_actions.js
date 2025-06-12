// item_actions.js

// Проверяем, был ли этот скрипт уже инициализирован
if (typeof window.itemActionsGlobalInitialized === 'undefined') {
    // Если нет, устанавливаем глобальный флаг и выполняем весь код скрипта
    window.itemActionsGlobalInitialized = true;

    // ... (весь код до updateModalRatingButtonsUI остается без изменений) ...
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // --- ФУНКЦИИ ОБНОВЛЕНИЯ UI ---
    function updateFavoriteStatusUI(container, isFavorite) {
        const favButton = container.querySelector('button[data-action="toggle-favorite"]');
        if (!favButton) return;
        const icon = favButton.querySelector('.fav-icon');
        if (!icon) return;

        const isSmall = container.classList.contains('item-actions-container--small');
        let iconPath = isFavorite
            ? (isSmall ? favButton.dataset.iconSmallActive : favButton.dataset.iconActive)
            : (isSmall ? favButton.dataset.iconSmallDefault : favButton.dataset.iconDefault);
        iconPath = iconPath || (isFavorite ? favButton.dataset.iconActive : favButton.dataset.iconDefault); // Запасной вариант

        const altText = isFavorite ? "In Wishlist" : "Add to Wishlist";

        if (iconPath) {
            icon.src = iconPath;
            icon.alt = altText;
        } else {
            console.warn("Не найдены data-атрибуты иконок избранного", favButton.dataset);
        }
    }

    function updateItemStatusUI(container, newStatusSlug, newIconPath, newText) {
        const mainStatusButton = container.querySelector('.btn-item-status');
        if (!mainStatusButton) return;

        const mainIcon = mainStatusButton.querySelector('.item-status-icon');
        const mainTextSpan = mainStatusButton.querySelector('.item-status-text');
        const optionsBlock = container.querySelector('.item-status-options');

        const resetButton = container.querySelector('.reset-status');
        const defaultIcon = mainStatusButton.dataset.defaultIcon || resetButton?.dataset.defaultIcon || '/static/imgs/icons/status_default.svg';
        const defaultText = mainStatusButton.dataset.defaultText || resetButton?.dataset.defaultText || 'Status';

        if (mainIcon) mainIcon.src = newIconPath || defaultIcon;
        if (mainTextSpan) mainTextSpan.textContent = newText || defaultText;

        if (optionsBlock) {
            optionsBlock.querySelectorAll('.option-btn').forEach(btn => {
                if (btn.classList.contains('reset-status')) return;
                const checkMark = btn.querySelector('.complete-check');
                const isSelected = btn.dataset.status === newStatusSlug && newStatusSlug !== 'none';
                btn.classList.toggle('selected', isSelected);
                if (checkMark) {
                    checkMark.style.display = isSelected ? 'block' : 'none';
                }
            });
        }
    }

    function updateRatingUI(container, currentRating) {
        console.log(">>> updateRatingUI START. Container:", container, "Rating:", currentRating);
        const isSmall = container.classList.contains('item-actions-container--small');

        if (isSmall) {
            const starButtonSmall = container.querySelector('.btn-star-small');
            if (starButtonSmall) {
                const starIconSmall = starButtonSmall.querySelector('.icon-star-small');
                const grayIconPath = starButtonSmall.dataset.iconStarGray;
                const yellowIconPath = starButtonSmall.dataset.iconStarYellow;

                if (starIconSmall && grayIconPath && yellowIconPath) {
                    if (currentRating && currentRating >= 1 && currentRating <= 10) {
                        starIconSmall.src = yellowIconPath;
                    } else {
                        starIconSmall.src = grayIconPath;
                    }
                }
            }
        } else {
            const ratingContainer = container.querySelector('.rating-container');
            if (!ratingContainer) return;
            const ratingStar = container.querySelector('.rating-star-indicator'); // было ratingContainer
            console.log("updateRatingUI (LARGE): ratingStar found?", ratingStar); // было

            const ratingOptions = container.querySelector('.rating-options'); // Убедись, что ищешь в container или ratingContainer
            if (!ratingOptions) {
                console.error("updateRatingUI (LARGE): .rating-options NOT FOUND!");
                return; // или return из этой ветки, если ratingOptions критичен
            }
            const ratingButtons = ratingOptions.querySelectorAll('.rating-btn'); // Ищем внутри ratingOptions
            console.log("updateRatingUI (LARGE): ratingButtons found (count)?", ratingButtons.length); // было

            const yellowStarIcon = ratingStar?.dataset.iconYellow || '/static/imgs/icons/yellow_star.svg'; // было
            const grayStarIcon = ratingStar?.dataset.iconGray || '/static/imgs/icons/gray_star.svg'; // было

            ratingButtons.forEach(btn => { // было
                btn.style.color = "";
                btn.classList.remove('active-rating');
            });

            if (currentRating && currentRating >= 1 && currentRating <= 10) { // было
                if (ratingStar) { // было
                    ratingStar.src = yellowStarIcon;
                    console.log("updateRatingUI (LARGE): Set ratingStar to YELLOW"); // ДОБАВЬ/РАСКОММЕНТИРУЙ
                }
                const activeButton = ratingOptions.querySelector(`.rating-btn[data-rating="${currentRating}"]`); // было
                if (activeButton) {
                    activeButton.style.color = currentRating <= 1 ? "#B7485C" : currentRating <= 4 ? "#FF4949" : currentRating <= 7 ? "#FFFF00" : "#15B000";
                    activeButton.classList.add('active-rating');
                    console.log("updateRatingUI (LARGE): Added 'active-rating'. Button now:", activeButton.outerHTML); // Показываем HTML кнопки
                    console.log("updateRatingUI (LARGE): Does button have 'active-rating' class NOW?", activeButton.classList.contains('active-rating')); // Проверяем наличие класса
                } else {
                    console.warn("updateRatingUI (LARGE): Active button for rating", currentRating, "NOT FOUND!");
                }
            } else { // было
                if (ratingStar) { // было
                    ratingStar.src = grayStarIcon;
                    console.log("updateRatingUI (LARGE): Set ratingStar to GRAY"); // ДОБАВЬ/РАСКОММЕНТИРУЙ
                }
            }
        }
    }

    function initializeRatingUI() {
        document.querySelectorAll('.item-actions-container[data-initial-rating]').forEach(container => {
            const initialRatingStr = container.dataset.initialRating;
            let initialRating = null;

            if (initialRatingStr && initialRatingStr !== '') {
                const parsedRating = parseInt(initialRatingStr, 10);
                 if (!isNaN(parsedRating) && parsedRating >= 1 && parsedRating <= 10) {
                     initialRating = parsedRating;
                 }
            }
            updateRatingUI(container, initialRating);
        });
    }

    function syncItemActionsUI(itemId, contentType, updatedStateType, newStateData) {
        if (!itemId || !contentType) return;
        const itemContainers = document.querySelectorAll(`.item-actions-container[data-item-id="${itemId}"][data-content-type="${contentType}"]`);

        itemContainers.forEach(container => {
            try {
                switch (updatedStateType) {
                    case 'favorite':
                        if (newStateData && typeof newStateData.is_favorite !== 'undefined') {
                            updateFavoriteStatusUI(container, newStateData.is_favorite);
                        }
                        break;
                    case 'status':
                        if (newStateData && typeof newStateData.status !== 'undefined') {
                            updateItemStatusUI(container, newStateData.status, newStateData.icon, newStateData.text);
                        }
                        break;
                    case 'rating':
                        if (newStateData && typeof newStateData.rating !== 'undefined') {
                            updateRatingUI(container, newStateData.rating);
                        }
                        break;
                }
            } catch (error) {
                console.error(`Ошибка синхронизации UI (${updatedStateType}) для ${contentType} ${itemId}:`, container, error);
            }
        });
    }

    function toggleFavorite(url, itemId, contentType) {
        fetch(url, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" }
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            syncItemActionsUI(itemId, contentType, 'favorite', { is_favorite: data.is_favorite });
            if (data.is_favorite && typeof launchAchievements === 'function') {
                const anyContainer = document.querySelector(`.item-actions-container[data-item-id="${itemId}"][data-content-type="${contentType}"]`);
                const anyButton = anyContainer?.querySelector('button[data-action="toggle-favorite"]');
                if (anyButton) launchAchievements(anyButton);
            }
        })
        .catch(error => console.error(`Ошибка обновления избранного для ${contentType} ${itemId}:`, error));
    }

    function setItemStatus(optionButton, container, itemId, contentType) {
        const url = optionButton.dataset.url;
        const newIcon = optionButton.dataset.icon;
        const newText = optionButton.dataset.text;
        const statusValue = optionButton.dataset.status;

        if (!url || url === '#') {
            console.error("Не найден URL для установки статуса:", optionButton);
            return;
        }

        fetch(url, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" }
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            const statusKey = `is_${statusValue}`;
            const isStatusActive = data[statusKey];

            let syncData;
            if (isStatusActive === true) {
                syncData = { status: statusValue, icon: newIcon, text: newText };
            } else {
                const mainStatusButton = container.querySelector('.btn-item-status');
                const resetButton = container.querySelector('.reset-status');
                const defaultIcon = mainStatusButton?.dataset.defaultIcon || resetButton?.dataset.defaultIcon || '/static/imgs/icons/status_default.svg';
                const defaultText = mainStatusButton?.dataset.defaultText || resetButton?.dataset.defaultText || 'Status';
                syncData = { status: 'none', icon: defaultIcon, text: defaultText };
            }
            syncItemActionsUI(itemId, contentType, 'status', syncData);
        })
        .catch(error => {
            console.error(`Ошибка установки статуса '${statusValue}' для ${contentType} ${itemId}:`, error);
        });
    }

    function resetItemStatus(resetButton, container, itemId, contentType) {
        const optionsBlock = resetButton.closest('.item-status-options');
        const currentSelected = optionsBlock?.querySelector('.option-btn.selected:not(.reset-status)');

        if (!currentSelected) {
            closeStatusMenu(container);
            return;
        }
        const url = currentSelected.dataset.url;
        const mainStatusButton = container.querySelector('.btn-item-status');
        const defaultIcon = mainStatusButton?.dataset.defaultIcon || resetButton?.dataset.defaultIcon || '/static/imgs/icons/status_default.svg';
        const defaultText = mainStatusButton?.dataset.defaultText || resetButton?.dataset.defaultText || 'Status';

        if (!url || url === '#') {
            console.error("Не найден URL для сброса статуса (у активной кнопки):", currentSelected);
            return;
        }

        fetch(url, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" }
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok for reset');
            return response.json();
        })
        .then(data => {
            syncItemActionsUI(itemId, contentType, 'status', { status: 'none', icon: defaultIcon, text: defaultText });
        })
        .catch(error => {
            console.error(`Ошибка при сбросе статуса для ${contentType} ${itemId}:`, error);
        });
    }

    function sendRatingUpdate(contentType, itemPk, ratingValue, container) {
        const url = `/user/rate/${contentType}/${itemPk}/`;
        const csrftoken = getCookie('csrftoken');

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ rating: ratingValue })
        })
        .then(response => {
            if (!response.ok) {
                 return response.json().then(errData => {
                     throw new Error(errData.message || `HTTP error! status: ${response.status}`);
                 }).catch(() => {
                     throw new Error(`HTTP error! status: ${response.status}`);
                 });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                updateRatingUI(container, data.current_rating);
                container.dataset.initialRating = data.current_rating === null ? '' : data.current_rating.toString();

                const itemIdToSync = container.dataset.itemId || itemPk;
                if(itemIdToSync) {
                    syncItemActionsUI(String(itemIdToSync), contentType, 'rating', { rating: data.current_rating });
                }

                if (modalRateButton) {
                    if (data.current_rating !== null && data.current_rating >=1 && data.current_rating <=10) {
                        modalRateButton.classList.add('active');
                        modalRateButton.textContent = "Rated";
                    } else {
                        modalRateButton.classList.remove('active');
                        modalRateButton.textContent = "Rate";
                    }
                }
                setTimeout(() => {
                    closeRatingModal();
                }, 700);

            } else {
                console.error(`Ошибка сохранения рейтинга: ${data.message}`);
                alert(`Error: ${data.message}`);
            }
        })
        .catch(error => {
            console.error(`Fetch ошибка при обновлении рейтинга для ${contentType} ${itemPk}:`, error);
            alert(`Error updating rating: ${error.message}`);
        });
    }

    const modalOverlay = document.getElementById('modal-overlay-rating');
    const modalWindow = modalOverlay ? modalOverlay.querySelector('.modal-window') : null;
    const modalCloseButton = modalOverlay ? modalOverlay.querySelector('.close-modal') : null;
    const modalImage = document.getElementById('modal-image');
    const modalTitle = document.getElementById('modal-title');
    const modalRatingOptionsContainer = modalOverlay ? modalOverlay.querySelector('.modal-rating-container .rating-options') : null;
    const modalRateButton = modalOverlay ? modalOverlay.querySelector('.btn-rate-modal') : null;
    // ----- НОВЫЙ ЭЛЕМЕНТ -----
    const modalStarIndicator = document.getElementById('modal-rating-star-indicator'); // Получаем звезду из модалки
    // ----- КОНЕЦ НОВОГО ЭЛЕМЕНТА -----


    let currentOpenModalContext = {
        originalContainer: null,
        contentType: null,
        itemPk: null,
        itemId: null,
        currentSelectedRatingInModal: null,
        initialRatingOnOpen: null
    };

    function updateModalRatingButtonsUI(selectedRatingInModal) {
        if (!modalRatingOptionsContainer) return;
        const buttons = modalRatingOptionsContainer.querySelectorAll('button.rating-btn'); // Только кнопки с цифрами
        const trashButton = modalRatingOptionsContainer.querySelector('button.btn-trash');

        // Обновляем кнопки-цифры
        buttons.forEach(btn => {
            btn.classList.remove('active-rating-modal');
            btn.style.color = ""; // Сброс цвета
            const btnRating = parseInt(btn.textContent, 10);
            if (btnRating === selectedRatingInModal) {
                btn.classList.add('active-rating-modal');
                btn.style.color = selectedRatingInModal <= 1 ? "#B7485C" : selectedRatingInModal <= 4 ? "#FF4949" : selectedRatingInModal <= 7 ? "#FFFF00" : "#15B000";
            }
        });

        // Обновляем кнопку корзины
        if (trashButton) {
            trashButton.classList.remove('active-rating-modal'); // Сначала убираем класс
            if (selectedRatingInModal === null) {
                trashButton.classList.add('active-rating-modal');
            }
        }

        // ----- ИЗМЕНЕНИЕ ЗДЕСЬ: Обновляем звезду-индикатор в модалке -----
        if (modalStarIndicator) {
            const grayStarSrc = modalStarIndicator.dataset.iconGray || '/static/imgs/icons/gray_star.svg'; // Фоллбэк
            const yellowStarSrc = modalStarIndicator.dataset.iconYellow || '/static/imgs/icons/yellow_star.svg'; // Фоллбэк

            if (selectedRatingInModal !== null && selectedRatingInModal >= 1 && selectedRatingInModal <= 10) {
                modalStarIndicator.src = yellowStarSrc;
            } else {
                modalStarIndicator.src = grayStarSrc;
            }
        }
        // ----- КОНЕЦ ИЗМЕНЕНИЯ -----


        // Управляем кнопкой "Rate"
        if (modalRateButton) {
            const ratingIsDifferentFromInitialOrNew = selectedRatingInModal !== currentOpenModalContext.initialRatingOnOpen;

            if (ratingIsDifferentFromInitialOrNew) {
                modalRateButton.classList.add('active');
                if (selectedRatingInModal === null && currentOpenModalContext.initialRatingOnOpen !== null) {
                    modalRateButton.textContent = "Clear Rate";
                } else {
                    modalRateButton.textContent = "Rate";
                }
            } else {
                modalRateButton.classList.remove('active');
                modalRateButton.textContent = (selectedRatingInModal !== null) ? "Rated" : "Rate";
            }
        }
    }

    function openRatingModal(container) {
        if (!modalOverlay || !container) return;

        const contentType = container.dataset.contentType;
        const itemPk = container.dataset.itemPk;
        const itemId = container.dataset.itemId || itemPk;
        const itemTitleStr = container.dataset.itemTitle || "Rate this item";
        const itemImageUrlStr = container.dataset.itemImageUrl;
        const initialRatingStr = container.dataset.initialRating;

        if (!contentType || !itemPk) {
            console.error("Missing data-content-type or data-item-pk on container:", container);
            return;
        }

        currentOpenModalContext.originalContainer = container;
        currentOpenModalContext.contentType = contentType;
        currentOpenModalContext.itemPk = itemPk;
        currentOpenModalContext.itemId = itemId;

        if (modalTitle) modalTitle.textContent = itemTitleStr;
        if (modalImage) {
            if (itemImageUrlStr) {
                modalImage.src = itemImageUrlStr;
                modalImage.alt = itemTitleStr;
                modalImage.style.display = 'block';
            } else {
                modalImage.style.display = 'none';
            }
        }

        let actualInitialRating = null;
        if (initialRatingStr && initialRatingStr !== '') {
            const parsedRating = parseInt(initialRatingStr, 10);
            if (!isNaN(parsedRating) && parsedRating >= 1 && parsedRating <= 10) {
                actualInitialRating = parsedRating;
            }
        }
        currentOpenModalContext.initialRatingOnOpen = actualInitialRating;
        currentOpenModalContext.currentSelectedRatingInModal = actualInitialRating;

        updateModalRatingButtonsUI(currentOpenModalContext.currentSelectedRatingInModal);

        modalOverlay.style.display = 'flex';
    }

    function closeRatingModal() {
        if (modalOverlay) modalOverlay.style.display = 'none';
        if (modalRateButton) {
            modalRateButton.classList.remove('active');
            modalRateButton.textContent = "Rate";
        }
        // Сбрасываем звезду на серую при закрытии, если это нужно
        if (modalStarIndicator) {
             modalStarIndicator.src = modalStarIndicator.dataset.iconGray || '/static/imgs/icons/gray_star.svg';
        }
        currentOpenModalContext = {
            originalContainer: null, contentType: null, itemPk: null, itemId: null,
            currentSelectedRatingInModal: null, initialRatingOnOpen: null
        };
    }
    
    function selectRating(ratingButton, container) {
        const ratingValue = parseInt(ratingButton.dataset.rating, 10);
        const contentType = container.dataset.contentType;
        const itemPk = container.dataset.itemPk;

        if (!contentType || !itemPk || isNaN(ratingValue)) {
            console.error("Missing data for rating:", contentType, itemPk, ratingValue);
            return;
        }
        sendRatingUpdate(contentType, itemPk, ratingValue, container);
    }

    function resetRating(trashButton, container) {
       const contentType = container.dataset.contentType;
       const itemPk = container.dataset.itemPk;

       if (!contentType || !itemPk) {
           console.error("Missing data for resetting rating:", contentType, itemPk);
           return;
       }
       sendRatingUpdate(contentType, itemPk, 0, container);
    }

    function toggleRatingBlock(starButton, container) {
        if (!container || !starButton) return;
        const ratingContainer = container.querySelector('.rating-container');
        const starIcon = starButton.querySelector('.icon-star');
        const closeIcon = starButton.querySelector('.icon-close');

        if (!ratingContainer || !starIcon || !closeIcon) {
            console.error("Не найдены элементы рейтинга или иконки в кнопке:", container, starButton);
            return;
        }

        const isRatingActive = container.classList.contains('rating-active');
        const useGsap = typeof gsap !== 'undefined';

        if (isRatingActive) {
            ratingContainer.classList.remove('visible');
            container.classList.remove('rating-active');
            starIcon.classList.remove('hidden');
            closeIcon.classList.add('hidden');
            if (useGsap) {
                gsap.to(starIcon, { opacity: 1, duration: 0.2 });
                gsap.to(closeIcon, { opacity: 0, duration: 0.2 });
            } else {
                starIcon.style.opacity = 1;
                closeIcon.style.opacity = 0;
            }
        } else {
            ratingContainer.classList.add('visible');
            container.classList.add('rating-active');
            starIcon.classList.add('hidden');
            closeIcon.classList.remove('hidden');
            if (useGsap) {
                gsap.to(starIcon, { opacity: 0, duration: 0.2 });
                gsap.to(closeIcon, { opacity: 1, duration: 0.2 });
            } else {
                starIcon.style.opacity = 0;
                closeIcon.style.opacity = 1;
            }
            closeStatusMenu(container);
        }
    }

    function toggleStatusMenu(statusButton, container) {
        const statusContainer = statusButton.closest('.item-status-container');
        if (statusContainer) {
            const isActive = statusContainer.classList.toggle('active');
            if (isActive) {
                document.querySelectorAll('.item-status-container.active').forEach(openContainer => {
                    if (openContainer !== statusContainer) openContainer.classList.remove('active');
                });
                 const ratingActiveContainer = statusButton.closest('.item-actions-container.rating-active');
                 if(ratingActiveContainer) {
                     const starBtn = ratingActiveContainer.querySelector('.btn-star[data-action="toggle-rating"]');
                     if(starBtn) toggleRatingBlock(starBtn, ratingActiveContainer);
                 }
            }
        }
    }

    function closeStatusMenu(container) {
        const statusContainer = container.querySelector('.item-status-container');
        if (statusContainer) statusContainer.classList.remove('active');
    }

    function closeDropdownsOnClickOutside(event) {
        if (!event.target.closest('.item-status-container')) {
            document.querySelectorAll('.item-status-container.active').forEach(c => c.classList.remove('active'));
        }
        const ratingBlock = event.target.closest('.rating-container');
        const ratingToggle = event.target.closest('.btn-star[data-action="toggle-rating"]');
        if (!ratingBlock && !ratingToggle) {
            document.querySelectorAll('.item-actions-container.rating-active').forEach(c => {
                const starButton = c.querySelector('.btn-star[data-action="toggle-rating"]');
                if (starButton && c.classList.contains('rating-active')) {
                    toggleRatingBlock(starButton, c);
                }
            });
        }
    }

    function launchAchievements(button) {
        if (typeof gsap === 'undefined') {
            return;
        }
        const icons = ["trophy.svg", "gamepad.svg", "playstation.svg", "packman.svg", "fast_game.svg"];
        const iconBasePath = "/static/imgs/icons/";
        const rect = button.getBoundingClientRect();

        for (let i = 0; i < 15; i++) {
            let achievement = document.createElement("img");
            achievement.src = `${iconBasePath}${icons[Math.floor(Math.random() * icons.length)]}`;
            achievement.classList.add("achievement-particle");
            Object.assign(achievement.style, {
                position: "fixed", width: "25px", height: "25px", pointerEvents: "none",
                left: `${rect.left + rect.width / 2 - 12.5}px`, top: `${rect.top + rect.height / 2 - 12.5}px`,
                zIndex: 2100, opacity: 1,
            });
            document.body.appendChild(achievement);

            gsap.to(achievement, {
                x: (Math.random() - 0.5) * 120, y: (Math.random() - 0.5) * 120 - 40,
                opacity: 0, scale: Math.random() * 0.5 + 0.8, rotation: (Math.random() - 0.5) * 360,
                duration: 1.2, ease: "power1.out",
                onComplete: () => achievement.remove(),
            });
        }
    }

    function handleItemActionButtonClick(event) {
        const buttonOrLink = event.target.closest('button[data-action], a[data-action]');
        if (!buttonOrLink) return;

        const action = buttonOrLink.dataset.action;
        const container = buttonOrLink.closest('.item-actions-container');
        if (!container) {
            console.error("!! Не найден .item-actions-container для:", buttonOrLink);
            return;
        }

        const contentType = container.dataset.contentType;
        const itemId = container.dataset.itemId;
        const itemPk = container.dataset.itemPk;

        if (!contentType) {
            console.error("!! Не найден data-content-type в:", container);
            return;
        }
        
        if ((action === 'toggle-favorite' || action === 'set-status' || action === 'reset-status') && !itemId) {
            console.error(`!! Не найден data-item-id для действия '${action}' в:`, container);
            return;
        }
        if ((action === 'set-rating' || action === 'reset-rating' || action === 'open-rating-modal') && !itemPk) {
            console.error(`!! Не найден data-item-pk для действия '${action}' в:`, container);
            return;
        }
        
        if (action === 'toggle-favorite' || (buttonOrLink.tagName === 'A' && buttonOrLink.dataset.action)) {
            event.preventDefault();
        }

        switch (action) {
            case 'toggle-favorite':
                const favUrl = container.dataset.favoriteUrl;
                if (favUrl && favUrl !== '#') {
                    toggleFavorite(favUrl, itemId, contentType);
                } else {
                    console.error("Не найден корректный URL (data-favorite-url) для toggle-favorite:", container);
                }
                break;
            
            case 'open-rating-modal':
                openRatingModal(container);
                break;

            case 'toggle-status-menu':
                toggleStatusMenu(buttonOrLink.closest('.btn-item-status'), container);
                break;
            case 'set-status':
                 setItemStatus(buttonOrLink, container, itemId, contentType);
                 closeStatusMenu(container);
                 break;
            case 'reset-status':
                 resetItemStatus(buttonOrLink, container, itemId, contentType);
                 closeStatusMenu(container);
                 break;

            case 'toggle-rating':
                toggleRatingBlock(buttonOrLink, container);
                break;
            case 'set-rating':
                 selectRating(buttonOrLink, container);
                 break;
            case 'reset-rating':
                 resetRating(buttonOrLink, container);
                 break;

            default:
                console.warn("Неизвестное действие:", action, buttonOrLink);
        }
    }


    document.addEventListener('DOMContentLoaded', () => {
        document.body.addEventListener('click', handleItemActionButtonClick);
        document.addEventListener('click', closeDropdownsOnClickOutside);
        initializeRatingUI();

        if (modalOverlay) {
            if (modalCloseButton) {
                modalCloseButton.addEventListener('click', closeRatingModal);
            }
            modalOverlay.addEventListener('click', (event) => {
                if (event.target === modalOverlay) {
                    closeRatingModal();
                }
            });

            if (modalRatingOptionsContainer) {
                modalRatingOptionsContainer.addEventListener('click', (event) => {
                    const button = event.target.closest('button');
                    if (!button) return;

                    let ratingToSetInModal;
                    if (button.classList.contains('btn-trash')) {
                        ratingToSetInModal = null;
                    } else if (button.classList.contains('rating-btn')) { // Убедимся, что это кнопка с цифрой
                        const ratingVal = parseInt(button.textContent, 10);
                        if (isNaN(ratingVal) || ratingVal < 1 || ratingVal > 10) return;
                        ratingToSetInModal = ratingVal;
                    } else {
                        return; // Клик не по кнопке рейтинга или корзине
                    }
                    currentOpenModalContext.currentSelectedRatingInModal = ratingToSetInModal;
                    updateModalRatingButtonsUI(currentOpenModalContext.currentSelectedRatingInModal);
                });
            }

            if (modalRateButton) {
                modalRateButton.addEventListener('click', () => {
                    if (!modalRateButton.classList.contains('active')) {
                        if (currentOpenModalContext.currentSelectedRatingInModal === currentOpenModalContext.initialRatingOnOpen) {
                             closeRatingModal();
                        }
                        return;
                    }

                    if (!currentOpenModalContext.originalContainer || !currentOpenModalContext.contentType || !currentOpenModalContext.itemPk) {
                        console.error("Cannot submit rating from modal: context is missing.");
                        closeRatingModal();
                        return;
                    }
                    
                    const ratingToSendToServer = currentOpenModalContext.currentSelectedRatingInModal === null ? 0 : currentOpenModalContext.currentSelectedRatingInModal;

                    sendRatingUpdate(
                        currentOpenModalContext.contentType,
                        currentOpenModalContext.itemPk,
                        ratingToSendToServer,
                        currentOpenModalContext.originalContainer
                    );
                });
            }
        }
    });

} else {
    // console.warn("item_actions.js: Попытка повторной инициализации. Пропущено.");
}