export interface AgentReasoning {
  decision: "ACCEPT" | "REJECT" | "HOLD";
  confidence_score: number;
  reasoning: string;
  generated_message?: string;
}

export interface FeedItem {
  id: string;
  decision: "ACCEPT" | "REJECT" | "HOLD";
  reasoning: AgentReasoning;
  timestamp: string;
}

export interface TriggerResponse {
  status: string;
  trace_id?: string;
  energy_remaining: number;
  message?: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  bio?: string;
  location?: string;
  role?: string;
  skills?: string[];
  created_at: string;
}

export interface Connection {
  id: string;
  initiator_id: string;
  receiver_id: string;
  status: string;
  created_at: string;
  other_user_name?: string;
  other_user_bio?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  full_name: string;
}
