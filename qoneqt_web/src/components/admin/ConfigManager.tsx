"use client";

import { useState, useEffect } from "react";
import { adminApi, SystemConfig } from "@/lib/admin-api";

export default function ConfigManager() {
  const [configs, setConfigs] = useState<SystemConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<any>("");
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    loadConfigs();
  }, [filter]);

  const loadConfigs = async () => {
    try {
      const scope = filter === "all" ? undefined : filter;
      const response = await adminApi.config.list(scope);
      setConfigs(response.data);
    } catch (err) {
      console.error("Failed to load configs:", err);
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (config: SystemConfig) => {
    setEditingKey(config.key);
    setEditValue(config.value.data !== undefined ? config.value.data : config.value);
  };

  const saveEdit = async (key: string) => {
    try {
      await adminApi.config.update(key, editValue);
      setEditingKey(null);
      loadConfigs();
    } catch (err: any) {
      alert(`Failed to update: ${err.message}`);
    }
  };

  const cancelEdit = () => {
    setEditingKey(null);
    setEditValue("");
  };

  const getValueColor = (type: string) => {
    const colors = {
      string: "text-blue-600",
      integer: "text-green-600",
      float: "text-green-600",
      boolean: "text-purple-600",
      json: "text-orange-600",
    };
    return colors[type as keyof typeof colors] || "text-gray-600";
  };

  if (loading) {
    return <div className="p-6">Loading configurations...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Configuration</h1>
          <p className="text-gray-600 mt-1">
            Manage all system settings - NO CODE CHANGES NEEDED!
          </p>
        </div>
        <button
          onClick={loadConfigs}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex gap-2">
          {["all", "system", "service", "user", "agent"].map((scope) => (
            <button
              key={scope}
              onClick={() => setFilter(scope)}
              className={`px-4 py-2 rounded-lg transition ${
                filter === scope
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {scope.charAt(0).toUpperCase() + scope.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Configurations List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Key
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Value
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Scope
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {configs.map((config) => (
              <tr key={config.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <div className="font-semibold text-gray-900">{config.key}</div>
                    {config.description && (
                      <div className="text-sm text-gray-500">{config.description}</div>
                    )}
                    {config.requires_restart && (
                      <div className="text-xs text-orange-600 mt-1">⚠️ Requires restart</div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  {editingKey === config.key ? (
                    <input
                      type={config.value_type === "boolean" ? "checkbox" : "text"}
                      value={
                        config.value_type === "boolean"
                          ? undefined
                          : typeof editValue === "object"
                          ? JSON.stringify(editValue)
                          : editValue
                      }
                      checked={config.value_type === "boolean" ? editValue : undefined}
                      onChange={(e) =>
                        setEditValue(
                          config.value_type === "boolean"
                            ? e.target.checked
                            : config.value_type === "integer"
                            ? parseInt(e.target.value)
                            : config.value_type === "float"
                            ? parseFloat(e.target.value)
                            : config.value_type === "json"
                            ? JSON.parse(e.target.value)
                            : e.target.value
                        )
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <span className={`font-mono ${getValueColor(config.value_type)}`}>
                      {typeof config.value === "object"
                        ? JSON.stringify(config.value.data !== undefined ? config.value.data : config.value)
                        : String(config.value.data !== undefined ? config.value.data : config.value)}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">
                    {config.value_type}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      config.scope === "system"
                        ? "bg-red-100 text-red-700"
                        : config.scope === "service"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-green-100 text-green-700"
                    }`}
                  >
                    {config.scope}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {editingKey === config.key ? (
                    <div className="flex gap-2">
                      <button
                        onClick={() => saveEdit(config.key)}
                        className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                      >
                        ✓ Save
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600"
                      >
                        ✕ Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => startEdit(config)}
                      disabled={!config.is_editable}
                      className={`px-3 py-1 rounded ${
                        config.is_editable
                          ? "bg-blue-500 text-white hover:bg-blue-600"
                          : "bg-gray-300 text-gray-500 cursor-not-allowed"
                      }`}
                    >
                      ✏️ Edit
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-blue-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              <strong>Pro Tip:</strong> Changes to system-wide configurations take effect
              immediately or after service restart (check the restart indicator). No code
              deployment required!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
