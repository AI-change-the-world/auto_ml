import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './i18n';
import './index.css'
import App from './App.tsx'
import { registerApiErrorHandler } from './utils/apiError';

registerApiErrorHandler((error) => {
  if (error.code === 401 || error.errorCode === 'UNAUTHORIZED') {
    console.warn('[API Unauthorized]', error.message);
    return;
  }
  if (error.code === 403 || error.errorCode === 'FORBIDDEN') {
    console.warn('[API Forbidden]', error.message);
    return;
  }
  if (error.code === 503 || error.errorCode === 'CAPABILITY_UNAVAILABLE') {
    console.warn('[API Capability/Service Unavailable]', error.message, error.detail);
  }
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
