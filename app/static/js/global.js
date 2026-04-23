function enterEditMode(element) {
    const titleWrapper = element.parentElement;
    const input = titleWrapper.querySelector('input');
    const h2 = element.querySelector('h2');

    element.classList.add('hidden');
    input.classList.remove('hidden');
    input.focus();
    input.select();
}

function exitEditMode(inputElement) {
    const titleWrapper = inputElement.parentElement;
    const view = titleWrapper.querySelector('#header-view');
    const h2 = view.querySelector('h2');

    if (inputElement.value.trim() !== "") {
        h2.innerText = inputElement.value;
    } else {
        inputElement.value = h2.innerText;
    }

    inputElement.classList.add('hidden');
    view.classList.remove('hidden');
}

function addNewList(event) {
    if (event) event.preventDefault();

    const container = document.getElementById('extra-lists-container');
    const inputElement = document.getElementById('new-list-input');
    const listTitle = inputElement.value.trim() || "New List";

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch(`/create-list`, {
        method: 'POST',
        body: JSON.stringify({
            title: listTitle
        }),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Server rejected the request.');
        }
        return res.text();
    })
    .then(htmlSnippet => {
        container.insertAdjacentHTML('beforeend', htmlSnippet);
        inputElement.value = '';
    })
    .catch(error => {
        console.error("Error creating list:", error);
        alert("Unable to save list. Please try again.");
    });
}

function setupThemeToggler() {
    const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
    const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');

    if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
        themeToggleLightIcon.classList.remove('hidden');
    } else {
        themeToggleDarkIcon.classList.remove('hidden');
    }

    const themeToggleBtn = document.getElementById('theme-toggle');

    function toggleTheme() {
        themeToggleDarkIcon.classList.toggle('hidden');
        themeToggleLightIcon.classList.toggle('hidden');

        if (localStorage.getItem('color-theme')) {
            if (localStorage.getItem('color-theme') === 'light') {
                document.documentElement.classList.add('dark');
                localStorage.setItem('color-theme', 'dark');
            } else {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('color-theme', 'light');
            }
        } else {
            if (document.documentElement.classList.contains('dark')) {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('color-theme', 'light');
            } else {
                document.documentElement.classList.add('dark');
                localStorage.setItem('color-theme', 'dark');
            }
        }
    }

    themeToggleBtn.addEventListener('click', toggleTheme);
}

document.addEventListener('DOMContentLoaded', setupThemeToggler)
