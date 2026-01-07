"use client";

import { useState, useEffect } from "react";
import { adminApi, AdminStats } from "@/lib/admin-api";

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
    // Refresh every 30 seconds
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const response = await adminApi.health.stats();
      setStats(response.data);
      setError(null);
    } catch (err: any) {
      console.error("Admin stats error:", err);
      const errorMessage = err.response?.data?.detail || err.message || "Unknown error";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          Error loading stats: {error}
        </div>
      </div>
    );
  }

  const healthColor = {
    healthy: "bg-green-500",
    warning: "bg-yellow-500",
    degraded: "bg-orange-500",
    critical: "bg-red-500",
  }[stats?.system_health || "healthy"];

  const healthText = {
    healthy: "All Systems Operational",
    warning: "Minor Issues Detected",
    degraded: "System Degraded",
    critical: "Critical Issues",
  }[stats?.system_health || "healthy"];

  return (
    <div className="p-6 space-y-6 bg-[#0a0a0a] min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Control Center</h1>
          <p className="text-gray-400 mt-1">Monitor and manage all agents, costs, and system configuration</p>
        </div>
        <button
          onClick={loadStats}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition"
        >
          🔄 Refresh
        </button>
      </div>

      {/* System Health Status */}
      <div className={`${healthColor} text-white p-6 rounded-lg shadow-lg border border-gray-700`}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">{healthText}</h2>
            <p className="mt-1 opacity-90">Last updated: {new Date().toLocaleTimeString()}</p>
          </div>
          <div className="text-5xl">
            {stats?.system_health === "healthy" ? "✅" : 
             stats?.system_health === "warning" ? "⚠️" : 
             stats?.system_health === "degraded" ? "🟠" : "🚨"}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Users */}
        <div className="bg-gray-900/50 border border-gray-700 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Agents</p>
              <p className="text-3xl font-bold text-white">{stats?.total_users || 0}</p>
            </div>
            <div className="text-4xl">👥</div>
          </div>
          <div className="mt-2 text-sm text-cyan-400">
            {stats?.active_users || 0} active now
          </div>
        </div>

        {/* Connections */}
        <div className="bg-gray-900/50 border border-gray-700 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Connections</p>
              <p className="text-3xl font-bold text-white">{stats?.total_connections || 0}</p>
            </div>
            <div className="text-4xl">🔗</div>
          </div>
          <div className="mt-2 text-sm text-yellow-400">
            {stats?.pending_connections || 0} pending
          </div>
        </div>

        {/* Alerts (24h) */}
        <div className="bg-gray-900/50 border border-gray-700 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Alerts (24h)</p>
              <p className="text-3xl font-bold text-white">{stats?.total_alerts_24h || 0}</p>
            </div>
            <div className="text-4xl">🔔</div>
          </div>
          <div className="mt-2 text-sm text-gray-400">
            {stats?.critical_alerts_active || 0} critical active
          </div>
        </div>

        {/* Critical Alerts */}
        <div className={`p-6 rounded-lg shadow border ${
          (stats?.critical_alerts_active || 0) > 0 
            ? "bg-red-900/30 border-red-500" 
            : "bg-gray-900/50 border-gray-700"
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Critical Alerts</p>
              <p className={`text-3xl font-bold ${
                (stats?.critical_alerts_active || 0) > 0 ? "text-red-400" : "text-white"
              }`}>
                {stats?.critical_alerts_active || 0}
              </p>
            </div>
            <div className="text-4xl">
              {(stats?.critical_alerts_active || 0) > 0 ? "🚨" : "✅"}
            </div>
          </div>
          <div className="mt-2 text-sm text-gray-400">
            Active critical issues
          </div>
        </div>
      </div>

      {/* Services Status */}
      <div className="bg-gray-900/50 border border-gray-700 p-6 rounded-lg shadow">
        <h3 className="text-xl font-bold text-white mb-4">Services Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(stats?.services_status || {}).map(([service, status]) => (
            <div
              key={service}
              className={`p-4 rounded-lg border-2 ${
                status === "healthy"
                  ? "border-green-500 bg-green-500/10"
                  : status === "degraded"
                  ? "border-yellow-500 bg-yellow-500/10"
                  : "border-red-500 bg-red-500/10"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold capitalize text-white">{service}</span>
                <span className="text-xl">
                  {status === "healthy" ? "✅" : status === "degraded" ? "⚠️" : "❌"}
                </span>
              </div>
              <div className="text-sm text-gray-400 mt-1 capitalize">{status}</div>
            </div>
          ))}
        </div>
      </div>

      {/* System Configuration & Tools */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Tools */}
        <div className="bg-gray-900/50 border border-gray-700 p-6 rounded-lg shadow">
          <h3 className="text-xl font-bold text-white mb-4">🔧 Quick Tools</h3>
          <div className="grid grid-cols-2 gap-3">
            <a
              href="http://localhost:8080/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-cyan-600/20 border border-cyan-500 rounded-lg hover:bg-cyan-600/30 transition text-center"
            >
              <div className="text-2xl mb-2">📚</div>
              <div className="font-semibold text-white text-sm">API Docs</div>
            </a>
            <a
              href="http://localhost:8081"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-blue-600/20 border border-blue-500 rounded-lg hover:bg-blue-600/30 transition text-center"
            >
              <div className="text-2xl mb-2">💾</div>
              <div className="font-semibold text-white text-sm">Database</div>
            </a>
            <a
              href="http://localhost:15672"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-purple-600/20 border border-purple-500 rounded-lg hover:bg-purple-600/30 transition text-center"
            >
              <div className="text-2xl mb-2">🐰</div>
              <div className="font-semibold text-white text-sm">RabbitMQ</div>
            </a>
            <a
              href="http://localhost:9090"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-orange-600/20 border border-orange-500 rounded-lg hover:bg-orange-600/30 transition text-center"
            >
              <div className="text-2xl mb-2">📊</div>
              <div className="font-semibold text-white text-sm">Prometheus</div>
            </a>
            <a
              href="http://localhost:3001"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-green-600/20 border border-green-500 rounded-lg hover:bg-green-600/30 transition text-center"
            >
              <div className="text-2xl mb-2">📈</div>
              <div className="font-semibold text-white text-sm">Grafana</div>
            </a>
          </div>
        </div>

        {/* System Configuration */}
        <div className="bg-gray-900/50 border border-gray-700 p-6 rounded-lg shadow">
          <h3 className="text-xl font-bold text-white mb-4">⚙️ System Configuration</h3>
          <div className="space-y-4">
            <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-600">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-300 font-semibold">Max Search Results</span>
                <input 
                  type="number" 
                  defaultValue="10"
                  className="w-20 px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white"
                />
              </div>
              <p className="text-xs text-gray-500">Number of users to search per query</p>
            </div>
            
            <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-600">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-300 font-semibold">API Cost per Request</span>
                <input 
                  type="number" 
                  step="0.001"
                  defaultValue="0.005"
                  className="w-24 px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white"
                />
              </div>
              <p className="text-xs text-gray-500">Cost in USD for LLM API calls</p>
            </div>
            
            <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-600">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-300 font-semibold">Agent Energy Decay</span>
                <input 
                  type="number" 
                  step="0.1"
                  defaultValue="1.0"
                  className="w-20 px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white"
                />
              </div>
              <p className="text-xs text-gray-500">Energy consumption rate per action</p>
            </div>

            <button className="w-full py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-semibold transition">
              Save Configuration
            </button>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-900/50 border border-gray-700 p-6 rounded-lg shadow">
        <h3 className="text-xl font-bold text-white mb-4">📋 Management Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="p-4 bg-yellow-600/20 border-2 border-yellow-500 rounded-lg hover:bg-yellow-600/30 transition text-center">
            <div className="text-3xl mb-2">🔔</div>
            <div className="font-semibold text-white">View Alerts</div>
          </button>
          <button className="p-4 bg-purple-600/20 border-2 border-purple-500 rounded-lg hover:bg-purple-600/30 transition text-center">
            <div className="text-3xl mb-2">📋</div>
            <div className="font-semibold text-white">Audit Logs</div>
          </button>
          <button className="p-4 bg-green-600/20 border-2 border-green-500 rounded-lg hover:bg-green-600/30 transition text-center">
            <div className="text-3xl mb-2">👥</div>
            <div className="font-semibold text-white">Manage Users</div>
          </button>
          <button className="p-4 bg-red-600/20 border-2 border-red-500 rounded-lg hover:bg-red-600/30 transition text-center">
            <div className="text-3xl mb-2">🗑️</div>
            <div className="font-semibold text-white">Clear Cache</div>
          </button>
        </div>
      </div>
    </div>
  );
}
