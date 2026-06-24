import React from "react";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
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

const QUALITY_STYLE: Record<string, string> = {
  high: "bg-[#EDF3EC] text-[#346538]",
  "medium-high": "bg-[#E6F3E6] text-[#2C552F]",
  medium: "bg-[#FBF3DB] text-[#956400]",
  "low-medium": "bg-[#FDEBEC] text-[#9F2F2D]",
  low: "bg-[#FDEBEC] text-[#9F2F2D]",
  na: "bg-[#F7F6F3] text-[#787774]",
};

export function DataCard({
  title,
  year,
  projectionYear,
  val,
  valMin,
  valMax,
  unit = "TWh",
  quality,
  fields,
  note,
  index = 0,
}: {
  title: string;
  year?: number | null;
  projectionYear?: number | null;
  val?: number | null;
  valMin?: number | null;
  valMax?: number | null;
  unit?: string;
  quality?: string;
  fields?: { label: string; value: React.ReactNode }[];
  note?: string;
  index?: number;
}) {
  const isRange = valMin != null && valMax != null;
  const displayVal = isRange
    ? `${valMin} - ${valMax}`
    : val != null
    ? val.toLocaleString()
    : "N/A";
  const isProj = projectionYear != null;
  const displayYear = isProj ? projectionYear : year;

  return (
    <div
      className="fade-in border border-[#EAEAEA] rounded-[8px] bg-white p-5 h-full flex flex-col"
      style={{ "--index": index } as React.CSSProperties}
    >
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="text-base font-medium text-[#111111] mb-1">{title}</h3>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-serif tracking-tight text-[#4F39F6] leading-none">
              {displayVal}
              <span className="text-sm text-[#787774] font-sans ml-1.5">
                {unit}
              </span>
            </span>
          </div>
        </div>
        {quality && (
          <span
            className={`shrink-0 text-[10px] uppercase tracking-[0.06em] px-2.5 py-1 rounded-full font-mono ${
              QUALITY_STYLE[quality] ?? QUALITY_STYLE["na"]
            }`}
          >
            {quality}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-3 border-t border-[#EAEAEA] pt-4 flex-1">
        <Field label="Year">
          {displayYear}{" "}
          {isProj && <span className="text-[#787774] text-xs ml-1">(Proj.)</span>}
        </Field>
        {fields?.map((f, i) => (
          <Field key={i} label={f.label}>
            {f.value}
          </Field>
        ))}
      </div>

      {note && (
        <p className="text-xs text-[#787774] leading-relaxed mt-4 pt-3 border-t border-[#EAEAEA]">
          {note}
        </p>
      )}
    </div>
  );
}
