import { useState, useEffect } from "react";
import type {
  EnergyRecord,
  Source,
  Meta,
  ModelComparisonRecord,
  UsModelComparisonRecord,
  RegionalDemandRecord,
} from "../types/data";

interface DataState {
  records: EnergyRecord[];
  sources: Source[];
  meta: Meta | null;
  modelComparison: ModelComparisonRecord[];
  usModelComparison: UsModelComparisonRecord[];
  regionalDemand: RegionalDemandRecord[];
  loading: boolean;
  error: string | null;
}

export function useEnergyData(): DataState {
  const [state, setState] = useState<DataState>({
    records: [],
    sources: [],
    meta: null,
    modelComparison: [],
    usModelComparison: [],
    regionalDemand: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    Promise.all([
      fetch("/data/energy-demand.json").then((r) => r.json()),
      fetch("/data/sources.json").then((r) => r.json()),
      fetch("/data/meta.json").then((r) => r.json()),
      fetch("/data/model-comparison.json").then((r) => r.json()),
      fetch("/data/us-model-comparison.json").then((r) => r.json()),
      fetch("/data/regional-demand.json").then((r) => r.json()),
    ])
      .then(
        ([
          records,
          sources,
          meta,
          modelComparison,
          usModelComparison,
          regionalDemand,
        ]) => {
          setState({
            records,
            sources,
            meta,
            modelComparison,
            usModelComparison,
            regionalDemand,
            loading: false,
            error: null,
          });
        }
      )
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
