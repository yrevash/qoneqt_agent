// src/lib/api.ts
import axios from "axios";

// Pointing to your FastAPI Backend
const API_URL = "http://localhost:8080/api/v1";

// Create a configured instance
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add your Hardcoded Token for Dev (or implement login later)
// Token generated for: Alice Rust (alice@qoneqt.com)
const DEV_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhY2M1MmU1ZC04M2VmLTRlNDAtYTFmMi1lMGNjNGQ5OGFmYWIiLCJleHAiOjE3Njc2MzY3NTB9.PUKi0O_m6NKoU1ZgStTi16kXbETb0oPyjY9zE-aSRoM"; 

api.interceptors.request.use((config) => {
  config.headers.Authorization = `Bearer ${DEV_TOKEN}`;
  return config;
});

export const agentApi = {
  // The Trigger
  triggerSearch: (query: string) => 
    api.post("/agent/trigger", { query, intent: "frontend_search" }),

  // The Feed
  getFeed: () => 
    api.get("/agent/feed"),
};