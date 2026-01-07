// Admin Panel API Extensions
import { api } from "./api";

export interface SystemConfig {
  id: string;
  key: string;
  value: any;
  value_type: string;
  scope: string;
  description?: string;
  requires_restart: boolean;
  is_editable: boolean;
  last_modified_at: string;
}

export interface Alert {
  id: string;
  alert_name: string;
  severity: string;
  status: string;
  summary?: string;
  description?: string;
  starts_at: string;
  ends_at?: string;
  acknowledged: boolean;
  created_at: string;
}

export interface SystemHealth {
  service_name: string;
  status: string;
  cpu_usage?: number;
  memory_usage?: number;
  disk_usage?: number;
  request_count?: number;
  error_count?: number;
  avg_response_time?: number;
  timestamp: string;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  total_connections: number;
  pending_connections: number;
  total_alerts_24h: number;
  critical_alerts_active: number;
  system_health: string;
  services_status: Record<string, string>;
}

export interface AuditLog {
  id: string;
  user_id?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  success: boolean;
  timestamp: string;
  details: any;
}

export const adminApi = {
  // Configuration Management
  config: {
    list: (scope?: string) => 
      api.get<SystemConfig[]>("/admin/config", { params: { scope } }),
    
    get: (key: string) => 
      api.get<SystemConfig>(`/admin/config/${key}`),
    
    create: (config: Partial<SystemConfig>) => 
      api.post<SystemConfig>("/admin/config", config),
    
    update: (key: string, value: any, description?: string) => 
      api.put<SystemConfig>(`/admin/config/${key}`, { value, description }),
    
    delete: (key: string) => 
      api.delete(`/admin/config/${key}`),
  },

  // Alert Management
  alerts: {
    list: (severity?: string, status?: string, limit = 50) => 
      api.get<Alert[]>("/admin/alerts", { params: { severity, status, limit } }),
    
    acknowledge: (alertId: string, notes?: string) => 
      api.post(`/admin/alerts/${alertId}/acknowledge`, { notes }),
  },

  // System Health
  health: {
    get: (hours = 1) => 
      api.get<SystemHealth[]>("/admin/health", { params: { hours } }),
    
    stats: () => 
      api.get<AdminStats>("/admin/stats"),
  },

  // Audit Logs
  audit: {
    list: (userId?: string, action?: string, limit = 100) => 
      api.get<AuditLog[]>("/admin/audit-logs", { 
        params: { user_id: userId, action, limit } 
      }),
  },

  // User Management
  users: {
    toggleActive: (userId: string) => 
      api.put(`/admin/users/${userId}/toggle-active`),
    
    update: (userId: string, data: any) => 
      api.put(`/admin/users/${userId}/update`, data),
  },

  // Notifications (test)
  notifications: {
    test: (channel: string, recipient: string) => 
      api.post("/admin/notifications/test", { channel, recipient }),
  },
};
