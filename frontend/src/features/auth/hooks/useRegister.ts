import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { AxiosError } from "axios";
import { authApi } from "../../../lib/api/auth";
import { useAuth } from "../../../context/AuthContext";
import { RegisterRequest } from "../../../types/auth";

export const useRegister = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (data: RegisterRequest) => {
      // 1. Create the account
      await authApi.register(data);
      // 2. Immediately log in to get a token pair
      const tokens = await authApi.login({
        email: data.email,
        password: data.password,
      });
      return tokens;
    },
    onSuccess: (tokens) => {
      login(tokens);
      navigate("/dashboard", { replace: true });
    },
    onError: (error: AxiosError<{ detail: string }>) => {
      return (
        error.response?.data?.detail ?? "Registration failed. Please try again."
      );
    },
  });
};
