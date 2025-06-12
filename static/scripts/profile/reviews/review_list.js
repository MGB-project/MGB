document.addEventListener('click', function(event) {
  if (event.target.classList.contains('read-more-review-link')) {
      event.preventDefault();
      const reviewId = event.target.dataset.reviewId;
      event.target.closest('.review-text-snippet').style.display = 'none';
      const fullTextEl = document.querySelector(`.full-review-text[data-review-id="${reviewId}"]`);
      if (fullTextEl) fullTextEl.style.display = 'block';
  }
  if (event.target.classList.contains('read-less-review-link')) {
      event.preventDefault();
      const reviewId = event.target.dataset.reviewId;
      event.target.closest('.full-review-text').style.display = 'none';
      const snippetEl = document.querySelector(`.review-text-snippet a[data-review-id="${reviewId}"]`);
      if (snippetEl) snippetEl.closest('.review-text-snippet').style.display = 'block';
  }
});