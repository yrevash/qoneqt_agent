// src/lib/api.ts
import axios from "axios";

// Pointing to your FastAPI Backend
// Use environment variable or fallback to localhost
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api/v1";

// Create a configured instance
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Token management
let currentToken: string | null = null;

export const setAuthToken = (token: string) => {
  currentToken = token;
  localStorage.setItem("auth_token", token);
};

export const getAuthToken = () => {
  if (!currentToken) {
    currentToken = localStorage.getItem("auth_token");
  }
  return currentToken;
};

export const clearAuthToken = () => {
  currentToken = null;
  localStorage.removeItem("auth_token");
  localStorage.removeItem("current_user");
};

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  // Select which user to control
  selectUser: (userId: string) => 
    api.post("/auth/select-user", { user_id: userId }),
  
  // Create new user
  createUser: (data: {
    email: string;
    full_name: string;
    bio?: string;
    location?: string;
    role?: string;
    skills?: string[];
  }) => api.post("/users/create", data),
  
  // List all users - NO AUTH REQUIRED
  listUsers: () => api.get("/users"),
  
  // Get current user
  getCurrentUser: () => api.get("/users/me"),
};

export const agentApi = {
  // Trigger agent search
  triggerSearch: (query: string) => 
    api.post("/agent/trigger", { query, intent: "frontend_search" }),

  // Get agent feed
  getFeed: (offset = 0) => 
    api.get("/agent/feed", { params: { limit: 20, offset } }),
  
  // Get energy balance
  getEnergy: () => api.get("/energy"),
  
  // Reset energy (admin)
  resetEnergy: (userId?: string) => 
    api.post("/admin/reset-energy", { user_id: userId }),
};

export const connectionApi = {
  // Get connections
  getConnections: (status?: string) => 
    api.get("/connections", { params: { status_filter: status } }),
  
  // Respond to connection
  respondToConnection: (connectionId: string, action: "ACCEPT" | "REJECT") =>
    api.post(`/connections/${connectionId}/respond`, null, { params: { action } }),
};

export const adminApi = {
  // Get all users (no auth)
  getAllUsers: () => api.get("/admin/users"),
};
