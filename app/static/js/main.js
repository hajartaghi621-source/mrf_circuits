/**
 * MRF Circuits — Main JavaScript
 * Handles: language selector, cart counter, nav interactions, toasts
 */

// ===== LANGUAGE SELECTOR =====
const langToggle = document.getElementById('lang-toggle');
const langDropdown = document.getElementById('lang-dropdown');

if (langToggle && langDropdown) {
  langToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    langDropdown.classList.toggle('hidden');
  });
  document.addEventListener('click', () => langDropdown.classList.add('hidden'));
}

// ===== CART COUNTER (fetch on load) =====
async function updateCartCount() {
  try {
    const res = await fetch('/cart/count');
    if (res.ok) {
      const data = await res.json();
      const counter = document.getElementById('cart-count');
      if (counter) {
        if (data.count > 0) {
          counter.textContent = data.count;
          counter.classList.remove('hidden');
        } else {
          counter.classList.add('hidden');
        }
      }
    }
  } catch (e) {
    // Not logged in or endpoint not available
  }
}
updateCartCount();

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'success') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.add('show');
  });

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ===== SLUG GENERATOR (for admin forms) =====
function generateSlug(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim();
}

// Auto-generate slug from product name in admin forms
const nameInput = document.getElementById('admin-product-name');
const slugInput = document.getElementById('admin-product-slug');
if (nameInput && slugInput && !slugInput.value) {
  nameInput.addEventListener('input', () => {
    slugInput.value = generateSlug(nameInput.value);
  });
}

// ===== SMOOTH SCROLL =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', (e) => {
    const target = document.querySelector(anchor.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// ===== ANIMATE ON SCROLL =====
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('animate-fade-in');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.card-hover, .stat-card').forEach(el => {
  observer.observe(el);
});

// ===== CONFIRM DELETE =====
document.querySelectorAll('[data-confirm]').forEach(btn => {
  btn.addEventListener('click', (e) => {
    if (!confirm(btn.dataset.confirm)) {
      e.preventDefault();
    }
  });
});
