/**
 * api.js — API client configuration
 * 
 * In production (Vercel), we fetch from the Render URL.
 * In development, we fetch from the local Vite proxy.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const getApiUrl = (path) => {
  // If path starts with slash, remove it to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.substring(1) : path;
  
  // If API_BASE_URL is empty, it uses the current domain (works with Vite proxy)
  if (!API_BASE_URL) return `/${cleanPath}`;
  
  // Otherwise, append to the base URL
  return `${API_BASE_URL}/${cleanPath}`;
};

export default API_BASE_URL;
