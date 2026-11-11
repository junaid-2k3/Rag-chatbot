export type Source = { title: string; heading: string; url: string; page: number | null };
export type ChatMessage = { role: "user" | "assistant"; content: string };
export type ChatResult = { answer: string; sources: Source[]; found: boolean };

/** kind drives the message shown to the user: busy and network can be retried. */
export class ApiError extends Error {
  constructor(message: string, readonly kind: "busy" | "network" | "invalid" | "server") {
    super(message);
  }
}

const API_URL = (import.meta.env.PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const MAX_HISTORY = 8; // backend limit: 4 turns
const MAX_CONTENT = 2000; // backend limit per message

export async function sendChat(question: string, history: ChatMessage[]): Promise<ChatResult> {
  const body = {
    question,
    history: history.slice(-MAX_HISTORY).map((m) => ({ role: m.role, content: m.content.slice(0, MAX_CONTENT) })),
  };
  let res: Response;
  try {
    res = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(60_000),
    });
  } catch {
    throw new ApiError("Can't reach the assistant. Check your connection and try again.", "network");
  }
  if (res.ok) return (await res.json()) as ChatResult;
  if (res.status === 503) throw new ApiError("The assistant is busy right now. Try again in a minute.", "busy");
  if (res.status === 422) throw new ApiError("That question can't be sent. Keep it under 500 characters.", "invalid");
  throw new ApiError("The assistant ran into a problem. Try again.", "server");
}
