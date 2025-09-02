import { useState, useMemo, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getQuestion } from "../../api/questionApi";
import { getScenario } from "../../api/scenarioApi";
import { submitChoice } from "../../api/answerApi";
import Button from "../components/Button/Button";
import { useNavigate } from "react-router-dom";

const POLL_MS = 1500;

const GamePlay = () => {
  const [year, setYear] = useState(2035);
  const [screen, setScreen] = useState("scenario"); // "scenario" or "question"
  const navigate = useNavigate();

  const [counts, setCounts] = useState({});
  const [waiting, setWaiting] = useState(false);
  const qc = useQueryClient()

  // Stable anonymous id (backend falls back to IP/UA, but this helps)
  const clientId = useMemo(() => {
    let id = localStorage.getItem("clientId");
    if (!id) {
      id = "guest-" + Math.random().toString(36).slice(2, 8);
      localStorage.setItem("clientId", id);
    }
    return id;
  }, []);

  // Poll backend state to sync year/advance + counts
  useEffect(() => {
    let stop = false;
    const tick = async () => {
      try {
        const { data } = await api.get("/storyline/state");
        if (stop || !data) return;
        setCounts(data.counts || {});
        // if backend has advanced, follow it
        if (typeof data.year === "number" && data.year !== year) {
          setYear(data.year);
          setScreen("scenario");
          setWaiting(false);
          // refresh caches for new year
          qc.invalidateQueries({ queryKey: ["scenario", data.year] });
          qc.invalidateQueries({ queryKey: ["question", data.year] });
        }
      } catch {
        /* ignore */
      }
    };
    tick(); // initial
    const id = setInterval(tick, POLL_MS);
    return () => { stop = true; clearInterval(id); };
  }, [year, qc]);


  // Fetch scenarios everytim the screen changes to scenario
  const {
    data: scenarioData,
    isLoading: isScenarioLoading,
    error: scenarioError,
  } = useQuery({
    queryKey: ["scenario", year],
    queryFn: () => getScenario(year),
    enabled: screen === "scenario",
  });

  // Fetches questiosn everytime the scren chnges to questions
  const {
    data: questionData,
    isLoading: isQuestionLoading,
    error: questionError,
  } = useQuery({
    queryKey: ["question", year],
    queryFn: () => getQuestion(year),
    enabled: screen === "question", // only fetch when we are on question screen
  });

  const handleContinue = () => {
    setScreen("question");
    setWaiting(false);
  };

  const handleChoice = async (answer) => {
    try {
      setWaiting(true);
      // minimal change: keep your existing submitChoice signature
      // (backend will accept missing clientId/players; it defaults to 2 players)
      const res = await submitChoice(year, answer, clientId);
      // if round decided, move to next (backend also advances; our poll will confirm)
      if (res?.decided && res?.next_year) {
        setYear(res.next_year);
        setScreen("scenario");
        setWaiting(false);
        qc.invalidateQueries({ queryKey: ["scenario", res.next_year] });
        qc.invalidateQueries({ queryKey: ["question", res.next_year] });
      } else if (res?.counts) {
        setCounts(res.counts);
      }
    } catch (error) {
      console.error("Error submitting choice:", error);
      setWaiting(false);
    }
  };

  // --- UI Loading/Error States ---
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
          <Button baseButton="btn-primary" action={handleContinue} title="Continue" />
        </div>
      )}

      {/* Question screen */}
      {screen === "question" && questionData && (
        <div>
          <div className="question-container">
            <h3>{questionData.question}</h3>
          </div>
          <div className="choice-container" style={{ display: "grid", gap: 12 }}>
            {Object.entries(questionData.options).map(([key, value]) => (
              <Button
                baseButton="choice-btn"
                key={key}
                action={() => handleChoice(key)}
                title={
                  <>
                    <span>{value}</span>
                    {/* tiny count badge */}
                    {typeof counts[key] === "number" && (
                      <span
                        style={{
                          marginLeft: 8,
                          padding: "2px 8px",
                          borderRadius: 12,
                          border: "1px solid #999",
                          fontSize: 12,
                        }}
                      >
                        {counts[key]}
                      </span>
                    )}
                  </>
                }
              />
            ))}
          </div>
          {waiting && (
            <div style={{ marginTop: 10, opacity: 0.85, fontSize: 14 }}>
              Waiting for other player…
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GamePlay;
