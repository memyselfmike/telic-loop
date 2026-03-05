// Scroll-triggered animation system using Intersection Observer

// Initialize all animations when DOM is ready
if (typeof window !== 'undefined') {
  document.addEventListener('DOMContentLoaded', initAnimations);
}

function initAnimations() {
  // Set up Intersection Observer for scroll-triggered animations
  const observerOptions = {
    threshold: 0.1, // Trigger when 10% of element is visible
    rootMargin: '0px 0px -50px 0px', // Start animation slightly before element enters viewport
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animated');

        // Handle staggered animations for children
        if (entry.target.hasAttribute('data-stagger')) {
          staggerChildren(entry.target);
        }

        // Handle counter animations on the element itself
        if (entry.target.hasAttribute('data-counter')) {
          animateCounter(entry.target);
        }

        // Also find and animate any data-counter elements within this element
        const counterChildren = entry.target.querySelectorAll('[data-counter]');
        counterChildren.forEach((counter) => {
          animateCounter(counter);
        });

        // Optionally unobserve after animation (one-time animation)
        // observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Observe all elements with data-animate, data-stagger, or data-counter attributes
  const animatedElements = document.querySelectorAll('[data-animate], [data-stagger], [data-counter]');
  animatedElements.forEach((el) => observer.observe(el));

  // Set up parallax scroll effect
  initParallax();
}

// Stagger animation for child elements
function staggerChildren(parent) {
  const children = Array.from(parent.children);
  const delay = 100; // milliseconds between each child animation

  children.forEach((child, index) => {
    setTimeout(() => {
      child.classList.add('stagger-animated');
    }, index * delay);
  });
}

// Animate number counter from 0 to target value
function animateCounter(element) {
  const target = parseInt(element.getAttribute('data-counter'), 10);
  const duration = 2000; // 2 seconds
  const increment = target / (duration / 16); // 60fps
  let current = 0;

  const updateCounter = () => {
    current += increment;
    if (current < target) {
      element.textContent = Math.floor(current).toLocaleString();
      requestAnimationFrame(updateCounter);
    } else {
      element.textContent = target.toLocaleString();
    }
  };

  updateCounter();
}

// Parallax scroll effect for backgrounds
function initParallax() {
  const parallaxElements = document.querySelectorAll('[data-parallax]');

  if (parallaxElements.length === 0) return;

  window.addEventListener('scroll', () => {
    parallaxElements.forEach((el) => {
      const speed = parseFloat(el.getAttribute('data-parallax')) || 0.5;
      const rect = el.getBoundingClientRect();
      const scrolled = window.pageYOffset;
      const rate = scrolled * speed;

      // Only apply parallax when element is in viewport
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        el.style.transform = `translateY(${rate}px)`;
      }
    });
  });
}

// Export for use in other modules if needed
export { initAnimations, staggerChildren, animateCounter };
