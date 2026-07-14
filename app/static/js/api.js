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
export async function apiFetch(endpoint, method = 'GET', body = null) {
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
    const options = { method, credentials: 'same-origin', headers };
    if (body) options.body = JSON.stringify(body);

    // 3. Send a fetch request and await response
    const response = await fetch(endpoint, options);

    // 4. Interpret the response

    // Error handling
    if (!response.ok) {
        // - Try to parse the JSON error payload from Flask
        let errorData = {};
        try {
            errorData = await response.json();
        } catch (e) {
            // If it's not JSON (e.g., a raw 500 HTML page), just ignore
        }

        // - Create a standard Error with Flask data attached
        const error = new Error(`API Error: ${response.status}`);
        error.field = errorData.field || 'global';
        error.serverMessage = errorData.error || 'A network error occurred.';

        throw error;
    }

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