document.addEventListener('DOMContentLoaded', () => {
    console.log("Profile Overview Script V8 (Smooth Morphing Attempt) Loaded");

    // --- Глобальные DOM-элементы ---
    const favGridContent = document.getElementById('overview-fav-grid-content');
    const dynamicGridContainer = favGridContent ? favGridContent.querySelector('.overview-fav-grid-actual') : null;
    const initialDataSourceContainer = document.getElementById('initial-favorite-data-source');
    const favListContent = document.getElementById('overview-fav-list-content');
    const favTabsContainer = document.querySelector('.fav-container .fav-tabs');
    const favTabButtons = favTabsContainer ? favTabsContainer.querySelectorAll('.fav-tab-button') : [];
    const favListUl = favListContent ? favListContent.querySelector('.overview-favorites-ul') : null;
    const favFiltersButton = document.querySelector('.fav-container .btn-fav-filters');
    const favFiltersPopover = document.getElementById('overview-fav-filters-popover');
    const favFiltersList = favFiltersPopover ? favFiltersPopover.querySelector('.fav-filters-list') : null;
    let allFilterCheckbox;
    let typeFilterCheckboxes = [];

    if (favFiltersList) {
        allFilterCheckbox = favFiltersList.querySelector('input[data-filter-type="all"]');
        typeFilterCheckboxes = Array.from(favFiltersList.querySelectorAll('input[name="fav_filter_type_popover"]'))
            .filter(cb => cb !== allFilterCheckbox);
    }

    // --- Константы и состояние ---
    const ACTIVE_VIEW_SWITCH_CLASS = 'favorite-active-tab';
    const ACTIVE_VIEW_CONTENT_CLASS = 'active-fav-view';
    const FADE_DURATION = 600; // Длительность анимации opacity в мс
    const BIG_BLOCK_LAYOUT_CHANGE_INTERVAL = 8000;
    const CELL_CONTENT_CHANGE_BASE_INTERVAL = 4000;
    const SHOWCASE_CELL_CONTENT_CHANGE_INTERVAL = 3000;

    let allPossibleFavItemsData = [];
    let currentlyDisplayedFavItemIds = new Set();
    const bigBlocksState = [];
    let globalUpdateActive = false;
    let systemDataInitialized = false;

    // --- Логика для СТАРОГО вида (список и его фильтры) - ОСТАВЛЯЕМ КАК ЕСТЬ ---
    function switchFavView(targetView) {
        if (favTabButtons.length > 0) {
            favTabButtons.forEach(button => {
                button.classList.remove(ACTIVE_VIEW_SWITCH_CLASS);
                if (button.dataset.favView === targetView) {
                    button.classList.add(ACTIVE_VIEW_SWITCH_CLASS);
                }
            });
        }
        if (favGridContent) favGridContent.classList.remove(ACTIVE_VIEW_CONTENT_CLASS);
        if (favListContent) favListContent.classList.remove(ACTIVE_VIEW_CONTENT_CLASS);

        if (targetView === 'grid' && favGridContent) {
            favGridContent.classList.add(ACTIVE_VIEW_CONTENT_CLASS);
        } else if (targetView === 'list' && favListContent) {
            favListContent.classList.add(ACTIVE_VIEW_CONTENT_CLASS);
        }
        if (targetView === 'list') applyLegacyFavFilters();
        observerDynamicGridState();
    }
    function toggleLegacyFiltersPopover() {
         if (!favFiltersPopover) return;
        const isVisible = favFiltersPopover.style.display === 'block';
        favFiltersPopover.style.display = isVisible ? 'none' : 'block';
    }
    function applyLegacyFavFilters() {
        if (!favListUl) return;
        const currentListItems = Array.from(favListUl.children);
        const noFilterControls = !allFilterCheckbox && typeFilterCheckboxes.length === 0;
        const selectedFilters = [];
         if (!noFilterControls) {
            if (allFilterCheckbox && allFilterCheckbox.checked) {
                typeFilterCheckboxes.forEach(cb => { if (cb.dataset.filterType) selectedFilters.push(cb.dataset.filterType); });
                if (selectedFilters.length === 0) selectedFilters.push('movie', 'game', 'book');
            } else if (allFilterCheckbox) {
                typeFilterCheckboxes.forEach(cb => { if (cb.checked && cb.dataset.filterType) selectedFilters.push(cb.dataset.filterType); });
            }
        } else { selectedFilters.push('movie', 'game', 'book');}
        let visibleCount = 0;
        currentListItems.forEach(item => {
            const itemType = item.dataset.itemType;
            const shouldShow = noFilterControls || selectedFilters.includes(itemType);
            item.style.display = shouldShow ? '' : 'none';
            if (shouldShow) visibleCount++;
        });
        const messageList = favListContent ? favListContent.querySelector('.no-filtered-favorites-message') : null;
        if (messageList) messageList.style.display = (currentListItems.length > 0 && visibleCount === 0 && !noFilterControls) ? 'block' : 'none';
    }
    function handleLegacyAllCheckboxChange() { 
        if (!allFilterCheckbox) return;
        const i = allFilterCheckbox.checked;
        typeFilterCheckboxes.forEach(cb => { cb.disabled=i; if(i)cb.checked=true;});
        applyLegacyFavFilters(); 
    }
    function handleLegacyTypeCheckboxChange() { if (!allFilterCheckbox) {applyLegacyFavFilters(); return;} const a = typeFilterCheckboxes.every(cb=>cb.checked); if(a){if(!allFilterCheckbox.checked){allFilterCheckbox.checked=true; handleLegacyAllCheckboxChange(); return;}}else{if(allFilterCheckbox.checked){allFilterCheckbox.checked=false; typeFilterCheckboxes.forEach(cb=>cb.disabled=false);}} applyLegacyFavFilters(); }
    function initializeLegacyFilterControls() {
        if (favFiltersList) { if (allFilterCheckbox) handleLegacyAllCheckboxChange(); else applyLegacyFavFilters(); if (favFiltersPopover) favFiltersPopover.style.display = 'none'; } else { applyLegacyFavFilters(); }
        if (favTabsContainer) { favTabsContainer.addEventListener('click', (event) => { const clickedButton = event.target.closest('.fav-tab-button'); if (clickedButton && clickedButton.dataset.favView) switchFavView(clickedButton.dataset.favView); }); }
        if (favFiltersButton) { favFiltersButton.addEventListener('click', (event) => { event.stopPropagation(); toggleLegacyFiltersPopover(); }); }
        if (allFilterCheckbox) allFilterCheckbox.addEventListener('change', handleLegacyAllCheckboxChange);
        typeFilterCheckboxes.forEach(cb => cb.addEventListener('change', handleLegacyTypeCheckboxChange));
        document.addEventListener('click', (event) => { if (favFiltersPopover && favFiltersPopover.style.display === 'block') if (!favFiltersPopover.contains(event.target) && (!favFiltersButton || !favFiltersButton.contains(event.target))) favFiltersPopover.style.display = 'none'; });
    }

    // --- Логика для НОВОЙ ДИНАМИЧЕСКОЙ СЕТКИ ---
    function parseSourceItemData(element) {
        if (!element || !element.dataset) return null;
        return { id: element.dataset.itemId, type: element.dataset.itemType, imageUrl: element.dataset.imageUrl, detailUrl: element.dataset.detailUrl, title: element.dataset.title };
    }
    function initializeDataSourceOnce() {
        if (systemDataInitialized) return;
        allPossibleFavItemsData = [];
        if (!initialDataSourceContainer) { systemDataInitialized = true; return; }
        const initialDataItems = initialDataSourceContainer.querySelectorAll('.initial-fav-data-item');
        initialDataItems.forEach(element => { const itemData = parseSourceItemData(element); if (itemData) allPossibleFavItemsData.push(itemData); });
        systemDataInitialized = true;
    }
    function getRandomAvailableFavItems(count = 1, excludeIds = new Set()) {
        const available = allPossibleFavItemsData.filter(item => !currentlyDisplayedFavItemIds.has(item.id) && !excludeIds.has(item.id));
        if (available.length < count) {
            const backupAvailable = allPossibleFavItemsData.filter(item => !excludeIds.has(item.id));
            const shuffledBackup = [...backupAvailable].sort(() => 0.5 - Math.random());
            return shuffledBackup.slice(0, count);
        }
        return [...available].sort(() => 0.5 - Math.random()).slice(0, count);
    }

    function fadeOutPromise(element, duration = FADE_DURATION) {
        return new Promise(resolve => {
            if (!element || !element.style) { resolve(); return; }
            element.style.transition = `opacity ${duration}ms ease-in-out`;
            element.style.opacity = '0';
            setTimeout(resolve, duration);
        });
    }
    function fadeInPromise(element, duration = FADE_DURATION) {
        return new Promise(resolve => {
            if (!element || !element.style) { resolve(); return; }
            if (element.style.display === 'none') element.style.display = ''; // Убедимся, что элемент видим перед анимацией opacity
            element.style.transition = `opacity ${duration}ms ease-in-out`;
            requestAnimationFrame(() => { // Дает браузеру время применить display: '' если он был none
                requestAnimationFrame(() => { // Второй rAF для старта анимации opacity
                    element.style.opacity = '1';
                    setTimeout(resolve, duration);
                });
            });
        });
    }

    async function renderCellContent(cellState, animateAppearance = true) {
        const { element: cellElement, type: cellType, favIds: currentCellFavIds } = cellState;

        currentCellFavIds.forEach(id => currentlyDisplayedFavItemIds.delete(id));
        currentCellFavIds.clear();

        const itemsToDisplay = getRandomAvailableFavItems(cellType === 'showcase4' ? 4 : 1, new Set());
        const oldChildren = Array.from(cellElement.children);

        if (animateAppearance && oldChildren.length > 0) { // Анимируем исчезновение только если animateAppearance=true
            await Promise.all(oldChildren.map(child => fadeOutPromise(child)));
        }
        cellElement.innerHTML = ''; // Очищаем после исчезновения или сразу, если не анимируем

        if (itemsToDisplay.length === 0) {
            cellElement.innerHTML = '<div class="placeholder-content" style="opacity: 0;">N/A</div>';
            const placeholder = cellElement.querySelector('.placeholder-content');
            if (placeholder) {
                 if (animateAppearance) await fadeInPromise(placeholder); else placeholder.style.opacity = '1';
            }
            return;
        }

        itemsToDisplay.forEach(item => {
            currentlyDisplayedFavItemIds.add(item.id);
            currentCellFavIds.add(item.id);
        });

        let newContentWrapper;
        if (cellType === 'showcase4') {
            cellElement.classList.add('showcase-cell');
            const miniGrid = document.createElement('div');
            miniGrid.className = 'fav-cell-mini-grid';
            itemsToDisplay.slice(0, 4).forEach(favItem => {
                const mc = document.createElement('div'); mc.className = 'fav-cell-mini-item';
                const l = document.createElement('a'); l.href = favItem.detailUrl;
                const i_ = document.createElement('img'); i_.src = favItem.imageUrl; i_.alt = favItem.title;
                l.appendChild(i_); mc.appendChild(l); miniGrid.appendChild(mc);
            });
            newContentWrapper = miniGrid;
        } else {
            cellElement.classList.remove('showcase-cell');
            const favItem = itemsToDisplay[0];
            const link = document.createElement('a'); link.href = favItem.detailUrl;
            const img = document.createElement('img'); img.src = favItem.imageUrl; img.alt = favItem.title;
            link.appendChild(img);
            newContentWrapper = link;
        }
        
        // Устанавливаем начальную прозрачность в зависимости от animateAppearance
        newContentWrapper.style.opacity = animateAppearance ? '0' : '1';
        cellElement.appendChild(newContentWrapper);

        if (animateAppearance) {
            await fadeInPromise(newContentWrapper);
        }
    }

    async function setupBigBlockLayout(bbState) {
        const layouts = ['single-item', 'four-cells', 'one-cell-showcasing-four'];
        let newLayout = bbState.currentLayout;
        // Выбираем новый layout, отличный от текущего, если возможно
        if (bbState.currentLayout && layouts.length > 1) { 
            const possibleLayouts = layouts.filter(l => l !== bbState.currentLayout);
            newLayout = possibleLayouts.length > 0 ? possibleLayouts[Math.floor(Math.random() * possibleLayouts.length)] : layouts[Math.floor(Math.random() * layouts.length)];
        } else {
            newLayout = layouts[Math.floor(Math.random() * layouts.length)];
        }

        // Если layout не изменился и блок уже отрисован, ничего не делаем (или можно добавить принудительное обновление)
        if (bbState.currentLayout === newLayout && bbState.cells && bbState.cells.length > 0 && bbState.element.children.length > 0 && !bbState.forceUpdate) {
            return; 
        }
        bbState.forceUpdate = false; // Сбрасываем флаг принудительного обновления
        console.log(`BigBlock ${bigBlocksState.indexOf(bbState)}: Changing layout from ${bbState.currentLayout} to ${newLayout}`);
        
        const oldChildren = Array.from(bbState.element.children);
        const oldLayoutName = bbState.currentLayout;

        // Останавливаем интервалы старых ячеек
        bbState.cells.forEach(cellState => {
            if (cellState.intervalId) clearInterval(cellState.intervalId);
            cellState.intervalId = null;
        });
        
        // 1. Создаем *новые* ячейки для нового layout'а во временном фрагменте
        const newLayoutFragment = document.createDocumentFragment();
        const newCellStates = [];

        if (newLayout === 'single-item') {
            const cellElement = document.createElement('div'); cellElement.className = 'fav-cell';
            newLayoutFragment.appendChild(cellElement);
            const cellState = { element: cellElement, type: 'single_in_cell', favIds: new Set(), intervalId: null };
            newCellStates.push(cellState);
            // Содержимое будет создано с opacity: 1, т.к. animateAppearance = false
            await renderCellContent(cellState, false); 
        } else { // 'four-cells' или 'one-cell-showcasing-four'
            let showcaseCellIndex = (newLayout === 'one-cell-showcasing-four') ? Math.floor(Math.random() * 4) : -1;
            for (let i = 0; i < 4; i++) {
                const cellElement = document.createElement('div'); cellElement.className = 'fav-cell';
                newLayoutFragment.appendChild(cellElement);
                const cellType = (i === showcaseCellIndex) ? 'showcase4' : 'single_in_cell';
                const cellState = { element: cellElement, type: cellType, favIds: new Set(), intervalId: null };
                newCellStates.push(cellState);
                await renderCellContent(cellState, false);
            }
        }
        
        // 2. Создаем временный контейнер для нового layout'а (будет анимироваться его opacity)
        const newLayoutContainer = document.createElement('div');
        newLayoutContainer.style.position = 'absolute';
        newLayoutContainer.style.top = '0';
        newLayoutContainer.style.left = '0';
        newLayoutContainer.style.width = '100%';
        newLayoutContainer.style.height = '100%';
        newLayoutContainer.style.opacity = '0'; // Начинает невидимым
        newLayoutContainer.style.display = 'grid'; // Общее для всех layout'ов контейнера

        if (newLayout === 'single-item') {
            newLayoutContainer.style.gridTemplateColumns = '1fr';
            newLayoutContainer.style.gridTemplateRows = '1fr';
            // No gap for single item
        } else { // 'four-cells' или 'one-cell-showcasing-four'
            newLayoutContainer.style.gridTemplateColumns = 'repeat(2, 1fr)';
            newLayoutContainer.style.gridTemplateRows = 'repeat(2, 1fr)';
            newLayoutContainer.style.gap = '6px'; // Gap для 2x2 layout'ов
        }
        newLayoutContainer.appendChild(newLayoutFragment);
        bbState.element.appendChild(newLayoutContainer);

        // 3. Запускаем анимации одновременно: старые исчезают, новый слой появляется
        // oldChildren находятся в bbState.element, который еще имеет СТАРЫЕ классы layout'а.
        const fadeOutPromises = oldChildren.length > 0 ? oldChildren.map(child => fadeOutPromise(child)) : [Promise.resolve()];
        
        await Promise.all([
            ...fadeOutPromises,
            fadeInPromise(newLayoutContainer) 
        ]);

        // 4. После анимации:
        oldChildren.forEach(child => child.remove()); // Удаляем старые элементы
        
        // Теперь безопасно меняем классы на самом bbState.element для соответствия новому layout'у
        if (newLayout === 'single-item') {
            bbState.element.classList.remove('layout-2x2');
        } else {
            bbState.element.classList.add('layout-2x2');
        }
        bbState.currentLayout = newLayout; // Обновляем текущий layout в состоянии

        // Переносим детей из newLayoutContainer (уже видимого) напрямую в bbState.element
        Array.from(newLayoutContainer.children).forEach(child => bbState.element.appendChild(child));
        newLayoutContainer.remove(); // Удаляем временный слой

        bbState.cells = newCellStates; // Обновляем состояние ячеек на новые

        // 5. Запускаем новые интервалы для обновления контента в ячейках
        bbState.cells.forEach(cellState => {
            const intervalDuration = cellState.type === 'showcase4' ? SHOWCASE_CELL_CONTENT_CHANGE_INTERVAL : CELL_CONTENT_CHANGE_BASE_INTERVAL;
            const randomOffset = Math.random() * 1000 + (bbState.cells.indexOf(cellState) * 200);
            if (cellState.intervalId) clearInterval(cellState.intervalId);
            cellState.intervalId = setInterval(() => renderCellContent(cellState, true), intervalDuration + randomOffset);
        });
        console.log(`BigBlock ${bigBlocksState.indexOf(bbState)}: Layout cross-faded from ${oldLayoutName} to ${newLayout}.`);
    }

    function initializeDynamicGridSystem() {
        if (!dynamicGridContainer) { console.warn("DynamicGrid: Main container .overview-fav-grid-actual missing."); return; }
        console.log("DynamicGrid: Initializing Big Blocks system...");
        stopAllDynamicGridIntervals(); // Остановка предыдущих интервалов
        dynamicGridContainer.innerHTML = ''; 
        currentlyDisplayedFavItemIds.clear();
        bigBlocksState.length = 0; // Очистка состояния старых блоков

        if (!systemDataInitialized) initializeDataSourceOnce();
        if (allPossibleFavItemsData.length === 0) {
            dynamicGridContainer.innerHTML = `<p style="color: #888; text-align: center; width: 100%; padding-top: 50px;">No favorites to display.</p>`;
            globalUpdateActive = false; return;
        }

        for (let i = 0; i < 3; i++) {
            const bbElement = document.createElement('div');
            bbElement.className = 'big-block';
            dynamicGridContainer.appendChild(bbElement);
            const bbState = { 
                element: bbElement, 
                currentLayout: null, 
                cells: [], 
                layoutIntervalId: null,
                forceUpdate: true // Принудительное обновление при первой инициализации
            };
            bigBlocksState.push(bbState);
        }
        
        const initialSetupPromises = bigBlocksState.map(bbState => setupBigBlockLayout(bbState));

        Promise.all(initialSetupPromises).then(() => {
            console.log("All big blocks initially setup and content rendered.");
            bigBlocksState.forEach(bbState => {
                if (bbState.element.parentElement) { // Убедимся, что элемент все еще в DOM
                    bbState.layoutIntervalId = setInterval(() => setupBigBlockLayout(bbState), BIG_BLOCK_LAYOUT_CHANGE_INTERVAL + Math.random() * 1500);
                }
            });
            globalUpdateActive = true;
        }).catch(error => {
            console.error("Error during initial setup of big blocks:", error);
        });
    }
    
    function stopAllDynamicGridIntervals() { 
        console.log("DynamicGrid: Stopping all intervals."); 
        bigBlocksState.forEach(bb => { 
            if (bb.layoutIntervalId) clearInterval(bb.layoutIntervalId); 
            bb.layoutIntervalId = null; 
            bb.cells.forEach(cell => { if(cell.intervalId) clearInterval(cell.intervalId); cell.intervalId = null; }); 
        }); 
        globalUpdateActive = false; 
    }

    const overviewTab = document.getElementById('tab-overview');
    const observerDynamicGridState = () => { 
        const isOverviewTabActive = overviewTab ? overviewTab.classList.contains('active-content') : false; 
        const isFavGridActiveView = favGridContent ? favGridContent.classList.contains(ACTIVE_VIEW_CONTENT_CLASS) : false; 
        if (isOverviewTabActive && isFavGridActiveView) { 
            if (!globalUpdateActive) initializeDynamicGridSystem(); 
        } else { 
            if (globalUpdateActive) stopAllDynamicGridIntervals(); 
        } 
    };
    
    if (favGridContent || favListContent) {
        initializeLegacyFilterControls();
        if (dynamicGridContainer) {
            initializeDataSourceOnce(); 
            const mutationObserver = new MutationObserver(observerDynamicGridState);
            if (overviewTab) mutationObserver.observe(overviewTab, { attributes: true, attributeFilter: ['class'] });
            if (favGridContent) mutationObserver.observe(favGridContent, { attributes: true, attributeFilter: ['class'] });
            
            const profileTabsNav = document.querySelector('.profile-tabs-nav');
            if (profileTabsNav) profileTabsNav.addEventListener('click', () => setTimeout(observerDynamicGridState, 50));
            if (favTabsContainer) favTabsContainer.addEventListener('click', () => setTimeout(observerDynamicGridState, 50));
            
            observerDynamicGridState(); 
        } else { console.log("DynamicGrid: Container .overview-fav-grid-actual not found."); }
    } else { console.log("Profile overview content containers not found."); }
});