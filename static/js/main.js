// ============================================================
// main.js — General UI JavaScript
// Handles: navbar scroll, scroll animations, etc.
// ============================================================

// ---- Navbar changes on scroll ----
window.addEventListener('scroll', function () {
    const navbar = document.querySelector('.glass-nav');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
});

// ---- Animate elements when they come into view ----
// (Simple version without external library)
const animateOnScroll = function () {
    const elements = document.querySelectorAll('[data-aos]');
    elements.forEach(function (el) {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight - 50) {
            el.style.opacity    = '1';
            el.style.transform  = 'translateY(0)';
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        }
    });
};

// Initial setup: make all AOS elements invisible
document.querySelectorAll('[data-aos]').forEach(function (el) {
    el.style.opacity   = '0';
    el.style.transform = 'translateY(20px)';
});

window.addEventListener('scroll', animateOnScroll);
window.addEventListener('load', animateOnScroll);
