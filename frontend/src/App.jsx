import { useState } from 'react';
import MainGameScreen from './MainGameScreen.jsx';

function App() {
  const [screen, setScreen] = useState('main');

  const handleStart = () => setScreen('game');

  if (screen === 'main') return <MainGameScreen onStart={handleStart} />;

  // You can add other screens here
  return null;
}

export default App;
