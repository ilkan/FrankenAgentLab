/**
 * Application configuration
 * 
 * Environment-aware configuration that adapts based on VITE_ENVIRONMENT.
 * Uses Vite's import.meta.env for environment variables.
 */

// Backend API URL - configured per environment
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Current environment
export const ENVIRONMENT = import.meta.env.VITE_ENVIRONMENT || 'development';

// Environment checks
export const isDevelopment = ENVIRONMENT === 'development';
export const isProduction = ENVIRONMENT === 'production';

// Log configuration in development
if (isDevelopment) {
  console.log('🔧 FrankenAgent Lab - Development Mode');
  console.log('API Base URL:', API_BASE_URL);
}
