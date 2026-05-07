// Mobile nav toggle
const toggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('.nav-links');

if (toggle && navLinks) {
  toggle.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
  });
  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!toggle.contains(e.target) && !navLinks.contains(e.target)) {
      navLinks.classList.remove('open');
    }
  });
}

// Blog search
const searchInput = document.getElementById('blog-search');
if (searchInput) {
  const feedItems = document.querySelectorAll('.feed-item');
  const featuredPost = document.getElementById('featured-post');
  const yearGroups = document.querySelectorAll('.year-group');
  const noResults = document.getElementById('search-no-results');

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    let visible = 0;

    // Filter featured post
    if (featuredPost) {
      const title = (featuredPost.dataset.searchTitle || '').toLowerCase();
      const excerpt = (featuredPost.dataset.searchExcerpt || '').toLowerCase();
      const match = !q || title.includes(q) || excerpt.includes(q);
      featuredPost.style.display = match ? '' : 'none';
      if (match) visible++;
    }

    // Filter feed items
    feedItems.forEach(item => {
      const title = item.querySelector('.feed-title')?.textContent.toLowerCase() || '';
      const excerpt = item.querySelector('.feed-excerpt')?.textContent.toLowerCase() || '';
      const match = !q || title.includes(q) || excerpt.includes(q);
      item.style.display = match ? '' : 'none';
      if (match) visible++;
    });

    // Hide year dividers when no visible items remain in that group
    yearGroups.forEach(group => {
      const hasVisible = [...group.querySelectorAll('.feed-item')].some(i => i.style.display !== 'none');
      const divider = group.querySelector('.year-divider');
      if (divider) divider.style.display = hasVisible ? '' : 'none';
    });

    if (noResults) noResults.style.display = visible === 0 ? '' : 'none';
  });
}

// Mark current page as active in nav
const currentPath = window.location.pathname.replace(/\/$/, '') || '/index.html';
document.querySelectorAll('.nav-links a').forEach(a => {
  const href = new URL(a.href, location.href).pathname.replace(/\/$/, '');
  if (href === currentPath || (currentPath === '' && href.endsWith('index.html'))) {
    a.classList.add('active');
  }
});

// Writings QR popover
const qrTriggers = document.querySelectorAll('[data-qr-src]');
if (qrTriggers.length) {
  const modal = document.createElement('div');
  modal.className = 'qr-modal';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.innerHTML = `
    <div class="qr-modal-panel">
      <button class="qr-modal-close" type="button" aria-label="Close">×</button>
      <img alt="">
    </div>
  `;
  document.body.appendChild(modal);

  const img = modal.querySelector('img');
  const close = modal.querySelector('.qr-modal-close');
  const closeModal = () => {
    modal.classList.remove('open');
    img.removeAttribute('src');
    document.body.style.overflow = '';
  };

  qrTriggers.forEach(trigger => {
    trigger.addEventListener('click', () => {
      img.src = trigger.dataset.qrSrc;
      img.alt = trigger.dataset.qrTitle || 'QR code';
      modal.classList.add('open');
      document.body.style.overflow = 'hidden';
    });
  });

  close.addEventListener('click', closeModal);
  modal.addEventListener('click', event => {
    if (event.target === modal) closeModal();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && modal.classList.contains('open')) closeModal();
  });
}
