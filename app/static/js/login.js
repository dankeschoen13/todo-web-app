import { apiFetch } from "./api.js";

// ===============================================================
// LOGIN LOGIC

const loginForm = document.getElementById('login-form');

if (loginForm) {
    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        await loginUser(event.target);
    });
}

/**
 * LOGS IN A USER: **************************
 * Logs in a user via API POST request and dynamically handle
 * responses by modifying error elements for clear user feedback.
 *
 * @async
 * @returns {Promise<void>}
 */
async function loginUser(loginForm){
    const formData = new FormData(loginForm);
    const formValues = Object.fromEntries(formData.entries());

    // Clear any previous errors first
    document.querySelectorAll('[id^="error-"]').forEach(el => {
        el.classList.add('hidden');
        el.textContent = '';
    });

    // Disable submit button while loading
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Logging in...";
    }

    try {
        await apiFetch(`/api/login`, 'POST', formValues);
        console.log("Success: User logged in.");
        window.location.href = '/';

    } catch (error) {
        console.error("Login failed:", error);

        if (error.field && error.serverMessage) {
            // Catch the specific field error sent from Flask and display it
            const errorElement = document.getElementById(`error-${error.field}`);
            if (errorElement) {
                errorElement.textContent = error.serverMessage;
                errorElement.classList.remove('hidden');
            }
        } else {
            // Fallback for major crashes
            const globalError = document.getElementById('error-global');
            if (globalError) {
                globalError.textContent = "An unexpected error occurred. Please try again.";
                globalError.classList.remove('hidden');
            }
        }
    } finally {
        if (submitBtn) {
            // Reset the button state
            submitBtn.disabled = false;
            submitBtn.textContent = "Log In";
        }
    }
}