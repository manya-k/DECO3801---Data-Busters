import React, { useState } from "react";
import backgroundImg from "./assets/background.jpg"; // Update filename as needed
import "./index.css";

const MainGameScreen = ({ onStart }) => {
  const [showModal, setShowModal] = useState(false);

  return (
    <div
      className="main-screen"
      style={{ backgroundImage: `url(${backgroundImg})` }}
    >
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
