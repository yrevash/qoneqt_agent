"use client";

import { useState } from "react";
import { Settings, Database, Zap, Link, Activity, Eye } from "lucide-react";

interface AdminPanelProps {
  userId: string;
}

export default function AdminPanel({ userId }: AdminPanelProps) {
  return (
    <div className="space-y-6">
      
      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <QuickLinkCard
          title="Swagger API Docs"
          description="Interactive API testing"
          icon={<Settings className="w-6 h-6" />}
          href="http://localhost:8080/docs"
          color="cyan"
        />
        <QuickLinkCard
          title="Database Admin"
          description="Adminer interface"
          icon={<Database className="w-6 h-6" />}
          href="http://localhost:8081"
          color="blue"
        />
        <QuickLinkCard
          title="RabbitMQ Management"
          description="View message queues"
          icon={<Activity className="w-6 h-6" />}
          href="http://localhost:15672"
          color="purple"
        />
        <QuickLinkCard
          title="Prometheus Metrics"
          description="System monitoring"
          icon={<Zap className="w-6 h-6" />}
          href="http://localhost:9090"
          color="orange"
        />
        <QuickLinkCard
          title="Grafana Dashboards"
          description="Data visualization"
          icon={<Eye className="w-6 h-6" />}
          href="http://localhost:3001"
          color="green"
        />
        <QuickLinkCard
          title="API Root"
          description="Backend status"
          icon={<Link className="w-6 h-6" />}
          href="http://localhost:8080"
          color="pink"
        />
      </div>

      {/* System Status */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-cyan-400" />
          System Status
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatusCard label="API" status="Running" color="green" />
          <StatusCard label="Database" status="Healthy" color="green" />
          <StatusCard label="Redis" status="Connected" color="green" />
          <StatusCard label="RabbitMQ" status="Active" color="green" />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <button
            onClick={() => window.open('http://localhost:8080/docs#/default/list_users_users_get', '_blank')}
            className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors group"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center group-hover:bg-cyan-500/30 transition-colors">
                <Database className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <div className="font-semibold text-white">View All Users</div>
                <div className="text-sm text-gray-400">List users via API</div>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => window.open('http://localhost:8080/docs#/default/trigger_agent_agent_trigger_post', '_blank')}
            className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors group"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center group-hover:bg-purple-500/30 transition-colors">
                <Zap className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <div className="font-semibold text-white">Trigger Agent</div>
                <div className="text-sm text-gray-400">Test agent trigger</div>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => window.open('http://localhost:15672', '_blank')}
            className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors group"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-500/20 rounded-lg flex items-center justify-center group-hover:bg-orange-500/30 transition-colors">
                <Activity className="w-5 h-5 text-orange-400" />
              </div>
              <div>
                <div className="font-semibold text-white">View Queues</div>
                <div className="text-sm text-gray-400">RabbitMQ management</div>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => window.open('http://localhost:9090/targets', '_blank')}
            className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors group"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center group-hover:bg-green-500/30 transition-colors">
                <Eye className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <div className="font-semibold text-white">Metrics Targets</div>
                <div className="text-sm text-gray-400">Prometheus status</div>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Environment Info */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Environment Info</h2>
        <div className="space-y-2 font-mono text-sm">
          <InfoRow label="API URL" value="http://localhost:8080" />
          <InfoRow label="Web URL" value="http://localhost:3000" />
          <InfoRow label="Database" value="PostgreSQL + pgvector" />
          <InfoRow label="Cache" value="Redis" />
          <InfoRow label="Queue" value="RabbitMQ" />
          <InfoRow label="LLM" value="Ollama (Local)" />
          <InfoRow label="Current User ID" value={userId} />
        </div>
      </div>

    </div>
  );
}

interface QuickLinkCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  href: string;
  color: string;
}

function QuickLinkCard({ title, description, icon, href, color }: QuickLinkCardProps) {
  const colorClasses = {
    cyan: "from-cyan-500/20 to-cyan-600/20 border-cyan-500/30 hover:border-cyan-500",
    blue: "from-blue-500/20 to-blue-600/20 border-blue-500/30 hover:border-blue-500",
    purple: "from-purple-500/20 to-purple-600/20 border-purple-500/30 hover:border-purple-500",
    orange: "from-orange-500/20 to-orange-600/20 border-orange-500/30 hover:border-orange-500",
    green: "from-green-500/20 to-green-600/20 border-green-500/30 hover:border-green-500",
    pink: "from-pink-500/20 to-pink-600/20 border-pink-500/30 hover:border-pink-500",
  };

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={`block p-6 rounded-lg border bg-gradient-to-br transition-all hover:shadow-lg ${colorClasses[color as keyof typeof colorClasses]}`}
    >
      <div className="flex items-start gap-4">
        <div className="text-white">{icon}</div>
        <div className="flex-1">
          <h3 className="font-bold text-white mb-1">{title}</h3>
          <p className="text-sm text-gray-400">{description}</p>
        </div>
      </div>
    </a>
  );
}

interface StatusCardProps {
  label: string;
  status: string;
  color: "green" | "red" | "yellow";
}

function StatusCard({ label, status, color }: StatusCardProps) {
  const colors = {
    green: "bg-green-500/20 text-green-400 border-green-500/30",
    red: "bg-red-500/20 text-red-400 border-red-500/30",
    yellow: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  };

  return (
    <div className={`p-4 rounded-lg border ${colors[color]}`}>
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className="font-semibold">{status}</div>
    </div>
  );
}

interface InfoRowProps {
  label: string;
  value: string;
}

function InfoRow({ label, value }: InfoRowProps) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-800">
      <span className="text-gray-400">{label}:</span>
      <span className="text-cyan-400">{value}</span>
    </div>
  );
}
