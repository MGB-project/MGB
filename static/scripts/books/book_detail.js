document.addEventListener('DOMContentLoaded', () => {
    const detailsBlock = document.getElementById('detailsBlock');
    const toggleButton = document.getElementById('toggleDetailsBtn');
    const detailsHeader = detailsBlock.querySelector('.details-header'); // Получаем шапку
    const content = document.getElementById('detailsContent');

    // Функция для переключения состояния
    const toggleDetails = () => {
        const isCollapsed = detailsBlock.classList.contains('collapsed');

        if (isCollapsed) {
            // Разворачиваем
            detailsBlock.classList.remove('collapsed');
            toggleButton.setAttribute('aria-expanded', 'true');
        } else {
            // Сворачиваем
            detailsBlock.classList.add('collapsed');
            toggleButton.setAttribute('aria-expanded', 'false');
        }
    };

    // Добавляем обработчик клика на кнопку
    toggleButton.addEventListener('click', (event) => {
        event.stopPropagation(); // Остановить всплытие, если клик был именно по кнопке
        toggleDetails();
    });

    // Добавляем обработчик клика на всю шапку (опционально)
    // Если хочешь, чтобы блок открывался/закрывался по клику на всю шапку, а не только на кнопку
    detailsHeader.addEventListener('click', toggleDetails);

    // Начальное состояние: по умолчанию блок раскрыт (нет класса 'collapsed' в HTML)
    // Если хочешь, чтобы блок был изначально свернут, добавь класс "collapsed"
    // к <div class="details-block"> в HTML и установи aria-expanded="false" у кнопки.
});

document.addEventListener('DOMContentLoaded', () => {
    const statsBlock = document.getElementById('statsBlock');
    const toggleButtonStats = document.getElementById('toggleStatsBtn');
    const detailsHeader = statsBlock.querySelector('.stats-header'); // Получаем шапку
    const content = document.getElementById('statsContent');

    // Функция для переключения состояния
    const toggleDetails = () => {
        const isCollapsed = statsBlock.classList.contains('collapsed');

        if (isCollapsed) {
            // Разворачиваем
            statsBlock.classList.remove('collapsed');
            toggleButtonStats.setAttribute('aria-expanded', 'true');
        } else {
            // Сворачиваем
            statsBlock.classList.add('collapsed');
            toggleButtonStats.setAttribute('aria-expanded', 'false');
        }
    };

    // Добавляем обработчик клика на кнопку
    toggleButtonStats.addEventListener('click', (event) => {
        event.stopPropagation(); // Остановить всплытие, если клик был именно по кнопке
        toggleDetails();
    });

    // Добавляем обработчик клика на всю шапку (опционально)
    // Если хочешь, чтобы блок открывался/закрывался по клику на всю шапку, а не только на кнопку
    detailsHeader.addEventListener('click', toggleDetails);

    // Начальное состояние: по умолчанию блок раскрыт (нет класса 'collapsed' в HTML)
    // Если хочешь, чтобы блок был изначально свернут, добавь класс "collapsed"
    // к <div class="details-block"> в HTML и установи aria-expanded="false" у кнопки.
});