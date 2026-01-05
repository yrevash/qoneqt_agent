"use client";

import { useState } from "react";
import { Send, Zap } from "lucide-react";
import { motion } from "framer-motion";
import { agentApi } from "@/lib/api"; // We will ensure this exists

export default function BriefingInput({ onTrigger }: { onTrigger: () => void }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setStatus(null);

    try {
      const res = await agentApi.triggerSearch(query);
      if (res.data.status === "QUEUED") {
        setStatus(`✅ Agent Deployed (Energy: ${res.data.energy_remaining})`);
        setQuery("");
        onTrigger(); // Refresh feed
      } else {
        setStatus(`❌ ${res.data.message || "Request Rejected"}`);
      }
    } catch (err) {
      setStatus("❌ Connection Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-2xl mx-auto mb-12"
    >
      <form onSubmit={handleSubmit} className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
        <div className="relative bg-black rounded-lg p-1 flex items-center border border-gray-800">
          <div className="pl-4 pr-2">
            <Zap className={`w-5 h-5 ${loading ? "text-yellow-400 animate-pulse" : "text-cyan-500"}`} />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe your target (e.g., 'Find a Rust Developer in London')..."
            className="w-full bg-transparent text-white p-4 focus:outline-none placeholder-gray-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className="p-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md transition-all disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
      {status && (
        <p className={`mt-3 text-center text-sm font-mono ${status.includes("❌") ? "text-red-400" : "text-green-400"}`}>
          {status}
        </p>
      )}
    </motion.div>
  );
}