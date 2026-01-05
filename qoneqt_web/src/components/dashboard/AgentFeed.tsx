"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { agentApi } from "@/lib/api";
import { FeedItem } from "@/lib/types";
import { CheckCircle, XCircle, Clock, RefreshCw } from "lucide-react";

export default function AgentFeed({ refreshKey }: { refreshKey: number }) {
  const [feed, setFeed] = useState<FeedItem[]>([]);

  const fetchFeed = useCallback(async () => {
    try {
      const res = await agentApi.getFeed();
      setFeed(res.data);
    } catch (err) {
      console.error("Failed to fetch feed");
    }
  }, []);

  // Poll for updates every 5 seconds or when manually triggered
  useEffect(() => {
    fetchFeed();
    const interval = setInterval(fetchFeed, 5000);
    return () => clearInterval(interval);
  }, [refreshKey, fetchFeed]);

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <RefreshCw className="w-5 h-5 text-cyan-500" />
          Live Agent Feed
        </h2>
      </div>

      <AnimatePresence>
        {feed.map((item) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0 }}
            className={`p-5 rounded-lg border border-opacity-20 backdrop-blur-sm ${
              item.decision === "ACCEPT" 
                ? "bg-green-900/20 border-green-500" 
                : item.decision === "REJECT"
                ? "bg-red-900/10 border-red-500"
                : "bg-yellow-900/10 border-yellow-500"
            }`}
          >
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-3 mb-2">
                {item.decision === "ACCEPT" ? (
                  <CheckCircle className="text-green-400 w-6 h-6" />
                ) : item.decision === "REJECT" ? (
                  <XCircle className="text-red-400 w-6 h-6" />
                ) : (
                  <Clock className="text-yellow-400 w-6 h-6" />
                )}
                <span className={`font-mono font-bold ${
                  item.decision === "ACCEPT" 
                    ? "text-green-400" 
                    : item.decision === "REJECT"
                    ? "text-red-400"
                    : "text-yellow-400"
                }`}>
                  {item.decision}
                </span>
                <span className="text-xs text-gray-500 font-mono">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <span className="text-xs font-mono text-cyan-300">
                Confidence: {Math.round(item.reasoning.confidence_score * 100)}%
              </span>
            </div>
            
            <p className="text-gray-300 mt-2 leading-relaxed">
              {item.reasoning.reasoning}
            </p>

            {item.decision === "ACCEPT" && item.reasoning.generated_message && (
              <div className="mt-4 p-3 bg-black/40 rounded border-l-2 border-cyan-500 text-sm text-gray-400 italic">
                "{item.reasoning.generated_message}"
              </div>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}