import { useState, useEffect, useRef, useCallback } from "react";
import { Plus, Pencil, Trash2, Send, X, Check } from "lucide-react";
import toast from "react-hot-toast";
import {
  listBrainstormThreads,
  createBrainstormThread,
  renameBrainstormThread,
  deleteBrainstormThread,
  getBrainstormMessages,
  sendBrainstormMessage,
} from "@/lib/api";
import { useAppStore } from "@/store/appStore";

interface Thread {
  id: string;
  title: string;
  created_at: string;
}

interface Msg {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

interface Props {
  sessionId: string;
}

export default function BrainstormChat({ sessionId }: Props) {
  const { activeBrainstormThreadId, setActiveBrainstormThread } = useAppStore();
  // activeBrainstormThreadId is already scoped per-session by BrainstormChat mounting
  const [threads, setThreads] = useState<Thread[]>([]);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    listBrainstormThreads(sessionId)
      .then((data: Thread[]) => {
        setThreads(data);
        if (!activeBrainstormThreadId && data.length > 0) {
          setActiveBrainstormThread(data[0].id);
        }
      })
      .catch(() => {});
  }, [sessionId]);

  useEffect(() => {
    if (!activeBrainstormThreadId) return;
    getBrainstormMessages(sessionId, activeBrainstormThreadId)
      .then(setMessages)
      .catch(() => {});
  }, [sessionId, activeBrainstormThreadId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleNewThread = async () => {
    const title = prompt("Thread title:");
    if (!title?.trim()) return;
    try {
      const thread = await createBrainstormThread(sessionId, title.trim());
      setThreads((prev) => [...prev, thread]);
      setActiveBrainstormThread(thread.id);
      setMessages([]);
    } catch {
      toast.error("Failed to create thread");
    }
  };

  const handleRename = async (id: string) => {
    if (!editTitle.trim()) return;
    try {
      const updated = await renameBrainstormThread(sessionId, id, editTitle.trim());
      setThreads((prev) => prev.map((t) => (t.id === id ? updated : t)));
    } catch {
      toast.error("Failed to rename");
    } finally {
      setEditingId(null);
    }
  };

  const handleDeleteThread = async (id: string) => {
    if (!confirm("Delete this thread and all its messages?")) return;
    try {
      await deleteBrainstormThread(sessionId, id);
      const next = threads.filter((t) => t.id !== id);
      setThreads(next);
      if (activeBrainstormThreadId === id) {
        const newId = next[0]?.id ?? null;
        setActiveBrainstormThread(newId);
        setMessages([]);
      }
    } catch {
      toast.error("Failed to delete thread");
    }
  };

  const handleSend = async () => {
    if (!input.trim() || sending || !activeBrainstormThreadId) return;
    const text = input.trim();
    setInput("");
    setSending(true);
    const tempUser: Msg = { id: `tmp-${Date.now()}`, role: "user", content: text, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, tempUser]);
    try {
      const data = await sendBrainstormMessage(sessionId, activeBrainstormThreadId, text);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUser.id),
        { id: `user-${data.message.id}`, role: "user", content: text, created_at: tempUser.created_at },
        data.message,
      ]);
    } catch {
      toast.error("Failed to send");
      setMessages((prev) => prev.filter((m) => m.id !== tempUser.id));
    } finally {
      setSending(false);
    }
  };

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  }, []);

  const activeThread = threads.find((t) => t.id === activeBrainstormThreadId);

  return (
    <div className="flex gap-4 h-full" style={{ minHeight: "70vh" }}>
      {/* Thread list */}
      <div
        className="w-48 shrink-0 flex flex-col glass-card-static rounded-lg"
        style={{ height: "70vh" }}
      >
        <div className="px-4 py-3 border-b flex items-center justify-between" style={{ borderColor: "rgba(72,72,75,0.2)" }}>
          <span className="text-xs font-manrope uppercase tracking-widest text-text-muted">Threads</span>
          <button className="p-1 text-text-muted hover:text-text-primary transition-colors" onClick={handleNewThread}>
            <Plus className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-2">
          {threads.length === 0 ? (
            <p className="text-center text-text-muted text-xs py-6 px-3">No threads yet</p>
          ) : (
            threads.map((thread) => (
              <div
                key={thread.id}
                className={`group flex items-center gap-1 px-3 py-2 cursor-pointer transition-colors ${
                  activeBrainstormThreadId === thread.id
                    ? "text-text-primary bg-white/[0.04]"
                    : "text-text-muted hover:text-text-secondary hover:bg-white/[0.02]"
                }`}
                style={
                  activeBrainstormThreadId === thread.id
                    ? { borderLeft: "2px solid rgba(198,198,199,0.6)" }
                    : { borderLeft: "2px solid transparent" }
                }
                onClick={() => {
                  if (editingId !== thread.id) {
                    setActiveBrainstormThread(thread.id);
                    setMessages([]);
                  }
                }}
              >
                {editingId === thread.id ? (
                  <div className="flex items-center gap-1 w-full" onClick={(e) => e.stopPropagation()}>
                    <input
                      className="flex-1 text-xs bg-transparent border-b border-text-muted outline-none text-text-primary"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") handleRename(thread.id); if (e.key === "Escape") setEditingId(null); }}
                      autoFocus
                    />
                    <button onClick={() => handleRename(thread.id)} className="text-success"><Check className="w-3 h-3" /></button>
                    <button onClick={() => setEditingId(null)} className="text-text-muted"><X className="w-3 h-3" /></button>
                  </div>
                ) : (
                  <>
                    <span className="flex-1 text-xs truncate">{thread.title}</span>
                    <div className="hidden group-hover:flex items-center gap-0.5">
                      <button
                        className="p-0.5 hover:text-text-primary"
                        onClick={(e) => { e.stopPropagation(); setEditingId(thread.id); setEditTitle(thread.title); }}
                      >
                        <Pencil className="w-3 h-3" />
                      </button>
                      <button
                        className="p-0.5 hover:text-danger"
                        onClick={(e) => { e.stopPropagation(); handleDeleteThread(thread.id); }}
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat panel */}
      <div className="flex-1 glass-card-static rounded-lg flex flex-col" style={{ height: "70vh" }}>
        {!activeBrainstormThreadId ? (
          <div className="flex-1 flex items-center justify-center text-text-muted text-sm">
            Select or create a thread to start brainstorming
          </div>
        ) : (
          <>
            <div className="px-5 py-4 border-b" style={{ borderColor: "rgba(72,72,75,0.2)" }}>
              <h3 className="font-manrope font-light text-text-primary truncate">
                {activeThread?.title ?? "Brainstorm"}
              </h3>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              {messages.length === 0 && (
                <p className="text-text-muted text-sm text-center py-8">
                  Start brainstorming your interview strategy here.
                </p>
              )}
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className="max-w-[80%] px-4 py-3 rounded-lg text-sm leading-relaxed"
                    style={
                      msg.role === "user"
                        ? { background: "rgba(100,200,255,0.1)", border: "1px solid rgba(100,200,255,0.2)" }
                        : { background: "rgba(37,38,40,0.8)", border: "1px solid rgba(72,72,75,0.3)" }
                    }
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="px-4 py-3 rounded-lg" style={{ background: "rgba(37,38,40,0.8)", border: "1px solid rgba(72,72,75,0.3)" }}>
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
                placeholder="Brainstorm ideas, strategies, questions…"
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
          </>
        )}
      </div>
    </div>
  );
}
