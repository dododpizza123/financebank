document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    initMobileMenu();
    initAccessibilityPanel();
    initDepositCalculator();
    initFormValidation();
    initFlashMessages();
    initScrollButton();
    initCounterAnimation();

    function initMobileMenu() {
        const nav = document.querySelector('.nav');
        const header = document.querySelector('.header');

        if (!nav || !header) {
            return;
        }

        const button = document.createElement('button');
        button.className = 'burger-btn';
        button.type = 'button';
        button.setAttribute('aria-label', 'Открыть меню');
        button.innerHTML = '<span></span><span></span><span></span>';

        header.appendChild(button);

        button.addEventListener('click', () => {
            nav.classList.toggle('nav-open');
            button.classList.toggle('burger-active');
        });

        nav.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                nav.classList.remove('nav-open');
                button.classList.remove('burger-active');
            });
        });
    }

    function initAccessibilityPanel() {
        const panel = document.querySelector('.accessibility-panel');

        if (!panel) {
            return;
        }

        const fontButtons = panel.querySelectorAll('[data-font]');
        const themeButtons = panel.querySelectorAll('[data-theme]');
        const savedFont = localStorage.getItem('site-font-size');
        const savedTheme = localStorage.getItem('site-theme');

        if (savedFont) {
            body.dataset.font = savedFont;
        }

        if (savedTheme) {
            body.dataset.theme = savedTheme;
        }

        fontButtons.forEach((button) => {
            button.addEventListener('click', () => {
                const value = button.dataset.font;

                body.dataset.font = value;
                localStorage.setItem('site-font-size', value);
            });
        });

        themeButtons.forEach((button) => {
            button.addEventListener('click', () => {
                const value = button.dataset.theme;

                body.dataset.theme = value;
                localStorage.setItem('site-theme', value);
            });
        });
    }

    function initDepositCalculator() {
        const form = document.querySelector('#deposit-calculator');

        if (!form) {
            return;
        }

        const amountInput = form.querySelector('[name="amount"]');
        const rateInput = form.querySelector('[name="rate"]');
        const monthsInput = form.querySelector('[name="months"]');
        const resultBlock = form.querySelector('.calculator-result');

        form.addEventListener('submit', (event) => {
            event.preventDefault();

            const amount = Number(amountInput.value);
            const rate = Number(rateInput.value);
            const months = Number(monthsInput.value);

            if (amount <= 0 || rate <= 0 || months <= 0) {
                showCalculatorResult(
                    resultBlock,
                    'Введите сумму, процент и срок больше нуля.',
                    true
                );
                return;
            }

            const income = amount * (rate / 100) * (months / 12);
            const total = amount + income;

            showCalculatorResult(
                resultBlock,
                `Доход: ${formatMoney(income)} ₽. Итоговая сумма: ${formatMoney(total)} ₽.`,
                false
            );
        });
    }

    function showCalculatorResult(block, text, isError) {
        if (!block) {
            return;
        }

        block.textContent = text;
        block.classList.toggle('calculator-error', isError);
        block.classList.add('calculator-result-visible');
    }

    function initFormValidation() {
        const forms = document.querySelectorAll('form');

        forms.forEach((form) => {
            form.addEventListener('submit', (event) => {
                clearFormErrors(form);

                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;

                requiredFields.forEach((field) => {
                    if (!field.value.trim()) {
                        isValid = false;
                        markFieldError(field, 'Поле нужно заполнить.');
                    }
                });

                const password = form.querySelector('[name="password"]');
                const passwordRepeat = form.querySelector('[name="password_confirm"], [name="confirm_password"]');

                if (
                    password &&
                    passwordRepeat &&
                    password.value !== passwordRepeat.value
                ) {
                    isValid = false;
                    markFieldError(passwordRepeat, 'Пароли не совпадают.');
                }

                if (!isValid) {
                    event.preventDefault();
                }
            });
        });
    }

    function markFieldError(field, message) {
        field.classList.add('field-error');

        const error = document.createElement('div');
        error.className = 'field-error-text';
        error.textContent = message;

        field.insertAdjacentElement('afterend', error);
    }

    function clearFormErrors(form) {
        form.querySelectorAll('.field-error').forEach((field) => {
            field.classList.remove('field-error');
        });

        form.querySelectorAll('.field-error-text').forEach((error) => {
            error.remove();
        });
    }

    function initFlashMessages() {
        const messages = document.querySelectorAll('.flash-message, .alert');

        messages.forEach((message) => {
            const closeButton = document.createElement('button');

            closeButton.type = 'button';
            closeButton.className = 'flash-close';
            closeButton.textContent = '×';

            message.appendChild(closeButton);

            closeButton.addEventListener('click', () => {
                message.remove();
            });

            setTimeout(() => {
                message.classList.add('flash-hidden');

                setTimeout(() => {
                    message.remove();
                }, 400);
            }, 5000);
        });
    }

    function initScrollButton() {
        const button = document.createElement('button');

        button.type = 'button';
        button.className = 'scroll-top-btn';
        button.textContent = '↑';
        button.setAttribute('aria-label', 'Наверх');

        document.body.appendChild(button);

        window.addEventListener('scroll', () => {
            button.classList.toggle('scroll-top-visible', window.scrollY > 350);
        });

        button.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    function initCounterAnimation() {
        const counters = document.querySelectorAll('[data-counter]');

        if (!counters.length) {
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                animateCounter(entry.target);
                observer.unobserve(entry.target);
            });
        }, {
            threshold: 0.4
        });

        counters.forEach((counter) => {
            observer.observe(counter);
        });
    }

    function animateCounter(element) {
        const target = Number(element.dataset.counter);
        const duration = 900;
        const startTime = performance.now();

        function update(currentTime) {
            const progress = Math.min((currentTime - startTime) / duration, 1);
            const value = Math.floor(target * progress);

            element.textContent = value.toLocaleString('ru-RU');

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    function formatMoney(value) {
        return value.toLocaleString('ru-RU', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
});


let currentFontSize = Number(localStorage.getItem('fontSize')) || 16;

function applyFontSize() {
    document.documentElement.style.setProperty(
        '--fs-base',
        `${currentFontSize}px`
    );

    localStorage.setItem('fontSize', String(currentFontSize));
}

function changeFontSize(step) {
    currentFontSize += step;

    if (currentFontSize < 14) {
        currentFontSize = 14;
    }

    if (currentFontSize > 24) {
        currentFontSize = 24;
    }

    applyFontSize();
}

function setTheme(themeName) {
    const page = document.documentElement;

    if (themeName !== 'accessible') {
        themeName = 'standard';
    }

    page.setAttribute('data-theme', themeName);
    localStorage.setItem('siteTheme', themeName);
}

document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('siteTheme') || 'standard';

    setTheme(savedTheme);
    applyFontSize();
});