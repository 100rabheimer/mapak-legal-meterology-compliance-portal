import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { LoginPage } from "./pages/LoginPage";
import { NewInspectionPage } from "./pages/NewInspectionPage";
import { OfficerDashboardPage } from "./pages/OfficerDashboardPage";
import { OfficerManagementPage } from "./pages/OfficerManagementPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ResultPage } from "./pages/ResultPage";
import { ReviewPage } from "./pages/ReviewPage";
import { RulesPage } from "./pages/RulesPage";
import { MyInspectionsPage } from "./pages/MyInspectionsPage";
import { ProductsPage } from "./pages/ProductsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { useAuthStore } from "./stores/authStores";

function App() {
  const restoreSession = useAuthStore((state) => state.restoreSession);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/"
        element={
          <ProtectedRoute allowedRoles={["officer", "admin"]}>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardLanding />} />

        <Route path="inspections/new" element={<NewInspectionPage />} />

        <Route path="inspections/demo/review" element={<ReviewPage />} />

        <Route path="inspections/demo/result" element={<ResultPage />} />

        <Route path="analytics" element={<AnalyticsPage />} />

        <Route path="settings" element={<ProfilePage />} />

        <Route path="my-inspections" element={<MyInspectionsPage />} />

        <Route path="products" element={<ProductsPage />} />

        <Route path="reports" element={<ReportsPage />} />

        <Route path="rules" element={<RulesPage />} />

        <Route
          path="admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <AdminDashboardPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="admin/officers"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <OfficerManagementPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="/unauthorized" element={<Navigate to="/" replace />} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function DashboardLanding() {
  const user = useAuthStore((state) => state.user);

  if (user?.role === "admin") {
    return <Navigate to="/admin/dashboard" replace />;
  }

  return <OfficerDashboardPage />;
}

export default App;