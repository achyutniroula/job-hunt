import { useMemo, useState } from "react";
import { ZoomIn, ZoomOut, FileText, Pencil, Save, X } from "lucide-react";
import toast from "react-hot-toast";
import { updateSessionResume } from "@/lib/api";

interface Props {
  resumeText: string;
  sessionId?: string;
  onUpdate?: (text: string) => void;
}

type LineKind =
  | { k: "name"; text: string }
  | { k: "contact"; text: string }
  | { k: "section"; text: string }
  | { k: "entry_primary"; left: string; right: string }
  | { k: "entry_secondary"; left: string; right: string }
  | { k: "bullet"; text: string }
  | { k: "text"; text: string }
  | { k: "blank" };

function parseResume(raw: string): LineKind[] {
  const lines = raw.split("\n");
  const out: LineKind[] = [];
  let foundName = false;
  let contactDone = false;
  let prevKind: LineKind["k"] | null = null;

  for (const line of lines) {
    const t = line.trim();

    // Name: first non-empty line
    if (!foundName) {
      if (t) {
        out.push({ k: "name", text: t });
        foundName = true;
        prevKind = "name";
      }
      continue;
    }

    // Blank line
    if (!t) {
      if (!contactDone) contactDone = true;
      if (prevKind !== "blank") out.push({ k: "blank" });
      prevKind = "blank";
      continue;
    }

    // Section header: ALL_CAPS letters/spaces/&/-, ≤50 chars, ≥3 alpha chars
    if (
      t.length <= 50 &&
      /^[A-Z][A-Z\s&\/\-]+$/.test(t) &&
      (t.match(/[A-Z]/g) || []).length >= 3
    ) {
      contactDone = true;
      out.push({ k: "section", text: t });
      prevKind = "section";
      continue;
    }

    // Contact block (before first blank or section header)
    if (!contactDone) {
      out.push({ k: "contact", text: t });
      prevKind = "contact";
      continue;
    }

    // Bullet point
    if (/^\s*[•\-–—*▪]\s/.test(line)) {
      const text = t.replace(/^[•\-–—*▪]\s*/, "");
      out.push({ k: "bullet", text });
      prevKind = "bullet";
      continue;
    }

    // Two-column entry header: left content   right content (3+ spaces between)
    const twoCol = t.match(/^(.+?)\s{3,}(.+)$/);
    if (twoCol) {
      const isSecondary =
        prevKind === "entry_primary" || prevKind === "entry_secondary";
      if (isSecondary) {
        out.push({ k: "entry_secondary", left: twoCol[1].trim(), right: twoCol[2].trim() });
        prevKind = "entry_secondary";
      } else {
        out.push({ k: "entry_primary", left: twoCol[1].trim(), right: twoCol[2].trim() });
        prevKind = "entry_primary";
      }
      continue;
    }

    // Single-column entry secondary (role/location without right-align) after primary
    if (prevKind === "entry_primary") {
      out.push({ k: "entry_secondary", left: t, right: "" });
      prevKind = "entry_secondary";
      continue;
    }

    out.push({ k: "text", text: t });
    prevKind = "text";
  }

  return out;
}

export default function ResumePreview({ resumeText, sessionId, onUpdate }: Props) {
  const [scale, setScale] = useState(1.0);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(resumeText);
  const [saving, setSaving] = useState(false);
  const lines = useMemo(() => parseResume(resumeText), [resumeText]);

  const handleSave = async () => {
    if (!sessionId) return;
    setSaving(true);
    try {
      await updateSessionResume(sessionId, editText);
      onUpdate?.(editText);
      setEditing(false);
      toast.success("Resume saved");
    } catch {
      toast.error("Failed to save resume");
    } finally {
      setSaving(false);
    }
  };

  if (!resumeText.trim()) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: "60vh" }}>
        <div className="text-center text-text-muted">
          <FileText className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p className="text-sm">No resume text for this session</p>
        </div>
      </div>
    );
  }

  if (editing) {
    return (
      <div className="flex flex-col gap-4 h-full">
        <div className="flex items-center justify-between">
          <h2 className="font-manrope font-light text-text-primary">Edit Resume</h2>
          <div className="flex items-center gap-2">
            <button
              className="btn-ghost flex items-center gap-1.5 text-sm px-3 py-1.5"
              onClick={() => { setEditing(false); setEditText(resumeText); }}
            >
              <X className="w-3.5 h-3.5" /> Cancel
            </button>
            <button
              className="btn-primary flex items-center gap-1.5 text-sm px-3 py-1.5"
              onClick={handleSave}
              disabled={saving}
            >
              <Save className="w-3.5 h-3.5" />
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
        <textarea
          className="flex-1 w-full rounded-lg p-4 text-xs font-mono resize-none focus:outline-none"
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
            color: "#c6c6c7",
            minHeight: "70vh",
          }}
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          spellCheck={false}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <h2 className="font-manrope font-light text-text-primary">Resume Preview</h2>
        <div className="flex items-center gap-2">
          {sessionId && (
            <button
              className="btn-ghost flex items-center gap-1.5 text-sm px-3 py-1.5"
              onClick={() => { setEditText(resumeText); setEditing(true); }}
            >
              <Pencil className="w-3.5 h-3.5" /> Edit
            </button>
          )}
          <button
            className="btn-ghost p-2"
            onClick={() => setScale((s) => Math.max(0.4, +(s - 0.1).toFixed(1)))}
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-text-muted text-sm w-12 text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            className="btn-ghost p-2"
            onClick={() => setScale((s) => Math.min(2, +(s + 0.1).toFixed(1)))}
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Paper container */}
      <div
        className="flex-1 overflow-auto rounded-lg"
        style={{ background: "rgba(0,0,0,0.15)", minHeight: "60vh" }}
      >
        <div
          style={{
            transform: `scale(${scale})`,
            transformOrigin: "top center",
            paddingBottom: `${(1 - scale) * 100 * -1}px`,
          }}
        >
          {/* White paper */}
          <div
            style={{
              background: "#ffffff",
              color: "#141414",
              fontFamily: "'Helvetica Neue', Helvetica, Arial, sans-serif",
              maxWidth: "780px",
              margin: "24px auto",
              padding: "52px 56px",
              minHeight: "1056px",
              fontSize: "11px",
              lineHeight: "1.45",
              boxShadow: "0 4px 32px rgba(0,0,0,0.45)",
            }}
          >
            {lines.map((line, i) => {
              switch (line.k) {
                case "name":
                  return (
                    <div
                      key={i}
                      style={{
                        textAlign: "center",
                        fontWeight: 700,
                        fontSize: "22px",
                        letterSpacing: "0.01em",
                        marginBottom: "5px",
                      }}
                    >
                      {line.text}
                    </div>
                  );

                case "contact":
                  return (
                    <div
                      key={i}
                      style={{
                        textAlign: "center",
                        fontSize: "10px",
                        color: "#4D4D4D",
                        marginBottom: "2px",
                      }}
                    >
                      {line.text}
                    </div>
                  );

                case "section":
                  return (
                    <div key={i} style={{ marginTop: "16px", marginBottom: "6px" }}>
                      <div
                        style={{
                          fontWeight: 700,
                          fontSize: "12.5px",
                          letterSpacing: "0.04em",
                        }}
                      >
                        {line.text}
                      </div>
                      <div
                        style={{
                          height: "2px",
                          background: "#D4D4D4",
                          marginTop: "3px",
                        }}
                      />
                    </div>
                  );

                case "entry_primary":
                  return (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "baseline",
                        fontWeight: 700,
                        fontSize: "11px",
                        marginTop: "7px",
                      }}
                    >
                      <span>{line.left}</span>
                      {line.right && (
                        <span style={{ color: "#4D4D4D", fontWeight: 400, fontSize: "10px" }}>
                          {line.right}
                        </span>
                      )}
                    </div>
                  );

                case "entry_secondary":
                  return (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "baseline",
                        fontStyle: "italic",
                        fontSize: "10.5px",
                        color: "#4D4D4D",
                        marginBottom: "3px",
                      }}
                    >
                      <span>{line.left}</span>
                      {line.right && <span>{line.right}</span>}
                    </div>
                  );

                case "bullet":
                  return (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        gap: "5px",
                        fontSize: "10.5px",
                        marginLeft: "14px",
                        marginBottom: "1px",
                        lineHeight: "1.4",
                      }}
                    >
                      <span style={{ flexShrink: 0, marginTop: "0.5px" }}>•</span>
                      <span>{line.text}</span>
                    </div>
                  );

                case "text":
                  return (
                    <div key={i} style={{ fontSize: "11px", marginBottom: "1px" }}>
                      {line.text}
                    </div>
                  );

                case "blank":
                  return <div key={i} style={{ height: "5px" }} />;

                default:
                  return null;
              }
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
