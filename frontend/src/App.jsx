import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import MainGameScreen from "./screens/MainGameScreen.jsx";
import StoryScreen from "./screens/StoryScreen.jsx";
import HowToPlayScreen from "./screens/HowToPlayScreen.jsx";


function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainGameScreen />} />
        <Route path="/story" element={<StoryScreen />} />
        <Route path="/how-to-play" element={<HowToPlayScreen/>} />
      </Routes>
    </Router>
  );
}

export default App;