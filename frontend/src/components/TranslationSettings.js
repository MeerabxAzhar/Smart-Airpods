import { useState } from "react";
import { FaBluetoothB } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import "../styles/TranslationSettings.css";
import logo from '../icons/logo.png';

export default function TranslationSettings() {
  const [selectedLanguage, setSelectedLanguage] = useState("English");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const languages = [
    "English", 
    "Hindi", 
    "Spanish", 
    "French", 
    "German", 
    "Italian", 
    "Japanese", 
    "Korean", 
    "Chinese"
  ];

  const handleStartTranslation = async () => {
    setIsTranslating(true);
    setError(null);
    
    try {
      console.log(`Starting translation with language: ${selectedLanguage}`);
      
      // Send the selected language to the backend API
      const response = await fetch('http://localhost:5000/run/translation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ language: selectedLanguage }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      
      if (data.status === 'success') {
        console.log('Translation started successfully:', data.message);
        // You could add a success message or notification here
      } else {
        setError(data.message || 'Failed to start translation');
        console.error('Failed to start translation:', data.message);
        setIsTranslating(false); // Reset state if failed to start
      }
    } catch (error) {
      setError(error.message || 'Error connecting to backend');
      console.error('Error connecting to backend:', error);
      setIsTranslating(false); // Reset state if error occurred
    }
  };

  const handleStopTranslation = async () => {
    try {
      console.log('Stopping translation...');
      
      // Send a request to stop the translation
      const response = await fetch('http://localhost:5000/run/translation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ language: selectedLanguage }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Stop response data:', data);
      
      if (data.status === 'success') {
        console.log('Translation stopped successfully:', data.message);
        setIsTranslating(false);
      } else {
        setError(data.message || 'Failed to stop translation');
        console.error('Failed to stop translation:', data.message);
      }
    } catch (error) {
      setError(error.message || 'Error connecting to backend');
      console.error('Error connecting to backend:', error);
    }
  };

  return (
    <div className="translation-container">
      {/* Header */}
      <div className="translation-header">
        <img src={logo} alt="AuroraFX Logo" className="translation-logo" />
        <FaBluetoothB className="translation-bluetooth-icon" />
      </div>

      {/* Real-Time Translation Section */}
      <div className="translation-settings">
        <h2>Real-Time Translation</h2>
        
        {/* Dropdown */}
        <div className="dropdown">
          <button className="dropdown-btn" onClick={() => setDropdownOpen(!dropdownOpen)}>
            {selectedLanguage} <span className="dropdown-arrow">▼</span>
          </button>
          {dropdownOpen && (
            <ul className="dropdown-menu">
              {languages.map((lang, index) => (
                <li
                  key={index}
                  className={lang === selectedLanguage ? "active" : ""}
                  onClick={() => {
                    setSelectedLanguage(lang);
                    setDropdownOpen(false);
                  }}
                >
                  {lang}
                </li>
              ))}
            </ul>
          )}
        </div>
        
        {/* Translation Buttons */}
        <div className="translation-button-container">
          {!isTranslating ? (
            <button 
              className="translation-button"
              onClick={handleStartTranslation}
            >
              Start Translation
            </button>
          ) : (
            <button 
              className="translation-button stop-button"
              onClick={handleStopTranslation}
            >
              Stop Translation
            </button>
          )}
          {error && <div className="error-message">{error}</div>}
        </div>
      </div>
    </div>
  );
}
