// static/scripts/favourite_list.js

document.addEventListener('DOMContentLoaded', function() {
    //--------------------------------------------------------------------------
    // SECTION: DOM Element References
    //--------------------------------------------------------------------------
    const viewButtons = document.querySelectorAll('.view-toggle-btn');
    const filterSortControls = document.querySelector('.filter-sort-controls');
    const libraryContentArea = document.querySelector('.library-content-area');
    const detailedListViewButtonId = 'view-detailed-list';

    // Dropdown elements
    const filterDropdownWrapper = document.querySelector('#filter-options')?.closest('.custom-dropdown-wrapper');
    const sortDropdownWrapper = document.querySelector('#sort-options')?.closest('.custom-dropdown-wrapper');

    //--------------------------------------------------------------------------
    // SECTION: State Variables
    //--------------------------------------------------------------------------
    let currentView = 'view-grid'; // Default view
    let currentFilter = 'all';
    // currentSortState: stores individual column sort states e.g., { date_added: 'desc', rating: 'asc' }
    let currentSortState = {};
    // currentSortParam: the actual param sent to backend e.g., "date_added_desc"
    let currentSortParam = 'date_added_desc'; // Default sort param

    //--------------------------------------------------------------------------
    // SECTION: Initialization
    //--------------------------------------------------------------------------
    function initializeState() {
        // Initialize currentView
        const initialActiveViewButton = document.querySelector('.view-toggle-btn.active');
        if (initialActiveViewButton) {
            currentView = initialActiveViewButton.id;
        }

        // Initialize currentFilter
        const initialActiveFilterOption = document.querySelector('#filter-options li.active');
        if (initialActiveFilterOption) {
            currentFilter = initialActiveFilterOption.dataset.value;
            const filterToggleText = document.querySelector('#selected-filter-status');
            if (filterToggleText) filterToggleText.textContent = initialActiveFilterOption.textContent;
        }

        // Initialize currentSortParam and currentSortState from Django's initial_sort
        const initialSortKeyFromDjango = document.body.dataset.initialSort || // Check body
                                       document.querySelector('.profile-container')?.dataset.initialSort || // Check profile-container
                                       'date_added'; // Fallback
        
        if (initialSortKeyFromDjango === 'date_added' || initialSortKeyFromDjango === 'rating') {
            currentSortParam = `${initialSortKeyFromDjango}_desc`;
            currentSortState[initialSortKeyFromDjango] = 'desc';
        } else if (initialSortKeyFromDjango === 'title') {
            currentSortParam = `${initialSortKeyFromDjango}_asc`;
            currentSortState[initialSortKeyFromDjango] = 'asc';
        } else {
            currentSortParam = 'date_added_desc'; // Fallback default
            currentSortState['date_added'] = 'desc';
        }

        // Update sort dropdown text based on DOM
        const initialActiveSortOption = document.querySelector('#sort-options li.active');
        if (initialActiveSortOption) {
            const sortToggleText = document.querySelector('#selected-sort-criteria');
            if (sortToggleText) sortToggleText.textContent = initialActiveSortOption.textContent;
        }
        
        // Initial UI updates
        if (filterSortControls) {
            filterSortControls.style.display = (currentView === detailedListViewButtonId) ? 'none' : 'flex';
        }
        updateSortUI(initialSortKeyFromDjango); // Update arrows and dropdown text based on initialized sort
    }

    //--------------------------------------------------------------------------
    // SECTION: UI Update Functions
    //--------------------------------------------------------------------------
    function updateSortUI(activeSortColumnKey) {
        // Update sort arrows on table headers
        if (libraryContentArea) {
            libraryContentArea.querySelectorAll('.sortable-header').forEach(header => {
                const sortKey = header.dataset.sortValue;
                header.classList.remove('sort-asc', 'sort-desc', 'active-sort'); // Remove active-sort as well
                if (currentSortState[sortKey]) { // Only add if this column is being sorted
                    header.classList.add('active-sort'); // Mark as active sorting column
                    if (currentSortState[sortKey] === 'asc') {
                        header.classList.add('sort-asc');
                    } else if (currentSortState[sortKey] === 'desc') {
                        header.classList.add('sort-desc');
                    }
                }
            });
        }

        // Update main sort dropdown text and active item
        const mainSortDropdownToggleText = document.querySelector('#selected-sort-criteria');
        const mainSortDropdownOptions = document.querySelectorAll('#sort-options li');
        let foundActiveInDropdown = false;

        if (mainSortDropdownOptions.length > 0) {
            mainSortDropdownOptions.forEach(opt => {
                if (opt.dataset.value === activeSortColumnKey && currentSortState[activeSortColumnKey]) {
                    opt.classList.add('active');
                    if (mainSortDropdownToggleText) mainSortDropdownToggleText.textContent = opt.textContent;
                    foundActiveInDropdown = true;
                } else {
                    opt.classList.remove('active');
                }
            });
             // If no specific column is active (e.g. after a reset to default sort), select default in dropdown
            if (!foundActiveInDropdown && mainSortDropdownToggleText) {
                const defaultDropdownOption = document.querySelector(`#sort-options li[data-value="${activeSortColumnKey || 'date_added'}"]`) || document.querySelector('#sort-options li');
                if (defaultDropdownOption) {
                    mainSortDropdownToggleText.textContent = defaultDropdownOption.textContent;
                    defaultDropdownOption.classList.add('active');
                }
            }
        }
    }

    //--------------------------------------------------------------------------
    // SECTION: Data Fetching
    //--------------------------------------------------------------------------
    function fetchAndRenderItems() {
        const baseUrl = window.location.pathname;
        const queryParams = new URLSearchParams({
            status_filter: currentFilter,
            sort_by: currentSortParam,
            view_mode: currentView
        });

        console.log(`Fetching: ${baseUrl}?${queryParams.toString()}`);
        if (!libraryContentArea) {
            console.error('.library-content-area not found!');
            return;
        }
        libraryContentArea.innerHTML = '<p class="loading-indicator">Loading...</p>'; // Use a class for styling

        fetch(`${baseUrl}?${queryParams.toString()}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status} ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            if (data.html_items) {
                libraryContentArea.innerHTML = data.html_items;
                let activeSortKeyForUI = 'date_added'; // Default
                if (currentSortParam.includes('_')) {
                    activeSortKeyForUI = currentSortParam.substring(0, currentSortParam.lastIndexOf('_'));
                }
                if (currentView === 'view-tierlist') {
                    initializeTierListDragAndDrop(); // <--- ВАЖНО
                }
                updateSortUI(activeSortKeyForUI); // Update arrows after new content is rendered
            } else {
                libraryContentArea.innerHTML = "<p class='error-message'>Error: No items HTML received.</p>";
            }

            if (currentView === 'view-tierlist') { // currentView должен быть уже установлен в initializeState
                initializeTierListDragAndDrop();
            }
        })
        .catch(error => {
            console.error('Error fetching items:', error);
            libraryContentArea.innerHTML = `<p class='error-message'>Error loading items. Check console.</p>`;
        });
    }

    //--------------------------------------------------------------------------
    // SECTION: Event Listeners - View Toggles
    //--------------------------------------------------------------------------
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.classList.contains('active')) return;

            viewButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentView = this.id;

            if (filterSortControls) {
                filterSortControls.style.display = (this.id === detailedListViewButtonId) ? 'none' : 'flex';
            }
            fetchAndRenderItems();
        });
    });

    //--------------------------------------------------------------------------
    // SECTION: Event Listeners - Custom Dropdowns (Generic Logic)
    //--------------------------------------------------------------------------
    function setupDropdown(wrapperElement, onOptionSelectCallback) {
        if (!wrapperElement) return;

        const toggle = wrapperElement.querySelector('.custom-dropdown-toggle');
        const optionsList = wrapperElement.querySelector('.custom-dropdown-options');
        const selectedTextSpan = toggle?.querySelector('span:first-child');

        if (!toggle || !optionsList || !selectedTextSpan) {
            // console.warn('Dropdown component missing parts in wrapper:', wrapperElement);
            return;
        }

        toggle.addEventListener('click', function(event) {
            event.stopPropagation();
            // Close other open dropdowns
            document.querySelectorAll('.custom-dropdown-options.show').forEach(openDropdown => {
                if (openDropdown !== optionsList) {
                    openDropdown.classList.remove('show');
                    const otherToggle = openDropdown.closest('.custom-dropdown-wrapper')?.querySelector('.custom-dropdown-toggle');
                    if (otherToggle) otherToggle.setAttribute('aria-expanded', 'false');
                }
            });
            const isExpanded = optionsList.classList.toggle('show');
            toggle.setAttribute('aria-expanded', isExpanded.toString());
        });

        optionsList.addEventListener('click', function(event) {
            if (event.target.tagName === 'LI') {
                const li = event.target;
                selectedTextSpan.textContent = li.textContent;
                optionsList.querySelectorAll('li').forEach(opt => opt.classList.remove('active'));
                li.classList.add('active');
                optionsList.classList.remove('show');
                toggle.setAttribute('aria-expanded', 'false');
                
                onOptionSelectCallback(li.dataset.value, li);
            }
        });
    }

    // Setup Filter Dropdown
    setupDropdown(filterDropdownWrapper, (selectedValue) => {
        currentFilter = selectedValue;
        fetchAndRenderItems();
    });

    // Setup Sort Dropdown (Main Toolbar)
    setupDropdown(sortDropdownWrapper, (selectedValue) => {
        // selectedValue is "date_added", "rating", "title"
        currentSortState = {}; // Reset column-specific states
        if (selectedValue === 'date_added' || selectedValue === 'rating') {
            currentSortState[selectedValue] = 'desc';
            currentSortParam = `${selectedValue}_desc`;
        } else { // title
            currentSortState[selectedValue] = 'asc';
            currentSortParam = `${selectedValue}_asc`;
        }
        updateSortUI(selectedValue);
        fetchAndRenderItems();
    });

    // Close dropdowns if clicking outside
    document.addEventListener('click', function(event) {
        document.querySelectorAll('.custom-dropdown-options.show').forEach(dropdown => {
            if (!dropdown.closest('.custom-dropdown-wrapper').contains(event.target)) {
                dropdown.classList.remove('show');
                const toggle = dropdown.closest('.custom-dropdown-wrapper').querySelector('.custom-dropdown-toggle');
                if (toggle) toggle.setAttribute('aria-expanded', 'false');
            }
        });
    });

    //--------------------------------------------------------------------------
    // SECTION: Event Listeners - Library Content Area (Delegated)
    //--------------------------------------------------------------------------
    if (libraryContentArea) {
        libraryContentArea.addEventListener('click', function(event) {
            // --- Section Toggle ---
            const sectionToggleButton = event.target.closest('.section-toggle-btn');
            if (sectionToggleButton) {
                event.preventDefault();
                const sectionContentId = sectionToggleButton.getAttribute('aria-controls');
                const sectionContent = document.getElementById(sectionContentId);
                if (sectionContent) {
                    const isExpanded = sectionToggleButton.getAttribute('aria-expanded') === 'true';
                    sectionContent.style.display = isExpanded ? 'none' : '';
                    sectionToggleButton.setAttribute('aria-expanded', (!isExpanded).toString());
                }
            }

            // --- Table Header Sort ---
            const sortableHeader = event.target.closest('.sortable-header');
            if (sortableHeader) {
                event.preventDefault();
                const columnKey = sortableHeader.dataset.sortValue; // "date_added", "rating", "title"
                let newDirection;
                let newSortParamForRequest;

                const currentDirectionForColumn = currentSortState[columnKey];
                const isCurrentlyActiveColumn = Object.keys(currentSortState).length === 1 && currentSortState[columnKey];


                if (isCurrentlyActiveColumn) {
                    if (currentDirectionForColumn === 'desc') {
                        newDirection = 'asc'; 
                    } else {
                        currentSortState = { 'date_added': 'desc' };
                        newSortParamForRequest = 'date_added_desc';
                        updateSortUI('date_added');
                        currentSortParam = newSortParamForRequest;
                        fetchAndRenderItems();
                        return; 
                    }
                } else {
                    if (columnKey === 'date_added' || columnKey === 'rating') {
                        newDirection = 'desc';
                    } else {
                        newDirection = 'asc';
                    }
                }
                
                currentSortState = {};
                currentSortState[columnKey] = newDirection;
                newSortParamForRequest = `${columnKey}_${newDirection}`;
                
                currentSortParam = newSortParamForRequest;
                updateSortUI(columnKey);
                fetchAndRenderItems();
            }

            // --- More Options Button ---
            const moreOptionsButton = event.target.closest('.more-options-btn');
            if (moreOptionsButton) {
                event.preventDefault();
                console.log('More options clicked for an item.');
            }
        });
    }

    function initializeTierListDragAndDrop() {
        const tierlistContainer = document.querySelector('.tierlist-container');
        if (!tierlistContainer) {
            console.warn("Tierlist container not found, D&D not initialized.");
            return;
        }
    
        const sortableLists = tierlistContainer.querySelectorAll('.sortable-list');
        if (sortableLists.length === 0) {
            console.warn("No sortable lists found in tierlist container.");
            return;
        }
    
        console.log(`Initializing D&D for ${sortableLists.length} sortable lists.`);
    
        sortableLists.forEach(listElement => {
            new Sortable(listElement, {
                group: 'tierlist-items',
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                fallbackOnBody: true,
                swapThreshold: 0.65,
    
                onEnd: function (evt) { // evt - это контекст события SortableJS
                    const itemEl = evt.item; // Перетаскиваемый элемент
                    const toListEl = evt.to;   // Список, куда перетащили
                    // const fromListEl = evt.from; // Список, откуда перетащили (может быть тот же самый)
                
                    const itemPk = itemEl.dataset.itemId;
                    const contentType = itemEl.dataset.contentType; 
                    
                    const targetTierRow = toListEl.closest('.tier-row');
                    if (!targetTierRow) {
                        console.error('Could not find parent .tier-row for the target list.');
                        if(evt.from) evt.from.appendChild(itemEl);
                        return;
                    }
                
                    const newRatingValueStr = targetTierRow.dataset.ratingValue;
                    let newRatingApiValue;
                
                    if (newRatingValueStr && newRatingValueStr.toLowerCase() !== 'none' && newRatingValueStr.toLowerCase() !== 'unranked') {
                        const parsedRating = parseInt(newRatingValueStr, 10);
                        if (!isNaN(parsedRating) && parsedRating >= 1 && parsedRating <= 10) {
                            newRatingApiValue = parsedRating;
                        } else {
                            console.error('Invalid rating value on target tier row:', newRatingValueStr);
                            if(evt.from) evt.from.appendChild(itemEl);
                            return;
                        }
                    } else {
                        newRatingApiValue = null; 
                    }
                
                    console.log(`Item PK: ${itemPk} (${contentType}) moved to tier with rating value: ${newRatingValueStr}. Sending API rating: ${newRatingApiValue}`);
                
                    updateItemRatingViaAPI(contentType, itemPk, newRatingApiValue, itemEl, evt);
                }
            });
        });
    }

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

    function checkTierEmptyPlaceholders(tierItemsContainer) {
        if (!tierItemsContainer || !tierItemsContainer.classList.contains('tier-items-container')) {
            // console.warn("Invalid element passed to checkTierEmptyPlaceholders or not a tier-items-container", tierItemsContainer);
            return;
        }
        const placeholder = tierItemsContainer.querySelector('.tier-empty-placeholder');
        if (!placeholder) {
            // console.warn("No placeholder found in tier:", tierItemsContainer);
            return;
        }
    
        // Считаем только карточки айтемов, исключая сам плейсхолдер, если он тоже .tier-item-card (не должен быть)
        const itemCount = tierItemsContainer.querySelectorAll('.tier-item-card').length;
        
        if (itemCount === 0) {
            placeholder.style.display = 'block'; // Или 'flex', в зависимости от твоей верстки
        } else {
            placeholder.style.display = 'none';
        }
    }
    
    function updateItemRatingViaAPI(contentType, itemPk, ratingValue, draggedElement, evtContext) { // evtContext для доступа к evt.from
        const url = `/user/tierlist/rate/${contentType}/${itemPk}/`;
        const csrftoken = getCookie('csrftoken');

        console.log("Attempting to update rating. URL:", url);
        console.log("ContentType:", contentType, "Item PK:", itemPk, "Rating Value:", ratingValue);
    
        let apiRatingPayload;
        if (ratingValue === 0 || ratingValue === null || ratingValue === undefined || ratingValue === 'none' || ratingValue === 'unranked') {
            apiRatingPayload = null; // Бэкенд ожидает null для сброса оценки
        } else {
            apiRatingPayload = parseInt(ratingValue, 10);
            if (isNaN(apiRatingPayload) || apiRatingPayload < 1 || apiRatingPayload > 10) {
                console.error("Invalid rating value before sending to API:", ratingValue);
                // Можно откатить перетаскивание тут, если значение некорректно
                if (evtContext && evtContext.from && draggedElement) {
                    evtContext.from.appendChild(draggedElement);
                    checkTierEmptyPlaceholders(draggedElement.parentElement); // Обновить старый список
                    if (evtContext.to) checkTierEmptyPlaceholders(evtContext.to); // Обновить новый список
                }
                alert("Error: Invalid rating value assigned.");
                return;
            }
        }
    
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ rating: apiRatingPayload })
        })
        .then(response => {
            if (!response.ok) {
                 return response.json().then(errData => {
                     throw new Error(errData.message || `HTTP error! Status: ${response.status}`);
                 }).catch(() => { // Если .json() тоже фейлится или нет errData.message
                     throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
                 });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                console.log(`Rating for ${contentType} (PK: ${itemPk}) successfully updated to: ${data.current_rating === null ? 'None' : data.current_rating}`);
                if (draggedElement) {
                    draggedElement.dataset.currentRating = data.current_rating === null ? '' : data.current_rating;
                    // Элемент уже визуально перемещен SortableJS. Ничего откатывать не нужно.
                }
                // Обновляем плейсхолдеры для списка, куда перетащили, и откуда (если это разные списки)
                if (evtContext && evtContext.to) checkTierEmptyPlaceholders(evtContext.to);
                if (evtContext && evtContext.from && evtContext.from !== evtContext.to) {
                     checkTierEmptyPlaceholders(evtContext.from);
                }
    
            } else {
                console.error(`Error saving rating: ${data.message}`);
                alert(`Error: ${data.message}. Reverting drag.`);
                // Если ошибка, откатываем перетаскивание
                if (evtContext && evtContext.from && draggedElement) {
                    evtContext.from.appendChild(draggedElement); // Перемещаем элемент обратно
                    // Обновляем плейсхолдеры после отката
                    checkTierEmptyPlaceholders(draggedElement.parentElement); // Обновить старый список (куда вернули)
                    if (evtContext.to) checkTierEmptyPlaceholders(evtContext.to); // Обновить новый список (откуда вернули)
                }
            }
        })
        .catch(error => {
            console.error(`Fetch error while updating rating for ${contentType} (PK: ${itemPk}):`, error);
            alert(`Network or other error updating rating: ${error.message}. Reverting drag.`);
            // Если ошибка сети, откатываем перетаскивание
            if (evtContext && evtContext.from && draggedElement) {
                evtContext.from.appendChild(draggedElement); // Перемещаем элемент обратно
                checkTierEmptyPlaceholders(draggedElement.parentElement);
                if (evtContext.to) checkTierEmptyPlaceholders(evtContext.to);
            }
        });
    }   

    //--------------------------------------------------------------------------
    // SECTION: Initial Call (if any needed beyond Django render)
    //--------------------------------------------------------------------------
    initializeState();
    console.log('Initial state:', { currentView, currentFilter, currentSortParam, currentSortState });
});