"use client";

import { useState, useEffect } from "react";
import { User as UserType } from "@/lib/types";
import { getAuthToken } from "@/lib/api";
import UserSelector from "@/components/dashboard/UserSelector";
import Dashboard from "@/components/dashboard/Dashboard";
import CreateUserModal from "@/components/dashboard/CreateUserModal";
import AdminDashboard from "@/components/admin/AdminDashboard";

export default function Home() {
  const [currentUser, setCurrentUser] = useState<UserType | null>(null);
  const [showUserSelector, setShowUserSelector] = useState(false);
  const [showAdminPanel, setShowAdminPanel] = useState(false);

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
    setShowUserSelector(true);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setShowUserSelector(true);
    setShowAdminPanel(false);
    localStorage.removeItem("current_user");
    localStorage.removeItem("auth_token");
  };

  // Show admin panel
  if (showAdminPanel) {
    return (
      <main className="min-h-screen bg-[#0a0a0a]">
        <div className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-8 py-4 flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-600">
                🛠️ SYSTEM ADMIN PANEL
              </h1>
              <p className="text-gray-500 text-sm mt-1">Engineer Control Center</p>
            </div>
            <button
              onClick={() => setShowAdminPanel(false)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              ← Back to Agents
            </button>
          </div>
        </div>
        <AdminDashboard />
      </main>
    );
  }

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
          
          {/* Admin Panel Access Button */}
          <div className="mt-12 text-center">
            <button
              onClick={() => setShowAdminPanel(true)}
              className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold rounded-lg transition-all shadow-lg hover:shadow-xl"
            >
              <span className="text-2xl">🛠️</span>
              <div className="text-left">
                <div className="text-lg">System Admin Panel</div>
                <div className="text-xs opacity-80">Engineer Control Center</div>
              </div>
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <Dashboard 
      userId={currentUser.id} 
      userName={currentUser.full_name || currentUser.email}
      onLogout={handleLogout}
    />
  );
}
