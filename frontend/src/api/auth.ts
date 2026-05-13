import { apiRequest } from "./client";

export interface StudentRegisterData {
  registration_number: string;
  name: string;
  email: string;
  phone_number: string;
  password: string;
  block: string;
  floor: number;
  room_number: string;
  language_preference: string;
}

export interface StaffRegisterData {
  name: string;
  employee_id: string;
  phone_number: string;
  password: string;
  role: "staff" | "admin";
}

export interface LoginData {
  identifier: string;
  password: string;
  role: "student" | "staff" | "admin";
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: string;
}

export const authApi = {
  registerStudent: (data: StudentRegisterData) =>
    apiRequest<AuthResponse>("/auth/register/student", { method: "POST", body: data }),

  registerStaff: (data: StaffRegisterData) =>
    apiRequest<AuthResponse>("/auth/register/staff", { method: "POST", body: data }),

  login: (data: LoginData) =>
    apiRequest<AuthResponse>("/auth/login", { method: "POST", body: data }),

  refresh: (refreshToken: string) =>
    apiRequest<{ access_token: string }>("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    }),
};
