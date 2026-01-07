"use client";

import { useState } from "react";
import { LogOut, Zap } from "lucide-react";
import BriefingInput from "./BriefingInput";
import AgentFeed from "./AgentFeed";
import ConnectionsView from "./ConnectionsView";
import EnergyMonitor from "./EnergyMonitor";
import AdminPanel from "./AdminPanel";

interface DashboardProps {
  userId: string;
  userName: string;
  onLogout: () => void;
}

export default function Dashboard({ userId, userName, onLogout }: DashboardProps) {
  const [refreshKey, setRefreshKey] = useState(0);
  const [activeTab, setActiveTab] = useState<"feed" | "connections" | "admin">("feed");

  return (
    <div className="min-h-screen text-white p-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="flex justify-between items-center mb-12">
          <div>
            <h1 className="text-4xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-600">
              QONEQT AGENT
            </h1>
            <p className="text-gray-400 mt-2">
              Controlling: <span className="text-cyan-400 font-semibold">{userName}</span>
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <EnergyMonitor />
            <button
              onClick={onLogout}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Switch Agent
            </button>
          </div>
        </div>

        {/* Input Section */}
        <BriefingInput onTrigger={() => setRefreshKey((k) => k + 1)} />

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-gray-800">
          <button
            onClick={() => setActiveTab("feed")}
            className={`px-6 py-3 font-semibold transition-colors relative ${
              activeTab === "feed"
                ? "text-cyan-400"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            Agent Feed
            {activeTab === "feed" && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan-400" />
            )}
          </button>
          <button
            onClick={() => setActiveTab("connections")}
            className={`px-6 py-3 font-semibold transition-colors relative ${
              activeTab === "connections"
                ? "text-cyan-400"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            Connections
            {activeTab === "connections" && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan-400" />
            )}
          </button>
          <button
            onClick={() => setActiveTab("admin")}
            className={`px-6 py-3 font-semibold transition-colors relative ${
              activeTab === "admin"
                ? "text-cyan-400"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            🛠️ Admin Panel
            {activeTab === "admin" && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan-400" />
            )}
          </button>
        </div>

        {/* Content */}
        <div className="mt-8">
          {activeTab === "feed" ? (
            <AgentFeed refreshKey={refreshKey} />
          ) : activeTab === "connections" ? (
            <ConnectionsView />
          ) : (
            <AdminPanel userId={userId} />
          )}
        </div>

      </div>
    </div>
  );
}
