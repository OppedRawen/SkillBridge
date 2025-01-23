import React, { useState } from 'react';

const JobSearch = () => {
  const [query, setQuery] = useState('');
  const [jobs, setJobs] = useState([]);

  const handleSearch = async () => {
    // Example: call your /jobs/search endpoint
    // const response = await axios.get(`http://127.0.0.1:8000/jobs/search?query=${query}`);
    // setJobs(response.data);

    console.log(`Searching for jobs related to: ${query}`);
  };

  return (
    <div>
      <h2>Job Search</h2>
      <input
        placeholder="Search for a job..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={handleSearch}>Search</button>

      <div>
        {jobs.length === 0 ? (
          <p>No jobs found yet.</p>
        ) : (
          <ul>
            {jobs.map((job) => (
              <li key={job.jobId}>
                <strong>{job.title}</strong> at {job.company} - {job.location}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default JobSearch;
