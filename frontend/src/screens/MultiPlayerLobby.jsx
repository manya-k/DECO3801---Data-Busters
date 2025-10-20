import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listRooms, createRoom, joinRoom } from "../../api/multiplayer/RoomManagementApi.js";
import "../styles/MultiplayerLobby.css"; // Import CSS for styling
import Button from "../components/Button/Button.jsx";
import BasePage from "./BasePage.jsx";
import { useSession } from "../../SessionContext.jsx";
import { startPrerender } from "../../api/single-player/GameApi.js";

/**
 * MultiplayerLobby Component
 * 
 * This component renders the multiplayer lobby screen where users can:
 *  - Enter their nickname.
 *  - Create a new multiplayer room for collaboration
 *  - View the list of available rooms.
 *  - Join an existing room using the codes provided on the screen.
 * 
 * The component uses React Query to fetch the list of rooms from the backend
 * and React Router's `useNavigate` for programmatic navigation to rooms.
 * Local state is used to manage the player's name and the current room code.
 */
const MultiplayerLobby = () => {
  // Local state to store player name and room code
  const [playerName, setPlayerName] = useState("");
  const [roomCode, setRoomCode] = useState("");
  const { sessionId, setSessionId } = useSession();
  const [mode, setMode] = useState("peer"); // "peer" or "host"
  const navigate = useNavigate();

  // Fetch list of available rooms using React Query
  const {
      data: roomList,
      isLoading: isRoomsLoading,
      error: roomError,
  } = useQuery({
      queryKey: ["rooms"],
      queryFn: () => listRooms(),
  });

  /**
   * Handle creating a new multiplayer room.
   * - Ensures the player enters a nickname.
   * - Calls API to create a new room.
   * - Updates local state with the room code.
   * - Navigates to the created room.
   */
  const handleCreateRoom = async () => {
    if (!playerName) {
        return alert("Please Enter a NickName");
    }
    const data = await createRoom(playerName, mode);
    setSessionId(data.session_id);
    await startPrerender(data.session_id, 2035);
    setRoomCode(data.room_code);
    console.log(roomCode);
      if (mode === "peer") {
 navigate(`/background-multi/${data.room_code}/${playerName}`);
  } else {
    navigate(`/projection-host/${data.room_code}?playerName=${playerName}&hostName=${playerName}&mode=${mode}`);
  }
    // Navigate to multiplayer room screen
    // navigate(`/multiplayer-room/${data.room_code}/${playerName}`);
    console.log("navigated with session id " + data.session_id);
  };


  /**
   * Handle joining an existing multiplayer room.
   * - Prompts the user for a name.
   * - Calls API to join the specified room.
   * - Updates local state with player name and room code.
   * - Navigates to the joined room on success.
   *
   * @async
   * @param {string} code - The room code to join.
   * @returns {Promise<void>}
   */
  const handleJoinRoom = async (code) => {
    const name = window.prompt("Enter your name to join the room:");
    if (!name) {
      alert("Sorry");
    }
    setRoomCode(code);
    setPlayerName(name); 
    try {
      const data = await joinRoom(code, name);
      if (data.success == "True") {
        setSessionId(data.session_id);
        console.log("session id is " + data.session_id);
        console.log("the host of this room is: " + data.host)
        console.log("the game has started? " + data.game_started)

        if (data.mode == "host") {
          if (data.game_started == "False") {
            console.log("went to background screen");
              navigate(`/projection-host/${code}?playerName=${name}&hostName=${data.host}&mode=${mode}`);
          } else {
              navigate(`/player-room/${code}?playerName=${name}&hostName=${data.host}&mode=${mode}`);
          }
        } else { 
          navigate(`/background-multi/${code}/${name}&mode=${mode}`);
          console.log("navigated")
        }

      } else {
        alert("Sorry, unable to join the room. Please try again.");
      }
    } catch (err) {
      console.error(err);
      alert("Error joining room. Please try again.");
    }
  };

  return (
    <BasePage>
      <div className="multiplayer-lobby">
        <h2 className="title">Multiplayer Lobby</h2>
        <div className="room-input-container">
          <div className="input-row">
            <input
              className="player-input"
              type="text"
              placeholder="Enter your name"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
            />
            <button className="btn-create-room" onClick={handleCreateRoom}>
              Create Room
            </button>
          </div>

          {/* Toggle moved below input + button */}
          <div className="inline-mode-toggle">
            <label className={`mode-switch ${mode}`}>
              <input
                type="checkbox"
                checked={mode === "host"}
                onChange={(e) => setMode(e.target.checked ? "host" : "peer")}
              />
              <span className="slider"></span>
            </label>
            <span className="mode-inline-label">
              {mode === "host" ? (
                <>
                  🖥️ Host Mode
                </>
              ) : (
                <>
                  👥 Peer-to-Peer
                </>
              )}
            </span>
          </div>
        </div>


        <h3 className="subheading">Available Rooms</h3>
        <ul className="room-list">
          {roomList?.rooms?.map((code) => (
            <li key={code} className="room-item">
              <span className="room-code">{code}</span>
              <button className="btn-create-room" onClick={() => handleJoinRoom(code)}>Join</button>
            </li>
          ))}
        </ul>
        <div className="button-container">
          <Button baseButton="btn-exit" action={() => navigate("/")} title="Back" />
        </div>
      </div>
    </BasePage >
  );
};

export default MultiplayerLobby;



