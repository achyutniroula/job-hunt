import { ExternalLink, Globe, Briefcase, Star, Linkedin, Search } from "lucide-react";

interface Session {
  company_name: string;
  company_website?: string | null;
  company_careers_url?: string | null;
  company_glassdoor_url?: string | null;
  company_linkedin_url?: string | null;
  company_indeed_url?: string | null;
}

interface Props {
  session: Session;
}

const LINKS = [
  { key: "company_website",     label: "Official Website",  icon: Globe },
  { key: "company_careers_url", label: "Careers Page",      icon: Briefcase },
  { key: "company_linkedin_url",label: "LinkedIn",          icon: Linkedin },
  { key: "company_glassdoor_url",label: "Glassdoor",        icon: Star },
  { key: "company_indeed_url",  label: "Indeed",            icon: Search },
] as const;

export default function CompanyLinks({ session }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="font-manrope font-light text-text-primary">{session.company_name}</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {LINKS.map(({ key, label, icon: Icon }) => {
          const url = session[key as keyof Session] as string | null | undefined;
          return (
            <div key={key} className="glass-card p-5 flex items-center gap-4">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                style={{ background: "rgba(72,72,75,0.3)" }}
              >
                <Icon className="w-5 h-5 text-text-muted" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-manrope text-sm text-text-secondary">{label}</p>
                {url ? (
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent-blue text-sm hover:underline flex items-center gap-1 mt-0.5 truncate"
                  >
                    <span className="truncate">{url}</span>
                    <ExternalLink className="w-3 h-3 shrink-0" />
                  </a>
                ) : (
                  <p className="text-text-muted text-sm mt-0.5 italic">Search manually</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <p className="text-text-muted text-sm italic">
        Links are auto-generated best guesses — verify before use.
      </p>
    </div>
  );
}
