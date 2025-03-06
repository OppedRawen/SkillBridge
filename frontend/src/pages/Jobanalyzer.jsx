import React, { useState } from 'react';
import axios from 'axios';

const Jobanalyzer = () => {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [useSemanticMatching, setUseSemanticMatching] = useState(true);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleDescriptionChange = (event) => {
    setJobDescription(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);

    if (!file || !jobDescription) {
      setError('Please provide both a resume file and job description.');
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('job_description', jobDescription);
    formData.append('use_semantic', useSemanticMatching);

    try {
      const response = await axios.post('http://127.0.0.1:8000/jobs/jobAnalyzer', formData);
      setResults(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error uploading data:', error);
      setError('An error occurred while processing your request. Please try again.');
      setLoading(false);
    }
  };

  // Helper function to render skill lists
  const renderSkillList = (skills, type) => {
    if (!skills || Object.keys(skills).length === 0) {
      return <p>No {type} skills found.</p>;
    }

    return (
      <ul className="space-y-1">
        {Object.entries(skills).map(([skill, value]) => (
          <li key={skill} className="flex items-center">
            <span className="font-medium">{skill}</span>
            {typeof value === 'number' && (
              <span className="ml-2 text-sm text-gray-600">
                (Priority: {value.toFixed(1)})
              </span>
            )}
            {value && value.similarity_score && (
              <span className="ml-2 text-sm text-green-600">
                (Matches "{value.resume_match}" with {(value.similarity_score * 100).toFixed(1)}% similarity)
              </span>
            )}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white shadow-md rounded-md">
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
            rows="5"
            value={jobDescription}
            onChange={handleDescriptionChange}
            required
            className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-300"
            placeholder="Paste the job description here..."
          />
        </div>

        {/* Vector Embedding Mode Toggle */}
        <div className="mt-4">
          <label className="inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={useSemanticMatching}
              onChange={(e) => setUseSemanticMatching(e.target.checked)}
              className="form-checkbox h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
            />
            <span className="ml-2 text-gray-700 font-medium">
              Use semantic matching (vector embeddings)
            </span>
          </label>
          <div className="text-sm text-gray-500 ml-7">
            Enables matching similar skills even when terminology differs
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className={`px-4 py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 ${
            loading ? 'opacity-70 cursor-not-allowed' : ''
          }`}
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </form>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Results Section */}
      {results && (
        <div className="mt-8">
          <h3 className="text-xl font-semibold mb-4">Analysis Results</h3>
          
          {/* Analysis Type Badge */}
          {results.analysis_type && (
            <div className="mb-4">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                results.analysis_type === 'semantic' 
                  ? 'bg-purple-100 text-purple-800' 
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {results.analysis_type === 'semantic' 
                  ? '✨ Semantic Matching' 
                  : '🔍 Exact Matching'}
              </span>
              {results.analysis_type === 'semantic' && results.analysis.similarity_threshold && (
                <span className="text-xs ml-2 text-gray-500">
                  (Similarity threshold: {results.analysis.similarity_threshold})
                </span>
              )}
            </div>
          )}
          
          {/* Display in a 2-column grid for desktop */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Skills Analysis */}
            <div className="space-y-4">
              {/* Missing Skills */}
              <div className="p-4 bg-red-50 rounded border border-red-200">
                <h4 className="font-semibold text-red-700 mb-2">Missing Skills</h4>
                {results.analysis?.missing_skills ? 
                  renderSkillList(results.analysis.missing_skills, "missing") : 
                  <p>No data available</p>
                }
              </div>
              
              {/* Matching Skills */}
              <div className="p-4 bg-green-50 rounded border border-green-200">
                <h4 className="font-semibold text-green-700 mb-2">Matching Skills</h4>
                {results.analysis?.matching_skills ?
                  renderSkillList(results.analysis.matching_skills, "matching") :
                  <p>No data available</p>
                }
              </div>
              
              {/* Resume-only Skills */}
              <div className="p-4 bg-blue-50 rounded border border-blue-200">
                <h4 className="font-semibold text-blue-700 mb-2">Additional Skills on Resume</h4>
                {results.analysis?.resume_only_skills ?
                  renderSkillList(results.analysis.resume_only_skills, "resume-only") :
                  <p>No data available</p>
                }
              </div>
            </div>
            
            {/* Learning Resources */}
            <div className="p-4 bg-yellow-50 rounded border border-yellow-200">
              <h4 className="font-semibold text-yellow-800 mb-2">Learning Recommendations</h4>
              <div className="prose prose-sm">
                {results.llm_output ? (
                  <div dangerouslySetInnerHTML={{ __html: results.llm_output.replace(/\n/g, '<br/>') }} />
                ) : (
                  <p>No recommendations available</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Jobanalyzer;