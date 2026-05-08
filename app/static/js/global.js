
/**
 * Initializes the dark/light mode theme toggler. Checks system preferences
 * or localStorage for the initial state, updates the UI icons, and binds
 * the toggle button click listener.
 *
 * @returns {void}
 */
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


/**
 * Dynamically adjusts the max-width of the masonry wrapper based on the number of task lists.
 *
 * This prevents the CSS column layout from stretching to the edges when there are
 * fewer lists than the maximum allowed columns, ensuring the grid stays centered.
 *
 * @returns {void}
 */
function updateMasonryLayout() {
    const wrapper = document.getElementById('masonry-wrapper');
    const listCount = wrapper.querySelectorAll('section').length;

    if (listCount === 1) {
        wrapper.style.maxWidth = '380px';
    } else if (listCount === 2) {
        wrapper.style.maxWidth = '824px';
    } else {
        wrapper.style.maxWidth = '1280px';
    }
}


/**
 * Creates a new task list via an API POST request and dynamically injects
 * the returned HTML snippet into the DOM. Also triggers a masonry layout update.
 *
 * @param {Event} [event] - The optional form submission or click event.
 * @returns {void}
 */
function addNewList(event) {
    if (event) event.preventDefault();

    const container = document.getElementById('extra-lists-container');
    const inputElement = document.getElementById('new-list-input');
    const listTitle = inputElement.value.trim() || "New List";

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch(`/api/new-list`, {
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
        updateMasonryLayout();
    })
    .catch(error => {
        console.error("Error creating list:", error);
        alert("Unable to save list. Please try again.");
    });
}


/**
 * Adds a new task to a specific list via an API POST request, dynamically
 * updates the UI, and removes the "empty state" placeholder if it exists.
 *
 * @param {Event} [event] - The optional form submission or click event.
 * @param {number} listId - The unique database ID of the parent list.
 * @returns {void}
 */
function addNewTask(event, listId) {
    if (event) event.preventDefault();

    const inputElement = document.getElementById(`new-task-input-${listId}`)
    const taskContent = inputElement.value.trim();

    if (!taskContent) return;

    const ulElement = document.getElementById(`task-list-${listId}`);
    const emptyListElement = document.getElementById(`empty-state-${listId}`)
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch(`/api/lists/${listId}/task`, {
        method: 'POST',
        body: JSON.stringify({content: taskContent}),
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
        ulElement.insertAdjacentHTML('beforeend', htmlSnippet);
        inputElement.value = '';
        if (emptyListElement) {
            emptyListElement.remove();
        }
    })
    .catch(error => {
        console.error("Error creating list:", error);
        alert("Unable to save list. Please try again.");
    });
}


/**
 * Transitions a list's header from display mode to edit mode by hiding
 * the heading text and revealing the text input field.
 *
 * @param {HTMLElement} element - The clickable header view container.
 * @returns {void}
 */
function enterEditMode(element) {
    const titleWrapper = element.parentElement;
    const input = titleWrapper.querySelector('input');

    element.classList.add('hidden');
    input.classList.remove('hidden');
    input.focus();
    input.select();
}

function exitEditMode(inputElement) {
    const titleWrapper = inputElement.parentElement;
    const view = titleWrapper.querySelector('.header-view');
    const h2 = view.querySelector('h2');

    if (inputElement.value.trim() !== "") {
        h2.innerText = inputElement.value;
    } else {
        inputElement.value = h2.innerText;
    }

    inputElement.classList.add('hidden');
    view.classList.remove('hidden');
}


/**
 * Saves an updated list title to the backend via an API PATCH request.
 * Automatically exits edit mode before sending the request.
 *
 * @param {HTMLInputElement} input - The text input field containing the new title.
 * @param {number} listId - The unique database ID of the list being updated.
 * @returns {void}
 */
function saveListTitle(input, listId) {
    exitEditMode(input);

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch(`/api/lists/${listId}/title`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ title: input.value })
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Server rejected the request.');
        }
    })
    .catch(err => console.error("Save Error:", err));
}


function deleteList(listId, listElement) {
    const parentElement = listElement.parentElement;

    listElement.remove();

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch(`/api/lists/${listId}/delete`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Server rejected the request.');
        }
        updateMasonryLayout();
    })
    .catch(err => {
        console.error("Delete Error:", err);
        // Rollback the UI if the delete fails
        parentElement.appendChild(listElement);
        alert("Failed to delete list. Please check your connection.");
    });
}



/**
 * Sends a PATCH request to toggle a task's completion status.
 * Reverts the UI state if the server request fails.
 *
 * @param {string} taskId - The database ID of the task.
 * @param {HTMLInputElement} checkbox - The checkbox element toggled by the user.
 * @returns {void}
 */
function updateTaskStatus(taskId, checkbox) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch(`/api/task/${taskId}/toggle`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Server rejected the request.');
        }
    })
    .catch(err => {
        console.error("Save Error:", err);
        // Rollback the UI if the fetch fails
        checkbox.checked = !checkbox.checked;
        alert("Failed to update task. Please check your connection.");
    });
}


/**
 * Sends a DELETE request to remove a task.
 * Optimistically removes the item from the DOM, but restores it if the server fails.
 *
 * @param {string} taskId - The database ID of the task.
 * @param {HTMLElement} taskElement - The <li> element being deleted.
 * @returns {void}
 */
function deleteTask(taskId, taskElement) {
    const parentElement = taskElement.parentElement;

    taskElement.remove();

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch(`/api/task/${taskId}/delete`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Server rejected the request.');
        }
    })
    .catch(err => {
        console.error("Delete Error:", err);
        // Rollback the UI if the delete fails
        parentElement.appendChild(taskElement);
        alert("Failed to delete task. Please check your connection.");
    });
}


// EVENT LISTENERS

/**
 * Listens for actions triggered within the masonry wrapper and initiates
 * the API call to apply those changes to the database.
 *
 * Events being listened to:
 *
 * - checkbox completion toggle
 * - hide/show completed button is clicked
 * - delete task is clicked
 * - delete list is clicked
 *
 * @param {Event} event - The change event from the DOM.
 * @returns {void}
 */
function listActionsListener(event) {
    const target = event.target;

    // LISTENS FOR CHANGES IN CHECKBOX
    if (target.classList.contains('task-checkbox')) {
        const taskID = target.id.split("-").pop();
        const taskItemElement = target.closest('li');
        const parentList = taskItemElement.parentElement;
        const toggleBtn = parentList.querySelector('.toggle-completed-btn');

        if (target.checked) {
            // When task item is checked, do the following:
            //
            // 1. cut and paste the task item to the bottom of parentList
            // 2. immediately hide the task item in 'collapsed' state
            parentList.appendChild(taskItemElement);
            if (toggleBtn && toggleBtn.getAttribute('data-state') === 'collapsed') {
                taskItemElement.classList.add('hidden');
            }
        } else {
            // When task item is unchecked, do the following:
            //
            // 1. cut and paste the task item to the top of parentList
            // 2. remove the hidden class
            parentList.prepend(taskItemElement);
            taskItemElement.classList.remove('hidden'); // Ensure it becomes visible
        }

        if (toggleBtn) {
            // Dynamically update the completed count and
            // hide the completed toggle when there are no checked tasks
            const checkedCount = parentList.querySelectorAll('.task-checkbox:checked').length;
            toggleBtn.querySelector('.completed-count').textContent = checkedCount;

            if (checkedCount === 0) {
                toggleBtn.classList.add('hidden');
            } else {
                toggleBtn.classList.remove('hidden');
            }
        }

        updateTaskStatus(taskID, target);
    }

    // LISTENS FOR COMPLETED TOGGLE BUTTON CLICKS
    const toggleCompletedBtn = target.closest('.toggle-completed-btn');
    if (toggleCompletedBtn) {
        const taskList = toggleCompletedBtn.parentElement;
        const checkedTasks = taskList.querySelectorAll('.task-checkbox:checked');
        const chevron = toggleCompletedBtn.querySelector('.chevron-icon');

        // Check current state
        const isCurrentlyExpanded = toggleCompletedBtn.getAttribute('data-state') === 'expanded';

        if (isCurrentlyExpanded) {
            toggleCompletedBtn.setAttribute('data-state', 'collapsed');
        } else {
            toggleCompletedBtn.setAttribute('data-state', 'expanded');
        }

        // Enforce toggle rule depending on status: Add class if expanded, remove if not.
        chevron.classList.toggle('-rotate-90', isCurrentlyExpanded);
        checkedTasks.forEach((item) => {
            item.closest('li').classList.toggle('hidden', isCurrentlyExpanded);
        });
    }

    // --- DELETE TASK LISTENER ---
    const taskDeleteBtn = target.closest('.delete-task-btn');
    if (taskDeleteBtn) {
        const taskID = taskDeleteBtn.id.split("-").pop();
        const taskItemElement = taskDeleteBtn.closest('li');
        deleteTask(taskID, taskItemElement);
    }

    // --- DELETE LIST LISTENER ---
    const listDeleteBtn = target.closest('.delete-list-btn');
    if (listDeleteBtn) {
        const listID = listDeleteBtn.id.split('-').pop();
        const listElement = listDeleteBtn.closest('.todo-list');
        deleteList(listID, listElement);
    }
}

function newListInputListener(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        addNewList();
    }
}


const newListInput = document.getElementById('new-list-input')
newListInput.addEventListener('keydown', newListInputListener)

const listWrapper = document.getElementById('masonry-wrapper')
listWrapper.addEventListener('change', listActionsListener)
listWrapper.addEventListener('click', listActionsListener)

document.addEventListener('DOMContentLoaded', setupThemeToggler)