import { useEnergyData } from "../hooks/useEnergyData";
import type { EnergyRecord, Source } from "../types/data";

/* ─── helpers ─────────────────────────────────────────── */

const SCENARIO_LABELS: Record<string, string> = {
  estimate: "Estimate",
  headwinds: "Headwinds",
  high_efficiency: "High efficiency",
  base: "Base case",
  lift_off: "Lift-off",
};

const CONFIDENCE_STYLE: Record<string, string> = {
  high: "bg-[#EDF3EC] text-[#346538]",
  medium: "bg-[#FBF3DB] text-[#956400]",
  low: "bg-[#FDEBEC] text-[#9F2F2D]",
};

function scenarioLabel(s: string) {
  return SCENARIO_LABELS[s] ?? s;
}

function sourceFor(sourceId: string, sources: Source[]) {
  return sources.find((s) => s.id === sourceId) ?? null;
}

/* ─── stat card ────────────────────────────────────────── */

function StatCard({
  label,
  value,
  unit,
  sub,
  index,
}: {
  label: string;
  value: number;
  unit: string;
  sub?: string;
  index: number;
}) {
  return (
    <div
      className="fade-in border border-[#EAEAEA] rounded-[8px] p-6 bg-white"
      style={{ "--index": index } as React.CSSProperties}
    >
      <p className="text-xs uppercase tracking-[0.08em] text-[#787774] mb-3 font-mono">
        {label}
      </p>
      <p className="text-4xl font-serif tracking-tight text-[#111111] leading-none">
        {value.toLocaleString()}
        <span className="text-base text-[#787774] ml-1 font-sans">{unit}</span>
      </p>
      {sub && (
        <p className="text-xs text-[#787774] mt-2">{sub}</p>
      )}
    </div>
  );
}

/* ─── SVG bar chart ─────────────────────────────────────── */

function BarChart({ records }: { records: EnergyRecord[] }) {
  const W = 640;
  const H = 220;
  const PAD = { top: 16, right: 16, bottom: 40, left: 56 };
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;

  const max = Math.max(...records.map((r) => r.value)) * 1.1;
  const barW = Math.floor(innerW / records.length) - 8;

  const y = (v: number) => PAD.top + innerH - (v / max) * innerH;
  const barH = (v: number) => (v / max) * innerH;

  const ticks = [0, 400, 800, 1200];

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      role="img"
      aria-label="Bar chart of data center electricity demand"
    >
      {/* grid lines */}
      {ticks.map((t) => (
        <g key={t}>
          <line
            x1={PAD.left}
            x2={W - PAD.right}
            y1={y(t)}
            y2={y(t)}
            stroke="#EAEAEA"
            strokeWidth={1}
          />
          <text
            x={PAD.left - 8}
            y={y(t) + 4}
            textAnchor="end"
            fontSize={10}
            fill="#787774"
            fontFamily="'JetBrains Mono', 'SF Mono', monospace"
          >
            {t}
          </text>
        </g>
      ))}

      {/* bars */}
      {records.map((r, i) => {
        const x = PAD.left + i * (innerW / records.length) + 4;
        const bh = barH(r.value);
        const by = y(r.value);
        const isBaseline = r.year === 2024;

        return (
          <g key={r.id}>
            <rect
              x={x}
              y={by}
              width={barW}
              height={bh}
              fill={isBaseline ? "#111111" : "#EAEAEA"}
              rx={3}
            />
            {/* value label */}
            <text
              x={x + barW / 2}
              y={by - 6}
              textAnchor="middle"
              fontSize={10}
              fill="#111111"
              fontFamily="'JetBrains Mono', 'SF Mono', monospace"
              fontWeight={isBaseline ? "600" : "400"}
            >
              {r.value}
            </text>
            {/* x-axis label */}
            <text
              x={x + barW / 2}
              y={H - PAD.bottom + 14}
              textAnchor="middle"
              fontSize={9}
              fill="#787774"
              fontFamily="'Helvetica Neue', sans-serif"
            >
              {r.year}
            </text>
            <text
              x={x + barW / 2}
              y={H - PAD.bottom + 26}
              textAnchor="middle"
              fontSize={9}
              fill="#787774"
              fontFamily="'Helvetica Neue', sans-serif"
            >
              {scenarioLabel(r.scenario)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/* ─── record detail card ────────────────────────────────── */

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-[0.08em] text-[#787774] font-mono mb-0.5">
        {label}
      </p>
      <div className="text-sm text-[#111111]">{children}</div>
    </div>
  );
}

function RecordRow({
  record,
  source,
  index,
}: {
  record: EnergyRecord;
  source: Source | null;
  index: number;
}) {
  return (
    <div
      className="fade-in border border-[#EAEAEA] rounded-[8px] bg-white p-5 mb-3"
      style={{ "--index": index } as React.CSSProperties}
    >
      {/* top row: value + confidence badge */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <p className="text-3xl font-serif tracking-tight text-[#111111] leading-none">
          {record.value.toLocaleString()}
          <span className="text-base text-[#787774] font-sans ml-1.5">{record.unit}</span>
        </p>
        <span
          className={`shrink-0 text-[10px] uppercase tracking-[0.06em] px-2.5 py-1 rounded-full font-mono ${
            CONFIDENCE_STYLE[record.confidence] ?? "bg-[#F7F6F3] text-[#787774]"
          }`}
        >
          {record.confidence} confidence
        </span>
      </div>

      {/* field grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3 border-t border-[#EAEAEA] pt-4">
        <Field label="Year">{record.year}</Field>
        <Field label="Scenario">{scenarioLabel(record.scenario)}</Field>
        <Field label="Unit">{record.unit}</Field>

        <Field label="Source">
          {source ? (
            <span>
              {source.name}
              {source.publisher && (
                <span className="text-[#787774]"> · {source.publisher}</span>
              )}
            </span>
          ) : (
            <span className="text-[#787774]">{record.source_label}</span>
          )}
        </Field>

        <Field label="Page">
          <span className="font-mono">p.{record.source_page}</span>
        </Field>

        <Field label="Region">{record.region}</Field>
      </div>

      {/* note */}
      {record.note && (
        <p className="text-xs text-[#787774] leading-relaxed mt-3 pt-3 border-t border-[#EAEAEA]">
          {record.note}
        </p>
      )}
    </div>
  );
}

/* ─── main page ─────────────────────────────────────────── */

export function HomePage() {
  const { records, sources, meta, loading, error } = useEnergyData();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-[#787774]">
        Loading dataset…
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-[#9F2F2D]">
        {error}
      </div>
    );
  }

  const baseline = records.find((r) => r.year === 2024);
  const projections = records.filter((r) => r.year === 2030);
  const maxProjection = projections.reduce(
    (a, b) => (b.value > a.value ? b : a),
    projections[0],
  );
  const minProjection = projections.reduce(
    (a, b) => (b.value < a.value ? b : a),
    projections[0],
  );

  return (
    <div className="min-h-screen bg-[#FBFBFA]">
      {/* nav */}
      <header className="border-b border-[#EAEAEA] bg-white sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 h-12 flex items-center justify-between">
          <span className="text-sm font-medium text-[#111111] tracking-tight font-mono">
            Data Center Map
          </span>
          {meta && (
            <span className="text-xs text-[#787774] font-mono">
              v{meta.version} · updated {meta.last_updated}
            </span>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-16 space-y-16">
        {/* hero */}
        <section className="fade-in" style={{ "--index": 0 } as React.CSSProperties}>
          <p className="text-xs uppercase tracking-[0.1em] text-[#787774] mb-4 font-mono">
            Global · Electricity Demand
          </p>
          <h1 className="font-serif text-4xl md:text-5xl text-[#111111] tracking-[-0.03em] leading-[1.1] max-w-2xl">
            How data centers are reshaping global electricity demand
          </h1>
          <p className="text-[#787774] mt-4 max-w-xl leading-relaxed text-sm">
            A visual map of how data centers and AI infrastructure are changing
            global electricity demand.
          </p>
        </section>

        {/* stat cards */}
        <section>
          <p className="text-xs uppercase tracking-[0.08em] text-[#787774] mb-5 font-mono">
            Key figures
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {baseline && (
              <StatCard
                index={1}
                label="2024 Baseline"
                value={baseline.value}
                unit={baseline.unit}
                sub={`${scenarioLabel(baseline.scenario)} scenario · ${baseline.source_label}`}
              />
            )}
            {minProjection && (
              <StatCard
                index={2}
                label="2030 Low projection"
                value={minProjection.value}
                unit={minProjection.unit}
                sub={`${scenarioLabel(minProjection.scenario)} · ${minProjection.confidence} confidence`}
              />
            )}
            {maxProjection && (
              <StatCard
                index={3}
                label="2030 High projection"
                value={maxProjection.value}
                unit={maxProjection.unit}
                sub={`${scenarioLabel(maxProjection.scenario)} · ${maxProjection.confidence} confidence`}
              />
            )}
          </div>
        </section>

        {/* chart */}
        <section
          className="fade-in border border-[#EAEAEA] rounded-[12px] bg-white p-8"
          style={{ "--index": 4 } as React.CSSProperties}
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-xs uppercase tracking-[0.08em] text-[#787774] font-mono mb-1">
                Chart
              </p>
              <h2 className="text-base font-medium text-[#111111]">
                Data center electricity demand (TWh)
              </h2>
            </div>
            <div className="flex items-center gap-4 text-xs text-[#787774] font-mono">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 bg-[#111111] rounded-sm inline-block" />
                2024
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 bg-[#EAEAEA] border border-[#EAEAEA] rounded-sm inline-block" />
                2030
              </span>
            </div>
          </div>
          <BarChart records={records} />
        </section>

        {/* all records detail */}
        <section className="fade-in" style={{ "--index": 5 } as React.CSSProperties}>
          <p className="text-xs uppercase tracking-[0.08em] text-[#787774] mb-5 font-mono">
            All records · {records.length} total
          </p>
          <div>
            {records.map((r, i) => (
              <RecordRow
                key={r.id}
                record={r}
                source={sourceFor(r.source_id, sources)}
                index={i + 6}
              />
            ))}
          </div>
        </section>

        {/* disclaimer */}
        <section
          className="fade-in border-t border-[#EAEAEA] pt-8"
          style={{ "--index": 11 } as React.CSSProperties}
        >
          <p className="text-xs uppercase tracking-[0.08em] text-[#787774] mb-3 font-mono">
            Disclaimer
          </p>
          {meta?.disclaimer && (
            <p className="text-xs text-[#787774] leading-relaxed max-w-2xl">
              {meta.disclaimer}
            </p>
          )}
          <p className="text-xs text-[#787774] leading-relaxed max-w-2xl mt-2">
            All figures are drawn from public research estimates and scenario
            modelling. This site does not reflect live or operational
            measurements.
          </p>
        </section>
      </main>

      <footer className="border-t border-[#EAEAEA] mt-16">
        <div className="max-w-5xl mx-auto px-6 py-6 flex items-center justify-between">
          <span className="text-xs text-[#787774] font-mono">Data Center Map</span>
          {meta && (
            <span className="text-xs text-[#787774] font-mono">
              {meta.total_records} records · {meta.source_count} sources
            </span>
          )}
        </div>
      </footer>
    </div>
  );
}
