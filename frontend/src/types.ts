export interface Settings {
  theme: 'light' | 'dark'; font_size: 'normal' | 'large';
  density: 'comfortable' | 'compact'; preferred_summary: 'concise' | 'detailed';
}
export type ResearchSource = 'local' | 'courtlistener';
export interface Matter {
  id: string; title: string; question: string; facts: string;
  source?: ResearchSource; court: string; date_from: string; date_to: string;
}
export interface Passage {
  text: string; pdf_page?: number; section_number?: number; locator_label?: string;
  opinion_id?: number | string; source_url: string; opinion_scope: string;
}
export interface CaseResult {
  id: string; case_name: string; citation: string; court: string; court_name?: string; decision_date: string;
  source_url: string; summary: string; summary_kind?: string; passages: Passage[]; explanation: string;
  is_new?: boolean; explanation_kind?: string; retrieval_mode?: string; text_status?: string;
}
export interface Feedback { relevance: 'relevant' | 'not_relevant'; reason: string }
export interface Round {
  id: string; number: number; query: string; status: string; stop_reason: string;
  actions: { tool: string; detail: string }[]; results: CaseResult[];
  feedback_snapshot: Record<string, Feedback>; created_at: string; mode: string; source?: ResearchSource;
  error?: { category?: string; retry_after_seconds?: number; retry_after?: number };
}
export interface MatterDetail {
  matter: Matter; rounds: Round[]; feedback: Record<string, Feedback>; selections: CaseResult[];
}
export interface Bootstrap {
  csrf_token: string; capabilities: { mode: string; agent_available: boolean; corpus_count: number; courtlistener_available?: boolean };
  sources?: { id: ResearchSource; label: string; available: boolean }[];
  courts?: { id: string; label: string }[];
  settings: Settings; matters: Matter[];
}
export interface Scenario {
  id: string; title: string; fact_pattern: string; research_question: string;
}
