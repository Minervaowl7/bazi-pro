import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AnalyzePage from './pages/AnalyzePage';
import ResultPage from './pages/ResultPage';
import HistoryPage from './pages/HistoryPage';
import AccountPage from './pages/AccountPage';

function App() {
  const init = useAuthStore((s) => s.init);

  useEffect(() => {
    init();
  }, [init]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/analyze" element={<AnalyzePage />} />
        <Route path="/result/:runId" element={<ResultPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/account" element={<AccountPage />} />
      </Route>
      <Route path="/" element={<Navigate to="/analyze" replace />} />
      <Route path="*" element={<Navigate to="/analyze" replace />} />
    </Routes>
  );
}

export default App;
