import React, { useState } from 'react';
import axios from 'axios';

const ResumeAnalyzer = () => {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [results, setResults] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleDescriptionChange = (event) => {
    setJobDescription(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!file || !jobDescription) {
      alert('Please provide both a file and job description.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('job_description', jobDescription);

    try {
      const response = await axios.post('http://127.0.0.1:8000/resumes/analyze', formData);
      setResults(response.data);
    } catch (error) {
      console.error('Error uploading data:', error);
    }
  };

  return (
    <div>
      <h2>Skill Gap Analysis Tool</h2>
      <form onSubmit={handleSubmit}>
        <label>Upload Resume (PDF): </label>
        <input type="file" accept=".pdf" onChange={handleFileChange} required />

        <br />

        <label>Job Description: </label>
        <textarea
          rows="4"
          value={jobDescription}
          onChange={handleDescriptionChange}
          required
        />

        <br />
        <button type="submit">Analyze</button>
      </form>

      {results && (
        <div style={{ marginTop: '20px' }}>
          <h3>Results:</h3>
          <p><strong>Matched Skills:</strong> {results.matched_skills.join(', ')}</p>
          <h4>Categorized Missing Skills:</h4>
          <ul>
            {Object.entries(results.categorized_missing_skills).map(([skill, categories]) => (
              <li key={skill}>
                <strong>{skill}:</strong>{' '}
                {categories.map(c => `${c[0]} (${(c[1] * 100).toFixed(2)}%)`).join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ResumeAnalyzer;
