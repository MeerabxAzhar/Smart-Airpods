## Smart Airpods

**Real-Time Noise Cancellation, Frequency Isolation, and Translation for Smart AirPods**

## Project Overview
SmartAirPods is an innovative audio solution combining three advanced functionalities:

1. **Active Noise Cancellation (ANC)** – Completely blocks external sounds.  
2. **Real-Time Frequency Isolation** – Amplify, reduce, or mute specific voices or sounds in your surroundings.  
3. **Real-Time Translation** – Translates foreign languages into your language with the same speaker accent.

This project is ideal for classrooms, group meetings, and noisy environments.

---

## Features
-  **ANC:** Blocks all unwanted noise efficiently  
-  **Frequency Isolation:** Control individual sound sources with sliders  
-  **Translation:** Real-time translation with speaker’s accent preserved  
-  **Mobile App:** React Native frontend with interactive UI  
-  **Low Latency Processing:** Near real-time performance for smooth experience  

---

## Architecture
Microphone -> App (Processing Module)
        |                                  |
        |----> Noise Cancellation           |
        |----> Frequency Isolation         |
        |----> Real-Time Translation       |
        v
      Output to SmartAirPods
## Installation Requirements

- Python
- Node.js
- Visual Studio Code
## Setup

- Clone the repository:
git clone https://github.com/MeerabxAzhar/SmartAirPods.git
cd SmartAirPods

- Install backend dependencies:
pip install -r requirements.txt

- Run the app:
python backend/main.py

- Launch the mobile frontend:
cd frontend
npm install
npx react-native run-android
## License

MIT License © 2025 Meerab Azhar
