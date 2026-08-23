import { LogtoProvider } from '@logto/react';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { App } from './App';
import './styles.css';

const endpoint = import.meta.env.VITE_LOGTO_ENDPOINT || 'https://logto.invalid';
const appId = import.meta.env.VITE_LOGTO_APP_ID || 'pusula-unconfigured';
const apiResource = import.meta.env.VITE_PUSULA_API_RESOURCE || 'https://api.pusula.invalid';

const root = document.getElementById('root');
if (!root) {
  throw new Error('Pusula root element is missing');
}

createRoot(root).render(
  <StrictMode>
    <LogtoProvider
      config={{
        endpoint,
        appId,
        resources: [apiResource],
        scopes: ['projects:read'],
      }}
    >
      <App apiResource={apiResource} />
    </LogtoProvider>
  </StrictMode>,
);
