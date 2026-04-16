import { Link, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { Eye, EyeOff } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

const SignInPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const { isLoggedIn, login } = useAuth();

  // Redirect if already logged in
  useEffect(() => {
    if (isLoggedIn) navigate("/dashboard");
  }, [isLoggedIn, navigate]);

  const validateForm = () => {
    if (!username.trim()) return "Username is required";
    if (!password.trim()) return "Password is required";
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/auth/signin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json(); // ✅ only once

      if (!res.ok) {
        setError(data.detail || "Invalid credentials");
        return;
      }

      // Save token via context
      login(data.access_token);

      // Optional: also store user info if backend sends it
      // localStorage.setItem("user", JSON.stringify(data.user));

      navigate("/dashboard");
    } catch (err) {
      setError("Server not reachable. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen fade-in bg-gray-50">
      <div className="card max-w-md w-full text-left shadow-lg">
        <h1 className="text-3xl font-bold mb-2 text-indigo-600">
          Welcome Back
        </h1>
        <p className="text-gray-500 mb-6">
          Sign in to access your dashboard.
        </p>

        <form className="space-y-5" onSubmit={handleSubmit}>
          {/* Username */}
          <div>
            <label className="block mb-2 font-medium">Username</label>
            <input
              type="text"
              placeholder="john_doe"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="input"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block mb-2 font-medium">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="input pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <p className="text-red-500 text-sm bg-red-100 p-2 rounded">
              {error}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="btn w-full mt-4 text-base disabled:opacity-50"
          >
            {loading ? "Signing in..." : "🔑 Sign In"}
          </button>
        </form>

        <p className="text-center text-gray-500 mt-6">
          Don't have an account?{" "}
          <Link
            to="/signup"
            className="text-indigo-500 hover:underline font-medium"
          >
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
};

export default SignInPage;