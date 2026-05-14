import { apiFetch } from "./api.js";

const registerForm = document.getElementById('register-form');

if (registerForm) {
    registerForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        await registerUser(event.target);
    });
}

/**
 * REGISTER A NEW USER: **************************
 * Registers a new user via an API POST request and dynamically handles
 * API responses by modifying error elements for clear user feedback
 *
 * @async
 * @returns {Promise<void>}
 */
async function registerUser(registerForm) {
    const formData = new FormData(registerForm);
    const formValues = Object.fromEntries(formData.entries());

    // Clear any previous errors first
    document.querySelectorAll('[id^="error-"]').forEach(el => {
        el.classList.add('hidden');
        el.textContent = '';
    });

    // Disable submit button while loading
    const submitBtn = registerForm.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Creating account...";
    }

    try {
        await apiFetch(`/api/register`, 'POST', formValues);
        console.log("Success: User created and logged in.");
        window.location.href = '/';

    } catch (error) {
        console.error("Registration failed:", error);

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
        // Reset the button state
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = "Sign Up";
        }
    }
}