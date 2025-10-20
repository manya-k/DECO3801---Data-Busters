import { useState, useEffect, useRef, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getQuestion, submitChoice, getVotingInfo } from "../../../api/multiplayer/GameFlowApi.js";
import Button from "../../components/Button/Button.jsx";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import "../../styles/GamePlay.css";
import { useSession } from "../../../SessionContext.jsx";
import background from "../../assets/background.jpg";
import ExitExperience from "../../components/ExitExperience/ExitExperience.jsx";
import BasePage from "../BasePage.jsx";
import LoadingScreen from "../../components/Loading/LoadingScreen.jsx";
import RoomDestroyedPopup from "../../components/RoomDestroy/RoomDestroyedDisplay.jsx";
import { getFunFacts } from "../../../api/single-player/GameApi.js";
import VotingDisplay from "../../components/Voting Display/VotingDisplay.jsx";
import { useBgm } from "../../audio/AudioProvider.jsx"; // <-- use bgm state/controls

const HostScreen = () => {
  const { roomCode } = useParams(); 
  const [searchParams] = useSearchParams();
  const playerName = searchParams.get("playerName");
  const { sessionId } = useSession();  
  const [year, setYear] = useState(2035);
  const [screen, setScreen] = useState("scenario"); 
  const [currentTurn, setCurrentTurn] = useState(null);
  const [loadingFacts, setLoadingFacts] = useState([]);
  const [isReady, setIsReady] = useState(false);
  const [option_id, setOptionId] = useState(null);
  const [turn, setTurn] = useState(-1);
  const [loadingState, setLoadingState] = useState("none");
    const [stage, setStage] = useState(0);
      const fadeDuration = 2000;
  const [roomDestroyed, setRoomDestroyed] = useState(false);
  const [votes, setVotes] = useState([]);
    const [hasAnimated, setHasAnimated] = useState(false); 
    // --- Tie narration to BGM ---
    const { isPlaying, volume, setVolume } = useBgm();
  const [totalPlayers, setTotalPlayers] = useState(1);
  const [scenarioData, setScenarioData] = useState({
  scenario: 
    "The year is 2035, and neurotechnology now makes memory manipulation precise and reliable. " +
    "Once experimental, memory editing, enhancement, and storage are mainstream, forcing governments " +
    "to confront choices that could redefine humanity. manipulation not just possible, but precise and reliable." +
    "Memory editing, enhancement," +
    "These technologies can erase trauma, boost learning, and even share memories, offering both promise " +
    "and peril. Nations clash over freedom versus regulation, while corporations drive new concerns around privacy," +
    " ownership, and the commercialization of consciousness.",
    image: background // no image for the first one
});


  const {
    data: questionData
  } = useQuery ({
    queryKey: ["question", roomCode, sessionId, turn, year], 
    queryFn: async() => {
        console.log("queryFn running for", year);
        const result = await getQuestion(sessionId, roomCode, turn , year);
        if (!result ) {
          setScreen("loading");
          setLoadingState("question");
          await fetchFunFacts();
          console("loading at the moment");
          return null;
        } else {
          setCurrentTurn(result);
          setTurn(result.turn_id);
          setScreen("question");
          setLoadingState("none")
          console.log("recieved question data: " + result);
          setScenarioData(null);
          return result;
        }
    }, enabled: loadingState == "question", 
    refetchInterval: 3000
  })


  // --- Minimal TTS: inline (no extra files/deps) ---
  const synthRef = useRef(typeof window !== "undefined" ? window.speechSynthesis : null);
  const prevVolRef = useRef(null); // remember user volume while narrating
  const duckFactor = 0.3; // simple lower (no separate ducking state)

  const cancelTTS = () => {
    try { synthRef.current?.cancel(); } catch { }
    // Restore volume if we changed it
    if (prevVolRef.current !== null) {
      setVolume(prevVolRef.current);
      prevVolRef.current = null;
    }
  };

  const speak = (text) => {
    if (!synthRef.current || !text) return;
    // Cancel any previous narration
    cancelTTS();

    // Only narrate if BGM is playing (toolbar controls this)
    if (!isPlaying) return;

    // Lower BGM volume temporarily (minimal approach)
    prevVolRef.current = volume;
    setVolume(Math.max(0, Math.min(1, volume * duckFactor)));

    const utter = new SpeechSynthesisUtterance(String(text));
    // --- choose voice here ---
    const voices = synthRef.current.getVoices();
    const prefs = [
      /Microsoft Sonia Online \(Natural\).*English \(United Kingdom\)/i, // Edge (neural)
      /Microsoft Jenny Online \(Natural\).*English \(United States\)/i,  // Edge (neural)
      /Samantha/i, /Victoria/i, /Serena/i, /Daniel/i,                    // macOS built-ins
      /Google UK English Female/i                                        // Chrome fallback
    ];
    const picked = prefs
      .map(rx => voices.find(v => rx.test(v.name)))
      .find(Boolean) || voices[0];
    utter.voice = picked;
    // tweak for more “majestic” feel
    utter.rate = 0.90;  // slower = more weighty
    utter.pitch = 1.12;  // deeper
    utter.volume = 1;   // full, since we ducked bgm


    utter.onend = utter.onerror = () => {
      // Restore BGM volume
      if (prevVolRef.current !== null) {
        setVolume(prevVolRef.current);
        prevVolRef.current = null;
      }
    };
  
  
      try { synthRef.current.speak(utter); } catch {
        // In case of any error, restore
        if (prevVolRef.current !== null) {
          setVolume(prevVolRef.current);
          prevVolRef.current = null;
        }
      }
    };
  
  
    // Build readout for question + options
    const questionReadout = useMemo(() => {
      if (!questionData) return "";
      const q = String(questionData.question || "");
      const alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
      const parts = Object.entries(questionData.options || {}).map(
        ([, text], i) => `Option ${alpha[i] || i + 1}: ${String(text)}`
      );
      return [q, ...parts].join(". ");
    }, [questionData]);
  
  
    // Auto-read Scenario when it shows (and BGM is playing)
    useEffect(() => {
      if (screen === "scenario" && scenarioData?.scenario) {
        speak(scenarioData.scenario);
      }
      return () => cancelTTS();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [screen, scenarioData?.scenario, isPlaying]); // tie to playing state
  
  
    // Auto-read Question + Options when it shows (and BGM is playing)
    useEffect(() => {
      if (screen === "question" && questionReadout) {
        speak(questionReadout);
      }
      return () => cancelTTS();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [screen, questionReadout, isPlaying]);
  
  
    // Replay narration when toolbar Play is clicked (even if already playing)
    useEffect(() => {
      const handler = () => {
        if (screen === "scenario" && scenarioData?.scenario) {
          speak(scenarioData.scenario);
        } else if (screen === "question" && questionReadout) {
          speak(questionReadout);
        }
      };
      window.addEventListener("bgm-play", handler);
      return () => window.removeEventListener("bgm-play", handler);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [screen, scenarioData?.scenario, questionReadout, isPlaying]);
  
  
    const {data: votingData} = useQuery({
      queryKey: ["votingStatus", roomCode, currentTurn?.turn_id], 
      queryFn: async() => {
          console.log("the current turn is: " + currentTurn)
          console.log(
          `[VotingQuery] Fetching voting info for room=${roomCode}, turn=${currentTurn.turn_id}...`
          );
          if (currentTurn === null) return;
          const res = await getVotingInfo(roomCode, currentTurn.turn_id);
          console.log("[VotingQuery] Raw API response:", res);
          const data = res.data
          console.log("[VotingQuery] Parsed data:", res.data);
          console.log("[VotingQuery] onSuccess triggered. Data:", data);
          if (!data) {
            console.log("[VotingQuery] Data empty, skipping state update.");
            return;
          }
                // Map backend vote dictionary → frontend structure
          const mappedVotes = Object.entries(data.votes).map(([player, option]) => ({
            name: player,
            votedFor: option,
            hasVoted: option !== "Pending",
          }));
          console.log(mappedVotes);
          console.log("[VotingQuery] Mapped votes:", mappedVotes);
          const votesCount = data.num_responses;
          const totalCount = data.total_players;
          const allVoted = votesCount >= totalCount;
          setVotes(mappedVotes);
          setTotalPlayers(data.total_players);
  
  
          console.log(
            `[VotingQuery] Vote Progress: ${votesCount}/${totalCount} | All voted? ${allVoted}`
          );
          if (allVoted) {
            console.log("All players voted!");
            setOptionId(data.final_option);
            setScreen("loading");
            setLoadingState("scenario");
            await fetchFunFacts();
            if (!scenarioData || !scenarioData.scenario) {
              console.log("Scenario not ready → go to loading screen");
              setScreen("loading");
              setLoadingState("scenario");
              await fetchFunFacts();
            } else {
              console.log("Scenario ready → show scenario");
              setScreen("scenario");
            }
          }
          return result;
        }, enabled: loadingState === "none", 
        refetchInterval: 3000
      
    })
  
  
    /**
     * Handles a player's choice when answering a question.
     *
     * @param {string} answer - The key of the chosen option.
     */
    const {
      data: out,
      isLoading: isTurnLoading,
      error: turnError,
      status: turnStatus,
      } = useQuery({
        queryKey: ["scenario", playerName, roomCode, currentTurn, sessionId, roomCode, option_id, year],
        queryFn: async () => {
          console.log("submitting option", sessionId);
          const out = await submitChoice(playerName, roomCode, sessionId,currentTurn.turn_id, year, option_id);
          if (!out || !out.scenario || !out.scenario.text) {
            if (!out.room_exists) {
              setRoomDestroyed(true); 
              setScreen("destroyed");
            }
            console.log("dont have scenario yet");
            return null;
        }
        console.log("the data is", out );
        const mapped = {
          scenario: out.scenario.text,
          image: out.image.url
        };
        console.log("Submit choice response:", mapped);
        setScreen("scenario");
        setScenarioData(mapped);
        setYear(year + 1);
        setOptionId(null);
        return out;
      },
      enabled: loadingState == "scenario",
      onError: (err) => {
        console.log("onError:", err);
      }, 
      refetchInterval: 1000
  });
  
  useEffect(() => {
    if (screen === "question") {
      console.log("[Animation] Resetting staged animation for new question");
      setHasAnimated(false);
      setStage(0);
    }
  }, [currentTurn, screen])
  
  
  // --- Staged reveal ---
    // 0 = nothing, 1 = question, 2 = option1, 3 = option2, 4 = final all
   
    useEffect(() => {
      if (screen === "question" && currentTurn) {
        setStage(1); // show question
        speak(currentTurn.question);
  
  
        const timer1 = setTimeout(() => {
          setStage(2);
          speak(currentTurn.options[0].option_text);
        }, 10000 - fadeDuration);
  
  
        const timer2 = setTimeout(() => {
          setStage(3);
          speak(currentTurn.options[1].option_text);
        }, 15000 - fadeDuration);
  
  
        const timer3 = setTimeout(() => {
          setStage(4); // show all together, no TTS
        }, 20000 - fadeDuration);
  
  
        return () => {
          clearTimeout(timer1);
          clearTimeout(timer2);
          clearTimeout(timer3);
          cancelTTS();
        };
      }
    }, [screen, currentTurn]);
  
  
  const getFadeClass = (idx) => {
    switch(idx) {
      case 1: return stage === 1 || stage === 4 ? "fade-in-out show" : stage > 1 ? "fade-in-out hide" : "fade-in-out";
      case 2: return stage === 2 || stage === 4 ? "fade-in-out show" : stage > 2 ? "fade-in-out hide" : "fade-in-out";
      case 3: return stage === 3 || stage === 4 ? "fade-in-out show" : stage > 3 ? "fade-in-out hide" : "fade-in-out";
      default: return "fade-in-out";
    }
  };
  
  
      // Fetch fun facts when loading scenario
      const fetchFunFacts = async () => {
        try {
          const facts = await getFunFacts(); // Fetch 3 fun facts
          setLoadingFacts(facts.data);
          console.log("Fun facts loaded:", facts);
        } catch (error) {
            console.error("Error fetching fun facts:", error);
        }
      }
  
  
  return (
    <BasePage>
      <ExitExperience code={roomCode} player={playerName} />

      {screen === "destroyed" && <RoomDestroyedPopup />}

      {screen === "loading" && (
        <LoadingScreen
          isReady={!!scenarioData?.scenario}
          funFacts={loadingFacts}
          onContinue={() => setScreen("scenario")}
        />
      )}

      {screen === "scenario" && scenarioData && (
        <div className="scenario-screen">

          <div className="text-container menu-glass">
          {/* Image in middle */}
          {scenarioData.image && (
            <div className="scenario-image">
              <img src={scenarioData.image} alt="scenario" className="scenario-img" />
            </div>
          )}
          </div>
          {/* Continue button at bottom */}
          <div className="scenario-footer">
            <Button
              baseButton="btn-primary"
              action={() => {
                setScreen("loading");
                setLoadingState("question");
                setCurrentTurn(null);
                //setFetchQuestion(true);
                setScenarioData(null);
                console.log("Session ID:", sessionId);
              }}
              title="Continue"
            />
          </div>
        </div>
      )}
      {screen === "question" && currentTurn && (
        <div className="question-screen">
          {/* Left side: question and choices */}
          <div className="question-main menu-glass">
            <div className="question-container">
              <h2 className={getFadeClass(1)}>{currentTurn.question}</h2>
            </div>
            {/* Host doesn’t need to choose, optionally hide buttons */}
            {/* Right side: voting display */}
          <div className="voting-sidebar">
            <VotingDisplay voters={votes} totalPlayers={totalPlayers} />
            </div>
          </div>
        </div>
      )}
    </BasePage>
  );
};

export default HostScreen;
