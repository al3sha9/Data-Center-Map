import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

export function ExpandableRow({
  header,
  details,
}: {
  header: React.ReactNode;
  details: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border-b border-[#EAEAEA] last:border-0 group">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left p-4 hover:bg-[#F7F6F3] transition-colors focus:outline-none"
      >
        <div className="flex-1 pr-4">{header}</div>
        <div className="shrink-0 text-[#787774]">
          {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="p-4 pt-4 text-sm text-[#787774] border-t border-[#EAEAEA] bg-[#FBFBFA]">
              {details}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function DataTable({ children }: { children: React.ReactNode }) {
  return (
    <div className="border border-[#EAEAEA] rounded-[8px] bg-white overflow-hidden shadow-sm">
      {children}
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

export function QualityBadge({ quality }: { quality: string | undefined }) {
  if (!quality || quality === "na") return null;
  return (
    <span
      className={`shrink-0 text-[10px] uppercase tracking-[0.06em] px-2.5 py-1 rounded-full font-mono ${
        QUALITY_STYLE[quality] ?? QUALITY_STYLE["na"]
      }`}
    >
      {quality}
    </span>
  );
}
