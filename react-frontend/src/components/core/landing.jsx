import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { LogIn, FileText, CloudCogIcon } from "lucide-react";

export default function Landing() {
  const contentContainerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.3,
      },
    },
  };
  const contentItemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.6, ease: "easeOut" },
    },
  };

  return (
    <div className="caret-transparent relative flex flex-col items-center justify-center min-h-screen bg-grid-black text-center p-4 overflow-hidden">
      <motion.div
        className="absolute w-[150%] h-[120%] bg-white"
        style={{ borderRadius: "0 0 0 100%" }}
        initial={{ y: "-115%", x: "-50%" }}
        animate={{ y: "-65%", x: "0%" }}
        transition={{ duration: 1.2, ease: [0.6, 0.01, -0.05, 0.9] }}
      />
      <motion.div
        className="relative z-10 flex flex-col items-center justify-center"
        variants={contentContainerVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div
          className="fixed top-8 left-8 flex items-center gap-3"
          variants={contentItemVariants}
        >
          <CloudCogIcon className="h-8 w-8 text-white" />
          <span className="text-2xl font-bold text-white">Acumen</span>
        </motion.div>

        <main className="flex flex-col items-center">
          <motion.div
            className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100"
            variants={contentItemVariants}
          >
            <FileText className="h-8 w-8 text-black" />
          </motion.div>

          <motion.h1
            className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl"
            variants={contentItemVariants}
          >
            The Smartest Way to Analyze PDFs
          </motion.h1>

          <motion.p
            className="mt-6 max-w-2xl text-lg text-white"
            variants={contentItemVariants}
          >
            Upload a current document and its past versions. Our AI-powered
            analysis will give you insights in seconds.
          </motion.p>

          <motion.div variants={contentItemVariants}>
            <Link
              to="/app"
              className="mt-10 flex items-center gap-2 rounded-lg bg-white px-8 py-4 text-lg font-semibold text-black shadow-md transition-transform hover:scale-105"
            >
              <LogIn className="h-5 w-5" />
            </Link>
          </motion.div>
        </main>
      </motion.div>
    </div>
  );
}
