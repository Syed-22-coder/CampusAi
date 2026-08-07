export type Role = "user" | "assistant";

export interface Source {
  title: string;
  url: string;
  verifiedDate?: string;
}

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  sources?: Source[];
  department?: string;
}
