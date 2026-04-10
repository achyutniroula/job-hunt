import { useState } from "react";
import { Github, Linkedin, Plus, X } from "lucide-react";

interface Props {
  githubUrls: string[];
  linkedinUrl: string;
  onGithubUrlsChange: (urls: string[]) => void;
  onLinkedinUrlChange: (url: string) => void;
}

export default function ProfileInputForm({
  githubUrls,
  linkedinUrl,
  onGithubUrlsChange,
  onLinkedinUrlChange,
}: Props) {
  const updateUrl = (i: number, val: string) => {
    const next = [...githubUrls];
    next[i] = val;
    onGithubUrlsChange(next);
  };

  const removeUrl = (i: number) =>
    onGithubUrlsChange(githubUrls.filter((_, idx) => idx !== i));

  const addUrl = () => {
    if (githubUrls.length < 10) onGithubUrlsChange([...githubUrls, ""]);
  };

  return (
    <div className="glass-card-static p-5 space-y-4">
      <p className="text-[11px] font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em] flex items-center gap-2">
        <Github className="w-3.5 h-3.5 text-text-muted" />
        GitHub Profile
      </p>

      <div className="space-y-2">
        {githubUrls.map((url, i) => (
          <div key={i} className="flex gap-2">
            <input
              type="text"
              className="input-base text-xs flex-1"
              placeholder={i === 0 ? "github.com/username or username" : "github.com/username/repo (optional)"}
              value={url}
              onChange={(e) => updateUrl(i, e.target.value)}
            />
            {i > 0 && (
              <button
                onClick={() => removeUrl(i)}
                className="btn-ghost px-2 py-1.5"
                style={{ color: "#f87171" }}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        ))}
        {githubUrls.length < 10 && (
          <button
            onClick={addUrl}
            className="flex items-center gap-1.5 text-[10px] text-text-muted hover:text-text-secondary transition-colors font-manrope"
          >
            <Plus className="w-3 h-3" />
            Add specific repo URL
          </button>
        )}
      </div>

      <div>
        <p className="text-[11px] font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em] flex items-center gap-2 mb-2">
          <Linkedin className="w-3.5 h-3.5 text-text-muted" />
          LinkedIn URL <span className="normal-case font-normal text-text-muted tracking-normal">(optional)</span>
        </p>
        <input
          type="url"
          className="input-base text-xs"
          placeholder="https://linkedin.com/in/your-profile"
          value={linkedinUrl}
          onChange={(e) => onLinkedinUrlChange(e.target.value)}
        />
        <p className="text-[10px] text-text-dim mt-1.5 font-inter">
          LinkedIn improves results but is optional. If access is blocked, optimization continues with GitHub only.
        </p>
      </div>
    </div>
  );
}
