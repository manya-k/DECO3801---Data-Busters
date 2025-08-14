import React, { useState } from "react";
import "./index.css";
import LetterGlitch from "././backgrounds/LetterGlitch.jsx";

const MainGameScreen = ({ onStart }) => {
  const [showModal, setShowModal] = useState(false);

  return (
    <div className="main-screen" style={{ position: "relative", height: "100vh" }}>
      {/* Animated Background */}
      <LetterGlitch
        glitchSpeed={0}
        centerVignette={true}
        outerVignette={true}
        smooth={false}
      />

      {/* Foreground Content */}
      <div style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1
      }}>
        {/* Title */}
        <h1 className="title">Future of Memory</h1>

        {/* Buttons */}
        <div className="button-group">
          <button className="btn-primary" onClick={onStart}>
            Start
          </button>
          <button className="btn-secondary" onClick={() => setShowModal(true)}>
            How to Play
          </button>
        </div>
      </div>

        {/* How to Play Modal */}
        {showModal && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h2>How to Play</h2>
              <p>
                Explore the world of memories, make choices, and see how your
                actions shape the story.
              </p>
              <button className="btn-primary" onClick={() => setShowModal(false)}>
                Close
              </button>
            </div>
          </div>
        )}
      </div>
  );
};

      export default MainGameScreen;
