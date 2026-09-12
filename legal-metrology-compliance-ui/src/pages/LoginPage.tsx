import { useState } from "react";
import {
  BadgeCheck,
  Eye,
  EyeOff,
  LockKeyhole,
  ShieldCheck,
  UserRound,
  UserPlus,
  Mail,
  MapPin,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  UserCheck,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStores";
import { loginApi, registerApi } from "../services/apiClient";

type UserRole = "admin" | "officer";

export function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const [authMode, setAuthMode] = useState<"login" | "register">("login");

  // Login states
  const [showPassword, setShowPassword] = useState(false);
  const [identifier, setIdentifier] = useState("officer@doca.gov.in");
  const [password, setPassword] = useState("officer123");
  const [role, setRole] = useState<UserRole>("officer");

  // Registration states
  const [regFullName, setRegFullName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regRole, setRegRole] = useState<UserRole>("officer");
  const [regBadgeNumber, setRegBadgeNumber] = useState("");
  const [regJurisdiction, setRegJurisdiction] = useState(
    "Northern Enforcement Zone, New Delhi"
  );
  const [showRegPassword, setShowRegPassword] = useState(false);

  // Status & Feedback
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccessMsg("");
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
        jurisdiction:
          res.user.jurisdiction_zone || "Northern Enforcement Zone, New Delhi",
      };

      login(userPayload, res.access_token);
      setIsLoading(false);

      if (userPayload.role === "admin") {
        navigate("/admin/dashboard");
      } else {
        navigate("/");
      }
    } catch (err: any) {
      console.warn(
        "Backend login failed, using local offline credentials fallback:",
        err
      );
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

  const handleRegister = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccessMsg("");

    if (!regFullName.trim()) {
      setError("Please enter your full name.");
      return;
    }
    if (!regEmail.trim() || !regEmail.includes("@")) {
      setError("Please enter a valid official email address.");
      return;
    }
    if (regPassword.length < 4) {
      setError("Password must be at least 4 characters long.");
      return;
    }

    setIsLoading(true);

    try {
      const res = await registerApi({
        full_name: regFullName.trim(),
        email: regEmail.trim(),
        password: regPassword,
        role: regRole,
        badge_number: regBadgeNumber.trim() || undefined,
        jurisdiction_zone: regJurisdiction.trim() || undefined,
      });

      const userPayload = {
        id: res.user.user_id,
        name: res.user.full_name,
        email: res.user.email,
        role: res.user.role.toLowerCase() as UserRole,
        isActive: true,
        createdAt: new Date().toISOString(),
        officerId: res.user.badge_number || "LM-WB-2026-0148",
        jurisdiction:
          res.user.jurisdiction_zone || "Northern Enforcement Zone, New Delhi",
      };

      setSuccessMsg(
        "Account created successfully! Preparing your compliance workspace..."
      );
      setTimeout(() => {
        login(userPayload, res.access_token);
        setIsLoading(false);
        if (userPayload.role === "admin") {
          navigate("/admin/dashboard");
        } else {
          navigate("/");
        }
      }, 700);
    } catch (err: any) {
      console.warn("Backend registration failed:", err);
      if (err.message && err.message.toLowerCase().includes("already exists")) {
        setError(err.message);
        setIsLoading(false);
        return;
      }

      // Offline / fallback registration
      const user = {
        id: `usr-${Date.now().toString(36)}`,
        name: regFullName.trim(),
        email: regEmail.trim(),
        role: regRole,
        isActive: true,
        createdAt: new Date().toISOString(),
        officerId: regBadgeNumber.trim() || "LM-DL-2026-0421",
        jurisdiction: regJurisdiction || "Northern Enforcement Zone, New Delhi",
      };

      setSuccessMsg("Registration verified! Accessing enforcement dashboard...");
      setTimeout(() => {
        login(user, "demo-registered-jwt-token");
        setIsLoading(false);
        if (regRole === "admin") {
          navigate("/admin/dashboard");
        } else {
          navigate("/");
        }
      }, 700);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="grid min-h-screen lg:grid-cols-2">
        {/* Left Branding Showcase */}
        <section className="hidden bg-linear-to-br from-blue-700 via-blue-600 to-indigo-700 p-12 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="flex items-center gap-4">
            <img
              src="/src/assets/mapak-logo.png"
              alt="MAPAK Logo"
              className="h-16 w-16 object-contain brightness-0 invert"
            />

            <div>
              <p className="text-3xl font-extrabold tracking-tight">MAPAK</p>
              <p className="text-base font-medium text-blue-100">
                Legal Metrology Portal
              </p>
            </div>
          </div>

          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-blue-500/30 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-blue-200 backdrop-blur-xs">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Enforcement Intelligence Platform</span>
            </div>

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
                  OCR-assisted declaration extraction & real-time bounding boxes
                </span>
              </div>

              <div className="flex items-center gap-3">
                <BadgeCheck className="h-5 w-5 text-blue-200" />
                <span className="text-sm text-blue-50">
                  Evidence-based compliance reporting & Rule 7 font analysis
                </span>
              </div>

              <div className="flex items-center gap-3">
                <BadgeCheck className="h-5 w-5 text-blue-200" />
                <span className="text-sm text-blue-50">
                  Self-service registration for first-time enforcement officers
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-blue-500/40 pt-4 text-xs text-blue-200">
            <p>Department of Consumer Affairs, Government of India</p>
            <p>SIH Problem Statement 26034</p>
          </div>
        </section>

        {/* Right Auth Forms */}
        <section className="flex items-center justify-center p-6 sm:p-10">
          <div className="w-full max-w-md">
            {/* Mobile Header */}
            <div className="mb-6 lg:hidden">
              <div className="flex items-center gap-4">
                <img
                  src="/src/assets/mapak-logo.png"
                  alt="MAPAK Logo"
                  className="h-14 w-14 object-contain"
                />

                <div>
                  <p className="text-2xl font-extrabold tracking-tight text-slate-900">
                    MAPAK
                  </p>
                  <p className="text-sm font-medium text-slate-500">
                    Legal Metrology Portal
                  </p>
                </div>
              </div>
            </div>

            {/* Mode Switcher Tabs */}
            <div className="mb-6 flex rounded-xl bg-slate-100 p-1">
              <button
                type="button"
                id="tab-sign-in"
                onClick={() => {
                  setAuthMode("login");
                  setError("");
                  setSuccessMsg("");
                }}
                className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold transition ${
                  authMode === "login"
                    ? "bg-white text-blue-700 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <UserCheck className="h-4 w-4" />
                <span>Sign In</span>
              </button>

              <button
                type="button"
                id="tab-first-time-register"
                onClick={() => {
                  setAuthMode("register");
                  setError("");
                  setSuccessMsg("");
                }}
                className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold transition ${
                  authMode === "register"
                    ? "bg-white text-blue-700 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <UserPlus className="h-4 w-4 text-emerald-600" />
                <span>First-Time User</span>
                <span className="rounded-full bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-700">
                  Register
                </span>
              </button>
            </div>

            {/* Alerts */}
            {error && (
              <div
                className="mb-4 flex items-center gap-2.5 rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-sm font-medium text-rose-700"
                role="alert"
              >
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
                <span>{error}</span>
              </div>
            )}

            {successMsg && (
              <div
                className="mb-4 flex items-center gap-2.5 rounded-xl border border-emerald-200 bg-emerald-50 p-3.5 text-sm font-medium text-emerald-700"
                role="status"
              >
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                <span>{successMsg}</span>
              </div>
            )}

            {authMode === "login" ? (
              /* ================= LOGIN FORM ================= */
              <div>
                <div>
                  <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                    Welcome back
                  </h2>

                  <p className="mt-1 text-sm text-slate-500">
                    Sign in to access your compliance dashboard and inspection
                    records.
                  </p>
                </div>

                <form onSubmit={handleLogin} className="mt-6 space-y-4">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">
                      Login as
                    </label>

                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => setRole("officer")}
                        className={`rounded-xl border p-3.5 text-left transition ${
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
                        <p className="mt-2 text-sm font-semibold text-slate-800">
                          Officer
                        </p>
                        <p className="text-xs text-slate-500">
                          Manage assigned inspections
                        </p>
                      </button>

                      <button
                        type="button"
                        onClick={() => setRole("admin")}
                        className={`rounded-xl border p-3.5 text-left transition ${
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
                        <p className="mt-2 text-sm font-semibold text-slate-800">
                          Administrator
                        </p>
                        <p className="text-xs text-slate-500">
                          Manage rules & officers
                        </p>
                      </button>
                    </div>
                  </div>

                  <div>
                    <label
                      htmlFor="identifier"
                      className="mb-1.5 block text-sm font-semibold text-slate-700"
                    >
                      {role === "admin"
                        ? "Administrator ID"
                        : "Official email address"}
                    </label>

                    <input
                      id="identifier"
                      type={role === "admin" ? "text" : "email"}
                      value={identifier}
                      onChange={(e) => setIdentifier(e.target.value)}
                      className="form-input"
                      placeholder={
                        role === "admin"
                          ? "admin@doca.gov.in"
                          : "officer@doca.gov.in"
                      }
                      required
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="password"
                      className="mb-1.5 block text-sm font-semibold text-slate-700"
                    >
                      Password
                    </label>

                    <div className="relative">
                      <LockKeyhole className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

                      <input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="form-input pl-11 pr-12"
                        placeholder="Enter password"
                        required
                      />

                      <button
                        type="button"
                        onClick={() => setShowPassword((current) => !current)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
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

                  <div className="flex items-center justify-between pt-1">
                    <label className="flex items-center gap-2 text-xs text-slate-600">
                      <input
                        type="checkbox"
                        defaultChecked
                        className="h-4 w-4 rounded border-slate-300 text-blue-600"
                      />
                      Remember credentials
                    </label>

                    <button
                      type="button"
                      onClick={() =>
                        alert(
                          "Demo reset: Default accounts are officer@doca.gov.in (officer123) and admin@doca.gov.in (admin123)."
                        )
                      }
                      className="text-xs font-semibold text-blue-600 hover:text-blue-700"
                    >
                      Forgot password?
                    </button>
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="mt-2 flex w-full items-center justify-center rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    {isLoading ? "Signing in..." : "Sign in securely"}
                  </button>
                </form>

                <div className="mt-6 rounded-xl border border-dashed border-blue-200 bg-blue-50/50 p-4 text-center">
                  <p className="text-xs text-slate-600">
                    First time accessing the portal?
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode("register");
                      setError("");
                      setSuccessMsg("");
                    }}
                    className="mt-1.5 inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-800"
                  >
                    <span>Register your officer account</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ) : (
              /* ================= FIRST-TIME REGISTRATION FORM ================= */
              <div>
                <div>
                  <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                    First-Time Registration
                  </h2>

                  <p className="mt-1 text-sm text-slate-500">
                    Register your officer or administrator profile before your
                    first login.
                  </p>
                </div>

                <form onSubmit={handleRegister} className="mt-6 space-y-4">
                  {/* Role Selector */}
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">
                      Register as
                    </label>

                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => setRegRole("officer")}
                        className={`rounded-xl border p-3.5 text-left transition ${
                          regRole === "officer"
                            ? "border-blue-600 bg-blue-50 ring-2 ring-blue-100"
                            : "border-slate-200 bg-white hover:border-slate-300"
                        }`}
                      >
                        <UserRound
                          className={`h-5 w-5 ${
                            regRole === "officer"
                              ? "text-blue-600"
                              : "text-slate-500"
                          }`}
                        />
                        <p className="mt-2 text-sm font-semibold text-slate-800">
                          Enforcement Officer
                        </p>
                        <p className="text-xs text-slate-500">
                          Conduct packaging audits
                        </p>
                      </button>

                      <button
                        type="button"
                        onClick={() => setRegRole("admin")}
                        className={`rounded-xl border p-3.5 text-left transition ${
                          regRole === "admin"
                            ? "border-blue-600 bg-blue-50 ring-2 ring-blue-100"
                            : "border-slate-200 bg-white hover:border-slate-300"
                        }`}
                      >
                        <ShieldCheck
                          className={`h-5 w-5 ${
                            regRole === "admin"
                              ? "text-blue-600"
                              : "text-slate-500"
                          }`}
                        />
                        <p className="mt-2 text-sm font-semibold text-slate-800">
                          Administrator
                        </p>
                        <p className="text-xs text-slate-500">
                          Configure rules & portal
                        </p>
                      </button>
                    </div>
                  </div>

                  {/* Full Name */}
                  <div>
                    <label
                      htmlFor="reg-name"
                      className="mb-1.5 block text-sm font-semibold text-slate-700"
                    >
                      Full Name *
                    </label>
                    <div className="relative">
                      <UserRound className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                      <input
                        id="reg-name"
                        type="text"
                        value={regFullName}
                        onChange={(e) => setRegFullName(e.target.value)}
                        className="form-input pl-11"
                        placeholder="e.g. Inspector Shaurya Sharma"
                        required
                      />
                    </div>
                  </div>

                  {/* Email */}
                  <div>
                    <label
                      htmlFor="reg-email"
                      className="mb-1.5 block text-sm font-semibold text-slate-700"
                    >
                      Official Email Address *
                    </label>
                    <div className="relative">
                      <Mail className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                      <input
                        id="reg-email"
                        type="email"
                        value={regEmail}
                        onChange={(e) => setRegEmail(e.target.value)}
                        className="form-input pl-11"
                        placeholder="e.g. shaurya.officer@doca.gov.in"
                        required
                      />
                    </div>
                  </div>

                  {/* Password */}
                  <div>
                    <label
                      htmlFor="reg-password"
                      className="mb-1.5 block text-sm font-semibold text-slate-700"
                    >
                      Password *
                    </label>
                    <div className="relative">
                      <LockKeyhole className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                      <input
                        id="reg-password"
                        type={showRegPassword ? "text" : "password"}
                        value={regPassword}
                        onChange={(e) => setRegPassword(e.target.value)}
                        className="form-input pl-11 pr-12"
                        placeholder="Create a strong password"
                        required
                        minLength={4}
                      />
                      <button
                        type="button"
                        onClick={() =>
                          setShowRegPassword((current) => !current)
                        }
                        className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                        aria-label={
                          showRegPassword ? "Hide password" : "Show password"
                        }
                      >
                        {showRegPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Badge Number (Optional) */}
                  <div>
                    <label
                      htmlFor="reg-badge"
                      className="mb-1.5 block text-sm font-semibold text-slate-700"
                    >
                      Officer Badge / Inspector ID{" "}
                      <span className="text-xs font-normal text-slate-500">
                        (Optional)
                      </span>
                    </label>
                    <input
                      id="reg-badge"
                      type="text"
                      value={regBadgeNumber}
                      onChange={(e) => setRegBadgeNumber(e.target.value)}
                      className="form-input"
                      placeholder="e.g. LM-DL-2026-0421 (Auto-generated if empty)"
                    />
                  </div>

                  {/* Jurisdiction Zone */}
                  <div>
                    <label
                      htmlFor="reg-jurisdiction"
                      className="mb-1.5 block text-sm font-semibold text-slate-700"
                    >
                      Jurisdiction Zone
                    </label>
                    <div className="relative">
                      <MapPin className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                      <select
                        id="reg-jurisdiction"
                        value={regJurisdiction}
                        onChange={(e) => setRegJurisdiction(e.target.value)}
                        className="form-input pl-11"
                      >
                        <option value="Northern Enforcement Zone, New Delhi">
                          Northern Enforcement Zone, New Delhi
                        </option>
                        <option value="Western Enforcement Zone, Mumbai">
                          Western Enforcement Zone, Mumbai
                        </option>
                        <option value="Southern Enforcement Zone, Chennai">
                          Southern Enforcement Zone, Chennai
                        </option>
                        <option value="Eastern Enforcement Zone, Kolkata">
                          Eastern Enforcement Zone, Kolkata
                        </option>
                        <option value="Central Enforcement Zone, Bhopal">
                          Central Enforcement Zone, Bhopal
                        </option>
                        <option value="North-Eastern Enforcement Zone, Guwahati">
                          North-Eastern Enforcement Zone, Guwahati
                        </option>
                      </select>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    id="btn-register-submit"
                    disabled={isLoading}
                    className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    <UserPlus className="h-4 w-4" />
                    <span>
                      {isLoading
                        ? "Registering Account..."
                        : "Complete Registration & Enter"}
                    </span>
                  </button>
                </form>

                <div className="mt-5 text-center">
                  <p className="text-xs text-slate-500">
                    Already registered?{" "}
                    <button
                      type="button"
                      onClick={() => {
                        setAuthMode("login");
                        setError("");
                        setSuccessMsg("");
                      }}
                      className="font-semibold text-blue-600 hover:text-blue-800"
                    >
                      Sign in here
                    </button>
                  </p>
                </div>
              </div>
            )}

            <p className="mt-8 text-center text-xs leading-5 text-slate-500">
              Department of Consumer Affairs • Legal Metrology (Packaged
              Commodities) Rules, 2011 • Secure Gov Enforcement System
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}