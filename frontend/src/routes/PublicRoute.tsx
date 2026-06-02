import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const PublicRoute = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    // Show a full page spinner while checking auth state
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    // If the user is already logged in, they shouldn't see the login/register pages.
    // Redirect them directly to the dashboard.
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
};
