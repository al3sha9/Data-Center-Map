import { useState } from "react";
import { Map, MapMarker, MarkerContent, MarkerTooltip } from "./ui/map";
import { REGION_COORDINATES, calculateBubbleRadius } from "../lib/map-utils";
import type { RegionalGroup } from "../lib/data-utils";

import { formatVal } from "../lib/data-utils";

export function EnergyMap({ groups }: { groups: RegionalGroup[] }) {
  const [show2030, setShow2030] = useState(false);

  return (
    <div className="relative w-full h-[500px] md:h-[600px] border border-[#EAEAEA] rounded-[12px] overflow-hidden bg-[#FBFBFA]">
      <Map
        theme="light"
        viewport={{
          center: [10, 25],
          zoom: 1.2,
          pitch: 0,
        }}
        className="w-full h-full"
        scrollZoom={false}
        doubleClickZoom={false}
        boxZoom={false}
        touchZoomRotate={false}
      >
        {groups.map((g) => {
          const coords = REGION_COORDINATES[g.name];
          if (!coords) return null;

          // Fallback to current if projection is missing, so countries don't disappear
          const record = show2030 ? (g.projection2030 || g.current) : g.current;
          if (!record) return null;

          const radius = calculateBubbleRadius(
            record.value_twh,
            record.value_min_twh,
            record.value_max_twh
          );

          const currentVal = g.current
            ? formatVal(
                g.current.value_twh,
                g.current.value_min_twh,
                g.current.value_max_twh
              )
            : "N/A";

          const projVal = g.projection2030
            ? formatVal(
                g.projection2030.value_twh,
                g.projection2030.value_min_twh,
                g.projection2030.value_max_twh
              )
            : "N/A";

          return (
            <MapMarker key={g.name} longitude={coords[0]} latitude={coords[1]}>
              <MarkerContent>
                <div
                  className="rounded-full bg-[#111111]/20 border border-[#111111]/40 backdrop-blur-[2px] transition-all duration-300 shadow-sm"
                  style={{ width: radius * 2, height: radius * 2 }}
                />
              </MarkerContent>
              <MarkerTooltip>
                <div className="flex flex-col gap-1.5 p-1 max-w-[220px]">
                  <p className="font-medium text-[#111111]">{g.name}</p>
                  
                  {currentVal !== "N/A" && (
                    <div className="text-xs text-[#787774] font-mono">
                      Current: {currentVal} TWh
                    </div>
                  )}
                  
                  {projVal !== "N/A" && (
                    <div className="text-xs text-[#787774] font-mono">
                      2030 Proj: {projVal} TWh
                    </div>
                  )}

                  {record.share_percent != null && (
                    <div className="text-xs text-[#787774]">
                      Share: {record.share_percent}%
                    </div>
                  )}
                  

                  
                  {record.note && (
                    <p className="text-[10px] text-[#787774] mt-1 border-t border-[#EAEAEA] pt-1 leading-relaxed line-clamp-3">
                      {record.note}
                    </p>
                  )}
                </div>
              </MarkerTooltip>
            </MapMarker>
          );
        })}
      </Map>

      <div className="absolute top-6 right-6 z-10 flex p-1 bg-white/80 backdrop-blur-md border border-[#EAEAEA] rounded-full shadow-[0_8px_30px_rgb(0,0,0,0.08)]">
        <button
          onClick={() => setShow2030(false)}
          className={`px-5 py-2 text-sm font-medium rounded-full transition-all duration-300 ease-out ${
            !show2030 
              ? "bg-[#4F39F6] text-white shadow-md" 
              : "text-[#787774] hover:text-[#111111] hover:bg-gray-100/50"
          }`}
        >
          Today
        </button>
        <button
          onClick={() => setShow2030(true)}
          className={`px-5 py-2 text-sm font-medium rounded-full transition-all duration-300 ease-out ${
            show2030 
              ? "bg-[#4F39F6] text-white shadow-md" 
              : "text-[#787774] hover:text-[#111111] hover:bg-gray-100/50"
          }`}
        >
          2030 Proj
        </button>
      </div>
    </div>
  );
}
