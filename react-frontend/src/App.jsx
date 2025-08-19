// src/App.js

import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { Provider } from "react-redux";
import { store } from "./redux/store";
import Workspace from "./components/core/workspace";
import LandingPage from "./components/core/landing";

export default function App() {
  return (
    <Provider store={store}>
      <Router>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 2000,
            style: {
              background: "#ffffff",
              color: "#25418f",
              border: "1px solid #dbe4f3",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
            },
            success: {
              iconTheme: { primary: "#2a6cef", secondary: "#ffffff" },
            },
            error: { iconTheme: { primary: "#e53e3e", secondary: "#ffffff" } },
          }}
        />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/app" element={<Workspace />} />
        </Routes>
      </Router>
    </Provider>
  );
}
