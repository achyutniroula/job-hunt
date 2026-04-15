import { useState, useEffect, useRef, useCallback } from "react";
import { Send, Trash2, X } from "lucide-react";
import toast from "react-hot-toast";
import {
  getInterviewChat,
  sendInterviewChat,
  deleteInterviewChatMessage,
  clearInterviewChat,
} from "@/lib/api";

interface ChatMsg {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

interface Props {
  sessionId: string;
  jobTitle: string;
}

export default function InterviewQA({ sessionId, jobTitle }: Props) {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    getInterviewChat(sessionId)
      .then(setMessages)
      .catch(() => {});
  }, [sessionId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || sending) return;
    const text = input.trim();
    setInput("");
    setSending(true);
    const tempUser: ChatMsg = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUser]);
    try {
      const data = await sendInterviewChat(sessionId, text);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUser.id),
        { id: `user-${data.message.id}`, role: "user", content: text, created_at: tempUser.created_at },
        data.message,
      ]);
    } catch {
      toast.error("Failed to send message");
      setMessages((prev) => prev.filter((m) => m.id !== tempUser.id));
    } finally {
      setSending(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteInterviewChatMessage(sessionId, id);
      setMessages((prev) => prev.filter((m) => m.id !== id));
    } catch {
      toast.error("Failed to delete message");
    }
  };

  const handleClearChat = async () => {
    if (!confirm("Clear all chat messages?")) return;
    try {
      await clearInterviewChat(sessionId);
      setMessages([]);
    } catch {
      toast.error("Failed to clear chat");
    }
  };

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  }, []);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-manrope font-light text-text-primary">Interview Chat</h2>
        {messages.length > 0 && (
          <button
            className="text-xs text-text-muted hover:text-danger transition-colors flex items-center gap-1"
            onClick={handleClearChat}
          >
            <X className="w-3.5 h-3.5" /> Clear
          </button>
        )}
      </div>

      <div
        className="glass-card-static rounded-lg flex flex-col flex-1"
        style={{ minHeight: "500px" }}
      >
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4" style={{ maxHeight: "65vh" }}>
          {messages.length === 0 && (
            <p className="text-text-muted text-sm text-center py-12">
              Ask anything about {jobTitle} interviews — questions, answers, strategies.
            </p>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex group ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className="relative max-w-[80%] px-4 py-3 rounded-lg text-sm leading-relaxed"
                style={
                  msg.role === "user"
                    ? { background: "rgba(100,200,255,0.1)", border: "1px solid rgba(100,200,255,0.2)" }
                    : { background: "rgba(37,38,40,0.8)", border: "1px solid rgba(72,72,75,0.3)" }
                }
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {!msg.id.startsWith("tmp-") && (
                  <button
                    className="absolute top-1 right-1 opacity-0 group-hover:opacity-60 hover:!opacity-100 transition-opacity"
                    onClick={() => handleDelete(msg.id)}
                  >
                    <Trash2 className="w-3 h-3 text-danger" />
                  </button>
                )}
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div
                className="px-4 py-3 rounded-lg"
                style={{ background: "rgba(37,38,40,0.8)", border: "1px solid rgba(72,72,75,0.3)" }}
              >
                <span className="typing-dot" />
                <span className="typing-dot mx-1" />
                <span className="typing-dot" />
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="px-5 py-4 border-t flex gap-3" style={{ borderColor: "rgba(72,72,75,0.2)" }}>
          <textarea
            ref={textareaRef}
            rows={1}
            className="input-base flex-1 resize-none overflow-hidden text-sm"
            style={{ minHeight: "40px" }}
            placeholder="Ask an interview question or strategy…"
            value={input}
            onChange={(e) => { setInput(e.target.value); autoResize(); }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
            }}
          />
          <button
            className="btn-primary px-4 py-2 shrink-0 self-end"
            onClick={handleSend}
            disabled={sending || !input.trim()}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
