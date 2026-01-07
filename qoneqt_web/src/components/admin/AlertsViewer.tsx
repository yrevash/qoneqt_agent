"use client";

import { useState, useEffect } from "react";
import { adminApi, Alert } from "@/lib/admin-api";

export default function AlertsViewer() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string | undefined>();
  const [statusFilter, setStatusFilter] = useState<string | undefined>();

  useEffect(() => {
    loadAlerts();
    // Auto-refresh every 15 seconds
    const interval = setInterval(loadAlerts, 15000);
    return () => clearInterval(interval);
  }, [severityFilter, statusFilter]);

  const loadAlerts = async () => {
    try {
      const response = await adminApi.alerts.list(severityFilter, statusFilter);
      setAlerts(response.data);
    } catch (err) {
      console.error("Failed to load alerts:", err);
    } finally {
      setLoading(false);
    }
  };

  const acknowledgeAlert = async (alertId: string) => {
    const notes = prompt("Enter acknowledgment notes (optional):");
    if (notes === null) return; // User cancelled

    try {
      await adminApi.alerts.acknowledge(alertId, notes || undefined);
      loadAlerts();
    } catch (err: any) {
      alert(`Failed to acknowledge: ${err.message}`);
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors = {
      critical: "bg-red-100 border-red-500 text-red-800",
      warning: "bg-yellow-100 border-yellow-500 text-yellow-800",
      info: "bg-blue-100 border-blue-500 text-blue-800",
    };
    return colors[severity as keyof typeof colors] || "bg-gray-100 border-gray-500 text-gray-800";
  };

  const getSeverityIcon = (severity: string) => {
    const icons = {
      critical: "🚨",
      warning: "⚠️",
      info: "ℹ️",
    };
    return icons[severity as keyof typeof icons] || "📢";
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Alerts</h1>
          <p className="text-gray-600 mt-1">Real-time system alerts and notifications</p>
        </div>
        <button
          onClick={loadAlerts}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Severity
          </label>
          <div className="flex gap-2">
            {[
              { value: undefined, label: "All" },
              { value: "critical", label: "Critical" },
              { value: "warning", label: "Warning" },
              { value: "info", label: "Info" },
            ].map((item) => (
              <button
                key={item.label}
                onClick={() => setSeverityFilter(item.value)}
                className={`px-4 py-2 rounded-lg transition ${
                  severityFilter === item.value
                    ? "bg-blue-500 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <div className="flex gap-2">
            {[
              { value: undefined, label: "All" },
              { value: "firing", label: "Active" },
              { value: "resolved", label: "Resolved" },
            ].map((item) => (
              <button
                key={item.label}
                onClick={() => setStatusFilter(item.value)}
                className={`px-4 py-2 rounded-lg transition ${
                  statusFilter === item.value
                    ? "bg-blue-500 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-8">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
            <div className="text-4xl mb-2">✅</div>
            <div className="text-lg font-semibold text-green-800">No Alerts</div>
            <div className="text-green-600">All systems operating normally</div>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`border-l-4 p-4 rounded-lg shadow ${getSeverityColor(
                alert.severity
              )}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getSeverityIcon(alert.severity)}</span>
                    <div>
                      <h3 className="font-bold text-lg">{alert.alert_name}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="px-2 py-1 text-xs rounded-full bg-white bg-opacity-50">
                          {alert.severity.toUpperCase()}
                        </span>
                        <span className="px-2 py-1 text-xs rounded-full bg-white bg-opacity-50">
                          {alert.status.toUpperCase()}
                        </span>
                        {alert.acknowledged && (
                          <span className="px-2 py-1 text-xs rounded-full bg-green-500 text-white">
                            ✓ Acknowledged
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {alert.summary && (
                    <p className="mt-2 font-semibold">{alert.summary}</p>
                  )}

                  {alert.description && (
                    <p className="mt-1 text-sm opacity-90">{alert.description}</p>
                  )}

                  <div className="mt-3 text-xs opacity-75">
                    <div>Started: {new Date(alert.starts_at).toLocaleString()}</div>
                    {alert.ends_at && (
                      <div>Ended: {new Date(alert.ends_at).toLocaleString()}</div>
                    )}
                    {!alert.ends_at && alert.status === "firing" && (
                      <div className="text-red-600 font-semibold">
                        Duration: {Math.floor(
                          (Date.now() - new Date(alert.starts_at).getTime()) / 1000 / 60
                        )}{" "}
                        minutes
                      </div>
                    )}
                  </div>
                </div>

                <div className="ml-4">
                  {!alert.acknowledged && alert.status === "firing" && (
                    <button
                      onClick={() => acknowledgeAlert(alert.id)}
                      className="px-4 py-2 bg-white bg-opacity-50 hover:bg-opacity-75 rounded-lg transition font-semibold"
                    >
                      ✓ Acknowledge
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
