import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  currentPdfMetadata: null,
  pastPdfsMetadata: [],
  viewingPdfId: null,
  relevantSections: [],
  insights: null,
  relevantSectionsLoading: false,
  insightsLoading: false,
  podcastLoading: false,
  podcastAudioUrl: null,
  uploadProgress: {},
  targetLocation: null,
  lastKnownCurrentPage: 1,
};

const pdfsSlice = createSlice({
  name: "pdfs",
  initialState,
  reducers: {
    setRelevantSectionsLoading: (state, action) => {
      state.relevantSectionsLoading = action.payload;
    },
    setInsightsLoading: (state, action) => {
      state.insightsLoading = action.payload;
    },
    setPodcastLoading: (state, action) => {
      state.podcastLoading = action.payload;
    },
    setPodcastAudioUrl: (state, action) => {
      state.podcastAudioUrl = action.payload;
    },
    setCurrentPdfMetadata: (state, action) => {
      state.currentPdfMetadata = action.payload;
      if (action.payload) {
        state.viewingPdfId = action.payload.id;
        state.lastKnownCurrentPage = 1;
        state.insights = null;
      } else {
        state.insights = null;
      }
    },
    addPastPdfMetadata: (state, action) => {
      if (!state.pastPdfsMetadata.some((pdf) => pdf.id === action.payload.id)) {
        state.pastPdfsMetadata.push(action.payload);
      }
    },
    removePastPdfMetadata: (state, action) => {
      state.pastPdfsMetadata = state.pastPdfsMetadata.filter(
        (pdf) => pdf.id !== action.payload
      );
      delete state.uploadProgress[action.payload];
    },
    setViewingPdfId: (state, action) => {
      state.viewingPdfId = action.payload;
    },
    setRelevantSections: (state, action) => {
      state.relevantSections = action.payload;
    },
    setTargetLocation: (state, action) => {
      state.targetLocation = action.payload;
    },
    setLastKnownCurrentPage: (state, action) => {
      state.lastKnownCurrentPage = action.payload;
    },
    setInsights: (state, action) => {
      state.insights = action.payload;
    },
    startUpload: (state, action) => {
      state.uploadProgress[action.payload.id] = 0;
    },
    updateUploadProgress: (state, action) => {
      const { id, progress } = action.payload;
      if (state.uploadProgress[id] !== undefined) {
        state.uploadProgress[id] = progress;
      }
    },
    finishUpload: (state, action) => {
      state.uploadProgress[action.payload.id] = 100;
    },
    resetAnalysisState: () => initialState,
  },
});

export const {
  setRelevantSectionsLoading,
  setInsightsLoading,
  setPodcastLoading,
  setPodcastAudioUrl,
  setCurrentPdfMetadata,
  addPastPdfMetadata,
  removePastPdfMetadata,
  setViewingPdfId,
  setRelevantSections,
  setTargetLocation,
  setLastKnownCurrentPage,
  setInsights,
  startUpload,
  updateUploadProgress,
  finishUpload,
  resetAnalysisState,
} = pdfsSlice.actions;

export default pdfsSlice.reducer;
