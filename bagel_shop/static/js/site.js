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

function initDropCountdowns() {
    document.querySelectorAll('[data-drop-countdown]').forEach((element) => {
        const target = new Date(element.dataset.target).getTime();
        function update() {
            const remaining = Math.max(0, target - Date.now());
            const days = Math.floor(remaining / 86400000);
            const hours = Math.floor((remaining % 86400000) / 3600000);
            const minutes = Math.floor((remaining % 3600000) / 60000);
            const seconds = Math.floor((remaining % 60000) / 1000);
            element.textContent = `${days ? days + 'd ' : ''}${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            if (remaining === 0) {
                window.clearInterval(element._dropTimer);
                window.setTimeout(() => window.location.reload(), 1000);
            }
        }
        update();
        element._dropTimer = window.setInterval(update, 1000);
    });
}

function initDropOrderForms() {
    document.querySelectorAll('[data-drop-order-form]').forEach((form) => {
        const bagelInputs = Array.from(form.querySelectorAll('[data-bagel-quantity]'));
        const extraInputs = Array.from(form.querySelectorAll('[data-extra-quantity]'));
        const output = form.querySelector('[data-selected-bagels]');
        const totalOutput = form.querySelector('[data-order-total]');
        const savingsOutput = form.querySelector('[data-order-savings]');
        const submit = form.querySelector('[data-order-submit]');
        const max = parseInt(form.dataset.maxBagels || '0', 10);
        const remaining = parseInt(form.dataset.remainingBagels || '0', 10);
        const tiersNode = document.getElementById('bagel-price-tiers');
        const tiers = tiersNode ? JSON.parse(tiersNode.textContent) : [];
        const money = new Intl.NumberFormat('he-IL', { style: 'currency', currency: 'ILS' });

        function quantity(input) {
            return Math.max(0, parseInt(input.value || '0', 10));
        }

        function bestBagelPrice(count) {
            const best = [0].concat(Array(count).fill(Number.POSITIVE_INFINITY));
            for (let current = 1; current <= count; current += 1) {
                tiers.forEach((tier) => {
                    if (tier.quantity <= current) {
                        best[current] = Math.min(best[current], best[current - tier.quantity] + tier.price_cents);
                    }
                });
            }
            return best[count];
        }

        function update() {
            const bagelCount = bagelInputs.reduce((sum, input) => sum + quantity(input), 0);
            const upcharges = bagelInputs.reduce(
                (sum, input) => sum + quantity(input) * parseInt(input.dataset.upchargeCents || '0', 10), 0
            );
            const extras = extraInputs.reduce(
                (sum, input) => sum + quantity(input) * parseInt(input.dataset.unitPriceCents || '0', 10), 0
            );
            const base = bestBagelPrice(bagelCount);
            const price = Number.isFinite(base) ? base + upcharges + extras : 0;
            const singleTier = tiers.find((tier) => tier.quantity === 1);
            const regular = singleTier ? singleTier.price_cents * bagelCount + upcharges + extras : price;
            const savings = Math.max(0, regular - price);
            const invalid = bagelCount < 1 || bagelCount > max || bagelCount > remaining || !Number.isFinite(base);

            output.textContent = bagelCount;
            output.closest('strong').classList.toggle('text-danger', invalid && bagelCount > 0);
            totalOutput.textContent = money.format(price / 100);
            if (bagelCount > max) {
                savingsOutput.textContent = `Maximum ${max} bagels per order`;
                savingsOutput.classList.add('text-danger');
            } else if (bagelCount > remaining) {
                savingsOutput.textContent = `Only ${remaining} bagels remain`;
                savingsOutput.classList.add('text-danger');
            } else {
                savingsOutput.textContent = savings ? `You save ${money.format(savings / 100)}` : 'Deal pricing applies automatically';
                savingsOutput.classList.remove('text-danger');
            }
            submit.disabled = invalid;
        }
        bagelInputs.concat(extraInputs).forEach((input) => input.addEventListener('input', update));
        update();
    });
}

function initFlashMessages() {
    document.querySelectorAll('[data-auto-dismiss]').forEach((alertElement) => {
        const delay = parseInt(alertElement.dataset.autoDismiss || '6000', 10);
        window.setTimeout(() => {
            if (!alertElement.isConnected) {
                return;
            }
            if (window.bootstrap && window.bootstrap.Alert) {
                window.bootstrap.Alert.getOrCreateInstance(alertElement).close();
            } else {
                alertElement.remove();
            }
        }, delay);
    });
}

document.addEventListener('DOMContentLoaded', function () {
    initHeroRotators();
    initDropCountdowns();
    initDropOrderForms();
    initFlashMessages();
});
