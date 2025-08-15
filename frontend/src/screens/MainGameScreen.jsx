import { useNavigate } from "react-router-dom";
import backgroundImg from "../assets/background.jpg";
import "./mainGameScreen.css";

const MainGameScreen = () => {
  const navigate = useNavigate();

  return (
    <div
      className="main-screen"
      style={{ backgroundImage: `url(${backgroundImg})` }}
    >
      <h1 className="title">Future of Memory</h1>

      <div className="button-group">
        <button className="btn-primary" onClick={() => navigate("/story")}>
          Start
        </button>
        <button className="btn-secondary" onClick={() => navigate("/how-to-play")}>
          How to Play
        </button>
      </div>
    </div>
  );
};

export default MainGameScreen;