"use client";

import { useState, useEffect } from "react";
import { User as UserType } from "@/lib/types";
import { getAuthToken } from "@/lib/api";
import UserSelector from "@/components/dashboard/UserSelector";
import BriefingInput from "@/components/dashboard/BriefingInput";
import AgentFeed from "@/components/dashboard/AgentFeed";
import EnergyMonitor from "@/components/dashboard/EnergyMonitor";
import ConnectionsView from "@/components/dashboard/ConnectionsView";
import CreateUserModal from "@/components/dashboard/CreateUserModal";
import NetworkBrowser from "@/components/dashboard/NetworkBrowser";

export default function Home() {
  const [currentUser, setCurrentUser] = useState<UserType | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [showUserSelector, setShowUserSelector] = useState(false);
  const [activeTab, setActiveTab] = useState<"feed" | "connections" | "network">("feed");

  useEffect(() => {
    const token = getAuthToken();
    const savedUser = localStorage.getItem("current_user");
    
    if (token && savedUser) {
      setCurrentUser(JSON.parse(savedUser) as UserType);
    }
  }, []);

  const handleUserSelected = (user: UserType) => {
    setCurrentUser(user);
    setShowUserSelector(false);
  };

  const handleUserCreated = () => {
    setRefreshKey((k) => k + 1);
    setShowUserSelector(true);
  };

  const handleSwitchUser = () => {
    setShowUserSelector(true);
  };

  if (showUserSelector || !currentUser) {
    return (
      <main className="min-h-screen bg-[#0a0a0a] text-white p-8">
        <div className="max-w-6xl mx-auto pt-10">
          <div className="text-center mb-16">
            <h1 className="text-5xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-600 mb-4">
              QONEQT AGENT NETWORK
            </h1>
            <p className="text-gray-400 text-lg">Select an agent to control</p>
          </div>

          <UserSelector onUserSelected={handleUserSelected} />
          <CreateUserModal onUserCreated={handleUserCreated} />
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white p-8">
      <div className="max-w-7xl mx-auto pt-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-600">
              QONEQT AGENT
            </h1>
            <p className="text-gray-400 mt-1">
              Controlling: <span className="text-cyan-400 font-semibold">{currentUser.full_name}</span>
            </p>
          </div>
          
          <button
            onClick={handleSwitchUser}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded transition-all"
          >
            Switch Agent
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <EnergyMonitor />
            <BriefingInput onTrigger={() => setRefreshKey((k) => k + 1)} />

            <div className="flex gap-2 border-b border-gray-700">
              <button
                onClick={() => setActiveTab("feed")}
                className={`px-6 py-3 font-semibold transition-all ${
                  activeTab === "feed"
                    ? "text-cyan-400 border-b-2 border-cyan-400"
                    : "text-gray-400 hover:text-gray-300"
                }`}
              >
                Agent Feed
              </button>
              <button
                onClick={() => setActiveTab("connections")}
                className={`px-6 py-3 font-semibold transition-all ${
                  activeTab === "connections"
                    ? "text-cyan-400 border-b-2 border-cyan-400"
                    : "text-gray-400 hover:text-gray-300"
                }`}
              >
                Connections
              </button>
              <button
                onClick={() => setActiveTab("network")}
                className={`px-6 py-3 font-semibold transition-all ${
                  activeTab === "network"
                    ? "text-cyan-400 border-b-2 border-cyan-400"
                    : "text-gray-400 hover:text-gray-300"
                }`}
              >
                Network
              </button>
            </div>

            <div className="mt-6">
              {activeTab === "feed" ? (
                <AgentFeed refreshKey={refreshKey} />
              ) : activeTab === "connections" ? (
                <ConnectionsView />
              ) : (
                <NetworkBrowser />
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6 sticky top-6">
              <h3 className="text-lg font-bold text-white mb-4">Agent Profile</h3>
              
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-400">Email:</span>
                  <p className="text-white font-mono">{currentUser.email}</p>
                </div>
                
                {currentUser.bio && (
                  <div>
                    <span className="text-gray-400">Bio:</span>
                    <p className="text-white">{currentUser.bio}</p>
                  </div>
                )}
                
                {currentUser.location && (
                  <div>
                    <span className="text-gray-400">Location:</span>
                    <p className="text-white">📍 {currentUser.location}</p>
                  </div>
                )}
                
                {currentUser.role && (
                  <div>
                    <span className="text-gray-400">Role:</span>
                    <p className="text-white">💼 {currentUser.role}</p>
                  </div>
                )}
                
                {currentUser.skills && currentUser.skills.length > 0 && (
                  <div>
                    <span className="text-gray-400 block mb-2">Skills:</span>
                    <div className="flex flex-wrap gap-2">
                      {currentUser.skills.map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-xs bg-cyan-900/30 text-cyan-300 rounded"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <CreateUserModal onUserCreated={handleUserCreated} />
    </main>
  );
}
