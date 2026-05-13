import { useAuth } from "@/contexts/AuthContext";
import StudentDashboard from "@/components/dashboards/StudentDashboard";
import StaffDashboard from "@/components/dashboards/StaffDashboard";
import AdminDashboard from "@/components/dashboards/AdminDashboard";

export default function DashboardPage() {
  const { role } = useAuth();
  if (role === "admin") return <AdminDashboard />;
  if (role === "staff") return <StaffDashboard />;
  return <StudentDashboard />;
}
