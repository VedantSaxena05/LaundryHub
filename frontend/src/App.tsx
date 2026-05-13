import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppLayout from "@/components/AppLayout";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import SlotsPage from "@/pages/SlotsPage";
import BagsPage from "@/pages/BagsPage";
import ForumPage from "@/pages/ForumPage";
import LostFoundPage from "@/pages/LostFoundPage";
import TodayOpsPage from "@/pages/staff/TodayOpsPage";
import DelaysPage from "@/pages/staff/DelaysPage";
import BlockedDatesPage from "@/pages/staff/BlockedDatesPage";
import RfidPage from "@/pages/staff/RfidPage";
import DevicesPage from "@/pages/staff/DevicesPage";
import AnalyticsPage from "@/pages/admin/AnalyticsPage";
import AdminStudentsPage from "@/pages/admin/AdminStudentsPage";
import AdminStaffPage from "@/pages/admin/AdminStaffPage";
import AdminSlotsPage from "@/pages/admin/AdminSlotsPage";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
      <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />} />

      {/* Student routes */}
      <Route path="/dashboard" element={<ProtectedRoute><AppLayout><DashboardPage /></AppLayout></ProtectedRoute>} />
      <Route path="/slots" element={<ProtectedRoute allowedRoles={["student"]}><AppLayout><SlotsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/bags" element={<ProtectedRoute allowedRoles={["student"]}><AppLayout><BagsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/forum" element={<ProtectedRoute><AppLayout><ForumPage /></AppLayout></ProtectedRoute>} />
      <Route path="/lost-found" element={<ProtectedRoute allowedRoles={["student"]}><AppLayout><LostFoundPage /></AppLayout></ProtectedRoute>} />

      {/* Staff routes */}
      <Route path="/staff/today" element={<ProtectedRoute allowedRoles={["staff", "admin"]}><AppLayout><TodayOpsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/staff/delays" element={<ProtectedRoute allowedRoles={["staff", "admin"]}><AppLayout><DelaysPage /></AppLayout></ProtectedRoute>} />
      <Route path="/staff/blocked-dates" element={<ProtectedRoute allowedRoles={["staff", "admin"]}><AppLayout><BlockedDatesPage /></AppLayout></ProtectedRoute>} />
      <Route path="/staff/rfid" element={<ProtectedRoute allowedRoles={["staff", "admin"]}><AppLayout><RfidPage /></AppLayout></ProtectedRoute>} />
      <Route path="/staff/devices" element={<ProtectedRoute allowedRoles={["staff", "admin"]}><AppLayout><DevicesPage /></AppLayout></ProtectedRoute>} />

      {/* Admin routes */}
      <Route path="/admin/analytics" element={<ProtectedRoute allowedRoles={["admin"]}><AppLayout><AnalyticsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/admin/students" element={<ProtectedRoute allowedRoles={["admin"]}><AppLayout><AdminStudentsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/admin/staff" element={<ProtectedRoute allowedRoles={["admin"]}><AppLayout><AdminStaffPage /></AppLayout></ProtectedRoute>} />
      <Route path="/admin/devices" element={<ProtectedRoute allowedRoles={["admin"]}><AppLayout><DevicesPage /></AppLayout></ProtectedRoute>} />
      <Route path="/admin/slots" element={<ProtectedRoute allowedRoles={["admin"]}><AppLayout><AdminSlotsPage /></AppLayout></ProtectedRoute>} />

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
