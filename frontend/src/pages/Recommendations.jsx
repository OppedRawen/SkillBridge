import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Recommendations = () => {
  const [resources, setResources] = useState([]);

  useEffect(() => {
    // Example GET request for recommendations
    // Suppose your backend route is /recommendations?skills=missingSkill1,missingSkill2
    // Adjust as necessary for your real endpoint
    const fetchRecommendations = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:8000/recommendations');
        setResources(response.data); // e.g. an array of { title, url, description }
      } catch (error) {
        console.error('Error fetching recommendations:', error);
      }
    };

    fetchRecommendations();
  }, []);

  return (
    <div>
      <h2>Recommended Resources</h2>
      {resources.length === 0 ? (
        <p>No resources found, or endpoint not yet implemented.</p>
      ) : (
        <ul>
          {resources.map((res, idx) => (
            <li key={idx}>
              <a href={res.url} target="_blank" rel="noreferrer">{res.title}</a>
              <p>{res.description}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Recommendations;
