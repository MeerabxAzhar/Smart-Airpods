import { useState, useEffect } from "react";
import { FaBluetoothB } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import "../styles/AuroraFXSettings.css";
import logo from '../icons/logo_white.png';

export default function AuroraFXSettings() {
  const [features, setFeatures] = useState({
    noiseCancellation: false,
    isolation: false,
    translation: false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Create an h1 element dynamically for the heading
    const heading = document.createElement('h1');
    heading.classList.add('dynamic-heading');

    // Create a span for the first part of the heading (Welcome)
    const welcomeText = document.createElement('span');
    welcomeText.textContent = 'Welcome to AuroraFX!';
    welcomeText.classList.add('welcome-text');

    // Create a span for the second part of the heading (From noise to clarity)
    const clarityText = document.createElement('span');
    clarityText.textContent = 'From noise to clarity';
    clarityText.classList.add('clarity-text');

    // Append both parts to the heading
    heading.appendChild(welcomeText);
    heading.appendChild(document.createElement('br'));  // To add a line break
    heading.appendChild(clarityText);

    // Append the heading to the container (after the header)
    const container = document.querySelector('.aurorafx-container');
    const header = container.querySelector('.aurorafx-header');
    container.insertBefore(heading, header.nextSibling); // Insert the heading below the header

    // Clean up (remove the heading) when component unmounts
    return () => {
      container.removeChild(heading);
    };
  }, []); // Empty dependency array ensures this runs only once when the component mounts

  const toggleFeature = async (feature) => {
    try {
      setIsLoading(true);
      setError(null);

      if (feature === "noiseCancellation") {
        if (!features.noiseCancellation) {
          // Start ANC
          const response = await fetch('http://localhost:5000/run/main_anc', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          const data = await response.json();
          if (data.status === 'success') {
            setFeatures((prev) => ({ ...prev, noiseCancellation: true }));
            console.log('ANC started successfully:', data.message);
          } else {
            setError(data.message || 'Failed to start ANC');
            console.error('Failed to start ANC:', data.message);
          }
        } else {
          // Stop ANC
          const response = await fetch('http://localhost:5000/stop/main_anc', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          const data = await response.json();
          if (data.status === 'success') {
            setFeatures((prev) => ({ ...prev, noiseCancellation: false }));
            console.log('ANC stopped successfully:', data.message);
          } else {
            setError(data.message || 'Failed to stop ANC');
            console.error('Failed to stop ANC:', data.message);
          }
        }
      } else if (feature === "isolation") {
        if (!features.isolation) {
          // Start Main Isolator
          const response = await fetch('http://localhost:5000/run/main_isolator', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          const data = await response.json();
          if (data.status === 'success' || data.status === 'running') {
            setFeatures((prev) => ({ ...prev, isolation: true }));
            console.log('Main Isolator started successfully:', data.message);
          } else {
            setError(data.message || 'Failed to start Main Isolator');
            console.error('Failed to start Main Isolator:', data.message);
          }
        } else {
          // Stop Main Isolator
          const response = await fetch('http://localhost:5000/stop/main_isolator', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          const data = await response.json();
          if (data.status === 'success') {
            setFeatures((prev) => ({ ...prev, isolation: false }));
            console.log('Main Isolator stopped successfully:', data.message);
          } else {
            setError(data.message || 'Failed to stop Main Isolator');
            console.error('Failed to stop Main Isolator:', data.message);
          }
        }
      } else if (feature === "translation") {
        // Toggle the translation feature
        setFeatures(prev => ({ ...prev, [feature]: !prev[feature] }));
        // Navigate to the translation settings page
        navigate('/translationsettings');
      } else {
        setFeatures(prev => ({ ...prev, [feature]: !prev[feature] }));
      }
    } catch (error) {
      setError(error.message || 'Error connecting to backend');
      console.error('Error connecting to backend:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="aurorafx-container">
      {/* Animated Background */}
      <div className="animated-background">
        <div className="animated-lines"></div>
      </div>

      {/* Header (Always on top) */}
      <div className="aurorafx-header">
        <img src={logo} alt="AuroraFX Logo" className="aurorafx-logo" />
        <FaBluetoothB className="aurorafx-bluetooth-icon" />
      </div>

      {/* Feature Toggles */}
      <div className="aurorafx-settings">
        {[{ key: "noiseCancellation", label: "Active Noise Cancellation" },
        { key: "isolation", label: "Isolation" },
        { key: "translation", label: "Real-Time Translation" }]
          .map(({ key, label }) => (
            <div key={key} className="aurorafx-toggle">
              <div
                className={`toggle-button ${features[key] ? "toggle-active" : ""} ${isLoading && features[key] ? "loading" : ""}`}
                onClick={() => !isLoading && toggleFeature(key)}
              >
                <div className="toggle-circle" />
              </div>
              <span>{label}</span>
            </div>
          ))}
        {error && <div className="error-message">{error}</div>}
      </div>
    </div>
  );
}
