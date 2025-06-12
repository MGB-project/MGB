// profile.js
document.addEventListener('DOMContentLoaded', () => {
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
    const csrftoken = getCookie('csrftoken');

    const profilePhotoDiv = document.querySelector('.profile-photo');
    const profileHeader = document.querySelector('.profile-header');
    
    // Получаем начальные URL из window переменных, установленных в шаблоне
    let currentAvatarUrl = window.PROFILE_USER_AVATAR_URL || profilePhotoDiv?.dataset.avatarUrl || "";
    let currentBannerColor = window.PROFILE_USER_BANNER_COLOR || profileHeader?.dataset.initialBannerColor || "";

    function applyColorThief(avatarUrlForThief) {
        if (typeof ColorThief === 'undefined') {
            // console.warn('ColorThief library is not loaded.');
            return; // Не делаем ничего, если ColorThief не загружен
        }

        if (avatarUrlForThief && profileHeader) {
            const img = new Image();
            img.crossOrigin = "Anonymous"; // Важно для CORS, если аватары с другого домена
            img.onload = () => {
                try {
                    const colorThief = new ColorThief();
                    const dominantColorRgb = colorThief.getColor(img);
                    const dominantColorCss = `rgb(${dominantColorRgb.join(',')})`;
                    const darkenFactor = 0.5; 
                    const darkRgb = dominantColorRgb.map(c => Math.round(c * darkenFactor));
                    const darkColorCss = `rgb(${darkRgb.join(',')})`;
                    const gradient = `linear-gradient(to bottom, ${darkColorCss} 10%, ${dominantColorCss} 50%, #2a313700 100%)`;
                    profileHeader.style.background = gradient;
                } catch (error) { 
                    console.error("Ошибка ColorThief:", error);
                    // Можно установить дефолтный фон, если очень нужно
                    // profileHeader.style.background = '#1e2328'; 
                }
            };
            img.onerror = (error) => {
                console.error("Ошибка загрузки аватара для ColorThief:", avatarUrlForThief, error);
                // profileHeader.style.background = '#1e2328'; 
            };
            img.src = avatarUrlForThief;
        } else if (profileHeader && !avatarUrlForThief) {
             // Если нет аватара, сбрасываем фон или ставим дефолт (если не установлен кастомный)
             // profileHeader.style.background = ''; // или '#1e2328'
        }
    }

    // --- Начальная установка фона хедера ---
    if (currentBannerColor && currentBannerColor.trim() !== '' && currentBannerColor !== 'null') {
        profileHeader.style.background = currentBannerColor;
    } else if (currentAvatarUrl) {
        applyColorThief(currentAvatarUrl);
    } else {
        // Дефолтный фон, если нет ни кастомного цвета, ни аватара
        // profileHeader.style.background = '#1e2328'; // Например
    }

    // --- КОД ДЛЯ ПЕРЕКЛЮЧЕНИЯ ТАБОВ (без изменений, как у тебя) ---
    const tabsNavContainer = document.querySelector('.profile-tabs-nav');
    const tabButtons = document.querySelectorAll('.profile-tabs-nav .tab-button');
    const contentPanels = document.querySelectorAll('.profile-tabs-content .tab-content');
    const defaultTabId = 'tab-overview';

    function activateTab(targetTabIdFull) {
        let targetTabId = targetTabIdFull;
        if (targetTabIdFull.startsWith('#')) {
            targetTabId = targetTabIdFull.substring(1);
        }
        const targetButton = document.querySelector(`.tab-button[data-tab-target="#${targetTabId}"]`);
        const targetPanel = document.getElementById(targetTabId);
        tabButtons.forEach(button => button.classList.remove('active-tab'));
        contentPanels.forEach(panel => panel.classList.remove('active-content'));
        if (targetButton && targetPanel) {
            targetButton.classList.add('active-tab');
            targetPanel.classList.add('active-content');
        } else {
            const defaultButtonElem = document.querySelector(`.tab-button[data-tab-target="#${defaultTabId}"]`);
            const defaultPanelElem = document.getElementById(defaultTabId);
            if (defaultButtonElem && defaultPanelElem) {
                defaultButtonElem.classList.add('active-tab');
                defaultPanelElem.classList.add('active-content');
            }
        }
    }
    if (tabsNavContainer && tabButtons.length > 0 && contentPanels.length > 0) {
        tabsNavContainer.addEventListener('click', (event) => {
            const clickedButton = event.target.closest('.tab-button');
            if (!clickedButton) return;
            const targetPanelSelector = clickedButton.dataset.tabTarget;
            if (!targetPanelSelector) return;
            activateTab(targetPanelSelector);
            const cleanHash = targetPanelSelector.replace('#tab-', '');
            if (window.location.hash !== '#' + cleanHash) {
                 history.pushState(null, null, '#' + cleanHash);
            }
        });
    }
    function activateTabFromUrlHash() {
        const hash = window.location.hash.substring(1);
        if (hash) {
            const targetTabIdFromHash = `tab-${hash}`;
            const targetPanelExists = document.getElementById(targetTabIdFromHash);
            if (targetPanelExists) activateTab(targetTabIdFromHash);
            else activateTab(defaultTabId);
        } else {
            activateTab(defaultTabId);
        }
    }
    activateTabFromUrlHash();
    window.addEventListener('hashchange', activateTabFromUrlHash);
    // --- КОНЕЦ КОДА ДЛЯ ТАБОВ ---

    // --- МОДАЛЬНОЕ ОКНО НАСТРОЕК ПРОФИЛЯ (первое) ---
    const editBtn = document.querySelector(".profile-edit-button");
    const optionsModal = document.getElementById("profile-options-modal"); // Переименовал для ясности
    const openEditDetailsBtnInOptionsModal = optionsModal ? optionsModal.querySelector(".edit-profile-btn") : null;
  
    if (editBtn && optionsModal) {
        editBtn.addEventListener("click", function (e) {
            const rect = editBtn.getBoundingClientRect();
            optionsModal.style.left = `${rect.left - 200}px`; // Подгони смещение, если нужно
            optionsModal.style.top = `${rect.bottom + 5}px`;
            optionsModal.style.display = optionsModal.style.display === "none" ? "block" : "none";
        });
    
        document.addEventListener("click", function (e) {
            if (optionsModal.style.display === 'block' && !optionsModal.contains(e.target) && e.target !== editBtn) {
                optionsModal.style.display = "none";
            }
        });
    }

    // --- МОДАЛЬНОЕ ОКНО РЕДАКТИРОВАНИЯ ДЕТАЛЕЙ ПРОФИЛЯ (второе) ---
    const editProfileDetailsModal = document.getElementById("edit-profile-details-modal");

    if (openEditDetailsBtnInOptionsModal && editProfileDetailsModal) {
        const cancelEditProfileBtn = document.getElementById("cancelEditProfileBtn");
        const saveEditProfileBtn = document.getElementById("saveEditProfileBtn");
        const usernameEditInput = document.getElementById("usernameEdit");
        const usernameCharCountSpan = document.getElementById("usernameCharCount");
        const bioEditInput = document.getElementById("bioEdit");
        const bioCharCountSpan = document.getElementById("bioCharCount");
        const bannerPreviewElement = editProfileDetailsModal.querySelector(".edit-profile-banner"); // Переименовал
        const colorSwatches = editProfileDetailsModal.querySelectorAll(".edit-profile-color-palette .color-swatch");
        const removeColorSwatch = editProfileDetailsModal.querySelector(".remove-color-swatch");
        const avatarPreviewContainer = editProfileDetailsModal.querySelector(".edit-profile-avatar-container"); // Переименовал
        const avatarUploadInput = document.getElementById("avatarUpload");
        const avatarPlaceholderIcon = editProfileDetailsModal.querySelector(".edit-profile-avatar-placeholder-icon");
        
        const defaultBannerColorInModalPreview = "rgb(30, 30, 30)"; // #1E1E1E, для предпросмотра при "remove color"

        function updateCharCount(inputElement, countElement) {
            const maxLength = inputElement.maxLength;
            const currentLength = inputElement.value.length;
            countElement.textContent = `${currentLength}/${maxLength}`;
        }

        function showEditProfileDetailsModal() {
            // Заполняем поля текущими данными пользователя со страницы
            const profileUsernameH1 = document.querySelector('.profile-info h1');
            const profileBioDiv = document.querySelector('.profile-bio');
            
            usernameEditInput.value = profileUsernameH1 ? profileUsernameH1.textContent.trim() : '';
            bioEditInput.value = profileBioDiv ? profileBioDiv.textContent.trim() : '';
            updateCharCount(usernameEditInput, usernameCharCountSpan);
            updateCharCount(bioEditInput, bioCharCountSpan);

            // Сбрасываем и устанавливаем предпросмотр аватара
            avatarUploadInput.value = ''; // Очищаем инпут файла
            const currentAvatarStyle = profilePhotoDiv ? profilePhotoDiv.style.backgroundImage : 'none';
            if (currentAvatarStyle && currentAvatarStyle !== 'none' && currentAvatarStyle !== '') {
                 avatarPreviewContainer.style.backgroundImage = currentAvatarStyle;
                 if (avatarPlaceholderIcon) avatarPlaceholderIcon.style.display = 'none';
            } else {
                 avatarPreviewContainer.style.backgroundImage = 'none';
                 if (avatarPlaceholderIcon) avatarPlaceholderIcon.style.display = 'flex';
            }

            // Устанавливаем цвет баннера в предпросмотре модалки и активный swatch
            const actualProfileHeaderBg = profileHeader.style.background; // Текущий фон главного хедера
            bannerPreviewElement.style.background = defaultBannerColorInModalPreview; // Сначала ставим дефолт
            let swatchMatched = false;
            colorSwatches.forEach(s => s.classList.remove("active-swatch"));

            // Пытаемся найти соответствующий swatch, если фон НЕ градиент
            if (actualProfileHeaderBg && !actualProfileHeaderBg.includes('gradient') && actualProfileHeaderBg.trim() !== '') {
                colorSwatches.forEach(swatch => {
                    if (!swatch.classList.contains('remove-color-swatch') && swatch.style.background === actualProfileHeaderBg) {
                        swatch.classList.add("active-swatch");
                        bannerPreviewElement.style.background = actualProfileHeaderBg; // Ставим этот цвет в предпросмотр
                        swatchMatched = true;
                    }
                });
            }
            
            // Если не нашлось совпадения (или это градиент/пустой), активируем "remove-color-swatch"
            if (!swatchMatched && removeColorSwatch) {
                removeColorSwatch.classList.add("active-swatch");
                // bannerPreviewElement.style.background остается defaultBannerColorInModalPreview
            }

            editProfileDetailsModal.style.display = "flex";
        }

        function hideEditProfileDetailsModal() {
            editProfileDetailsModal.style.display = "none";
        }

        // Открытие ВТОРОГО модального окна
        openEditDetailsBtnInOptionsModal.addEventListener("click", (e) => {
            e.preventDefault();
            if (optionsModal) optionsModal.style.display = "none"; // Закрываем первое модальное окно
            showEditProfileDetailsModal();
        });

        cancelEditProfileBtn.addEventListener("click", hideEditProfileDetailsModal);

        saveEditProfileBtn.addEventListener("click", () => {
            const formData = new FormData();
            formData.append('username', usernameEditInput.value);
            formData.append('bio', bioEditInput.value);
            
            if (avatarUploadInput.files[0]) {
                formData.append('avatar', avatarUploadInput.files[0]);
            }

            // Добавляем цвет баннера
            const activeSwatch = editProfileDetailsModal.querySelector(".color-swatch.active-swatch");
            let bannerColorToSend = ""; 
            if (activeSwatch) {
                if (activeSwatch.classList.contains('remove-color-swatch')) {
                    bannerColorToSend = "_REMOVE_BANNER_"; // Сигнал серверу для сброса
                } else {
                    bannerColorToSend = activeSwatch.style.background; // Отправляем выбранный цвет
                }
            }
            formData.append('banner_color', bannerColorToSend);

            fetch(window.location.pathname, { // Отправляем на текущий URL профиля
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Обновляем UI на главной странице профиля
                    const profileUsernameH1 = document.querySelector('.profile-info h1');
                    if (profileUsernameH1) profileUsernameH1.textContent = data.username || usernameEditInput.value;
                    
                    const profileBioDiv = document.querySelector('.profile-bio');
                    if (profileBioDiv) profileBioDiv.textContent = data.bio !== undefined ? data.bio : bioEditInput.value;

                    // Обновление аватара на странице
                    if (data.new_avatar_url) {
                        currentAvatarUrl = data.new_avatar_url; // Обновляем глобальную переменную
                        if (profilePhotoDiv) {
                            profilePhotoDiv.style.backgroundImage = `url('${currentAvatarUrl}')`;
                            profilePhotoDiv.dataset.avatarUrl = currentAvatarUrl; 
                        }
                    } else if (avatarUploadInput.files[0] && !data.new_avatar_url) {
                        // Локальное обновление, если сервер не вернул URL (менее предпочтительно)
                        const reader = new FileReader();
                        reader.onload = (e_reader) => {
                            if (profilePhotoDiv) {
                                profilePhotoDiv.style.backgroundImage = `url('${e_reader.target.result}')`;
                                // currentAvatarUrl = e_reader.target.result; // Не обновляем глобальный, если сервер не подтвердил
                            }
                        };
                        reader.readAsDataURL(avatarUploadInput.files[0]);
                    }

                    // Обновляем фон хедера (profileHeader)
                    currentBannerColor = data.updated_banner_color || ""; // Обновляем глобальную
                    if (currentBannerColor && currentBannerColor !== "") {
                        profileHeader.style.background = currentBannerColor;
                        profileHeader.dataset.initialBannerColor = currentBannerColor; // Для следующего открытия модалки
                    } else {
                        // Если цвет баннера был сброшен (updated_banner_color пустой)
                        profileHeader.dataset.initialBannerColor = "";
                        // Применяем ColorThief к текущему (возможно, новому) аватару
                        if (currentAvatarUrl) {
                           applyColorThief(currentAvatarUrl);
                        } else {
                           profileHeader.style.background = ''; // Или дефолтный фон
                        }
                    }
                    
                    // Обновляем глобальные переменные для следующего открытия модалки
                    window.PROFILE_USER_BANNER_COLOR = currentBannerColor;
                    window.PROFILE_USER_AVATAR_URL = currentAvatarUrl;


                    hideEditProfileDetailsModal();
                } else {
                    console.error('Ошибка обновления профиля:', data.errors);
                    let errorMessages = "Не удалось обновить профиль:\n";
                    if (data.errors && typeof data.errors === 'object') {
                        for (const field in data.errors) {
                            const fieldErrors = data.errors[field];
                            if (Array.isArray(fieldErrors)) {
                                errorMessages += `${field}: ${fieldErrors.map(e => e.message || e).join(', ')}\n`;
                            }
                        }
                    } else if (data.message) {
                         errorMessages += data.message;
                    }
                    alert(errorMessages);
                }
            })
            .catch(error => {
                console.error('Fetch ошибка:', error);
                alert('Произошла сетевая ошибка. Пожалуйста, попробуйте снова.');
            });
        });

        // Закрытие модалки по клику вне ее
        editProfileDetailsModal.addEventListener("click", (event) => {
            if (event.target === editProfileDetailsModal) {
                hideEditProfileDetailsModal();
            }
        });

        // Счетчики символов
        usernameEditInput.addEventListener("input", () => updateCharCount(usernameEditInput, usernameCharCountSpan));
        bioEditInput.addEventListener("input", () => updateCharCount(bioEditInput, bioCharCountSpan));

        // Выбор цвета в палитре
        colorSwatches.forEach(swatch => {
            swatch.addEventListener("click", () => {
                colorSwatches.forEach(s => s.classList.remove("active-swatch"));
                swatch.classList.add("active-swatch");
                if (swatch.classList.contains("remove-color-swatch")) {
                    bannerPreviewElement.style.background = defaultBannerColorInModalPreview;
                } else {
                    bannerPreviewElement.style.background = swatch.style.background;
                }
            });
        });

        // Клик по контейнеру аватара для выбора файла
        avatarPreviewContainer.addEventListener("click", () => {
            avatarUploadInput.click();
        });

        // Предпросмотр выбранного аватара
        avatarUploadInput.addEventListener("change", (event) => {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    avatarPreviewContainer.style.backgroundImage = `url('${e.target.result}')`;
                    if (avatarPlaceholderIcon) avatarPlaceholderIcon.style.display = 'none';
                };
                reader.readAsDataURL(file);
            }
        });
    }
});