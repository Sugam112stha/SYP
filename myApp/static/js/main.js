/* ================================================================
   ALPHA MART NEPAL — main.js
   Runs on every page via base.html
   ================================================================ */

document.addEventListener('DOMContentLoaded', function () {

    // ── AOS (Animate on Scroll) ────────────────────────────────
    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 600, once: true, offset: 60 });
    }

    // ── Preloader ──────────────────────────────────────────────
    window.addEventListener('load', function () {
        const pre = document.getElementById('preloader');
        if (pre) {
            pre.classList.add('fade-out');
            setTimeout(() => pre.remove(), 600);
        }
    });
    // Fallback: remove after 3s no matter what
    setTimeout(() => {
        const pre = document.getElementById('preloader');
        if (pre) pre.remove();
    }, 3000);

    // ── Mobile Menu Toggle ─────────────────────────────────────
    const menuBtn = document.getElementById('mobileMenu');
    const navMenu = document.getElementById('navMenu');
    if (menuBtn && navMenu) {
        menuBtn.addEventListener('click', function () {
            navMenu.classList.toggle('active');
            const icon = menuBtn.querySelector('i');
            icon.classList.toggle('fa-bars');
            icon.classList.toggle('fa-times');
        });
        // Close menu when a link is clicked
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                const icon = menuBtn.querySelector('i');
                icon.classList.add('fa-bars');
                icon.classList.remove('fa-times');
            });
        });
    }

    // ── Search Bar Toggle ──────────────────────────────────────
    const searchToggle = document.getElementById('searchToggle');
    const searchBar    = document.getElementById('searchBar');
    if (searchToggle && searchBar) {
        searchToggle.addEventListener('click', function () {
            searchBar.classList.toggle('active');
            if (searchBar.classList.contains('active')) {
                const input = searchBar.querySelector('input');
                if (input) setTimeout(() => input.focus(), 150);
            }
        });
    }

    // ── Back to Top ────────────────────────────────────────────
    const backBtn = document.getElementById('backToTop');
    if (backBtn) {
        window.addEventListener('scroll', () => {
            backBtn.classList.toggle('show', window.pageYOffset > 300);
        });
        backBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ── Active nav link highlight ──────────────────────────────
    // (Django template blocks handle this, but this is a fallback)
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-menu a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // ── Close dropdown on outside click ───────────────────────
    document.addEventListener('click', function (e) {
        const dropdown = document.querySelector('.user-dropdown');
        if (dropdown && !dropdown.contains(e.target)) {
            const menu = dropdown.querySelector('.dropdown-menu');
            if (menu) menu.style.display = '';
        }
    });

    // ── Quick View buttons → go to product page ────────────────
    document.querySelectorAll('.quick-view').forEach(btn => {
        btn.addEventListener('click', function (e) {
            const href = btn.closest('a')?.href || btn.dataset.href;
            if (href) window.location.href = href;
        });
    });

    // ── Auto-dismiss messages after 4.5s ──────────────────────
    const msgContainer = document.getElementById('messagesContainer');
    if (msgContainer) {
        setTimeout(() => {
            msgContainer.style.transition = 'opacity 0.5s';
            msgContainer.style.opacity = '0';
            setTimeout(() => msgContainer.remove(), 500);
        }, 4000);
    }

});