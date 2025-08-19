import React, { useState, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import toast from "react-hot-toast";
import { UploadCloud, FileText, X, Loader2 } from "lucide-react";
import { getSessionId } from "../../lib/utils";
import Navbar from "./navbar";
import AdobePDFViewer from "./pdf-view";
import RelevantSectionsPanel from "./relevant-section";
import InsightSectionsPanel from "./insight-section";
import PodcastSectionsPanel from "./podcast-section";
import { getFileFromDb, addFileToDb } from "../../services/db";
import {
  setRelevantSectionsLoading,
  setInsightsLoading,
  setCurrentPdfMetadata,
  addPastPdfMetadata,
  removePastPdfMetadata,
  setRelevantSections,
  setLastKnownCurrentPage,
  resetAnalysisState,
  startUpload,
  updateUploadProgress,
  finishUpload,
  setInsights,
  setPodcastAudioUrl,
  setPodcastLoading,
} from "../../redux/pdfsSlice";

const FileProgressItem = ({ file, progress, onRemove }) => {
  const isUploading = progress !== undefined && progress < 100;
  const handleRemoveClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onRemove();
  };
  return (
    <div className="flex items-center gap-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
      <FileText className="h-6 w-6 text-gray-400 flex-shrink-0" />
      <div className="flex-1 overflow-hidden">
        <p className="text-sm font-medium text-gray-900 truncate">
          {file.name}
        </p>
        {isUploading ? (
          <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
           <div
  className="bg-red-500 h-1.5 rounded-full"
  style={{ width: `${progress}%` }}
></div>
          </div>
        ) : (
          <p className="text-xs text-gray-500">Upload complete</p>
        )}
      </div>
      <button
        onClick={handleRemoveClick}
        className="text-gray-400 hover:text-red-500"
      >
        <X size={16} />
      </button>
    </div>
  );
};

const UploadView = ({ onStartAnalysis, isLoading }) => {
  const [dragOverCurrent, setDragOverCurrent] = useState(false);
  const [dragOverPast, setDragOverPast] = useState(false);
  const dispatch = useDispatch();
  const { currentPdfMetadata, pastPdfsMetadata, uploadProgress } = useSelector(
    (state) => state.pdfs
  );

  const handleFileUpload = async (file, isCurrent) => {
    if (!file || file.type !== "application/pdf") {
      toast.error("Only PDF files are supported.");
      return;
    }
    const id = await addFileToDb(file);
    const metadata = { id, name: file.name };
    dispatch(startUpload(metadata));
    if (isCurrent) {
      if (currentPdfMetadata) {
        dispatch(addPastPdfMetadata(currentPdfMetadata));
      }
      dispatch(setCurrentPdfMetadata(metadata));
    } else {
      dispatch(addPastPdfMetadata(metadata));
    }
    let currentProgress = 0;
    const progressInterval = setInterval(() => {
      currentProgress += 10;
      if (currentProgress <= 100) {
        dispatch(updateUploadProgress({ id, progress: currentProgress }));
      } else {
        clearInterval(progressInterval);
      }
    }, 150);
    setTimeout(() => {
      clearInterval(progressInterval);
      dispatch(finishUpload(metadata));
    }, 1700);
  };

  const handleCurrentFileChange = (e) =>
    handleFileUpload(e.target.files[0], true);
  const handleCurrentDrop = (e) => {
    e.preventDefault();
    setDragOverCurrent(false);
    handleFileUpload(e.dataTransfer.files, true);
  };
  const handleRemoveCurrent = () => dispatch(setCurrentPdfMetadata(null));
  const handlePastFilesChange = (e) => {
    Array.from(e.target.files).forEach((file) => handleFileUpload(file, false));
    e.target.value = null;
  };
  const handlePastDrop = (e) => {
    e.preventDefault();
    setDragOverPast(false);
    Array.from(e.dataTransfer.files).forEach((file) =>
      handleFileUpload(file, false)
    );
  };
  const handleRemovePast = (id) => dispatch(removePastPdfMetadata(id));

  return (
    <div className="w-full max-w-5xl mx-auto bg-white rounded-2xl shadow-2xl p-10">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-black">Upload Your Documents</h2>
        <p className="text-gray-400 mt-2">
          Upload a current document and any past versions for comparison.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="flex flex-col">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">
            Current Document
          </h3>
          <div className="flex-1">
            {!currentPdfMetadata ? (
              <label
                htmlFor="current-file-upload"
                className={`h-full flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-xl transition-all cursor-pointer ${
                  dragOverCurrent
                    ? "border-red-500 bg-red-50"
                    : "border-gray-300 bg-white hover:bg-gray-50"
                }`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOverCurrent(true);
                }}
                onDragLeave={() => setDragOverCurrent(false)}
                onDrop={handleCurrentDrop}
              >
                <UploadCloud className="h-10 w-10 text-gray-500 mb-3" />
                <p className="text-gray-600 font-semibold">
                  Drop PDF here or click to browse
                </p>
                <p className="text-xs text-gray-500 mt-1">One file only</p>
                <input
                  id="current-file-upload"
                  type="file"
                  className="hidden"
                  onChange={handleCurrentFileChange}
                  accept=".pdf"
                />
              </label>
            ) : (
              <FileProgressItem
                file={currentPdfMetadata}
                progress={uploadProgress[currentPdfMetadata.id]}
                onRemove={handleRemoveCurrent}
              />
            )}
          </div>
        </div>
        <div className="flex flex-col min-h-[200px]">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">
            Past Documents (Optional)
          </h3>
          <label
            htmlFor="past-files-upload"
            className={`flex-1 flex flex-col p-6 border-2 border-dashed rounded-xl transition-all ${
              pastPdfsMetadata.length > 0 ? "" : "cursor-pointer"
            } ${
              dragOverPast
                ? "border-red-500 bg-red-50"
                : "border-gray-300 bg-white hover:bg-gray-50"
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOverPast(true);
            }}
            onDragLeave={() => setDragOverPast(false)}
            onDrop={handlePastDrop}
          >
            {pastPdfsMetadata.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
                <UploadCloud className="h-10 w-10 text-gray-500 mb-3" />
                <p className="font-semibold text-gray-600">
                  Drop past files here
                </p>
                <p className="text-sm">or click to browse</p>
              </div>
            ) : (
              <div className="flex flex-col h-full w-full">
                <div className="space-y-3 flex-1 overflow-y-auto pr-2 max-h-[250px]">
                  {pastPdfsMetadata.map((pdf) => (
                    <FileProgressItem
                      key={pdf.id}
                      file={pdf}
                      progress={uploadProgress[pdf.id]}
                      onRemove={() => handleRemovePast(pdf.id)}
                    />
                  ))}
                </div>
                <p className="mt-4 text-center text-gray-500 font-semibold cursor-pointer">
                  Add More Files
                </p>
              </div>
            )}
          </label>
          <input
            id="past-files-upload"
            type="file"
            className="hidden"
            multiple
            onChange={handlePastFilesChange}
            accept=".pdf"
          />
        </div>
      </div>
      <div className="mt-10 text-center">
        <button
          onClick={onStartAnalysis}
          disabled={
            !currentPdfMetadata ||
            (uploadProgress[currentPdfMetadata.id] &&
              uploadProgress[currentPdfMetadata.id] < 100) ||
            isLoading
          }
          className="bg-black text-white px-10 py-3 rounded-lg font-semibold text-lg hover:bg-gray-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl w-60 h-14 flex items-center justify-center"
        >
          {isLoading ? (
            <Loader2 className="animate-spin h-6 w-6" />
          ) : (
            "Start Analysis"
          )}
        </button>
      </div>
    </div>
  );
};

export default function Workspace() {
  const dispatch = useDispatch();
  const viewerRef = useRef();
  const [showAnalysisView, setShowAnalysisView] = useState(false);
  const [activePanel, setActivePanel] = useState(null);

  const {
    currentPdfMetadata,
    pastPdfsMetadata,
    viewingPdfId,
    relevantSectionsLoading,
    insightsLoading,
    insights,
    podcastLoading,
  } = useSelector((state) => state.pdfs);

  const handleStartAnalysis = async () => {
    if (!currentPdfMetadata) {
      toast.error("Please upload a 'Current PDF' to proceed.");
      return;
    }
    try {
      const formData = new FormData();
      const currentFile = await getFileFromDb(currentPdfMetadata.id);
      if (currentFile) {
        formData.append("files_current", currentFile, currentFile.name);
      }
      for (const meta of pastPdfsMetadata) {
        const pastFile = await getFileFromDb(meta.id);
        if (pastFile) {
          formData.append("files_past", pastFile, pastFile.name);
        }
      }
      const response = await fetch("/api/upload_documents/", {
        method: "POST",
        body: formData,
        headers: { "X-Session-Id": getSessionId() },
      });
      if (!response.ok) {
        throw new Error(`Server Error: ${response.status}`);
      }
      toast.success("Documents are ready for analysis.");
      setShowAnalysisView(true);
    } catch (error) {
      console.error("Error uploading documents:", error);
      toast.error("Failed to upload documents. Please try again.");
    }
  };

  const handleDashboardClick = () => {
    if (relevantSectionsLoading || insightsLoading) {
      toast.error("Analysis is in progress. Please wait.");
      return;
    }
    dispatch(resetAnalysisState());
    dispatch(setInsights(null));
    setShowAnalysisView(false);
    setActivePanel(null);
  };

  const handleRelevantSectionsClick = async () => {
    if (relevantSectionsLoading || insightsLoading || podcastLoading) {
      toast.error("Another analysis is already running.");
      return;
    }
    if (activePanel === "sections") {
      setActivePanel(null);
      return;
    }
    if (!viewerRef.current) {
      toast.error("PDF Viewer not ready.");
      return;
    }
    const selectedText = await viewerRef.current.getSelectedText();
    if (!selectedText) {
      toast.error("Please select text in the document before searching.");
      return;
    }

    const currentPage = await viewerRef.current.getCurrentPage();
    dispatch(setLastKnownCurrentPage(currentPage));

    dispatch(setRelevantSectionsLoading(true));
    dispatch(setRelevantSections([]));
    setActivePanel("sections");
    try {
      const formData = new FormData();
      formData.append("selected_text", selectedText);
      const response = await fetch("/api/find_relevant_sections/", {
        method: "POST",
        body: formData,
        headers: { "X-Session-Id": getSessionId() },
      });
      if (!response.ok) {
        throw new Error(`Server Error: ${response.status}`);
      }
      const data = await response.json();
      console.log(data.extracted_sections);
      dispatch(setRelevantSections(data.extracted_sections || []));
      toast.success("Analysis complete!");
    } catch (error) {
      console.error("Error fetching relevant sections:", error);
      toast.error("Failed to fetch analysis.");
      setActivePanel(null);
    } finally {
      dispatch(setRelevantSectionsLoading(false));
    }
  };

  const handleInsightsClick = async () => {
    if (!currentPdfMetadata) {
      toast.error("Please upload a 'Current PDF' to proceed.");
      return;
    }
    if (relevantSectionsLoading || insightsLoading || podcastLoading) {
      toast.error("Another analysis is already running.");
      return;
    }
    if (activePanel === "insights") {
      setActivePanel(null);
      return;
    }

    if (insights) {
      setActivePanel("insights");
      return;
    }
    dispatch(setInsightsLoading(true));
    dispatch(setInsights(null));
    setActivePanel("insights");

    try {
      const response = await fetch("/api/get_insights/", {
        headers: { "X-Session-Id": getSessionId() },
      });
      if (!response.ok) {
        throw new Error(`Server Error: ${response.status}`);
      }
      const data = await response.json();
      dispatch(setInsights(data));
      toast.success("Insights generated successfully!");
    } catch (error) {
      console.error("Error fetching insights:", error);
      toast.error("Failed to fetch insights.");
      setActivePanel(null);
    } finally {
      dispatch(setInsightsLoading(false));
    }
  };

  const handlePodcastClick = async () => {
    if (!currentPdfMetadata) {
      toast.error("Please upload a 'Current PDF' to proceed.");
      return;
    }
    if (relevantSectionsLoading || insightsLoading || podcastLoading) {
      toast.error("Another analysis is already running.");
      return;
    }
    if (activePanel === "podcast") {
      setActivePanel(null);
      return;
    }

    dispatch(setPodcastLoading(true));
    dispatch(setPodcastAudioUrl(null));
    setActivePanel("podcast");
    try {
      const response = await fetch("/api/generate_audio_podcast/", {
        headers: { "X-Session-Id": getSessionId() },
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to generate podcast audio." }));
        throw new Error(errorData.detail || `Server Error: ${response.status}`);
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      dispatch(setPodcastAudioUrl(audioUrl));
      toast.success("Podcast generated successfully!");
    } catch (error) {
      console.error("Error fetching podcast:", error);
      toast.error(error.message);
      setActivePanel(null);
    } finally {
      dispatch(setPodcastLoading(false));
    }
  };

  const handleClosePanel = () => {
    setActivePanel(null);
  };

  const isAnalysisDisabled =
    relevantSectionsLoading || insightsLoading || podcastLoading;

  return (
    <div className="flex flex-col w-screen h-screen bg-grid-black">
      <Navbar
        onDashboardClick={handleDashboardClick}
        onRelevantSectionsClick={handleRelevantSectionsClick}
        onInsightsClick={handleInsightsClick}
        onPodcastClick={handlePodcastClick}
        isAnalysisDisabled={isAnalysisDisabled}
        relevantSectionsLoading={relevantSectionsLoading}
        insightsLoading={insightsLoading}
        podcastLoading={podcastLoading}
      />
      <main className="flex-1 pt-16 flex items-center justify-center overflow-hidden">
        {!showAnalysisView ? (
          <UploadView
            onStartAnalysis={handleStartAnalysis}
            isLoading={
              relevantSectionsLoading || insightsLoading || podcastLoading
            }
          />
        ) : (
          <div className="w-full h-full flex p-4 gap-4">
            <div className="flex-1 bg-zinc-900 rounded-lg shadow-md overflow-hidden">
              {viewingPdfId && (
                <AdobePDFViewer fileId={viewingPdfId} ref={viewerRef} />
              )}
            </div>

            {activePanel && (
              <div className="w-[450px] flex-shrink-0">
                {activePanel === "sections" && (
                  <RelevantSectionsPanel
                    onClose={handleClosePanel}
                    viewerRef={viewerRef}
                  />
                )}
                {activePanel === "insights" && (
                  <InsightSectionsPanel onClose={handleClosePanel} />
                )}
                {activePanel === "podcast" && (
                  <PodcastSectionsPanel onClose={handleClosePanel} />
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
