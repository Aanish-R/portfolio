// Theme Toggle
const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

// Check for saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    body.classList.toggle('dark-mode', savedTheme === 'dark');
}

themeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-mode');
    localStorage.setItem('theme', body.classList.contains('dark-mode') ? 'dark' : 'light');
    lucide.createIcons(); // Re-create icons on theme change if needed
});

// Mobile Menu Toggle
const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
const navLinksEl = document.querySelector('.nav-links');

// Create overlay element for mobile menu
const mobileOverlay = document.createElement('div');
mobileOverlay.className = 'mobile-overlay';
document.body.appendChild(mobileOverlay);

function toggleMobileMenu() {
    const isOpen = navLinksEl.classList.toggle('mobile-open');
    mobileMenuToggle.classList.toggle('active');
    mobileMenuToggle.setAttribute('aria-expanded', isOpen);
    mobileOverlay.classList.toggle('active');

    // Prevent body scroll when menu is open
    document.body.style.overflow = isOpen ? 'hidden' : '';
}

function closeMobileMenu() {
    navLinksEl.classList.remove('mobile-open');
    mobileMenuToggle.classList.remove('active');
    mobileMenuToggle.setAttribute('aria-expanded', 'false');
    mobileOverlay.classList.remove('active');
    document.body.style.overflow = '';
}

mobileMenuToggle.addEventListener('click', toggleMobileMenu);
mobileOverlay.addEventListener('click', closeMobileMenu);

// Close mobile menu when clicking nav links
navLinksEl.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', closeMobileMenu);
});

// Close mobile menu on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && navLinksEl.classList.contains('mobile-open')) {
        closeMobileMenu();
    }
});

// Initialize Icons
lucide.createIcons();

// Navbar and Back to Top Scroll Effect
const navbar = document.getElementById('navbar');
const backToTop = document.getElementById('back-to-top');

window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }

    if (window.scrollY > 500) {
        backToTop.classList.add('visible');
    } else {
        backToTop.classList.remove('visible');
    }
});

// Reveal Animations on Scroll
const revealElements = document.querySelectorAll('.reveal');
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('active');
            revealObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

revealElements.forEach(el => revealObserver.observe(el));

// Active Nav Link on Scroll
const sections = document.querySelectorAll('section, header');
const navLinks = document.querySelectorAll('.nav-links a');

window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (window.scrollY >= sectionTop - 100) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').includes(current)) {
            link.classList.add('active');
        }
    });
});

// Cursor Glow Effect
const cursorGlow = document.querySelector('.cursor-glow');
document.addEventListener('mousemove', (e) => {
    cursorGlow.style.left = e.clientX + 'px';
    cursorGlow.style.top = e.clientY + 'px';
});

// Form Submission with Formspree (Improved with Feedback)
const contactForm = document.getElementById('contact-form');
const formStatus = document.getElementById('form-status');

if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
        // e.preventDefault(); // Temporarily disabled to force activation page
        const btn = document.getElementById('submit-btn');
        const data = new FormData(contactForm);

        // Visual loading state
        btn.textContent = 'Sending...';
        btn.disabled = true;
        formStatus.style.display = 'none';

        try {
            const response = await fetch(contactForm.action, {
                method: contactForm.method,
                body: data,
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (response.ok) {
                // Success
                formStatus.textContent = "Thanks! Your message has been sent successfully.";
                formStatus.style.backgroundColor = "rgba(16, 185, 129, 0.2)"; // Emerald semi-transparent
                formStatus.style.color = "#10b981";
                formStatus.style.display = 'block';
                contactForm.reset();
            } else {
                // Server error
                const errorData = await response.json();
                throw new Error(errorData.errors ? errorData.errors[0].message : "Submission failed");
            }
        } catch (error) {
            // General error
            console.error('Form submission error:', error);
            formStatus.textContent = error.message.includes("Submission failed")
                ? "Oops! Submission failed. Please try again or use direct email."
                : "Oops! " + error.message;
            formStatus.style.backgroundColor = "rgba(244, 63, 94, 0.2)"; // Rose semi-transparent
            formStatus.style.color = "#f43f5e";
            formStatus.style.display = 'block';
        } finally {
            btn.textContent = 'Send Message';
            btn.disabled = false;
        }
    });
}


// Certificate Modal Functions
function openCertificate(pdfPath) {
    const modal = document.getElementById('certificateModal');
    const viewer = document.getElementById('certificateViewer');
    viewer.src = pdfPath;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = document.getElementById('certificateModal');
    const viewer = document.getElementById('certificateViewer');
    modal.classList.remove('active');
    viewer.src = '';
    document.body.style.overflow = 'auto';
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('certificateModal');
    if (e.target === modal) {
        closeModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});


// Auto-hide Navigation Dock (Desktop only)
let mouseTimer = null;

// Check if we're on desktop
function isDesktop() {
    return window.innerWidth > 768;
}

document.addEventListener('mousemove', (e) => {
    if (!isDesktop()) return; // Skip on mobile

    // Show nav when cursor is within 50px of left edge
    if (e.clientX <= 50) {
        navLinksEl.classList.add('show');

        // Clear any existing timer
        if (mouseTimer) {
            clearTimeout(mouseTimer);
        }
    } else if (e.clientX > 250) {
        // Hide nav when cursor moves away (unless hovering over nav)
        mouseTimer = setTimeout(() => {
            if (!navLinksEl.matches(':hover')) {
                navLinksEl.classList.remove('show');
            }
        }, 300);
    }
});

// Keep nav visible while hovering (desktop only)
navLinksEl.addEventListener('mouseenter', () => {
    if (!isDesktop()) return;
    navLinksEl.classList.add('show');
    if (mouseTimer) {
        clearTimeout(mouseTimer);
    }
});

// Hide nav when mouse leaves (with delay, desktop only)
navLinksEl.addEventListener('mouseleave', () => {
    if (!isDesktop()) return;
    mouseTimer = setTimeout(() => {
        navLinksEl.classList.remove('show');
    }, 500);
});
