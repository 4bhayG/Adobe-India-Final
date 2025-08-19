import { configureStore } from "@reduxjs/toolkit";
import pdfsReducer from "./pdfsSlice";

export const store = configureStore({
  reducer: {
    pdfs: pdfsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});
