"use client";

import { useEffect, useState } from "react";
import { Users, User, Search } from "lucide-react";
import { motion } from "framer-motion";
import axios from "axios";
import type { User as UserType } from "@/lib/types";

export default function NetworkBrowser() {
  const [users, setUsers] = useState<UserType[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<UserType[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    // Filter users based on search term
    if (searchTerm.trim() === "") {
      setFilteredUsers(users);
    } else {
      const term = searchTerm.toLowerCase();
      const filtered = users.filter(
        (u) =>
          u.full_name?.toLowerCase().includes(term) ||
          u.email?.toLowerCase().includes(term) ||
          u.bio?.toLowerCase().includes(term) ||
          u.role?.toLowerCase().includes(term) ||
          u.location?.toLowerCase().includes(term) ||
          u.skills?.some((s) => s.toLowerCase().includes(term))
      );
      setFilteredUsers(filtered);
    }
  }, [searchTerm, users]);

  const fetchUsers = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api/v1";
      const res = await axios.get(`${API_URL}/admin/users`);
      setUsers(res.data);
      setFilteredUsers(res.data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch users");
      setLoading(false);
    }
  };

  // Get current user from localStorage
  const getCurrentUserId = () => {
    const user = localStorage.getItem("current_user");
    return user ? JSON.parse(user).id : null;
  };

  const currentUserId = getCurrentUserId();

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Users className="w-6 h-6 text-cyan-500" />
          <h2 className="text-2xl font-bold text-white">Network Browser</h2>
          <span className="text-sm text-gray-400">({filteredUsers.length} users)</span>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name, role, skills, location..."
            className="w-full pl-10 pr-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {loading ? (
        <div className="text-center text-gray-400 py-12">Loading network...</div>
      ) : filteredUsers.length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          <Users className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <p>No users found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredUsers.map((user) => {
            const isCurrentUser = user.id === currentUserId;
            
            return (
              <motion.div
                key={user.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className={`p-4 rounded-lg border transition-all ${
                  isCurrentUser
                    ? "bg-cyan-900/20 border-cyan-500"
                    : "bg-gray-900/50 border-gray-700 hover:border-gray-600"
                }`}
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-bold text-white truncate">
                      {user.full_name}
                      {isCurrentUser && (
                        <span className="ml-2 text-xs text-cyan-400">(You)</span>
                      )}
                    </h3>
                    <p className="text-xs text-gray-400 truncate">{user.email}</p>
                  </div>
                </div>

                {user.bio && (
                  <p className="text-sm text-gray-300 mb-3 line-clamp-2">
                    {user.bio}
                  </p>
                )}

                <div className="flex flex-wrap gap-1 mb-2">
                  {user.location && (
                    <span className="px-2 py-0.5 text-xs bg-gray-800 text-gray-300 rounded">
                      📍 {user.location}
                    </span>
                  )}
                  {user.role && (
                    <span className="px-2 py-0.5 text-xs bg-gray-800 text-cyan-300 rounded">
                      💼 {user.role}
                    </span>
                  )}
                </div>

                {user.skills && user.skills.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {user.skills.slice(0, 3).map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 text-xs bg-cyan-900/30 text-cyan-300 rounded"
                      >
                        {skill}
                      </span>
                    ))}
                    {user.skills.length > 3 && (
                      <span className="px-2 py-0.5 text-xs text-gray-400">
                        +{user.skills.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
