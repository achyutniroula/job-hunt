interface Session {
  job_title: string;
  company_name: string;
  location?: string | null;
  seniority?: string | null;
  salary_info?: string | null;
  job_description: string;
}

interface Props {
  session: Session;
}

export default function JobDetails({ session }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-manrope font-light text-text-primary">{session.job_title}</h1>
        <p className="text-text-secondary mt-1">{session.company_name}</p>
        <div className="flex flex-wrap gap-3 mt-3">
          {session.location && (
            <span className="badge">{session.location}</span>
          )}
          {session.seniority && (
            <span className="badge capitalize">{session.seniority}</span>
          )}
          {session.salary_info && (
            <span className="badge" style={{ color: "#6ee7b7", borderColor: "rgba(110,231,183,0.3)" }}>
              {session.salary_info}
            </span>
          )}
        </div>
      </div>

      <div className="glass-card-static p-6 rounded-lg">
        <h2 className="font-manrope font-light text-text-secondary mb-4">Job Description</h2>
        <div
          className="text-text-primary leading-relaxed overflow-auto"
          style={{ maxHeight: "65vh", whiteSpace: "pre-wrap" }}
        >
          {session.job_description}
        </div>
      </div>
    </div>
  );
}
