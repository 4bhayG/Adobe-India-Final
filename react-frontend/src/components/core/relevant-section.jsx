import React, { useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import {
  FileText,
  X,
  ArrowLeftCircle,
  ChevronRight,
  SearchX,
  BookMarkedIcon,
  ArrowUpRight,
} from "lucide-react";
import {
  setViewingPdfId,
  setTargetLocation,
  setLastKnownCurrentPage,
} from "../../redux/pdfsSlice";
import toast from "react-hot-toast";

const normalizeName = (name) => {
  if (typeof name !== "string") return "";

  const filename = name.split(/[/\\]/).pop();

  const base = filename.replace(/\.pdf$/i, "");
  let normalized = base
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");

  return normalized + ".pdf";
};

const SectionCard = ({ section, onNavigate }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleNavigationClick = (e) => {
    e.stopPropagation();
    onNavigate(section);
  };

  return (
    <div
      onClick={() => setIsExpanded(!isExpanded)}
      className="bg-zinc-900 border border-zinc-800 rounded-xl transition-all duration-300 ease-in-out hover:border-red-500/80"
    >
      <div className="group flex items-center gap-4 p-4 cursor-pointer">
        <div className="flex-shrink-0 p-3 bg-zinc-950 rounded-lg border border-zinc-800">
          <FileText className="h-6 w-6 text-neutral-500 group-hover:text-red-500 transition-colors" />
        </div>
        <div className="flex-1 overflow-hidden">
          <div className="flex items-center justify-between">
            <p
              className="font-bold text-base text-neutral-100 truncate"
              title={section.document}
            >
              {section.document}
            </p>
            <p className="text-xs font-medium text-neutral-400 bg-zinc-800 px-2 py-1 rounded-full flex-shrink-0">
              Page: {section.page_number + 1}
            </p>
          </div>
          <p
            className={`text-sm text-neutral-400 mt-2 transition-all duration-300 ${
              isExpanded ? "line-clamp-none" : "line-clamp-3"
            }`}
          >
            {section.refined_text}
          </p>
        </div>
        <ChevronRight
          className={`h-6 w-6 text-zinc-600 group-hover:text-white transition-transform duration-300 ${
            isExpanded ? "rotate-90" : ""
          }`}
        />
      </div>

      {isExpanded && (
        <div className="px-5 pb-4 border-t border-zinc-800/50 mt-2 pt-4">
          <div className="space-y-4">
            <div>
              <h4 className="font-bold text-sm text-neutral-200 mb-1">
                Section Title
              </h4>
              <p className="text-sm text-neutral-400 italic">
                "{section.section_title || "N/A"}"
              </p>
            </div>
            <div>
              <h4 className="font-bold text-sm text-neutral-200 mb-1">
                Full Text
              </h4>
              <p className="text-sm text-neutral-300 bg-black/30 p-3 rounded-md border border-zinc-800">
                {section.refined_text}
              </p>
            </div>
            <button
              onClick={handleNavigationClick}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 transition-colors"
            >
              <ArrowUpRight size={16} />
              Go to Section
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const SkeletonCard = () => (
  <div className="flex items-center gap-4 p-4 bg-zinc-900 border border-zinc-800 rounded-xl">
    <div className="flex-shrink-0 p-3 bg-zinc-950 rounded-lg border border-zinc-800">
      <div className="h-6 w-6 bg-zinc-800 rounded"></div>
    </div>
    <div className="flex-1 overflow-hidden space-y-2">
      <div className="flex items-center justify-between">
        <div className="h-5 bg-zinc-800 rounded w-1/2"></div>
        <div className="h-4 bg-zinc-800 rounded w-1/4"></div>
      </div>
      <div className="h-4 bg-zinc-800 rounded w-full"></div>
      <div className="h-4 bg-zinc-800 rounded w-3/4"></div>
    </div>
    <div className="h-6 w-6 bg-zinc-800 rounded-full"></div>
  </div>
);

const SkeletonLoader = () => (
  <div className="space-y-4 animate-pulse">
    <SkeletonCard />
    <SkeletonCard />
    <SkeletonCard />
  </div>
);

export default function RelevantSectionsPanel({ onClose, viewerRef }) {
  const dispatch = useDispatch();
  const {
    relevantSections,
    relevantSectionsLoading,
    pastPdfsMetadata,
    currentPdfMetadata,
    viewingPdfId,
    lastKnownCurrentPage,
  } = useSelector((state) => state.pdfs);

  const handleGoBack = () => {
    if (currentPdfMetadata) {
      dispatch(setViewingPdfId(currentPdfMetadata.id));
      dispatch(setTargetLocation({ page: lastKnownCurrentPage, x: 0, y: 0 }));
      toast.success("Returned to original document.");
    }
  };

  const handleNavigateToSection = async (section) => {
    if (!section || !section.document) {
      toast.error("Invalid section data.");
      return;
    }

    if (
      viewerRef &&
      viewerRef.current &&
      typeof viewerRef.current.getCurrentPage === "function"
    ) {
      try {
        const currentPageBeforeNavigation =
          await viewerRef.current.getCurrentPage();
        if (currentPageBeforeNavigation > 0) {
          dispatch(setLastKnownCurrentPage(currentPageBeforeNavigation));
        }
      } catch (error) {
        console.error("Error getting current page:", error);
        dispatch(setLastKnownCurrentPage(1));
      }
    } else {
      dispatch(setLastKnownCurrentPage(1));
    }

    const normalName = section.document;
    let pdfToView =
      pastPdfsMetadata.find((pdf) => normalizeName(pdf.name) === normalName) ||
      (currentPdfMetadata &&
      normalizeName(currentPdfMetadata.name) === normalName
        ? currentPdfMetadata
        : null);

    if (pdfToView) {
      if (viewingPdfId !== pdfToView.id) {
        dispatch(setViewingPdfId(pdfToView.id));
      }
      if (typeof section.page_number === "number") {
        dispatch(
          setTargetLocation({ page: section.page_number + 1, x: 0, y: 0 })
        );
      } else {
        toast.error("Invalid page number for this section.");
        dispatch(setTargetLocation(null));
      }
    } else {
      toast.error(`PDF '${section.document}' not found.`);
    }
  };

  const showGoBackButton =
    currentPdfMetadata && viewingPdfId !== currentPdfMetadata.id;

  const renderContent = () => {
    if (relevantSectionsLoading) {
      return <SkeletonLoader />;
    }

    if (relevantSections.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-neutral-500 px-6 text-center">
          <SearchX className="h-12 w-12 mb-4" />
          <p className="font-bold text-lg text-neutral-300">
            No Relevant Sections
          </p>
          <p className="text-sm">
            Your selection did not match any text in the provided documents.
          </p>
        </div>
      );
    }
    return (
      <div className="space-y-4">
        {relevantSections.map((section, index) => (
          <SectionCard
            key={`${section.document}-${index}`}
            section={section}
            onNavigate={handleNavigateToSection}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="w-full h-full bg-zinc-950/90 backdrop-blur-lg border border-zinc-800 rounded-2xl shadow-2xl shadow-black/50 flex flex-col">
      <div className="flex-shrink-0 p-4 border-b border-zinc-800">
        <div className="flex justify-between items-center">
          <h2 className="flex items-center gap-2 text-xl font-bold text-white">
            <BookMarkedIcon className="text-red-500" />
            <span>Relevant Sections</span>
          </h2>
          {!showGoBackButton && (
            <button
              onClick={onClose}
              className="p-1.5 text-neutral-400 hover:bg-red-600 hover:text-white rounded-full transition-colors"
            >
              <X size={20} />
            </button>
          )}
        </div>
      </div>

      {showGoBackButton && (
        <div className="p-4 flex-shrink-0 border-b border-zinc-800">
          <button
            onClick={handleGoBack}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 transition-all duration-200 shadow-lg shadow-red-900/40"
          >
            <ArrowLeftCircle size={20} />
            Go Back to Original
          </button>
        </div>
      )}

      <div className="overflow-y-auto flex-1 p-4">{renderContent()}</div>
    </div>
  );
}
