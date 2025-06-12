// search_handler.js
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.querySelector('input#searchInput');
    const resultsDisplayContainer = document.querySelector('.search-results');
    const searchResultsContainer = document.querySelector('.search-results-container');
    const categoryButtons = document.querySelectorAll('.search-buttons .search-button');
    const categoryButtonsContainer = document.querySelector('.search-buttons');

    let currentCategory = 'all';
    let fetchTimeout;
    const MIN_QUERY_LENGTH = 2; // Минимальная длина запроса для показа результатов

    if (!searchInput || !resultsDisplayContainer || !searchResultsContainer || !categoryButtonsContainer || categoryButtons.length === 0) {
        // console.warn("One or more search elements are missing. Search functionality may be impaired.");
        return;
    }

    function showSearchResults() {
        if (searchResultsContainer) searchResultsContainer.classList.add('visible');
    }

    function hideSearchResults() {
        if (searchResultsContainer) searchResultsContainer.classList.remove('visible');
    }

    async function performSearch(query) {
        // Проверка длины запроса здесь уже не так важна, т.к. она будет в слушателе input
        // Но на всякий случай оставим, если performSearch вызовется откуда-то еще
        if (query.length < MIN_QUERY_LENGTH) {
            resultsDisplayContainer.innerHTML = '';
            // Не скрываем здесь, если хотим оставить кнопки категорий видимыми, если уже было > MIN_QUERY_LENGTH
            // hideSearchResults(); 
            return;
        }

        // Показываем контейнер, так как мы уже знаем, что query >= MIN_QUERY_LENGTH
        showSearchResults(); 

        try {
            const response = await fetch(`/search/?q=${encodeURIComponent(query)}&category=${currentCategory}`);
            const data = await response.json();

            resultsDisplayContainer.innerHTML = '';
            let contentRendered = false;

            const renderSection = (items, type, idsSet, title, iconSrc, itemRenderer) => {
                if (items && items.length > 0) {
                    if (contentRendered) {
                        const separator = document.createElement('div');
                        separator.classList.add('category-separator');
                        resultsDisplayContainer.appendChild(separator);
                    }
                    const sectionContainer = document.createElement('div');
                    sectionContainer.classList.add(`${type}-container-search`);
                    const header = document.createElement('div');
                    header.classList.add('category-header');
                    header.innerHTML = `<img src="${iconSrc}" class="category-icon"><h2>${title}</h2>`;
                    sectionContainer.appendChild(header);
                    items.forEach(item => {
                        if (!idsSet.has(item.id)) {
                            idsSet.add(item.id);
                            sectionContainer.appendChild(itemRenderer(item));
                        }
                    });
                    resultsDisplayContainer.appendChild(sectionContainer);
                    contentRendered = true;
                    return true;
                }
                return false;
            };

            // ... (функции movieItemRenderer, gameItemRenderer, bookItemRenderer остаются без изменений)
            const movieItemRenderer = (movie) => {
                const el = document.createElement('div');
                const releaseYear = movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A';
                
                 // ---  ЖАНРЫ ---
                let genresHtml = '';
                if (movie.genres && Array.isArray(movie.genres) && movie.genres.length > 0) {
                    // Берем последние 2 жанра. Если жанров меньше 2, slice вернет все, что есть.
                    const lastTwoGenres = movie.genres.slice(-2); 
                    genresHtml = lastTwoGenres.map(genre => {
                        // Если genre - это объект (например, {id: 1, name: "Action"}), берем genre.name
                        // Если genre - это просто строка, берем саму строку
                        const genreName = typeof genre === 'object' && genre.name ? genre.name : genre;
                        return `<span class="movie-genre-search">${genreName}</span>`;
                    }).join(', '); // Разделяем запятой и пробелом (nbsp для неразрывного пробела)
                }
                // --- КОНЕЦ ЛОГИКИ ДЛЯ ЖАНРОВ ---
                el.classList.add('search-result-item');
                el.innerHTML = `
                    <img src="${movie.poster_path || '/static/imgs/placeholder_poster.png'}" alt="${movie.title}" class="search-cover">
                    <div class="search-movie-info">
                        <h1 class="search-movie-name">${movie.title}</h1>
                        <div class="item-info-detail">
                            <span class="search-movie-rating" style="background-color:${movie.rating_color || '#777'};">
                                ${movie.vote_average ? movie.vote_average.toFixed(1) : '?'}
                            </span>
                            ${genresHtml ? `<div class="movie-genre-block">${genresHtml}</div>` : ''}
                            <span class="date-block-search">${releaseYear}</span>
                        </div>
                    </div>`;
                el.addEventListener('click', () => { window.location.href = `/movies/${movie.id}/`; });
                return el;
            };

            const gameItemRenderer = (game) => {
                const el = document.createElement('div');
                const genresHtml = game.genres && game.genres.length > 0 ? game.genres.slice(0, 2).map(genre => `<span class="game-genre-search">${genre}</span>`).join(', ') : '';
                const releaseYear = game.first_release_date || 'N/A';
                el.classList.add('search-result-item');
                el.innerHTML = `
                    <img src="${game.cover_url || '/static/imgs/placeholder_cover.png'}" alt="${game.name}" class="search-cover">
                    <div class="search-game-info">
                        <h1 class="search-game-name">${game.name}</h1>
                        <div class="item-info-detail">
                            <span class="search-game-rating" style="background-color:${game.rating_color || '#777'};">
                                ${game.total_rating || '?'}
                            </span>
                            ${genresHtml ? `<div class="game-genre-block">${genresHtml}</div>` : ''}
                            <span class="date-block-search">${releaseYear}</span>
                        </div>
                    </div>`;
                el.addEventListener('click', () => { window.location.href = `/games/${game.id}/`; });
                return el;
            };
            
            // search_handler.js (фрагмент)

            const bookItemRenderer = (book) => {
                const el = document.createElement('div');
                const publishedDate = book.published_date || 'N/A';

                // --- ЛОГИКА ДЛЯ АВТОРОВ КНИГИ ---
                let authorsHtml = '';
                // Предполагаем, что book.authors - это массив строк (имен авторов)
                if (book.authors && Array.isArray(book.authors) && book.authors.length > 0) {
                    // Возьмем первого автора или первых двух, если их много
                    const authorsToShow = book.authors.slice(0, 2); // Показать до 2 авторов
                    authorsHtml = authorsToShow.map(author => 
                        `<span class="book-author-search">${author}</span>`
                    ).join(', '); // Разделяем запятой и пробелом
                }
                // --- КОНЕЦ ЛОГИКИ ДЛЯ АВТОРОВ ---

                el.classList.add('search-result-item');
                el.innerHTML = `
                    <img src="${book.thumbnail || '/static/imgs/placeholder_thumbnail.png'}" alt="${book.title}" class="search-cover">
                    <div class="search-book-info">
                        <h1 class="search-book-name">${book.title}</h1>
                        <div class="item-info-detail">
                            <span class="search-book-rating" style="background-color:${book.rating_color || '#777'};">
                                ${book.mgb_average_rating || '?'} 
                            </span>
                            ${authorsHtml ? `<div class="book-authors-block">${authorsHtml}</div>` : ''}
                            <span class="date-block-search">${publishedDate}</span>
                        </div>
                    </div>`;
                
                const bookIdForDetailUrl = book.google_id; 
                            
                if (bookIdForDetailUrl) { 
                    el.addEventListener('click', () => { 
                        window.location.href = `/books/${encodeURIComponent(bookIdForDetailUrl)}/`; 
                    });
                } else {
                    console.warn("Book google_id is undefined for book:", book.title, book); 
                }
                return el;
            };


            const movieIds = new Set();
            const gameIds = new Set();
            const bookIds = new Set();

            let moviesRendered = false;
            let gamesRendered = false;
            let booksRendered = false;

            if (currentCategory === 'all' || currentCategory === 'movies') {
                moviesRendered = renderSection(data.movies, 'movies', movieIds, 'Movies', '/static/imgs/seacrh_icons/search_movies.svg', movieItemRenderer);
            }
            if (currentCategory === 'all' || currentCategory === 'games') {
                gamesRendered = renderSection(data.games, 'games', gameIds, 'Games', '/static/imgs/seacrh_icons/search_games.svg', gameItemRenderer);
            }
            if (currentCategory === 'all' || currentCategory === 'books') {
                booksRendered = renderSection(data.books, 'books', bookIds, 'Books', '/static/imgs/seacrh_icons/search_books.svg', bookItemRenderer);
            }

            if (!moviesRendered && !gamesRendered && !booksRendered) {
                resultsDisplayContainer.innerHTML = '<p class="no-results">No results found.</p>';
            }

        } catch (error) {
            console.error('Error fetching search results:', error);
            resultsDisplayContainer.innerHTML = '<p class="no-results">Error loading results.</p>';
        }
    }

    searchInput.addEventListener('input', (event) => {
        const query = event.target.value.trim();
        clearTimeout(fetchTimeout);

        // --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        if (query.length >= MIN_QUERY_LENGTH) {
            fetchTimeout = setTimeout(() => {
                performSearch(query); // performSearch сам вызовет showSearchResults()
            }, 300);
        } else {
            resultsDisplayContainer.innerHTML = ''; // Очищаем предыдущие результаты
            hideSearchResults(); // Скрываем контейнер, если символов меньше MIN_QUERY_LENGTH
        }
        // --- КОНЕЦ ИЗМЕНЕНИЯ ---
    });

    categoryButtons.forEach(button => {
        button.addEventListener('click', () => {
            categoryButtons.forEach(btn => {
                btn.classList.remove('active');
                const icon = btn.querySelector('.category-icon');
                if (icon && icon.dataset.defaultIcon) {
                    icon.src = icon.dataset.defaultIcon;
                }
            });

            button.classList.add('active');
            const activeIcon = button.querySelector('.category-icon');
            if (activeIcon && activeIcon.dataset.activeIcon) {
                activeIcon.src = activeIcon.dataset.activeIcon;
            }

            currentCategory = button.getAttribute('data-category');
            const currentQuery = searchInput.value.trim();
            
            // --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
            if (currentQuery.length >= MIN_QUERY_LENGTH) {
                performSearch(currentQuery); // Выполняем поиск с новой категорией
            } else {
                if(searchResultsContainer.classList.contains('visible')){
                    resultsDisplayContainer.innerHTML = ''; // Очищаем, если блок уже был виден
                }

            }
            // --- КОНЕЦ ИЗМЕНЕНИЯ ---
        });
    });

    document.addEventListener('click', function (event) {
        if (searchResultsContainer && searchResultsContainer.classList.contains('visible') &&
            !searchResultsContainer.contains(event.target) &&
            !searchInput.contains(event.target)
            ) {
            hideSearchResults();
        }
    });

    searchInput.addEventListener('focus', () => {
        const currentQuery = searchInput.value.trim();
        // --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        if (currentQuery.length >= MIN_QUERY_LENGTH) { // Показываем только если длина запроса достаточна
            if (resultsDisplayContainer.children.length > 0) { // Если уже есть результаты
                showSearchResults();
            } else {
                performSearch(currentQuery); // Или выполняем поиск, если результатов еще нет
            }
        } else if (currentQuery.length > 0 && currentQuery.length < MIN_QUERY_LENGTH) {
            // Если есть какой-то текст, но меньше MIN_QUERY_LENGTH,
            // можно показать контейнер с кнопками категорий, но без результатов
            showSearchResults();
            resultsDisplayContainer.innerHTML = '<p class="no-results">Enter at least ' + MIN_QUERY_LENGTH + ' characters.</p>'; // или пусто
        }
        // Если поле совсем пустое при фокусе, ничего не делаем (или можно показать кнопки, если это UX требование)
        // else { hideSearchResults(); } // если нужно скрывать, если пусто
        // --- КОНЕЦ ИЗМЕНЕНИЯ ---
    });
});