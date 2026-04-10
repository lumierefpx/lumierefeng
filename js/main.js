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

// Mark current page as active in nav
const currentPath = window.location.pathname.replace(/\/$/, '') || '/index.html';
document.querySelectorAll('.nav-links a').forEach(a => {
  const href = new URL(a.href, location.href).pathname.replace(/\/$/, '');
  if (href === currentPath || (currentPath === '' && href.endsWith('index.html'))) {
    a.classList.add('active');
  }
});
