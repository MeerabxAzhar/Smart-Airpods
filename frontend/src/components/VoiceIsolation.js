import { useState } from "react";
import { FaBluetoothB } from "react-icons/fa";
import "../styles/VoiceIsolation.css";
import logo from '../icons/logo.png';

export default function VoiceIsolation() {
  const [levels, setLevels] = useState({
    person1: 50,
    person2: 50,
    person3: 50,
    person4: 50,
  });
  const [ancEnabled, setAncEnabled] = useState(false);
  const [error, setError] = useState(null);

  const handleSliderChange = (person, value) => {
    setLevels({ ...levels, [person]: value });
  };

  const handleAncToggle = async () => {
    try {
      setError(null);
      console.log('Sending ANC toggle request...');
      const response = await fetch('http://localhost:5000/run/anc', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      console.log('Response received:', response.status);
      const data = await response.json();
      console.log('Response data:', data);
      
      if (data.status === 'success') {
        setAncEnabled(!ancEnabled);
        console.log('ANC toggled successfully');
      } else {
        setError(data.message || 'Failed to toggle ANC');
        console.error('Error in response:', data.message);
      }
    } catch (error) {
      setError('Failed to connect to the server. Please make sure the backend is running.');
      console.error('Error toggling ANC:', error);
    }
  };

  return (
    <div className="voice-isolation-container">
      {/* Header */}
      <div className="voice-isolation-header">
        <img src={logo} alt="AuroraFX Logo" className="voice-isolation-logo" />
        <FaBluetoothB className="voice-isolation-bluetooth-icon" />
      </div>

      {/* ANC Toggle Section */}
      <div className="anc-toggle-section">
        <h2>Active Noise Cancellation</h2>
        <button 
          className={`anc-toggle-button ${ancEnabled ? 'enabled' : 'disabled'}`}
          onClick={handleAncToggle}
        >
          {ancEnabled ? 'ON' : 'OFF'}
        </button>
        {error && <div className="error-message">{error}</div>}
      </div>

      {/* Voice Isolation Section */}
      <div className="voice-isolation-settings">
        <h2>Voice isolation</h2>
        {["person1", "person2", "person3", "person4"].map((person, index) => (
          <div key={index} className="voice-isolation-slider">
            <span>Person {index + 1}</span>
            <input
              type="range"
              min="0"
              max="100"
              value={levels[person]}
              onChange={(e) => handleSliderChange(person, e.target.value)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
