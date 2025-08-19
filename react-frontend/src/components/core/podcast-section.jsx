import React, { useState, useRef, useEffect } from "react";
import { useSelector } from "react-redux";
import {
  X,
  Play,
  Pause,
  Rewind,
  FastForward,
  Mic,
  Volume2,
  VolumeX,
  Loader2,
} from "lucide-react";

const SkeletonLoader = () => (
  <div className="p-6 space-y-6 animate-pulse w-full">
    <div className="h-48 w-48 bg-zinc-800 rounded-lg mx-auto"></div>
    <div className="space-y-3 text-center">
      <div className="h-7 bg-zinc-800 rounded w-3/4 mx-auto"></div>
      <div className="h-5 bg-zinc-800 rounded w-1/2 mx-auto"></div>
    </div>
    <div className="h-2 bg-zinc-800 rounded-full w-full"></div>
    <div className="flex justify-center items-center gap-8">
      <div className="h-10 w-10 bg-zinc-800 rounded-full"></div>
      <div className="h-16 w-16 bg-zinc-800 rounded-full"></div>
      <div className="h-10 w-10 bg-zinc-800 rounded-full"></div>
    </div>
  </div>
);

export default function PodcastSectionsPanel({ onClose }) {
  const { podcastLoading, podcastAudioUrl } = useSelector(
    (state) => state.pdfs
  );
  const audioRef = useRef(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const setAudioData = () => setDuration(audio.duration);
    const setAudioTime = () => setCurrentTime(audio.currentTime);
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    audio.addEventListener("loadeddata", setAudioData);
    audio.addEventListener("timeupdate", setAudioTime);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("ended", handlePause);

    if (podcastAudioUrl) {
      audio.play().catch((e) => console.error("Autoplay was prevented:", e));
    }

    return () => {
      audio.removeEventListener("loadeddata", setAudioData);
      audio.removeEventListener("timeupdate", setAudioTime);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("ended", handlePause);
    };
  }, [podcastAudioUrl]);

  const togglePlayPause = () => {
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
  };

  const handleSeek = (e) => {
    audioRef.current.currentTime = e.target.value;
    setCurrentTime(e.target.value);
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    audioRef.current.volume = newVolume;
    setVolume(newVolume);
    if (newVolume > 0 && isMuted) {
      setIsMuted(false);
      audioRef.current.muted = false;
    }
  };

  const toggleMute = () => {
    const currentlyMuted = !isMuted;
    audioRef.current.muted = currentlyMuted;
    setIsMuted(currentlyMuted);
    if (!currentlyMuted && volume > 0) {
      audioRef.current.volume = volume;
    }
  };

  const handleRewind = () => {
    audioRef.current.currentTime = Math.max(
      0,
      audioRef.current.currentTime - 10
    );
  };

  const handleFastForward = () => {
    audioRef.current.currentTime = Math.min(
      duration,
      audioRef.current.currentTime + 10
    );
  };

  const formatTime = (timeInSeconds) => {
    if (isNaN(timeInSeconds) || timeInSeconds === 0) return "0:00";
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  return (
    <div className="w-full h-full bg-black/90 backdrop-blur-lg border border-zinc-800 rounded-2xl shadow-2xl shadow-black/50 flex flex-col">
      <div className="flex justify-between items-center p-4 border-b border-zinc-800 flex-shrink-0">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Mic className="text-red-500" />
          Podcast Player
        </h2>
        <button
          onClick={onClose}
          className="p-1.5 text-neutral-400 hover:bg-red-600 hover:text-white rounded-full transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center p-6">
        {podcastLoading ? (
          <SkeletonLoader />
        ) : podcastAudioUrl ? (
          <div className="w-full flex flex-col items-center">
            <audio ref={audioRef} src={podcastAudioUrl}></audio>

            <div className="relative mb-6">
              <div className="w-48 h-48 bg-zinc-900 rounded-lg shadow-xl flex items-center justify-center border border-zinc-800">
                <Mic
                  className={`w-24 h-24 text-red-500/50 transition-all ${
                    isPlaying ? "scale-110" : "scale-100"
                  }`}
                />
              </div>
            </div>

            <h3 className="text-2xl font-bold text-white">Document Summary</h3>
            <p className="text-neutral-400">Generated by Acumen</p>

            <div className="w-full mt-6">
              <input
                type="range"
                min="0"
                max={duration}
                value={currentTime}
                onChange={handleSeek}
                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer range-sm accent-red-500"
              />
              <div className="flex justify-between text-xs text-neutral-400 mt-1">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>

            <div className="flex items-center justify-center gap-8 my-6">
              <button
                onClick={handleRewind}
                className="text-neutral-400 hover:text-white transition-colors"
              >
                <Rewind size={32} />
              </button>
              <button
                onClick={togglePlayPause}
                className="text-white bg-red-600 rounded-full p-4 hover:scale-110 transition-transform shadow-lg shadow-red-900/40"
              >
                {isPlaying ? (
                  <Pause size={32} />
                ) : (
                  <Play size={32} className="translate-x-0.5" />
                )}
              </button>
              <button
                onClick={handleFastForward}
                className="text-neutral-400 hover:text-white transition-colors"
              >
                <FastForward size={32} />
              </button>
            </div>

            <div className="flex items-center gap-3 w-full max-w-[200px] mx-auto">
              <button
                onClick={toggleMute}
                className="text-neutral-400 hover:text-white"
              >
                {isMuted || volume == 0 ? (
                  <VolumeX size={20} />
                ) : (
                  <Volume2 size={20} />
                )}
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                className="w-full h-1 bg-zinc-700 rounded-lg appearance-none cursor-pointer range-sm accent-white"
              />
            </div>
          </div>
        ) : (
          <div className="text-center text-zinc-500">
            <p className="text-lg font-semibold">Ready to Listen?</p>
            <p className="text-sm">
              Click the "Podcast" button in the navbar to generate an audio
              summary.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
