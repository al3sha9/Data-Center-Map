import type {
  RegionalDemandRecord,
  ModelComparisonRecord,
  UsModelComparisonRecord,
} from "../types/data";

export function formatVal(
  val: number | null | undefined,
  min: number | null | undefined,
  max: number | null | undefined
): string {
  if (min != null && max != null) {
    return `${min}-${max}`;
  }
  if (val != null) return val.toLocaleString();
  return "N/A";
}

export interface RegionalGroup {
  name: string;
  records: RegionalDemandRecord[];
  current?: RegionalDemandRecord;
  projection2030?: RegionalDemandRecord;
}

export function groupRegionalDemand(
  records: RegionalDemandRecord[]
): RegionalGroup[] {
  const groups = new Map<string, RegionalGroup>();

  for (const r of records) {
    const key = r.country || r.region;
    if (!groups.has(key)) {
      groups.set(key, { name: key, records: [] });
    }
    groups.get(key)!.records.push(r);
  }

  const result = Array.from(groups.values());

  for (const g of result) {
    const historical = g.records.filter((r) => r.projection_year == null);
    if (historical.length > 0) {
      g.current = historical.reduce((prev, current) =>
        prev.year > current.year ? prev : current
      );
    }

    const proj2030 = g.records.filter((r) => r.projection_year === 2030);
    if (proj2030.length > 0) {
      // Pick the first 2030 projection
      g.projection2030 = proj2030[0];
    }
  }

  // Sort by region name
  return result.sort((a, b) => a.name.localeCompare(b.name));
}

export function getGlobalProjections(records: ModelComparisonRecord[]) {
  return records.filter((r) => r.projection_year === 2030);
}

export function getUsProjections(records: UsModelComparisonRecord[]) {
  return records.filter(
    (r) => r.projection_year === 2030 || r.projection_year === 2028
  );
}
