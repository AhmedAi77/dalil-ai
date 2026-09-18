export type KnowledgeDocument = {
  id: string;
  filename: string;
  extension: string;
  source: string;
  character_count: number;
  size_bytes: number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type SourceReference = {
  document_id: string;
  filename: string;
  chunk_index: number;
  score: number;
};

export type Answer = {
  answer: string;
  sources: SourceReference[];
  transcription?: string;
  language?: string | null;
};

export type ChatTurn = {
  id: string;
  question: string;
  answer: Answer;
  created_at: string;
};

export type ChatSession = {
  id: string;
  title: string;
  document_id: string | null;
  turns: ChatTurn[];
  created_at: string;
  updated_at: string;
};

export type User = {
  id: string;
  name: string;
  email: string;
  created_at: string;
};

export type Notice = { kind: "success" | "error"; text: string } | null;
