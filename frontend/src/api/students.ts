import { apiRequest } from "./client";

export interface StudentProfile {
  id: string;
  registration_number: string;
  name: string;
  email: string;
  phone_number: string;
  block: string;
  floor: number;
  room_number: string;
  language_preference: string;
  is_active: boolean;
}

export const studentsApi = {
  getMe: (token: string) =>
    apiRequest<StudentProfile>("/students/me", { token }),

  updateMe: (token: string, data: Partial<StudentProfile>) =>
    apiRequest<StudentProfile>("/students/me", { method: "PATCH", token, body: data }),

  getById: (token: string, id: string) =>
    apiRequest<StudentProfile>(`/students/${id}`, { token }),
};
