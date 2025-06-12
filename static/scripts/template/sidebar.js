// template.js
document.addEventListener('DOMContentLoaded', function() {
  const headerSidebarToggleButton = document.querySelector('.sidebar-toggle'); // Кнопка в header-bottom
  const fullSidebarToggleButton = document.querySelector('.sidebar-full-toggle'); // Кнопка в sidebar-full-header
  const body = document.body;

  function toggleSidebar() {
      body.classList.toggle('sidebar-open');
      
      // Обновляем ARIA атрибут для доступности кнопки в хедере
      // (кнопка в полной шторке видна только когда шторка открыта, ее aria-expanded всегда true когда видна)
      if (headerSidebarToggleButton) {
           const isSidebarOpen = body.classList.contains('sidebar-open');
           headerSidebarToggleButton.setAttribute('aria-expanded', isSidebarOpen);
      }
  }

  if (headerSidebarToggleButton) {
      headerSidebarToggleButton.addEventListener('click', toggleSidebar);
      // Установка начального состояния ARIA для кнопки в хедере
      const initialSidebarOpen = body.classList.contains('sidebar-open');
      headerSidebarToggleButton.setAttribute('aria-expanded', initialSidebarOpen);
  }

  if (fullSidebarToggleButton) {
      fullSidebarToggleButton.addEventListener('click', toggleSidebar);
  }
});