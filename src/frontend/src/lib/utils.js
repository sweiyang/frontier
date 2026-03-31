/**
 * Authentication and utility functions for the Frontier frontend.
 */

const TOKEN_KEY = 'frontier_access_token';
const USER_KEY = 'frontier_user';
const PROJECT_KEY = 'frontier_current_project';

// In-memory project storage (also persisted to sessionStorage)
let currentProjectName = null;

// App configuration cache
let appConfig = null;

/**
 * Save the JWT token to localStorage.
 * @param {string} token - The JWT access token
 */
export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Get the JWT token from localStorage.
 * @returns {string|null} The stored token or null if not found
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Remove the JWT token from localStorage.
 */
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Save user info to localStorage.
 * @param {Object} user - User object with username and user_id
 */
export function saveUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Get user info from localStorage.
 * @returns {Object|null} The stored user or null if not found
 */
export function getUser() {
  const user = localStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
}

/**
 * Check if user is authenticated (has a token).
 * @returns {boolean} True if token exists
 */
export function isAuthenticated() {
  return !!getToken();
}

/**
 * Set the current project name (from URL).
 * @param {string} project - The project name
 */
export function setCurrentProject(project) {
  currentProjectName = project;
  if (project) {
    sessionStorage.setItem(PROJECT_KEY, project);
  } else {
    sessionStorage.removeItem(PROJECT_KEY);
  }
}

/**
 * Get the current project name.
 * @returns {string|null} The current project name or null
 */
export function getCurrentProject() {
  if (currentProjectName) return currentProjectName;
  return sessionStorage.getItem(PROJECT_KEY);
}

/**
 * Authenticated fetch wrapper that adds the Authorization header and project context.
 * Handles 401 responses by clearing the token.
 *
 * @param {string} url - The URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise<Response>} The fetch response
 */
export async function authFetch(url, options = {}) {
  const token = getToken();
  const project = getCurrentProject();

  const headers = {
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Add project header if a project is set
  if (project) {
    headers['X-Project'] = project;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // If we get a 401, clear the token (it's expired or invalid)
  if (response.status === 401) {
    clearToken();
    // Dispatch a custom event to notify the app about auth failure
    window.dispatchEvent(new CustomEvent('auth:logout'));
  }

  // If we get a 403, notify the app about forbidden access
  if (response.status === 403) {
    window.dispatchEvent(new CustomEvent('auth:forbidden', {
      detail: { url: url, project: project }
    }));
  }

  return response;
}

/**
 * Authenticated POST request helper.
 *
 * @param {string} url - The URL to post to
 * @param {Object} data - The data to send as JSON
 * @returns {Promise<Response>} The fetch response
 */
export async function authPost(url, data) {
  return authFetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
}

/**
 * Authenticated GET request helper.
 *
 * @param {string} url - The URL to get
 * @returns {Promise<Response>} The fetch response
 */
export async function authGet(url) {
  return authFetch(url, {
    method: 'GET',
  });
}

/**
 * Convert a File object to base64 encoded string.
 *
 * @param {File} file - The file to convert
 * @returns {Promise<string>} Base64 encoded file content
 */
export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      // Remove the data URL prefix (e.g., "data:image/png;base64,")
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = (error) => reject(error);
  });
}

/**
 * Prepare files for upload by converting to the expected format.
 *
 * @param {File[]} files - Array of File objects
 * @returns {Promise<Array<{filename: string, content_type: string, data: string}>>}
 */
export async function prepareFilesForUpload(files) {
  const prepared = [];
  for (const file of files) {
    const data = await fileToBase64(file);
    prepared.push({
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      data: data
    });
  }
  return prepared;
}

/**
 * Fetch application configuration from the backend.
 * This is a public endpoint, so no authentication is required.
 * Results are cached to avoid repeated requests.
 *
 * @returns {Promise<{app_name: string}>} The app configuration
 */
export async function getAppConfig() {
  // Return cached config if available
  if (appConfig) {
    return appConfig;
  }

  try {
    const response = await fetch('/config');
    if (response.ok) {
      appConfig = await response.json();
      return appConfig;
    } else {
      // Fallback to default if endpoint fails
      appConfig = { app_name: 'Frontier' };
      return appConfig;
    }
  } catch (error) {
    console.error('Failed to fetch app config:', error);
    // Fallback to default on error
    appConfig = { app_name: 'Frontier' };
    return appConfig;
  }
}
