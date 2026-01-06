"use client";

import { useEffect, useState } from "react";
import { Zap, TrendingUp, RotateCcw } from "lucide-react";
import { agentApi, getAuthToken } from "@/lib/api";

export default function EnergyMonitor() {
  const [energy, setEnergy] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    fetchEnergy();
    const interval = setInterval(fetchEnergy, 3000); // Update every 3s
    return () => clearInterval(interval);
  }, []);

  const fetchEnergy = async () => {
    // Only fetch if user is authenticated
    if (!getAuthToken()) return;
    
    try {
      const res = await agentApi.getEnergy();
      setEnergy(res.data.energy);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch energy");
    }
  };

  const handleReset = async () => {
    try {
      setResetting(true);
      await agentApi.resetEnergy();
      await fetchEnergy();
    } catch (err) {
      console.error("Failed to reset energy");
    } finally {
      setResetting(false);
    }
  };

  const getEnergyColor = () => {
    if (energy > 70) return "text-green-400";
    if (energy > 30) return "text-yellow-400";
    return "text-red-400";
  };

  const getEnergyBarColor = () => {
    if (energy > 70) return "bg-green-500";
    if (energy > 30) return "bg-yellow-500";
    return "bg-red-500";
  };

  if (loading) return null;

  return (
    <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Zap className={`w-5 h-5 ${getEnergyColor()}`} />
          <span className="text-sm font-semibold text-gray-300">Energy</span>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-2xl font-bold ${getEnergyColor()}`}>
            {energy}
          </span>
          <button
            onClick={handleReset}
            disabled={resetting}
            className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs transition-all flex items-center gap-1 disabled:opacity-50"
            title="Reset energy to 100"
          >
            <RotateCcw className={`w-3 h-3 ${resetting ? "animate-spin" : ""}`} />
            Reset
          </button>
        </div>
      </div>

      {/* Energy Bar */}
      <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full ${getEnergyBarColor()} transition-all duration-500`}
          style={{ width: `${energy}%` }}
        />
      </div>

      <div className="mt-2 flex items-center gap-1 text-xs text-gray-400">
        <TrendingUp className="w-3 h-3" />
        <span>Each search costs 10 energy</span>
      </div>
    </div>
  );
}
