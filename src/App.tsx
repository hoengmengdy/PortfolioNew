import { domAnimation, LazyMotion, MotionConfig } from 'framer-motion';
import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router';
import { Spinner } from './components/ui/Spinner';
import { LanguageProvider, useLanguage } from './hooks/useLanguage';
import { ThemeProvider } from './hooks/useTheme';
import Home from './pages/Home';

const NotFound = lazy(() => import('./pages/NotFound'));

function PageFallback() {
  const { t } = useLanguage();
  return (
    <div className="grid min-h-svh place-items-center">
      <Spinner label={t.common.loading} />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <LazyMotion features={domAnimation} strict>
          <MotionConfig reducedMotion="user">
            <BrowserRouter>
              <Suspense fallback={<PageFallback />}>
                <Routes>
                  {/* Home stays mounted behind the project modal, so scroll position is kept. */}
                  <Route element={<Home />}>
                    <Route index element={null} />
                    <Route path="projects/:slug" element={null} />
                  </Route>
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Suspense>
            </BrowserRouter>
          </MotionConfig>
        </LazyMotion>
      </LanguageProvider>
    </ThemeProvider>
  );
}
