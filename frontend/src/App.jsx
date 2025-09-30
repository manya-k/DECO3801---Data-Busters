import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import MainGameScreen from "./screens/MainGameScreen.jsx";
import BackgroundScreen from "./screens/BackgroundScreen.jsx";
import HowToScreen from "./screens/HowToScreen.jsx";
import GamePlay from "./screens/GamePlay.jsx";
import GalleryScreen from "./screens/GalleryScreen.jsx";
import '@fontsource/kanit/400.css';
import '@fontsource/kanit/500.css';

import BackgroundWrapper from "./screens/BasePage.jsx";
import AudioProvider from "./audio/AudioProvider.jsx";
import mainTheme from "./assets/Heaven_DavidFesliyan.mp3";

function App() {

  const routeAudioMap = {
    "*": { src: mainTheme, loop: true },
  };

  return (
    <Router>
      <AudioProvider routeAudioMap={routeAudioMap} crossfadeMs={1000} initialVolume={0.38}>
        <BackgroundWrapper>
          <Routes>
            <Route path="/" element={<MainGameScreen />} />
            <Route path="/story" element={<BackgroundScreen />} />
            <Route path="/how-to-play" element={<HowToScreen />} />
            <Route path="/game-play" element={<GamePlay />} />
            <Route path="/gallery" element={<GalleryScreen sessionId={19} />} />
          </Routes>
        </BackgroundWrapper>
      </AudioProvider>
    </Router >
  );
}

export default App;