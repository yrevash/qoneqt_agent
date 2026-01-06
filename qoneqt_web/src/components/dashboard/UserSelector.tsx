"use client";

import { useState, useEffect } from "react";
import { User, Users, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { authApi, setAuthToken, api } from "@/lib/api";
import type { User as UserType, AuthResponse } from "@/lib/types";

interface UserSelectorProps {
  onUserSelected: (user: UserType) => void;
}

export default function UserSelector({ onUserSelected }: UserSelectorProps) {
  const [users, setUsers] = useState<UserType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Call the NO-AUTH endpoint to get users using the configured API client
      const res = await api.get("/users");
      setUsers(res.data);
      
      if (res.data.length === 0) {
        setError("No users found. Create a user first!");
      }
    } catch (err: any) {
      console.error("Failed to load users:", err);
      setError(err.response?.data?.detail || "Failed to connect to backend. Is it running?");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectUser = async (userId: string) => {
    try {
      const res = await authApi.selectUser(userId);
      const data: AuthResponse = res.data;
      
      setAuthToken(data.access_token);
      
      // Find and pass the full user object
      const user = users.find(u => u.id === userId);
      if (user) {
        localStorage.setItem("current_user", JSON.stringify(user));
        setSelectedUserId(userId);
        onUserSelected(user);
      }
    } catch (err: any) {
      console.error("Failed to select user:", err);
      setError(err.response?.data?.detail || "Failed to select user");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-cyan-400 animate-pulse">Loading users...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center">
        <div className="text-red-400 mb-4">⚠️ {error}</div>
        <button
          onClick={loadUsers}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded transition-all"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Users className="w-6 h-6 text-cyan-500" />
        <h2 className="text-2xl font-bold text-white">Select Your Agent</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AnimatePresence>
          {users.map((user) => (
            <motion.div
              key={user.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-6 rounded-lg border cursor-pointer transition-all ${
                selectedUserId === user.id
                  ? "bg-cyan-900/30 border-cyan-500 shadow-lg shadow-cyan-500/20"
                  : "bg-gray-900/50 border-gray-700 hover:border-cyan-500/50"
              }`}
              onClick={() => handleSelectUser(user.id)}
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                    <User className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">{user.full_name}</h3>
                    <p className="text-sm text-gray-400">{user.email}</p>
                  </div>
                </div>
                {selectedUserId === user.id && (
                  <Check className="w-6 h-6 text-cyan-400" />
                )}
              </div>

              {user.bio && (
                <p className="text-sm text-gray-300 mb-3 line-clamp-2">{user.bio}</p>
              )}

              <div className="flex flex-wrap gap-2 text-xs">
                {user.location && (
                  <span className="px-2 py-1 bg-gray-800 text-gray-300 rounded">
                    📍 {user.location}
                  </span>
                )}
                {user.role && (
                  <span className="px-2 py-1 bg-gray-800 text-cyan-300 rounded">
                    💼 {user.role}
                  </span>
                )}
              </div>

              {user.skills && user.skills.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {user.skills.slice(0, 3).map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 text-xs bg-cyan-900/30 text-cyan-300 rounded"
                    >
                      {skill}
                    </span>
                  ))}
                  {user.skills.length > 3 && (
                    <span className="px-2 py-1 text-xs text-gray-400">
                      +{user.skills.length - 3} more
                    </span>
                  )}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
