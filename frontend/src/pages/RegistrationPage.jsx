import React, { useState } from "react";

const RegistrationPage = () => {
  const [emails, setEmails] = useState({
    email1: "",
    email2: "",
  });

  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const validateEmails = () => {
    if (!emails.email1) return "Primary email is required";

    if (emails.email1 === emails.email2 && emails.email2 !== "") {
      return "Both emails cannot be the same";
    }

    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitted(false);

    const validationError = validateEmails();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);

    try {
      const token = localStorage.getItem("token"); // ✅ important

      const res = await fetch("http://localhost:8000/auth/register-emails", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`, // ✅ send token
        },
        body: JSON.stringify({
          email1: emails.email1,
          email2: emails.email2 || null, // send null if empty
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Failed to register emails");
        return;
      }

      setSubmitted(true);
      setEmails({ email1: "", email2: "" });
    } catch (err) {
      setError("Server not reachable. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto card fade-in">
      <h1 className="text-3xl font-bold mb-4 text-blue-600 dark:text-blue-300">
        Register Alternate Emails 📧
      </h1>

      <p className="mb-6 opacity-80">
        Add up to two alternate email addresses for emergency alerts.
      </p>

      {/* Success */}
      {submitted && (
        <div className="p-3 bg-green-100 border-l-4 border-green-500 rounded-md mb-4">
          ✅ Emails successfully registered!
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-3 bg-red-100 border-l-4 border-red-500 rounded-md mb-4">
          ❌ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Email 1 */}
        <div>
          <label className="block text-sm font-semibold mb-1">
            Alternate Email 1 (Required)
          </label>
          <input
            type="email"
            required
            placeholder="primary@example.com"
            className="w-full p-2 border rounded-md focus:ring focus:ring-blue-200"
            value={emails.email1}
            onChange={(e) =>
              setEmails({ ...emails, email1: e.target.value })
            }
          />
        </div>

        {/* Email 2 */}
        <div>
          <label className="block text-sm font-semibold mb-1">
            Alternate Email 2 (Optional)
          </label>
          <input
            type="email"
            placeholder="secondary@example.com"
            className="w-full p-2 border rounded-md focus:ring focus:ring-blue-200"
            value={emails.email2}
            onChange={(e) =>
              setEmails({ ...emails, email2: e.target.value })
            }
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="btn w-full bg-blue-600 text-white p-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Saving..." : "Save Emails"}
        </button>
      </form>
    </div>
  );
};

export default RegistrationPage;