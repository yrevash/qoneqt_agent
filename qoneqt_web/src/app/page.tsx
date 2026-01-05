"use client";

import { useState } from "react";
import BriefingInput from "@/components/dashboard/BriefingInput";
import AgentFeed from "@/components/dashboard/AgentFeed";

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white p-8">
      <div className="max-w-6xl mx-auto pt-10">
        
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-600 mb-4">
            QONEQT AGENT
          </h1>
          <p className="text-gray-400 text-lg">
            Autonomous Networking Command Center
          </p>
        </div>

        {/* Input Section */}
        <BriefingInput onTrigger={() => setRefreshKey((k) => k + 1)} />

        {/* Feed Section */}
        <div className="mt-20">
          <AgentFeed refreshKey={refreshKey} />
        </div>

      </div>
    </main>
  );
}