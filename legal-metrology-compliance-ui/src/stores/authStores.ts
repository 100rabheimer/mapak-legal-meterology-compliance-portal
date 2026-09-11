import { create } from "zustand";
import type { User } from "../types/auth";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  restoreSession: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  login: (user, token) => {
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("access_token", token);

    set({
      user,
      isAuthenticated: true,
    });
  },

  logout: () => {
    localStorage.removeItem("user");
    localStorage.removeItem("access_token");

    set({
      user: null,
      isAuthenticated: false,
    });
  },

  restoreSession: () => {
    const savedUser = localStorage.getItem("user");
    const token = localStorage.getItem("access_token");

    if (!savedUser || !token) {
      return;
    }

    set({
      user: JSON.parse(savedUser) as User,
      isAuthenticated: true,
    });
  },
}));