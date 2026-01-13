/**
 * Authentication utilities for token storage and authenticated requests.
 */

const TOKEN_KEY = 'conduit_access_token';
const USER_KEY = 'conduit_user';
const PROJECT_KEY = 'conduit_current_project';

// In-memory project storage (also persisted to sessionStorage)
let currentProjectName = null;

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

