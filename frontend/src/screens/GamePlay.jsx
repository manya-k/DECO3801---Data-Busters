// frontend/src/screens/GamePlay.jsx
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getQuestion } from "../../api/questionApi";
import { getScenario } from "../../api/scenarioApi";
import { submitChoice } from "../../api/answerApi";
import Button from "../components/Button/Button";
import { useNavigate } from "react-router-dom";
import "./GamePlay.css";

const GamePlay = () => {
  const [year, setYear] = useState(2035);
  const [screen, setScreen] = useState("scenario"); // "scenario" or "question"
  const navigate = useNavigate();

  // Stable anonymous id (won't change UI)
  const clientId = useMemo(() => {
    let id = localStorage.getItem("clientId");
    if (!id) {
      id = "guest-" + Math.random().toString(36).slice(2, 8);
      localStorage.setItem("clientId", id);
    }
    return id;
  }, []);

  // Scenario (only when on scenario screen)
  const {
    data: scenarioData,
    isLoading: isScenarioLoading,
    error: scenarioError,
  } = useQuery({
    queryKey: ["scenario", year],
    queryFn: () => getScenario(year),
    enabled: screen === "scenario",
  });

  // Question (only when on question screen)
  const {
    data: questionData,
    isLoading: isQuestionLoading,
    error: questionError,
  } = useQuery({
    queryKey: ["question", year],
    queryFn: () => getQuestion(year),
    enabled: screen === "question",
  });

  // keep behavior simple like the other branch: submit → go to next year locally
  const handleChoice = async (answer) => {
    try {
      // still pass clientId (backend happy), but UI stays simple
      await submitChoice(year, answer, clientId, 1);
      setScreen("scenario");
      setYear((y) => y + 1);
    } catch (error) {
      console.error("Error submitting choice:", error);
    }
  };

  // ----- UI (IDENTICAL to the other branch) -----
  if (isScenarioLoading && screen === "scenario") return <p>Loading scenario...</p>;
  if (isQuestionLoading && screen === "question") return <p>Loading question...</p>;
  if (scenarioError) return <p>Error loading scenario</p>;
  if (questionError) return <p>Error loading question</p>;

  return (
    <div className="screen">
      <Button baseButton="btn-back" action={() => navigate("/")} title="Back" />

      {/* Scenario screen */}
      {screen === "scenario" && scenarioData && (
        <div className="text-container">
          <h3>{scenarioData.scenario}</h3>
          <Button
            baseButton="btn-primary"
            action={() => setScreen("question")}
            title="Continue"
          />
        </div>
      )}

      {/** Question Screen*/}
      {screen === "question" && questionData && (
        <div>
          <div className="question-container">
            <h3>{questionData.question}</h3>
          </div>
          <div className="choice-container">
            {/*Displays the questions and the choices */}
            {Object.entries(questionData.options).map(([key, value]) => (
              <Button
                baseButton="choice-btn"
                key={key}
                action={() => handleChoice(key)}
                title={value}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GamePlay;