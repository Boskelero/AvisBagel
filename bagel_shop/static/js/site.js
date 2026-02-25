function getCookie(name) {
    const cookieValue = document.cookie
        .split('; ')
        .find((row) => row.startsWith(name + '='));
    if (!cookieValue) {
        return null;
    }
    return decodeURIComponent(cookieValue.split('=')[1]);
}

document.body.addEventListener('htmx:configRequest', function (event) {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
        event.detail.headers['X-CSRFToken'] = csrfToken;
    }
});

function toggleDeliveryFields() {
    const fulfillmentSelect = document.getElementById('id_fulfillment_type');
    const deliveryFields = document.querySelector('.delivery-fields');
    const pickupField = document.querySelector('.pickup-field');
    if (!fulfillmentSelect || !deliveryFields || !pickupField) {
        return;
    }

    if (fulfillmentSelect.value === 'delivery') {
        deliveryFields.style.display = 'block';
        pickupField.style.display = 'none';
    } else {
        deliveryFields.style.display = 'none';
        pickupField.style.display = 'block';
    }
}

function initHeroRotators() {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const rotators = document.querySelectorAll('[data-hero-rotator]');

    rotators.forEach((rotator) => {
        const slides = Array.from(rotator.querySelectorAll('.hero-slide'));
        const dots = Array.from(rotator.querySelectorAll('[data-hero-dot]'));
        if (slides.length < 2) {
            return;
        }

        let currentIndex = slides.findIndex((slide) => slide.classList.contains('is-active'));
        if (currentIndex < 0) {
            currentIndex = 0;
            slides[0].classList.add('is-active');
        }

        const intervalMs = parseInt(rotator.dataset.interval || '5600', 10);
        let timerId = null;

        function paint(index) {
            slides.forEach((slide, slideIndex) => {
                slide.classList.toggle('is-active', slideIndex === index);
            });
            dots.forEach((dot, dotIndex) => {
                dot.classList.toggle('is-active', dotIndex === index);
            });
            currentIndex = index;
        }

        function nextSlide() {
            const nextIndex = (currentIndex + 1) % slides.length;
            paint(nextIndex);
        }

        function startRotation() {
            if (prefersReducedMotion) {
                return;
            }
            stopRotation();
            timerId = window.setInterval(nextSlide, intervalMs);
        }

        function stopRotation() {
            if (timerId) {
                window.clearInterval(timerId);
                timerId = null;
            }
        }

        dots.forEach((dot) => {
            dot.addEventListener('click', function () {
                const dotIndex = parseInt(this.dataset.heroDot || '0', 10);
                paint(dotIndex);
                startRotation();
            });
        });

        rotator.addEventListener('mouseenter', stopRotation);
        rotator.addEventListener('mouseleave', startRotation);

        paint(currentIndex);
        startRotation();
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const fulfillmentSelect = document.getElementById('id_fulfillment_type');
    if (fulfillmentSelect) {
        toggleDeliveryFields();
        fulfillmentSelect.addEventListener('change', toggleDeliveryFields);
    }

    initHeroRotators();
});
