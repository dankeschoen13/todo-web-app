// ===============================================================
// 1. MASTER DELEGATION

const listWrapper = document.getElementById('masonry-wrapper')

if (listWrapper) {
    ['change', 'click', 'submit', 'keydown', 'focusout'].forEach(eventType => {
        listWrapper.addEventListener(eventType, listEventsDelegator);
    });
}

/**
 * MASTER EVENT DELEGATOR: **************************************
 * Listens for events triggered within the masonry wrapper and
 * triggers the delegated effect.
 *
 * EVENTS being listened to
 *
 * 1. CHANGE on task checkboxes:
 *      > updates task position in the list
 *      > updates the completed task count
 *      > calls updateTaskStatus to make an API call
 *
 * 2. CLICK on completed toggle:
 *      > set data-state
 *      > manage UI (dynamially toggle hidden based on data-state)
 *
 * 3. CLICK on delete-task button:
 *      > calls deleteTask button to make an API call
 *
 * 4. CLICK on delete-list button:
 *      > calls deleteList button to make an API call
 *
 * @param {Event} event - The change event from the DOM.
 * @returns {void}
 */
function listEventsDelegator(event) {
    const target = event.target;

    // 1. A CHANGE on task checkboxes:
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

    // 2. A CLICK on completed toggle:
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

    // 3. A SUBMIT on add-new-task button:
    if (target.classList.contains('new-task-form')) {
        event.preventDefault();
        const listID = target.id.split('-').pop();
        addNewTask(target, listID)
    }

    // 4. A CLICK on list title
    const listTitle = target.closest('.list-title');
    if (listTitle) {
        event.preventDefault();
        enterEditMode(listTitle);
    }

    // 5. A KEYDOWN ENTER | FOCUSOUT on update list input field
    const updateListInput = target.closest('.update-list-input');
    if (updateListInput) {
        if (event.type === 'keydown' && event.key === 'Enter') {
            event.preventDefault();
            updateListInput.blur();
            return;
        }

        if (event.type === 'focusout') {
            const listId = updateListInput.id.split('-').pop();
            updateListTitle(updateListInput, listId);
        }
    }

    // 6. A CLICK on delete-task button:
    const listDeleteBtn = target.closest('.delete-list-btn');
    if (listDeleteBtn) {
        const listID = listDeleteBtn.id.split('-').pop();
        const listElement = listDeleteBtn.closest('.todo-list');
        deleteList(listID, listElement);
    }

    // 7. A CLICK on delete-list button:
    const taskDeleteBtn = target.closest('.delete-task-btn');
    if (taskDeleteBtn) {
        const taskID = taskDeleteBtn.id.split("-").pop();
        const taskItemElement = taskDeleteBtn.closest('li');
        deleteTask(taskID, taskItemElement);
    }
}


// ===============================================================
// 2. EVENT-DELEGATED FUNCTIONS

/**
 * Adds a new task to a specific list via an API POST request, dynamically
 * updates the UI, and removes the "empty state" placeholder if it exists.
 *
 * @async
 * @param {HTMLFormElement} newTaskForm - The form element that triggered submit.
 * @param {number} listId - The unique database ID of the parent list.
 * @returns {void}
 */
async function addNewTask(newTaskForm, listId) {

    const inputElement = newTaskForm.querySelector('input');
    const taskContent = inputElement.value.trim();

    if (!taskContent) return;

    const ulElement = document.getElementById(`task-list-${listId}`);
    const emptyListElement = document.getElementById(`empty-state-${listId}`)

    try {
        const response = await apiFetch(
            `/api/lists/${listId}/task`,
            'POST',
            {content: taskContent}
        )
        const toggleBtn = ulElement.querySelector('.toggle-completed-btn');

        if (toggleBtn) {
            toggleBtn.insertAdjacentHTML('beforebegin', response);
        } else {
            ulElement.insertAdjacentHTML('beforeend', response);
        }

        inputElement.value = '';
        if (emptyListElement) {
            emptyListElement.classList.add('hidden');
        }
    } catch (error) {
        console.error("Error creating list:", error);
        alert("Unable to save list. Please try again.");
    }
}

/**
 * Sends a PATCH request to toggle a task's completion status.
 * Reverts the UI state if the server request fails.
 *
 * @async
 * @param {string} taskId - The database ID of the task.
 * @param {HTMLInputElement} checkbox - The checkbox element toggled by the user.
 * @returns {void}
 */
async function updateTaskStatus(taskId, checkbox) {
    try {
        await apiFetch(
            `/api/task/${taskId}/toggle`,
            'PATCH',
        )
    } catch (error) {
        console.error("Save Error:", error);
        checkbox.checked = !checkbox.checked;
        alert("Failed to update task. Please check your connection.");
    }
}

/**
 * Transitions a list's title from display mode to edit mode by hiding
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

/**
 * Transitions the update list title input field  back to list title.
 *
 * @param {HTMLInputElement} inputElement - The input element to be unfocused.
 * @returns {void}
 */
function exitEditMode(inputElement) {
    const titleWrapper = inputElement.parentElement;
    const view = titleWrapper.querySelector('.list-title');
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
 * @async
 * @param {HTMLInputElement} input - The text input field containing the new title.
 * @param {number} listId - The unique database ID of the list being updated.
 * @returns {void}
 */
async function updateListTitle(input, listId) {
    exitEditMode(input);

    try {
        await apiFetch(
            `/api/lists/${listId}/title`,
            'PATCH',
            {title: input.value}
        )
    } catch (error) {
        console.error("Save Error:", error);
        alert("Failed to rename list. Please refresh page and/or check your connection.")
    }
}

/**
 * Sends a DELETE request to remove a list.
 * Optimistically removes the item from the DOM, but restores it if the server fails.
 *
 * @async
 * @param {string} listId - The database ID of the task.
 * @param {HTMLElement} listElement - The <li> element being deleted.
 * @returns {void}
 */
async function deleteList(listId, listElement) {
    listElement.classList.add('hidden');

    try {
        await apiFetch(`/api/lists/${listId}/delete`, 'DELETE');
        listElement.remove();
        updateMasonryLayout();
    } catch (error) {
        console.error("Delete Error:", error);
        listElement.classList.remove('hidden');
        alert("Failed to delete list. Please check your connection.");
    }
}

/**
 * Sends a DELETE request to remove a task.
 * Optimistically removes the item from the DOM, but restores it if the server fails.
 *
 * @async
 * @param {string} taskId - The database ID of the task.
 * @param {HTMLElement} taskElement - The <li> element being deleted.
 * @returns {void}
 */
async function deleteTask(taskId, taskElement) {
    taskElement.classList.add('hidden')

    try {
        await apiFetch(`/api/task/${taskId}/delete`, 'DELETE')
        taskElement.remove()
    } catch (error) {
        console.error("Delete Error:", error);
        taskElement.classList.remove('hidden');
        alert("Failed to delete task. Please check your connection.");
    }
}


// ===============================================================
// 3. FIXED/STATIC BUTTONS

const newListForm = document.getElementById('new-list-form');
if (newListForm) {
    newListForm.addEventListener('submit', (e) => {
        e.preventDefault();
        addNewList(e.target);
    });
}

/**
 * ADD NEW LIST: **************************
 * Creates a new task list via an API POST request and dynamically injects
 * the returned HTML snippet into the DOM. Also triggers a masonry layout update.
 *
 * @async
 * @returns {void}
 */
async function addNewList(newListForm) {
    const container = document.getElementById('extra-lists-container');
    const inputElement = newListForm.querySelector('input[type="text"]');
    const listTitle = inputElement.value.trim() || "New List";

    try {
        const responseData = await apiFetch(
            `/api/new-list`,
            'POST',
            {title: listTitle}
        );
        console.log("Success:", responseData);
        container.insertAdjacentHTML('beforeend', responseData);
        inputElement.value = '';
        updateMasonryLayout();
    } catch (error) {
        console.error("Error creating list:", error);
        alert("Unable to save list. Please try again.");
    }
}

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


// ===============================================================
// 4. HELPER METHODS

/**
 * A centralized wrapper for the native fetch API that automatically handles
 * headers, CSRF tokens, and response parsing.
 *
 * This function dynamically returns parsed JSON or raw HTML text based on the
 * server's 'Content-Type' header. It also automatically injects a CSRF token
 * from the document meta tag for mutating requests (POST, PUT, PATCH, DELETE).
 *
 * @async
 * @param {string} endpoint - The URL or API route to send the request to (e.g., '/api/users').
 * @param {string} [method='GET'] - The HTTP method to use. Defaults to 'GET'.
 * @param {Object|null} [body=null] - The data payload to send. It will be automatically stringified to JSON.
 * @returns {Promise<Object|string|null>} Returns a Promise that resolves to:
 *   - A parsed JavaScript Object (if the server returns JSON).
 *   - A raw string (if the server returns HTML).
 *   - `null` (if the server returns a 204 No Content status).
 * @throws {Error} Throws an error if the network response status is not OK (e.g., 400, 404, 500).
 */
async function apiFetch(endpoint, method = 'GET', body = null) {
    // 1. Building the header
    const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/html' // Accept both JSON and HTML from the server
    };
    if (method !== 'GET' && method !== 'HEAD') {
        const csrfToken = document.querySelector(
            'meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
    }
    // 2. Prepare the options object & optionally add a body
    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    // 3. Send a fetch request and await response
    const response = await fetch(endpoint, options);

    // 4. Interpret the response

    // Error handling
    if (!response.ok) {throw new Error(`API Error: ${response.status}`);}
    // Empty response handling
    if (response.status === 204) return null;
    // Text snippet response handling
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('text/html')) {
        // convert to text if HTML
        return response.text();
    }
    // else return as json
    return response.json();
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

document.addEventListener('DOMContentLoaded', setupThemeToggler)