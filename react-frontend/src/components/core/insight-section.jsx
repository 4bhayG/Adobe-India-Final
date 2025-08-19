import React from "react";
import { useSelector } from "react-redux";
import {
  X,
  Lightbulb,
  HelpCircle,
  AlertTriangle,
  ChevronsRight,
} from "lucide-react";

const SkeletonLoader = () => (
  <div className="p-4 space-y-8 animate-pulse">
    {[...Array(3)].map((_, i) => (
      <div key={i} className="space-y-4">
        <div className="h-7 bg-zinc-900 rounded w-1/2"></div>
        <div className="space-y-3 pl-4">
          <div className="h-4 bg-zinc-900 rounded w-full"></div>
          <div className="h-4 bg-zinc-900 rounded w-5/6"></div>
        </div>
      </div>
    ))}
  </div>
);

const InsightSection = ({ title, icon, items, colorClass }) => {
  if (!items || items.length === 0) return null;

  const cleanText = (text) => text.replace(/\\n/g, " ").trim();

  return (
    <div className="p-5 bg-zinc-950 rounded-xl border border-zinc-800/80">
      <h3
        className={`text-xl font-bold ${colorClass} flex items-center gap-3 mb-4`}
      >
        {icon}
        {title}
      </h3>
      <ul className="space-y-3">
        {items.map((item, index) => (
          <li key={index} className="flex items-start gap-3">
            <ChevronsRight
              className={`h-5 w-5 mt-0.5 flex-shrink-0 ${colorClass}`}
            />
            <span className="text-neutral-300">{cleanText(item)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default function InsightSectionsPanel({ onClose }) {
  const { insights, insightsLoading } = useSelector((state) => state.pdfs);

  const parseInsightField = (field) => {
    if (!field) return [];
    try {
      return typeof field === "string" ? JSON.parse(field) : field;
    } catch (error) {
      console.error("Failed to parse insight field:", error, field);
      return [];
    }
  };

  const hasInsights =
    insights &&
    (parseInsightField(insights.key_insights).length > 0 ||
      parseInsightField(insights.did_you_know).length > 0 ||
      parseInsightField(insights.counterpoints).length > 0);

  return (
    <div className="w-full h-full bg-black/90 backdrop-blur-lg border border-zinc-800 rounded-2xl shadow-2xl shadow-black/50 flex flex-col">
      <div className="flex justify-between items-center p-4 border-b border-zinc-800 flex-shrink-0">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Lightbulb className="text-red-500" />
          Document Insights
        </h2>
        <button
          onClick={onClose}
          className="p-1.5 text-neutral-400 hover:bg-red-600 hover:text-white rounded-full transition-colors"
        >
          <X size={20} />
        </button>
      </div>
      <div className="overflow-y-auto flex-1 p-4">
        {insightsLoading ? (
          <SkeletonLoader />
        ) : !insights || !hasInsights ? (
          <div className="flex flex-col items-center justify-center h-full text-zinc-500 px-6 text-center">
            <p className="text-lg font-semibold">No Insights Generated</p>
            <p className="text-sm">
              Click the "Insights" button again to analyze the documents.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            <InsightSection
              title="Key Insights"
              icon={<Lightbulb />}
              items={parseInsightField(insights.key_insights)}
              colorClass="text-yellow-400"
            />
            <InsightSection
              title="Did You Know?"
              icon={<HelpCircle />}
              items={parseInsightField(insights.did_you_know)}
              colorClass="text-blue-400"
            />
            <InsightSection
              title="Counterpoints"
              icon={<AlertTriangle />}
              items={parseInsightField(insights.counterpoints)}
              colorClass="text-red-500"
            />
          </div>
        )}
      </div>
    </div>
  );
}
