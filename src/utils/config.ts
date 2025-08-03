// Configuration for different environments

const isDevelopment = process.env.NODE_ENV === 'development';
const isProduction = process.env.NODE_ENV === 'production';

// Determine API URL based on environment
const getApiUrl = () => {
  // If explicitly set, use that
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // In production on Vercel, use relative URL
  if (isProduction && window.location.hostname.includes('vercel.app')) {
    return '/api';
  }
  
  // Default to localhost for development
  return 'http://localhost:8000';
};

export const config = {
  API_URL: getApiUrl(),
  isDevelopment,
  isProduction,
};

export default config;