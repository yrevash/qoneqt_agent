"use client";

import { useEffect, useState } from "react";
import { Link2, Clock, CheckCircle, XCircle, AlertCircle, ThumbsUp, ThumbsDown } from "lucide-react";
import { motion } from "framer-motion";
import { connectionApi, getAuthToken } from "@/lib/api";
import type { Connection } from "@/lib/types";

export default function ConnectionsView() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [filter, setFilter] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);

  useEffect(() => {
    fetchConnections();
  }, [filter]);

  const fetchConnections = async () => {
    // Only fetch if user is authenticated
    if (!getAuthToken()) return;
    
    try {
      const res = await connectionApi.getConnections(filter);
      setConnections(res.data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch connections");
      setLoading(false);
    }
  };

  const handleRespond = async (connectionId: string, action: "ACCEPT" | "REJECT") => {
    try {
      setProcessing(connectionId);
      await connectionApi.respondToConnection(connectionId, action);
      // Refresh the list
      await fetchConnections();
    } catch (err: any) {
      console.error("Failed to respond to connection:", err);
      alert(err.response?.data?.detail || "Failed to respond to connection");
    } finally {
      setProcessing(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toUpperCase()) {
      case "ACCEPTED":
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case "REJECTED":
        return <XCircle className="w-5 h-5 text-red-400" />;
      case "PENDING":
        return <Clock className="w-5 h-5 text-yellow-400" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case "ACCEPTED":
        return "border-green-500/30 bg-green-900/10";
      case "REJECTED":
        return "border-red-500/30 bg-red-900/10";
      case "PENDING":
        return "border-yellow-500/30 bg-yellow-900/10";
      default:
        return "border-gray-500/30 bg-gray-900/10";
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
          <Link2 className="w-6 h-6 text-cyan-500" />
          <h2 className="text-2xl font-bold text-white">Connections</h2>
        </div>

        {/* Filter Buttons */}
        <div className="flex gap-2">
          {["ALL", "PENDING", "ACCEPTED", "REJECTED"].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status === "ALL" ? undefined : status)}
              className={`px-4 py-2 rounded text-sm font-medium transition-all ${
                (status === "ALL" && !filter) || filter === status
                  ? "bg-cyan-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center text-gray-400 py-12">Loading connections...</div>
      ) : connections.length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          <Link2 className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <p>No connections yet</p>
        </div>
      ) : (
        <div className="space-y-3">
          {connections.map((conn) => {
            const isReceiver = conn.receiver_id === currentUserId;
            const isPending = conn.status === "PENDING";
            const canRespond = isReceiver && isPending;

            return (
              <motion.div
                key={conn.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={`p-4 rounded-lg border ${getStatusColor(conn.status)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    {getStatusIcon(conn.status)}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-lg font-semibold text-white">
                          {conn.other_user_name || "Unknown User"}
                        </h3>
                        {isReceiver && (
                          <span className="px-2 py-0.5 text-xs bg-blue-900/30 text-blue-300 rounded">
                            Received
                          </span>
                        )}
                        {!isReceiver && (
                          <span className="px-2 py-0.5 text-xs bg-purple-900/30 text-purple-300 rounded">
                            Sent
                          </span>
                        )}
                      </div>
                      {conn.other_user_bio && (
                        <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                          {conn.other_user_bio}
                        </p>
                      )}
                      <p className="text-xs text-gray-500 mt-2">
                        {new Date(conn.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {canRespond && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleRespond(conn.id, "ACCEPT")}
                          disabled={processing === conn.id}
                          className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded text-sm font-medium transition-all flex items-center gap-1 disabled:opacity-50"
                        >
                          <ThumbsUp className="w-4 h-4" />
                          Accept
                        </button>
                        <button
                          onClick={() => handleRespond(conn.id, "REJECT")}
                          disabled={processing === conn.id}
                          className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded text-sm font-medium transition-all flex items-center gap-1 disabled:opacity-50"
                        >
                          <ThumbsDown className="w-4 h-4" />
                          Reject
                        </button>
                      </div>
                    )}
                    <span
                      className={`px-3 py-1 text-xs font-semibold rounded-full ${
                        conn.status === "ACCEPTED"
                          ? "bg-green-900/30 text-green-300"
                          : conn.status === "REJECTED"
                          ? "bg-red-900/30 text-red-300"
                          : "bg-yellow-900/30 text-yellow-300"
                      }`}
                    >
                      {conn.status}
                    </span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
