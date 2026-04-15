import { useState, useEffect } from "react";
import { Github, Star, GitFork, ExternalLink, ChevronDown, Sparkles } from "lucide-react";
import { getInterviewGitHub, explainGitHubRepo } from "@/lib/api";

interface Repo {
  name: string;
  description: string | null;
  languages: Record<string, number>;
  topics: string[];
  readme: string | null;
  readme_excerpt?: string | null; // legacy compat
  file_tree: string[];
  key_files: Record<string, string>;
  stars: number;
  forks: number;
  updated_at: string;
}

interface GitHubData {
  username: string;
  repos: Repo[];
  top_languages: Record<string, number>;
  total_repos: number;
}

const LANG_COLORS: Record<string, string> = {
  Python: "#3572A5",
  TypeScript: "#2b7489",
  JavaScript: "#f1e05a",
  Rust: "#dea584",
  Go: "#00ADD8",
  Java: "#b07219",
  "C++": "#f34b7d",
  C: "#555555",
  Ruby: "#701516",
  Swift: "#ffac45",
  Kotlin: "#A97BFF",
  CSS: "#563d7c",
  HTML: "#e34c26",
  Shell: "#89e051",
};

function LangBar({ languages }: { languages: Record<string, number> }) {
  const total = Object.values(languages).reduce((a, b) => a + b, 0);
  if (!total) return null;
  const sorted = Object.entries(languages).sort((a, b) => b[1] - a[1]).slice(0, 6);
  return (
    <div className="flex h-1.5 rounded-full overflow-hidden gap-px">
      {sorted.map(([lang, bytes]) => (
        <div
          key={lang}
          title={`${lang} ${Math.round((bytes / total) * 100)}%`}
          style={{
            width: `${(bytes / total) * 100}%`,
            background: LANG_COLORS[lang] ?? "#6e7681",
            minWidth: "3px",
          }}
        />
      ))}
    </div>
  );
}

interface Props {
  sessionId: string;
  githubUrl?: string | null;
}

export default function GitHubRepos({ sessionId, githubUrl }: Props) {
  const [data, setData] = useState<GitHubData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openRepos, setOpenRepos] = useState<Record<string, boolean>>({});
  const [explanations, setExplanations] = useState<Record<string, string>>({});
  const [explaining, setExplaining] = useState<Record<string, boolean>>({});

  const toggleExplain = async (repoName: string) => {
    const nowOpen = !openRepos[repoName];
    setOpenRepos((prev) => ({ ...prev, [repoName]: nowOpen }));
    if (nowOpen && !explanations[repoName] && !explaining[repoName]) {
      setExplaining((prev) => ({ ...prev, [repoName]: true }));
      try {
        const res = await explainGitHubRepo(sessionId, repoName);
        setExplanations((prev) => ({ ...prev, [repoName]: res.explanation }));
      } catch {
        setExplanations((prev) => ({ ...prev, [repoName]: "Failed to generate explanation." }));
      } finally {
        setExplaining((prev) => ({ ...prev, [repoName]: false }));
      }
    }
  };

  useEffect(() => {
    getInterviewGitHub(sessionId)
      .then(setData)
      .catch(() => setError(githubUrl ? "GitHub data not available" : "No GitHub profile linked to this session"))
      .finally(() => setLoading(false));
  }, [sessionId, githubUrl]);

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => <div key={i} className="skeleton h-20 rounded-lg" />)}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass-card p-10 text-center text-text-muted">
        <Github className="w-10 h-10 mx-auto mb-3 opacity-30" />
        <p className="text-sm">{error ?? "No GitHub data"}</p>
        <p className="text-xs mt-2 opacity-60">Add a GitHub URL when creating a new session</p>
      </div>
    );
  }

  const topLangs = Object.entries(data.top_languages).slice(0, 8);
  const totalBytes = topLangs.reduce((a, [, b]) => a + b, 0);

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Github className="w-5 h-5 text-text-muted" />
        <div>
          <h2 className="font-manrope font-light text-text-primary">@{data.username}</h2>
          <p className="text-text-muted text-xs">{data.total_repos} public repos</p>
        </div>
      </div>

      {/* Language breakdown */}
      {topLangs.length > 0 && (
        <div className="glass-card p-5">
          <p className="text-text-muted text-xs uppercase tracking-widest mb-3">Top Languages</p>
          <div className="flex flex-wrap gap-2 mb-3">
            {topLangs.map(([lang, bytes]) => (
              <span
                key={lang}
                className="text-xs px-2.5 py-1 rounded-full"
                style={{
                  background: `${LANG_COLORS[lang] ?? "#6e7681"}22`,
                  border: `1px solid ${LANG_COLORS[lang] ?? "#6e7681"}55`,
                  color: LANG_COLORS[lang] ?? "#c6c6c7",
                }}
              >
                {lang} · {Math.round((bytes / totalBytes) * 100)}%
              </span>
            ))}
          </div>
          <div className="flex h-2 rounded-full overflow-hidden gap-px">
            {topLangs.map(([lang, bytes]) => (
              <div
                key={lang}
                title={lang}
                style={{
                  width: `${(bytes / totalBytes) * 100}%`,
                  background: LANG_COLORS[lang] ?? "#6e7681",
                  minWidth: "4px",
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Repos */}
      <div>
        <p className="text-text-muted text-xs uppercase tracking-widest mb-3">Repositories</p>
        <div className="space-y-3">
          {data.repos.map((repo) => (
            <div key={repo.name} className="glass-card p-4">
              <div className="flex items-start justify-between gap-3 mb-1.5">
                <a
                  href={`https://github.com/${data.username}/${repo.name}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-manrope font-medium text-text-primary hover:text-blue-400 transition-colors flex items-center gap-1.5 text-sm"
                >
                  {repo.name}
                  <ExternalLink className="w-3 h-3 opacity-50" />
                </a>
                <div className="flex items-center gap-3 shrink-0 text-text-muted text-xs">
                  {repo.stars > 0 && (
                    <span className="flex items-center gap-1"><Star className="w-3 h-3" />{repo.stars}</span>
                  )}
                  {repo.forks > 0 && (
                    <span className="flex items-center gap-1"><GitFork className="w-3 h-3" />{repo.forks}</span>
                  )}
                </div>
              </div>

              {repo.description && (
                <p className="text-text-secondary text-xs mb-2 leading-relaxed">{repo.description}</p>
              )}

              {Object.keys(repo.languages).length > 0 && (
                <div className="mb-2">
                  <LangBar languages={repo.languages} />
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {Object.keys(repo.languages).slice(0, 4).map((l) => (
                      <span key={l} className="text-xs text-text-muted" style={{ color: LANG_COLORS[l] ?? "#6e7681" }}>
                        {l}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {repo.topics.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {repo.topics.slice(0, 5).map((t) => (
                    <span
                      key={t}
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={{ background: "rgba(56,139,253,0.1)", border: "1px solid rgba(56,139,253,0.3)", color: "#58a6ff" }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {/* Understand dropdown */}
              <button
                onClick={() => toggleExplain(repo.name)}
                className="flex items-center gap-1.5 text-xs mt-1 transition-colors"
                style={{ color: openRepos[repo.name] ? "rgba(198,198,199,0.7)" : "rgba(198,198,199,0.4)" }}
              >
                <Sparkles className="w-3 h-3" />
                Understand this project
                <ChevronDown
                  className="w-3 h-3 transition-transform duration-200"
                  style={{ transform: openRepos[repo.name] ? "rotate(180deg)" : "rotate(0deg)" }}
                />
              </button>

              {openRepos[repo.name] && (
                <div
                  className="mt-3 pt-3 text-xs leading-relaxed"
                  style={{ borderTop: "1px solid rgba(72,72,75,0.25)", color: "rgba(198,198,199,0.85)" }}
                >
                  {explaining[repo.name] ? (
                    <div className="flex items-center gap-2 text-text-muted">
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="ml-1">Analyzing…</span>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{explanations[repo.name]}</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
