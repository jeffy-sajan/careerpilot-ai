import { useMutation } from '@tanstack/react-query';
import { useNavigate, useLocation } from 'react-router-dom';
import { AxiosError } from 'axios';
import { authApi } from '../../../lib/api/auth';
import { useAuth } from '../../../context/AuthContext';
import { LoginRequest } from '../../../types/auth';

export const useLogin = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect to the page they originally tried to visit, or /dashboard
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? '/dashboard';

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: (tokens) => {
      login(tokens);
      navigate(from, { replace: true });
    },
    // Return a clean error message string from the AxiosError
    onError: (error: AxiosError<{ detail: string }>) => {
      return error.response?.data?.detail ?? 'Login failed. Please try again.';
    },
  });
};
