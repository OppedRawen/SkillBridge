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
    <div className="max-w-3xl mx-auto p-6 bg-white shadow-md rounded-md">
      <h2 className="text-2xl font-bold mb-4">Skill Gap Analysis Tool</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* File Upload */}
        <div>
          <label className="block text-gray-700 font-semibold mb-1">Upload Resume (PDF):</label>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            required
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4
                       file:rounded file:border-0 file:text-sm file:font-semibold
                       file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>

        {/* Job Description Textbox */}
        <div>
          <label className="block text-gray-700 font-semibold mb-1">Job Description:</label>
          <textarea
            rows="4"
            value={jobDescription}
            onChange={handleDescriptionChange}
            required
            className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 focus:ring-4 focus:ring-blue-300"
        >
          Analyze
        </button>
      </form>

      {/* Results Section */}
      {results && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold mb-2">Results:</h3>
          <p>
            <strong className="font-medium">Matched Skills:</strong>{' '}
            {results.matched_skills.join(', ')}
          </p>
          <h4 className="mt-4 mb-2 text-lg font-medium">Categorized Missing Skills:</h4>
          <ul className="list-disc ml-6 space-y-1">
            {Object.entries(results.categorized_missing_skills).map(([skill, categories]) => (
              <li key={skill}>
                <strong className="font-semibold">{skill}:</strong>{' '}
                {categories
                  .map((c) => `${c[0]} (${(c[1] * 100).toFixed(2)}%)`)
                  .join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ResumeAnalyzer;
