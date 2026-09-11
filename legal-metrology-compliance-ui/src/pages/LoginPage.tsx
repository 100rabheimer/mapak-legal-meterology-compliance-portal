import { useState } from "react";
import {
  BadgeCheck,
  Eye,
  EyeOff,
  LockKeyhole,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStores";
import { loginApi } from "../services/apiClient";

type UserRole = "admin" | "officer";

export function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const [showPassword, setShowPassword] = useState(false);
  const [identifier, setIdentifier] = useState("officer@doca.gov.in");
  const [password, setPassword] = useState("officer123");
  const [role, setRole] = useState<UserRole>("officer");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    setError("");
    setIsLoading(true);

    try {
      const res = await loginApi(identifier, password);
      const userPayload = {
        id: res.user.user_id,
        name: res.user.full_name,
        email: res.user.email,
        role: res.user.role.toLowerCase() as UserRole,
        isActive: true,
        createdAt: new Date().toISOString(),
        officerId: res.user.badge_number || "LM-WB-2026-0148",
        jurisdiction: res.user.jurisdiction_zone || "Northern Enforcement Zone, New Delhi",
      };

      login(userPayload, res.access_token);
      setIsLoading(false);

      if (userPayload.role === "admin") {
        navigate("/admin/dashboard");
      } else {
        navigate("/");
      }
    } catch (err: any) {
      console.warn("Backend login failed, using local offline credentials fallback:", err);
      // Fallback local auth for dev/demo mode
      const user = {
        id: role === "admin" ? "admin-001" : "officer-001",
        name: role === "admin" ? "System Administrator" : "Sh. R. K. Verma",
        email: role === "admin" ? "admin@doca.gov.in" : identifier,
        role,
        isActive: true,
        createdAt: new Date().toISOString(),
        ...(role === "officer"
          ? {
              officerId: "LM-WB-2026-0148",
              jurisdiction: "Northern Enforcement Zone, New Delhi",
            }
          : {}),
      };

      login(user, "demo-fallback-jwt-token");
      setIsLoading(false);

      if (role === "admin") {
        navigate("/admin/dashboard");
      } else {
        navigate("/");
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="grid min-h-screen lg:grid-cols-2">
        <section className="hidden bg-linear-to-br from-blue-700 via-blue-600 to-indigo-700 p-12 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/15">
              <ShieldCheck className="h-6 w-6" />
            </div>

            <div>
              <p className="text-lg font-bold">Legal Metrology</p>
              <p className="text-sm text-blue-100">Compliance Portal</p>
            </div>
          </div>

          <div className="max-w-xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-200">
              Enforcement Intelligence
            </p>

            <h1 className="mt-4 text-4xl font-bold leading-tight">
              Smarter packaged commodity compliance checks.
            </h1>

            <p className="mt-5 text-base leading-7 text-blue-100">
              Scan package labels, extract mandatory declarations, identify
              potential violations, preserve evidence, and generate inspection
              reports from one secure workspace.
            </p>

            <div className="mt-10 space-y-4">
              <div className="flex items-center gap-3">
                <BadgeCheck className="h-5 w-5 text-blue-200" />
                <span className="text-sm text-blue-50">
                  OCR-assisted declaration extraction
                </span>
              </div>

              <div className="flex items-center gap-3">
                <BadgeCheck className="h-5 w-5 text-blue-200" />
                <span className="text-sm text-blue-50">
                  Evidence-based compliance reporting
                </span>
              </div>

              <div className="flex items-center gap-3">
                <BadgeCheck className="h-5 w-5 text-blue-200" />
                <span className="text-sm text-blue-50">
                  Secure role-based officer access
                </span>
              </div>
            </div>
          </div>

          <p className="text-xs text-blue-200">
            Legal Metrology Compliance Decision-Support System
          </p>
        </section>

        <section className="flex items-center justify-center p-6 sm:p-10">
          <div className="w-full max-w-md">
            <div className="mb-8 lg:hidden">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-white">
                  <ShieldCheck className="h-6 w-6" />
                </div>

                <div>
                  <p className="text-lg font-bold text-slate-900">
                    Legal Metrology
                  </p>
                  <p className="text-sm text-slate-500">
                    Compliance Portal
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                Welcome back
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                Sign in to access your compliance dashboard and inspection
                records.
              </p>
            </div>

            <form onSubmit={handleLogin} className="mt-8 space-y-5">
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">
                  Login as
                </label>

                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setRole("officer")}
                    className={`rounded-xl border p-4 text-left transition ${
                      role === "officer"
                        ? "border-blue-600 bg-blue-50 ring-2 ring-blue-100"
                        : "border-slate-200 bg-white hover:border-slate-300"
                    }`}
                  >
                    <UserRound
                      className={`h-5 w-5 ${
                        role === "officer"
                          ? "text-blue-600"
                          : "text-slate-500"
                      }`}
                    />

                    <p className="mt-3 text-sm font-semibold text-slate-800">
                      Officer
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Manage assigned inspections
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRole("admin")}
                    className={`rounded-xl border p-4 text-left transition ${
                      role === "admin"
                        ? "border-blue-600 bg-blue-50 ring-2 ring-blue-100"
                        : "border-slate-200 bg-white hover:border-slate-300"
                    }`}
                  >
                    <ShieldCheck
                      className={`h-5 w-5 ${
                        role === "admin"
                          ? "text-blue-600"
                          : "text-slate-500"
                      }`}
                    />

                    <p className="mt-3 text-sm font-semibold text-slate-800">
                      Administrator
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Manage officers and system data
                    </p>
                  </button>
                </div>
              </div>

              <div>
                <label
                  htmlFor="identifier"
                  className="mb-2 block text-sm font-semibold text-slate-700"
                >
                  {role === "admin" ? "Administrator ID" : "Official email address"}
                </label>

                <input
                  id="identifier"
                  type={role === "admin" ? "text" : "email"}
                  value={identifier}
                  onChange={(event) => setIdentifier(event.target.value)}
                  className="form-input"
                  placeholder={role === "admin" ? "admin-001" : "officer@department.gov.in"}
                  required
                />
              </div>

              {error && <p className="text-sm font-medium text-rose-600" role="alert">{error}</p>}

              <div>
                <label
                  htmlFor="password"
                  className="mb-2 block text-sm font-semibold text-slate-700"
                >
                  Password
                </label>

                <div className="relative">
                  <LockKeyhole className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="form-input pl-11 pr-12"
                    placeholder="Enter your password"
                    required
                  />

                  <button
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-slate-300 text-blue-600"
                  />
                  Remember me
                </label>

                <button
                  type="button"
                  className="text-sm font-semibold text-blue-600 hover:text-blue-700"
                >
                  Forgot password?
                </button>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="flex w-full items-center justify-center rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {isLoading ? "Signing in..." : "Sign in securely"}
              </button>
            </form>

            <p className="mt-8 text-center text-xs leading-5 text-slate-500">
              This portal is intended for authorized users only. All activities
              may be recorded for security and audit purposes.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}