export type UserRole = "admin" | "officer";

export interface User {
  id: string;
  officerId?: string;
  name: string;
  email: string;
  phone?: string;
  designation?: string;
  department?: string;
  jurisdiction?: string;
  role: UserRole;
  isActive: boolean;
  createdAt: string;
  lastLoginAt?: string;
}