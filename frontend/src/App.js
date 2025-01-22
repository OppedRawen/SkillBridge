import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Navbar from './components/Navbar';
import Home from './pages/Home';
import ResumeAnalyzer from './pages/ResumeAnalyzer';
import Recommendations from './pages/Recommendations';
import JobSearch from './pages/Jobsearch';
import Jobanalyzer from './pages/Jobanalyzer';

function App() {
  return (
    <Router>
      <Navbar />
      <div style={{ padding: '20px' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<ResumeAnalyzer />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/jobs" element={<JobSearch />} />
          <Route path="/jobanalyze" element={<Jobanalyzer />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
