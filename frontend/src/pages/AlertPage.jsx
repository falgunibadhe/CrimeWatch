import React, { useEffect, useState } from "react";

const AlertItem = ({ alert }) => {
  const isDanger = alert.danger_status !== "Safe";

  return (
    <div className={`card fade-in border-l-8 ${
      isDanger ? "border-red-500 bg-red-50 dark:bg-red-900/30" : "border-gray-300"
    }`}>
      <p><strong>Status:</strong> {alert.danger_status}</p>
      <p><strong>Camera:</strong> {alert.camera_id}</p>
      <p><strong>Time:</strong> {alert.timestamp}</p>

      <p>
        <strong>Violence:</strong> {alert.violence_label} 
        {" "}({(alert.violence_prob * 100).toFixed(1)}%)
      </p>

      <p>
        <strong>Weapon:</strong> {alert.weapon_detected ? "Yes" : "No"}
      </p>

      {/* Snapshot */}
      {alert.snapshot_path && (
        <img
          src={`http://localhost:8000/snapshot/${alert.snapshot_path.split("\\").pop()}`}
          alt="snapshot"
          className="mt-3 rounded-lg max-h-60 object-cover border"
        />
      )}
    </div>
  );
};

const AlertPage = () => {
  const [alerts, setAlerts] = useState([]);

  const fetchAlerts = async () => {
    try {
      const res = await fetch("http://localhost:8000/alerts");
      if (!res.ok) return;

      const data = await res.json();

      const filtered = (data || []).filter((a) => {
        const d = (a.danger_status || "").toLowerCase();
        return d.includes("weapon") || d.includes("violence");
      });

      setAlerts(filtered);
    } catch (err) {
      console.error("Error fetching alerts", err);
    }
  };

  useEffect(() => {
    fetchAlerts();

    // 🔁 Auto refresh every 5 seconds
    const interval = setInterval(fetchAlerts, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fade-in max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-red-600 text-center">
        Crime Alerts Dashboard
      </h1>

      {alerts.length === 0 ? (
        <p className="text-gray-500 text-center">No alerts yet.</p>
      ) : (
        <div className="space-y-4">
          {alerts.map((a, index) => (
            <AlertItem key={index} alert={a} />
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertPage;