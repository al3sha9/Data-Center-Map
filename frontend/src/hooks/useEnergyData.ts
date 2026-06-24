import { useState, useEffect } from "react";
import type { EnergyRecord, Source, Meta } from "../types/data";

interface DataState {
  records: EnergyRecord[];
  sources: Source[];
  meta: Meta | null;
  loading: boolean;
  error: string | null;
}

export function useEnergyData(): DataState {
  const [state, setState] = useState<DataState>({
    records: [],
    sources: [],
    meta: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    Promise.all([
      fetch("/data/energy-demand.json").then((r) => r.json()),
      fetch("/data/sources.json").then((r) => r.json()),
      fetch("/data/meta.json").then((r) => r.json()),
    ])
      .then(([records, sources, meta]) => {
        setState({ records, sources, meta, loading: false, error: null });
      })
      .catch((err) => {
        setState((s) => ({
          ...s,
          loading: false,
          error: err.message ?? "Failed to load data",
        }));
      });
  }, []);

  return state;
}
