document.addEventListener('DOMContentLoaded', function () {
  const reviewsListContainer = document.getElementById('reviews-list-container');
  if (!reviewsListContainer) return; // Only run if on profile page with reviews tab

  // Filter Dropdown
  const filterToggle = document.getElementById('review-filter-toggle');
  const filterOptionsList = document.getElementById('review-filter-options-list');
  const selectedFilterSpan = document.getElementById('selected-review-filter');

  // Sort Dropdown
  const sortToggle = document.getElementById('review-sort-toggle');
  const sortOptionsList = document.getElementById('review-sort-options-list');
  const selectedSortSpan = document.getElementById('selected-review-sort');

  // Search
  const searchInput = document.getElementById('review-search-input');
  const searchButton = document.getElementById('review-search-button');

  let currentReviewFilter = 'all';
  let currentReviewSort = 'date_added';
  let currentReviewSearch = '';

  // Initialize from current HTML state (set by Django context)
  if (filterToggle && filterOptionsList) {
      const activeFilter = filterOptionsList.querySelector('li.active');
      if (activeFilter) {
          currentReviewFilter = activeFilter.dataset.value;
      }
  }
  if (sortToggle && sortOptionsList) {
      const activeSort = sortOptionsList.querySelector('li.active');
      if (activeSort) {
          currentReviewSort = activeSort.dataset.value;
      }
  }
  if (searchInput) {
      currentReviewSearch = searchInput.value.trim();
  }


  function setupDropdown(toggleButton, optionsList, selectedSpan, updateVariableCallback) {
      if (!toggleButton || !optionsList || !selectedSpan) return;

      toggleButton.addEventListener('click', (e) => {
          e.stopPropagation();
          const isExpanded = toggleButton.getAttribute('aria-expanded') === 'true';
          toggleButton.setAttribute('aria-expanded', String(!isExpanded));
          optionsList.style.display = isExpanded ? 'none' : 'block';
      });

      optionsList.addEventListener('click', (e) => {
          if (e.target.tagName === 'LI') {
              const value = e.target.dataset.value;
              selectedSpan.textContent = e.target.textContent.trim();
              
              optionsList.querySelectorAll('li').forEach(li => li.classList.remove('active'));
              e.target.classList.add('active');
              
              toggleButton.setAttribute('aria-expanded', 'false');
              optionsList.style.display = 'none';
              
              updateVariableCallback(value); // Update current filter/sort variable
              fetchReviews(); // Then fetch
          }
      });
  }
  
  setupDropdown(filterToggle, filterOptionsList, selectedFilterSpan, (value) => currentReviewFilter = value);
  setupDropdown(sortToggle, sortOptionsList, selectedSortSpan, (value) => currentReviewSort = value);

  // Close dropdowns if clicked outside
  document.addEventListener('click', (event) => {
      if (filterToggle && filterOptionsList && !filterToggle.contains(event.target) && !filterOptionsList.contains(event.target)) {
          filterToggle.setAttribute('aria-expanded', 'false');
          filterOptionsList.style.display = 'none';
      }
      if (sortToggle && sortOptionsList && !sortToggle.contains(event.target) && !sortOptionsList.contains(event.target)) {
          sortToggle.setAttribute('aria-expanded', 'false');
          sortOptionsList.style.display = 'none';
      }
  });

  if (searchButton && searchInput) {
      searchButton.addEventListener('click', () => {
          currentReviewSearch = searchInput.value.trim();
          fetchReviews();
      });
      searchInput.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
              e.preventDefault(); // Prevent form submission if it's in a form
              currentReviewSearch = searchInput.value.trim();
              fetchReviews();
          }
      });
  }

  async function fetchReviews() {
      reviewsListContainer.innerHTML = '<p class="loading-reviews">Loading reviews...</p>'; // Loading state

      const params = new URLSearchParams();
      params.append('fetch_reviews', 'true'); // Important: tells the view this is an AJAX review fetch
      params.append('review_filter', currentReviewFilter);
      params.append('review_sort', currentReviewSort);
      if (currentReviewSearch) {
          params.append('review_search', currentReviewSearch);
      }

      try {
          // Use current page URL for the fetch, Django view will handle params
          const response = await fetch(`${window.location.pathname}?${params.toString()}`, {
              method: 'GET',
              headers: {
                  'X-Requested-With': 'XMLHttpRequest'
              }
          });
          if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
          }
          const data = await response.json();
          if (data.html_reviews) {
              reviewsListContainer.innerHTML = data.html_reviews;
          } else {
              reviewsListContainer.innerHTML = '<p class="no-reviews-message">No reviews found or error loading.</p>';
          }
      } catch (error) {
          console.error('Error fetching reviews:', error);
          reviewsListContainer.innerHTML = '<p class="error-reviews-message">Error loading reviews. Please try again.</p>';
      }
  }
});