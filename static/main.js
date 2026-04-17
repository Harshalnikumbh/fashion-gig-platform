/* AtelierX — main.js */

// ---- Navbar scroll effect ----
const navbar = document.querySelector('.navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 20);
  });
}

// ---- Hamburger (mobile) ----
const hamburger = document.getElementById('hamburger');
if (hamburger) {
  hamburger.addEventListener('click', () => {
    const nav = document.querySelector('.nav-links');
    const cta = document.querySelector('.nav-cta');
    if (nav) nav.style.display = nav.style.display === 'flex' ? 'none' : 'flex';
    if (cta) cta.style.display = cta.style.display === 'flex' ? 'none' : 'flex';
  });
}

// ---- Role toggle (sign up page) ----
const roleDescs = {
  learner: 'Access courses, browse gigs & build your fashion career.',
  creator: 'Publish video courses, post gig jobs & grow your design business.'
};

function selectRole(btn, role) {
  document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const roleInput = document.getElementById('roleInput');
  if (roleInput) roleInput.value = role;

  const desc = document.getElementById('roleDesc');
  if (desc) desc.textContent = roleDescs[role] || '';

  // Show/hide creator-only fields
  document.querySelectorAll('.creator-only').forEach(el => {
    el.classList.toggle('hidden', role !== 'creator');
  });
}

// ---- Pre-select role from URL param ----
(function () {
  const params = new URLSearchParams(window.location.search);
  const role = params.get('role');
  if (role === 'creator') {
    const creatorBtn = document.querySelector('[data-role="creator"]');
    if (creatorBtn) selectRole(creatorBtn, 'creator');
  }
})();

// ---- Password toggle ----
function togglePw(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon = document.getElementById(iconId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    if (icon) icon.textContent = '🙈';
  } else {
    input.type = 'password';
    if (icon) icon.textContent = '👁';
  }
}

// ---- Animate hero cards on load ----
window.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.hero-card');
  cards.forEach((c, i) => {
    c.style.opacity = '0';
    c.style.transform = 'translateY(20px)';
    c.style.transition = 'opacity .6s ease, transform .6s ease';
    setTimeout(() => {
      c.style.opacity = '1';
      c.style.transform = 'translateY(0)';
    }, 300 + i * 180);
  });

  // Reveal sections on scroll
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('.course-card, .how-card, .about-pill').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity .6s ease, transform .6s ease';
    observer.observe(el);
  });
});

// ---- Form validation feedback ----
const signupForm = document.getElementById('signupForm');
if (signupForm) {
  signupForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const pw = document.getElementById('pw');
    const pw2 = document.getElementById('pw2');
    if (pw && pw2 && pw.value !== pw2.value) {
      alert('Passwords do not match!');
      pw2.focus();
      return;
    }
    // TODO: wire to Flask backend
    alert('Account created! (Connect to Flask backend to proceed)');
  });
}

const signinForm = document.getElementById('signinForm');
if (signinForm) {
  signinForm.addEventListener('submit', (e) => {
    e.preventDefault();
    // TODO: wire to Flask backend
    alert('Sign in successful! (Connect to Flask backend to proceed)');
  });
}
