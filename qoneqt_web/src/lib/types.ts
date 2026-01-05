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