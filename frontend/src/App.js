// src/App.js
import React from 'react';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import Homepage from './components/home';
import NotFound from './components/NotFound';
import VoiceIsolation from './components/VoiceIsolation';
import TranslationSettings from './components/TranslationSettings';
import SplashScreen from "./components/SplashScreen";


function App() {
  return (

          <Router>
            <Routes>
              {/* <Route path='/' element={<SplashScreen />} /> */}
              {<Route path='/' element={<Homepage />} />}
              <Route path='/VoiceIsolation' element={<VoiceIsolation />} />
              <Route path='/TranslationSettings' element={<TranslationSettings />} />
              <Route path='*' element={<NotFound />} />
              
            </Routes>
          </Router>
  );
}

export default App;
