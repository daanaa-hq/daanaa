import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import '@fontsource/playfair-display/400.css'
import '@fontsource/playfair-display/400-italic.css'
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import './index.css'
import App from './App.tsx'
import { GivingListProvider } from './contexts/GivingListContext'
import GiveConfirmPrompt from './components/GiveConfirmPrompt'
import ScrollToTop from './components/ScrollToTop'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <GivingListProvider>
        <ScrollToTop />
        <App />
        <GiveConfirmPrompt />
      </GivingListProvider>
    </BrowserRouter>
  </StrictMode>,
)
