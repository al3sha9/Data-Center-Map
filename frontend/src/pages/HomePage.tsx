import { useState } from "react";
import { Header } from "../components/Header";
import { useEnergyData } from "../hooks/useEnergyData";
import type { EnergyRecord } from "../types/data";
import {
  DataTable,
  ExpandableRow,
  QualityBadge,
} from "../components/DataTable";
import {
  formatVal,
  groupRegionalDemand,
  getGlobalProjections,
  getUsProjections,
} from "../lib/data-utils";
import { EnergyMap } from "../components/EnergyMap";

/* ─── helpers ─────────────────────────────────────────── */

const SCENARIO_LABELS: Record<string, string> = {
  estimate: "Today’s estimate",
  headwinds: "Lower 2030 estimate",
  high_efficiency: "Efficiency improves",
  base: "Expected 2030 estimate",
  lift_off: "Higher 2030 estimate",
};

function scenarioLabel(s: string) {
  return SCENARIO_LABELS[s] ?? s;
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
              fill={isBaseline ? "#4F39F6" : "#EAEAEA"}
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

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  if (!children) return null;
  return (
    <div>
      <p className="text-[10px] uppercase tracking-[0.08em] text-[#787774] font-mono mb-0.5">
        {label}
      </p>
      <div className="text-sm text-[#111111]">{children}</div>
    </div>
  );
}

/* ─── main page ─────────────────────────────────────────── */

export function HomePage() {
  const {
    records,
    meta,
    modelComparison,
    usModelComparison,
    regionalDemand,
    loading,
    error,
  } = useEnergyData();

  const [showAllGlobal, setShowAllGlobal] = useState(false);
  const [showAllUs, setShowAllUs] = useState(false);

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
  const maxProjection = projections.length
    ? projections.reduce((a, b) => (b.value > a.value ? b : a), projections[0])
    : null;
  const minProjection = projections.length
    ? projections.reduce((a, b) => (b.value < a.value ? b : a), projections[0])
    : null;

  const regionalGroups = groupRegionalDemand(regionalDemand);

  const usShehabi = usModelComparison.find((r) => r.institution === "Shehabi et al." && r.year === 2023);
  const usProjection = usModelComparison.find((r) => r.institution === "Shehabi et al." && r.projection_year === 2028) || 
                       usModelComparison.find((r) => r.institution === "EPRI" && r.projection_year === 2030);

  if (usShehabi || usProjection) {
    regionalGroups.push({
      name: "United States",
      current: usShehabi ? {
        value_twh: usShehabi.value_twh,
        value_min_twh: usShehabi.value_min_twh,
        value_max_twh: usShehabi.value_max_twh,
        share_percent: usShehabi.share_percent,
        quality_assessment: usShehabi.quality_assessment,
        note: usShehabi.note || usShehabi.method_summary,
      } as any : undefined,
      projection2030: usProjection ? {
        value_twh: usProjection.value_twh,
        value_min_twh: usProjection.value_min_twh,
        value_max_twh: usProjection.value_max_twh,
        share_percent: usProjection.share_percent,
        quality_assessment: usProjection.quality_assessment,
        note: usProjection.note || usProjection.method_summary,
      } as any : undefined,
      records: [],
    });
  }

  const globalProjections = showAllGlobal
    ? modelComparison
    : getGlobalProjections(modelComparison);

  const usProjections = showAllUs
    ? usModelComparison
    : getUsProjections(usModelComparison);



  return (
    <div className="min-h-screen bg-[#FBFBFA]">
      {/* nav */}
      <Header />

      <main className="max-w-6xl mx-auto px-6 py-10 md:py-16 space-y-24 md:space-y-32">
        {/* hero / map section */}
        <section
          className="fade-in relative"
          style={{ "--index": 0 } as React.CSSProperties}
        >
          <div className="mb-8">
            <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl text-[#111111] tracking-[-0.03em] leading-[1.1] max-w-4xl">
              How much electricity could data centers use?
            </h1>
            <p className="text-[#787774] mt-4 max-w-xl leading-relaxed text-sm">
              Data centers already use hundreds of terawatt-hours of electricity each year. This site turns research reports into simple charts and maps so the trend is easier to understand.
            </p>
          </div>

          <div className="relative">
            {/* The Map Component */}
            <EnergyMap groups={regionalGroups} />

            {/* Floating Stat Card */}
            <div className="absolute bottom-6 left-6 z-10 w-56 md:w-64 flex flex-col pointer-events-none">
              <div className="bg-white/80 backdrop-blur-md border border-[#EAEAEA] p-5 rounded-[12px] shadow-sm pointer-events-auto">
                {baseline && (
                  <div className="mb-5">
                    <p className="text-[10px] uppercase tracking-[0.08em] text-[#787774] mb-1 font-mono">
                      Global 2024 Baseline
                    </p>
                    <p className="text-3xl font-serif tracking-tight text-[#4F39F6] leading-none">
                      {baseline.value.toLocaleString()}{" "}
                      <span className="text-sm font-sans text-[#787774]">
                        TWh
                      </span>
                    </p>
                  </div>
                )}
                {maxProjection && (
                  <div className="pt-4 border-t border-[#EAEAEA]">
                    <p className="text-[10px] uppercase tracking-[0.08em] text-[#787774] mb-1 font-mono">
                      2030 Projections
                    </p>
                    <p className="text-2xl font-serif tracking-tight text-[#4F39F6] leading-none">
                      {minProjection?.value.toLocaleString()} -{" "}
                      {maxProjection.value.toLocaleString()}{" "}
                      <span className="text-sm font-sans text-[#787774]">
                        TWh
                      </span>
                    </p>
                    <p className="text-[10px] text-[#787774] mt-2 line-clamp-2">
                      IEA scenario range
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* chart */}
        <section
          className="fade-in"
          style={{ "--index": 4 } as React.CSSProperties}
        >
          <div className="mb-8 max-w-2xl">
            <h2 className="text-3xl font-serif tracking-tight text-[#111111] mb-3">
              Global outlook
            </h2>
            <p className="text-[#787774] leading-relaxed text-sm">
              IEA estimates show data center electricity use could more than double by 2030.
            </p>
          </div>
          <div className="border border-[#EAEAEA] rounded-[12px] bg-white p-8 shadow-sm">
            <div className="flex items-center justify-between mb-8">
              <div>
                <p className="text-xs uppercase tracking-[0.08em] text-[#787774] font-mono mb-1">
                  Chart
                </p>
                <h3 className="text-base font-medium text-[#111111]">
                  Possible growth in data center electricity use
                </h3>
              </div>
              <div className="flex items-center gap-4 text-xs text-[#787774] font-mono">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-[#4F39F6] rounded-sm inline-block" />
                  2024
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-[#EAEAEA] border border-[#EAEAEA] rounded-sm inline-block" />
                  2030
                </span>
              </div>
            </div>
            <BarChart records={records} />
            <p className="text-xs text-[#787774] mt-6 text-center">
              These are not exact predictions. They show different possible futures depending on AI growth, efficiency, and grid constraints.
            </p>
          </div>
        </section>

        {/* Regional Demand */}
        <section
          className="fade-in"
          style={{ "--index": 5 } as React.CSSProperties}
        >
          <div className="mb-8 max-w-2xl">
            <h2 className="text-3xl font-serif tracking-tight text-[#111111] mb-3">
              Where demand is growing
            </h2>
            <p className="text-sm text-[#787774] leading-relaxed">
              Some countries and regions already use large amounts of electricity for data centers. Others may grow quickly by 2030.
            </p>
          </div>

          <DataTable>
            <div className="hidden md:grid grid-cols-3 gap-4 p-4 border-b border-[#EAEAEA] bg-[#FBFBFA] text-[10px] uppercase tracking-[0.08em] text-[#787774] font-mono">
              <div>Region / Country</div>
              <div>Current Estimate</div>
              <div>2030 Projection</div>
            </div>
            {regionalGroups.map((g) => {
              const currentVal = formatVal(
                g.current?.value_twh,
                g.current?.value_min_twh,
                g.current?.value_max_twh
              );
              const projVal = formatVal(
                g.projection2030?.value_twh,
                g.projection2030?.value_min_twh,
                g.projection2030?.value_max_twh
              );

              const header = (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                  <div className="font-medium text-[#4F39F6] text-base">
                    {g.name}
                  </div>
                  <div className="text-sm">
                    <span className="text-[#787774] block md:hidden text-xs mb-1">
                      Current
                    </span>
                    {currentVal !== "N/A" ? (
                      <span className="font-mono text-[#111111]">
                        {currentVal} TWh
                      </span>
                    ) : (
                      "—"
                    )}
                  </div>
                  <div className="text-sm">
                    <span className="text-[#787774] block md:hidden text-xs mb-1">
                      2030 Proj.
                    </span>
                    {projVal !== "N/A" ? (
                      <span className="font-mono text-[#111111]">
                        {projVal} TWh
                      </span>
                    ) : (
                      "—"
                    )}
                  </div>
                </div>
              );

              const details = (
                <div className="space-y-4">
                  <div className="font-mono text-[10px] uppercase tracking-[0.08em] text-[#787774] mb-2 border-b border-[#EAEAEA] pb-2">
                    All Recorded Estimates
                  </div>
                  {g.records.map((r, i) => (
                    <div
                      key={r.id || i}
                      className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3 pb-4 border-b border-[#EAEAEA] last:border-0 last:pb-0"
                    >
                      <Field label="Year">
                        {r.year} {r.projection_year ? "(Proj)" : ""}
                      </Field>
                      <Field label="Value (TWh)">
                        {formatVal(
                          r.value_twh,
                          r.value_min_twh,
                          r.value_max_twh
                        )}
                      </Field>
                      <Field label="Share">
                        {r.share_percent ? `${r.share_percent}%` : "—"}
                      </Field>
                      <Field label="Quality">
                        <QualityBadge quality={r.quality_assessment} />
                      </Field>
                      <div className="col-span-2 md:col-span-4 mt-1">
                        <Field label="Source">{r.source}</Field>
                      </div>
                      {r.note && (
                        <div className="col-span-2 md:col-span-4">
                          <p className="text-xs text-[#787774]">{r.note}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              );

              return (
                <ExpandableRow key={g.name} header={header} details={details} />
              );
            })}
          </DataTable>
        </section>

        {/* Global Model Comparison */}
        <section
          className="fade-in"
          style={{ "--index": 6 } as React.CSSProperties}
        >
          <div className="mb-8 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div className="max-w-2xl">
              <h2 className="text-3xl font-serif tracking-tight text-[#111111] mb-3">
                Why estimates vary
              </h2>
              <p className="text-sm text-[#787774] leading-relaxed">
                Different studies use different methods, so their numbers do not always match. This section shows the range instead of pretending there is one exact answer.
              </p>
            </div>
            <button
              onClick={() => setShowAllGlobal(!showAllGlobal)}
              className="shrink-0 px-4 py-2 text-xs font-mono uppercase tracking-[0.05em] bg-white border border-[#EAEAEA] rounded-md hover:bg-[#FBFBFA] transition-colors cursor-pointer"
            >
              {showAllGlobal ? "Show 2030 Only" : "Show All Models"}
            </button>
          </div>

          <DataTable>
            <div className="hidden md:grid grid-cols-3 gap-4 p-4 border-b border-[#EAEAEA] bg-[#FBFBFA] text-[10px] uppercase tracking-[0.08em] text-[#787774] font-mono">
              <div>Institution</div>
              <div>Year</div>
              <div>Value (TWh)</div>
            </div>
            {globalProjections.map((r) => {
              const val = formatVal(
                r.value_twh,
                r.value_min_twh,
                r.value_max_twh
              );
              const header = (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                  <div className="font-medium text-[#4F39F6] text-base">
                    {r.institution}
                  </div>
                  <div className="text-sm text-[#787774]">
                    {r.projection_year ? `${r.projection_year} (Proj)` : r.year}
                  </div>
                  <div className="text-sm font-mono text-[#111111]">
                    {val !== "N/A" ? `${val}` : "—"}
                  </div>
                </div>
              );

              const details = (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Field label="Quality">
                    <QualityBadge quality={r.quality_assessment} />
                  </Field>
                  <Field label="Publication">{r.publication}</Field>
                  <Field label="Source">{r.source}</Field>
                  <Field label="Includes Crypto">
                    {r.includes_crypto != null
                      ? r.includes_crypto
                        ? "Yes"
                        : "No"
                      : "Unknown"}
                  </Field>
                  <Field label="Includes AI">
                    {r.includes_ai != null
                      ? r.includes_ai
                        ? "Yes"
                        : "No"
                      : "Unknown"}
                  </Field>
                  {r.method_summary && (
                    <div className="col-span-1 sm:col-span-2">
                      <Field label="Method Summary">{r.method_summary}</Field>
                    </div>
                  )}
                  {r.note && (
                    <div className="col-span-1 sm:col-span-2">
                      <p className="text-xs text-[#787774]">{r.note}</p>
                    </div>
                  )}
                </div>
              );

              return (
                <ExpandableRow key={r.id} header={header} details={details} />
              );
            })}
          </DataTable>
        </section>

        {/* US Model Comparison */}
        <section
          className="fade-in"
          style={{ "--index": 7 } as React.CSSProperties}
        >
          <div className="mb-8 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div className="max-w-2xl">
              <h2 className="text-3xl font-serif tracking-tight text-[#111111] mb-3">
                United States outlook
              </h2>
              <p className="text-sm text-[#787774] leading-relaxed">
                The US is one of the largest data center markets, but estimates vary depending on the study.
              </p>
            </div>
            <button
              onClick={() => setShowAllUs(!showAllUs)}
              className="shrink-0 px-4 py-2 text-xs font-mono uppercase tracking-[0.05em] bg-white border border-[#EAEAEA] rounded-md hover:bg-[#FBFBFA] transition-colors cursor-pointer"
            >
              {showAllUs ? "Show 2030 Only" : "Show All Models"}
            </button>
          </div>

          <DataTable>
            <div className="hidden md:grid grid-cols-3 gap-4 p-4 border-b border-[#EAEAEA] bg-[#FBFBFA] text-[10px] uppercase tracking-[0.08em] text-[#787774] font-mono">
              <div>Institution</div>
              <div>Year</div>
              <div>Value (TWh)</div>
            </div>
            {usProjections.map((r) => {
              const val = formatVal(
                r.value_twh,
                r.value_min_twh,
                r.value_max_twh
              );
              const aiVal = formatVal(
                r.ai_value_twh,
                r.ai_value_min_twh,
                r.ai_value_max_twh
              );

              const header = (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                  <div className="font-medium text-[#4F39F6] text-base">
                    {r.institution}
                  </div>
                  <div className="text-sm text-[#787774]">
                    {r.projection_year ? `${r.projection_year} (Proj)` : r.year}
                  </div>
                  <div className="text-sm font-mono text-[#111111]">
                    {val !== "N/A" ? `${val}` : "—"}
                  </div>
                </div>
              );

              const details = (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Field label="Publication">{r.publication}</Field>
                  <Field label="Source">{r.source}</Field>
                  <Field label="AI Portion (TWh)">
                    {aiVal !== "N/A" ? aiVal : "Unknown"}
                  </Field>
                  <Field label="Share of US Grid">
                    {r.share_percent ? `${r.share_percent}%` : "Unknown"}
                  </Field>
                  <Field label="Quality">
                    <QualityBadge quality={r.quality_assessment} />
                  </Field>
                  {r.method_summary && (
                    <div className="col-span-1 sm:col-span-2">
                      <Field label="Method Summary">{r.method_summary}</Field>
                    </div>
                  )}
                  {r.note && (
                    <div className="col-span-1 sm:col-span-2">
                      <p className="text-xs text-[#787774]">{r.note}</p>
                    </div>
                  )}
                </div>
              );

              return (
                <ExpandableRow key={r.id} header={header} details={details} />
              );
            })}
          </DataTable>
        </section>

        {/* disclaimer */}
        <section
          className="fade-in border-t border-[#EAEAEA] pt-12"
          style={{ "--index": 11 } as React.CSSProperties}
        >
          <p className="text-[10px] uppercase tracking-[0.08em] text-[#787774] mb-4 font-mono">
            Methodology & Disclaimer
          </p>
          <p className="text-sm text-[#787774] leading-relaxed max-w-2xl mb-4">
            The Global Outlook section uses reviewed, high-confidence
            baseline records and projections. The comparison datasets show the
            range of uncertainty across different studies and models.
          </p>
          {meta?.disclaimer && (
            <p className="text-sm text-[#787774] leading-relaxed max-w-2xl">
              {meta.disclaimer}
            </p>
          )}
          <p className="text-sm text-[#787774] leading-relaxed max-w-2xl mt-4">
            All figures are drawn from public research estimates. This site does not reflect live or operational
            measurements.
          </p>
        </section>
      </main>


    </div>
  );
}
