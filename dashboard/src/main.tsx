import { useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import {
  AlertCircle,
  Award,
  BookOpen,
  CheckCircle2,
  Code2,
  Cpu,
  Layers,
  Moon,
  RefreshCw,
  Search,
  Sun,
  Zap
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import "./styles.css";

type Problem = {
  id: number;
  title: string;
  difficulty: "Easy" | "Medium" | "Hard";
  language: string;
  runtime: string;
  memory: string;
  submission_date: string;
  url: string;
  tags: string[];
  code?: string;
  analysis?: {
    time_complexity: string;
    space_complexity: string;
    explanation: string;
    loop_count: number;
    branch_count: number;
    max_loop_depth: number;
    mermaid: string;
  };
  review?: {
    summary: string;
    findings: Array<{ severity: string; title: string; detail: string }>;
  };
};

type Stats = {
  total_solved: number;
  easy: number;
  medium: number;
  hard: number;
  current_streak: number;
  longest_streak: number;
  language_distribution: Record<string, number>;
  topic_distribution: Record<string, number>;
  pattern_distribution: Record<string, number>;
  runtime_distribution: Record<string, number>;
  submission_heatmap: Record<string, number>;
};

type SyncStatus = {
  queue_depth: number;
  queued_retries?: Array<{
    action: string;
    payload: Record<string, unknown>;
    error: string;
    attempts: number;
    last_attempt?: string;
  }>;
  events: Array<{ event: string; created_at: number; payload: Record<string, unknown> }>;
};

const apiBase = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";
const difficultyColors = { Easy: "#10b981", Medium: "#f59e0b", Hard: "#ef4444" };

function App() {
  const [dark, setDark] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);
  const [problems, setProblems] = useState<Problem[]>([]);
  const [query, setQuery] = useState("");
  const [difficulty, setDifficulty] = useState("All");
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [expandedProblem, setExpandedProblem] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"problems" | "analytics" | "sync">("problems");

  const load = async () => {
    try {
      const [statsResponse, problemResponse, syncResponse] = await Promise.all([
        fetch(`${apiBase}/stats`),
        fetch(`${apiBase}/problems`),
        fetch(`${apiBase}/sync/status`)
      ]);
      setStats(await statsResponse.json());
      setProblems(await problemResponse.json());
      setSyncStatus(await syncResponse.json().catch(() => null));
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  const filtered = useMemo(() => {
    return problems.filter((problem) => {
      const matchesDifficulty = difficulty === "All" || problem.difficulty === difficulty;
      const text = `${problem.title} ${problem.language} ${problem.tags.join(" ")}`.toLowerCase();
      return matchesDifficulty && text.includes(query.toLowerCase());
    });
  }, [problems, query, difficulty]);

  const difficultyData = stats
    ? [
        { name: "Easy", value: stats.easy },
        { name: "Medium", value: stats.medium },
        { name: "Hard", value: stats.hard }
      ]
    : [];

  const topicData = Object.entries(stats?.topic_distribution ?? {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, value]) => ({ name, value }));

  const patternData = Object.entries(stats?.pattern_distribution ?? {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, value]) => ({ name, value }));

  const runtimeData = Object.entries(stats?.runtime_distribution ?? {}).map(([name, value]) => ({ name, value }));

  const heatmapData = Object.entries(stats?.submission_heatmap ?? {})
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-35);

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-900 transition-colors duration-300 dark:bg-zinc-950 dark:text-zinc-100">
      {/* Visual Background Accents */}
      <div className="absolute top-0 left-0 -z-10 h-[500px] w-full bg-gradient-to-b from-emerald-50/40 via-transparent to-transparent dark:from-emerald-950/20" />

      <section className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8">
        {/* Header Section */}
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-200/80 pb-6 dark:border-zinc-800/80">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-500/20">
              <Zap className="h-6 w-6 animate-pulse" />
            </div>
            <div>
              <h1 className="bg-gradient-to-r from-emerald-600 to-teal-500 bg-clip-text text-3xl font-extrabold tracking-tight text-transparent dark:from-emerald-400 dark:to-teal-300">
                Leet Sync
              </h1>
              <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
                Real-time LeetCode syncing, AI documentation, and static analytics.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="icon-button group" onClick={() => void load()} title="Refresh Data">
              <RefreshCw size={18} className="transition-transform group-hover:rotate-180 duration-500" />
            </button>
            <button className="icon-button" onClick={() => setDark((value) => !value)} title="Toggle theme">
              {dark ? <Sun size={18} className="text-amber-400" /> : <Moon size={18} />}
            </button>
          </div>
        </header>

        {/* Tab Selection */}
        <nav className="flex gap-2 border-b border-zinc-200/50 pb-2 dark:border-zinc-800/50">
          {(["problems", "analytics", "sync"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`rounded-lg px-4 py-2 text-sm font-semibold capitalize transition-all ${
                activeTab === tab
                  ? "bg-emerald-500 text-white shadow-md shadow-emerald-500/10"
                  : "text-zinc-600 hover:bg-zinc-150 dark:text-zinc-400 dark:hover:bg-zinc-900"
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>

        {activeTab === "problems" && (
          <>
            {/* Metric Overview Grid */}
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <MetricCard
                label="Total Solved"
                value={stats?.total_solved ?? 0}
                icon={<Award size={20} />}
                colorClass="border-l-4 border-l-blue-500 text-blue-600 dark:text-blue-400"
              />
              <MetricCard
                label="Easy Solved"
                value={stats?.easy ?? 0}
                icon={<CheckCircle2 size={20} />}
                colorClass="border-l-4 border-l-emerald-500 text-emerald-600 dark:text-emerald-400"
              />
              <MetricCard
                label="Medium Solved"
                value={stats?.medium ?? 0}
                icon={<Layers size={20} />}
                colorClass="border-l-4 border-l-amber-500 text-amber-600 dark:text-amber-400"
              />
              <MetricCard
                label="Hard Solved"
                value={stats?.hard ?? 0}
                icon={<Cpu size={20} />}
                colorClass="border-l-4 border-l-red-500 text-red-600 dark:text-red-400"
              />
              <MetricCard
                label="Streak"
                value={stats?.current_streak ?? 0}
                suffix="days"
                icon={<Zap size={20} />}
                colorClass="border-l-4 border-l-orange-500 text-orange-600 dark:text-orange-400"
              />
            </section>

            {/* Problem Table Section */}
            <section className="panel shadow-lg backdrop-blur-md bg-white/90 dark:bg-zinc-900/90">
              <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold tracking-tight">Solved Problems</h2>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Click on any problem to inspect solutions, AST diagrams, and AI reviews.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <label className="search">
                    <Search size={16} className="text-zinc-400" />
                    <input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      placeholder="Search title, language, or tags..."
                    />
                  </label>
                  <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
                    <option>All</option>
                    <option>Easy</option>
                    <option>Medium</option>
                    <option>Hard</option>
                  </select>
                </div>
              </div>

              <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
                <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
                  <thead className="bg-zinc-50 dark:bg-zinc-950">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider">Problem</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider">Difficulty</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider">Language</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider">Runtime</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider">Memory</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-200 bg-white dark:divide-zinc-800 dark:bg-zinc-900">
                    {filtered.map((problem) => {
                      const isExpanded = expandedProblem === problem.id;
                      return (
                        <>
                          <tr
                            key={`${problem.id}-${problem.language}`}
                            onClick={() => setExpandedProblem(isExpanded ? null : problem.id)}
                            className="cursor-pointer transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-950"
                          >
                            <td className="px-6 py-4 whitespace-nowrap font-semibold">
                              #{String(problem.id).padStart(4, "0")} {problem.title}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`badge ${problem.difficulty.toLowerCase()}`}>
                                {problem.difficulty}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-zinc-500 dark:text-zinc-400">
                              {problem.language}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap font-mono text-xs">
                              {problem.runtime}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap font-mono text-xs">
                              {problem.memory}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                              {problem.submission_date}
                            </td>
                          </tr>
                          {isExpanded && (
                            <tr className="bg-zinc-50/50 dark:bg-zinc-950/20">
                              <td colSpan={6} className="px-8 py-6">
                                <div className="grid gap-6 md:grid-cols-2">
                                  {/* Code Block */}
                                  <div className="flex flex-col gap-2">
                                    <div className="flex items-center justify-between border-b border-zinc-200 pb-2 dark:border-zinc-800">
                                      <h3 className="flex items-center gap-2 text-sm font-bold text-emerald-600 dark:text-emerald-400">
                                        <Code2 size={16} /> Solution Code
                                      </h3>
                                      <a
                                        href={problem.url}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="text-xs hover:underline"
                                      >
                                        View on LeetCode
                                      </a>
                                    </div>
                                    <pre className="max-h-[380px] overflow-auto rounded-lg border border-zinc-200 bg-zinc-900 p-4 font-mono text-xs text-zinc-100 dark:border-zinc-800">
                                      <code>{/* Solution code will be displayed here dynamically, if loaded */}
                                      {/* Note: since this UI displays stored records from DB, we fall back if code isn't fully detailed */}
                                      {problem.code ? problem.code : "# Solution code is stored in solution file."}</code>
                                    </pre>
                                  </div>

                                  {/* Complexity & AI review */}
                                  <div className="flex flex-col gap-4">
                                    <div className="flex flex-col gap-2">
                                      <h3 className="flex items-center gap-2 border-b border-zinc-200 pb-2 text-sm font-bold text-teal-600 dark:border-zinc-800 dark:text-teal-400">
                                        <BookOpen size={16} /> AST & Complexity Details
                                      </h3>
                                      <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div className="rounded bg-zinc-100 p-2 dark:bg-zinc-800">
                                          <span className="font-semibold text-zinc-500">Time Complexity</span>
                                          <p className="mt-1 font-bold text-sm">{problem.analysis?.time_complexity ?? "N/A"}</p>
                                        </div>
                                        <div className="rounded bg-zinc-100 p-2 dark:bg-zinc-800">
                                          <span className="font-semibold text-zinc-500">Space Complexity</span>
                                          <p className="mt-1 font-bold text-sm">{problem.analysis?.space_complexity ?? "N/A"}</p>
                                        </div>
                                      </div>
                                      <p className="text-xs text-zinc-650 dark:text-zinc-400 mt-2">
                                        {problem.analysis?.explanation ?? "No static code explanation available."}
                                      </p>
                                    </div>

                                    {problem.review?.findings && problem.review.findings.length > 0 && (
                                      <div className="flex flex-col gap-2">
                                        <h3 className="flex items-center gap-2 border-b border-zinc-200 pb-2 text-sm font-bold text-rose-500 dark:border-zinc-800">
                                          <AlertCircle size={16} /> Code Review Findings
                                        </h3>
                                        <div className="max-h-[150px] overflow-auto space-y-2">
                                          {problem.review.findings.map((f, i) => (
                                            <div key={i} className="rounded border border-red-200 bg-red-50/50 p-2 text-xs dark:border-red-950 dark:bg-red-950/20">
                                              <span className="font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">{f.severity}</span>: {f.title}
                                              <p className="mt-1 text-zinc-600 dark:text-zinc-400">{f.detail}</p>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </>
                      );
                    })}
                    {filtered.length === 0 && (
                      <tr>
                        <td colSpan={6} className="px-6 py-10 text-center text-zinc-500">
                          No problems match your query or filters.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {activeTab === "analytics" && stats && (
          <section className="flex flex-col gap-6">
            {/* Row 1: Difficulty & Topic Breakdown */}
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="panel flex flex-col items-center">
                <h2 className="self-start text-lg font-bold border-b border-zinc-200 pb-2 w-full mb-4 dark:border-zinc-800">Difficulty Distribution</h2>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={difficultyData} dataKey="value" nameKey="name" outerRadius={90} label line>
                      {difficultyData.map((entry) => (
                        <Cell key={entry.name} fill={difficultyColors[entry.name as keyof typeof difficultyColors]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: "8px" }} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="panel">
                <h2 className="text-lg font-bold border-b border-zinc-200 pb-2 w-full mb-4 dark:border-zinc-800">Top 10 Topics</h2>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={topicData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                    <XAxis dataKey="name" stroke="#888888" fontSize={11} tickLine={false} />
                    <YAxis allowDecimals={false} stroke="#888888" fontSize={11} tickLine={false} />
                    <Tooltip contentStyle={{ borderRadius: "8px" }} />
                    <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Row 2: Runtimes & Detected Patterns */}
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="panel">
                <h2 className="text-lg font-bold border-b border-zinc-200 pb-2 w-full mb-4 dark:border-zinc-800">Runtime Distribution</h2>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={runtimeData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                    <XAxis dataKey="name" stroke="#888888" fontSize={11} />
                    <YAxis allowDecimals={false} stroke="#888888" fontSize={11} />
                    <Tooltip contentStyle={{ borderRadius: "8px" }} />
                    <Bar dataKey="value" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="panel">
                <h2 className="text-lg font-bold border-b border-zinc-200 pb-2 w-full mb-4 dark:border-zinc-800">Detected Patterns</h2>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={patternData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                    <XAxis dataKey="name" stroke="#888888" fontSize={11} tickLine={false} />
                    <YAxis allowDecimals={false} stroke="#888888" fontSize={11} tickLine={false} />
                    <Tooltip contentStyle={{ borderRadius: "8px" }} />
                    <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Row 3: Heatmap */}
            <div className="panel">
              <div className="border-b border-zinc-200 pb-3 mb-4 dark:border-zinc-800 flex items-center justify-between">
                <h2 className="text-lg font-bold">Activity Heatmap</h2>
                <span className="text-xs text-zinc-500 font-medium">Last 35 days of submissions</span>
              </div>
              <div className="flex flex-wrap gap-2 justify-center py-4">
                {heatmapData.map(([day, count]) => (
                  <div
                    key={day}
                    title={`${day}: ${count} submission(s)`}
                    className={`h-8 w-8 rounded-md flex items-center justify-center font-bold text-xs transition-transform hover:scale-110 border ${
                      count > 0
                        ? "bg-emerald-500 border-emerald-600 text-white dark:bg-emerald-600 dark:border-emerald-700"
                        : "bg-zinc-100 border-zinc-200 text-zinc-405 dark:bg-zinc-900 dark:border-zinc-800"
                    }`}
                  >
                    {count > 0 ? count : ""}
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {activeTab === "sync" && (
          <section className="grid gap-6 lg:grid-cols-2">
            {/* Sync Logs */}
            <div className="panel">
              <h2 className="text-lg font-bold border-b border-zinc-200 pb-2 mb-4 dark:border-zinc-800">Sync Events</h2>
              <div className="space-y-3">
                {(syncStatus?.events ?? []).slice(0, 10).map((event, idx) => (
                  <div key={idx} className="status-row bg-white hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-950 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-2 rounded-full bg-emerald-500" />
                      <span className="font-semibold text-sm">{event.event}</span>
                    </div>
                    <span className="text-xs font-mono text-zinc-500">
                      {new Date(event.created_at * 1000).toLocaleString()}
                    </span>
                  </div>
                ))}
                {!syncStatus?.events?.length && (
                  <p className="text-center text-sm py-10 text-zinc-500">No sync events registered yet.</p>
                )}
              </div>
            </div>

            {/* Sync Queue Monitor */}
            <div className="panel flex flex-col gap-4">
              <div className="border-b border-zinc-200 pb-2 mb-2 dark:border-zinc-800 flex items-center justify-between">
                <h2 className="text-lg font-bold">Failed Sync Queue</h2>
                <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-bold text-red-800 dark:bg-red-950 dark:text-red-300">
                  {syncStatus?.queue_depth ?? 0} Pending
                </span>
              </div>
              <div className="flex-1 overflow-auto max-h-[400px] space-y-3">
                {syncStatus?.queued_retries && syncStatus.queued_retries.length > 0 ? (
                  syncStatus.queued_retries.map((item, idx) => (
                    <div key={idx} className="rounded-lg border border-red-200/80 bg-red-50/20 p-4 dark:border-red-950/40 dark:bg-red-950/10">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-xs text-red-700 dark:text-red-400 uppercase tracking-wider">{item.action}</span>
                        <span className="text-[10px] text-zinc-500 font-mono">Attempts: {item.attempts}</span>
                      </div>
                      <p className="font-bold text-xs text-red-900 dark:text-red-200 break-words">{item.error}</p>
                      <pre className="mt-2 overflow-auto bg-zinc-950 p-2 rounded text-[10px] font-mono text-zinc-300">
                        {JSON.stringify(item.payload, null, 2)}
                      </pre>
                    </div>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-zinc-500">
                    <CheckCircle2 size={36} className="text-emerald-500 mb-2" />
                    <p className="text-sm font-semibold">All synced successfully!</p>
                    <p className="text-xs">No failed items in queue.</p>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}
      </section>
    </main>
  );
}

function MetricCard({
  label,
  value,
  suffix = "",
  icon,
  colorClass = ""
}: {
  label: string;
  value: number;
  suffix?: string;
  icon?: React.ReactNode;
  colorClass?: string;
}) {
  return (
    <div className={`panel shadow-sm hover:shadow-md transition-shadow bg-white/60 dark:bg-zinc-900/60 ${colorClass}`}>
      <div className="flex items-center justify-between text-zinc-500 dark:text-zinc-400">
        <span className="text-xs font-semibold uppercase tracking-wider">{label}</span>
        {icon}
      </div>
      <p className="mt-2 text-3xl font-extrabold tracking-tight">
        {value} <span className="text-xs font-normal text-zinc-500">{suffix}</span>
      </p>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
