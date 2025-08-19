import React from "react";
import { CloudCog, Book, BarChart, Search, Mic, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

const NavButton = ({ onClick, disabled, isLoading, icon, children }) => {
  const baseClasses =
    "flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all duration-200 rounded-lg";
  const enabledClasses = "text-neutral-300 hover:bg-zinc-800 hover:text-white";
  const disabledClasses = "text-neutral-500 bg-zinc-900/50 cursor-not-allowed";

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${
        disabled ? disabledClasses : enabledClasses
      }`}
    >
      {isLoading ? (
        <Loader2 className="h-5 w-5 animate-spin text-red-500" />
      ) : (
        icon
      )}
      <span>{children}</span>
    </button>
  );
};

export default function Navbar({
  onDashboardClick,
  onRelevantSectionsClick,
  onInsightsClick,
  onPodcastClick,
  isAnalysisDisabled,
  relevantSectionsLoading,
  insightsLoading,
  podcastLoading,
}) {
  return (
    <nav className="fixed top-0 left-0 w-full bg-black/80 backdrop-blur-lg h-16 flex items-center justify-between px-6 z-50 border-b border-zinc-800">
      <Link to="/" className="flex items-center gap-3 group">
        <CloudCog className="h-8 w-8 text-red-500 group-hover:animate-spin" />
        <span className="text-2xl font-bold text-white tracking-wider">
          Acumen
        </span>
      </Link>

      <div className="flex items-center gap-2 p-1 bg-zinc-900 border border-zinc-800 rounded-xl">
        <NavButton
          onClick={onDashboardClick}
          disabled={isAnalysisDisabled}
          icon={<Book className="h-5 w-5" />}
        >
          Dashboard
        </NavButton>

        <NavButton
          onClick={onRelevantSectionsClick}
          disabled={isAnalysisDisabled && !relevantSectionsLoading}
          isLoading={relevantSectionsLoading}
          icon={<Search className="h-5 w-5" />}
        >
          Relevant Sections
        </NavButton>

        <NavButton
          onClick={onInsightsClick}
          disabled={isAnalysisDisabled && !insightsLoading}
          isLoading={insightsLoading}
          icon={<BarChart className="h-5 w-5" />}
        >
          Insights
        </NavButton>

        <NavButton
          onClick={onPodcastClick}
          disabled={isAnalysisDisabled && !podcastLoading}
          isLoading={podcastLoading}
          icon={<Mic className="h-5 w-5" />}
        >
          Podcast
        </NavButton>
      </div>
    </nav>
  );
}
