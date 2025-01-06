// frontend/src/components/FileUpload.js
import React, { useState } from "react";
import axios from "axios";

const FileUpload = () => {
    const [resumeFile, setResumeFile] = useState(null);
    const [jobDescription, setJobDescription] = useState("");
    const [results, setResults] = useState(null);

    const handleFileChange = (e) => {
        setResumeFile(e.target.files[0]);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!resumeFile || !jobDescription) {
            alert("Please upload a resume and provide a job description.");
            return;
        }

        const formData = new FormData();
        formData.append("resume", resumeFile);
        formData.append("job_description", jobDescription);

        try {
            const response = await axios.post("http://localhost:8000/analyze", formData);
            setResults(response.data);
        } catch (error) {
            console.error("Error uploading the data:", error);
        }
    };

    return (
        <div>
            <h2>Skill Gap Analysis</h2>
            <form onSubmit={handleSubmit}>
                <input type="file" onChange={handleFileChange} />
                <textarea
                    placeholder="Paste the job description here"
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                />
                <button type="submit">Analyze Skills</button>
            </form>

            {results && (
                <div>
                    <h3>Results:</h3>
                    <p><strong>Matched Skills:</strong> {results.matched_skills.join(", ")}</p>
                    <p><strong>Missing Skills:</strong> {results.missing_skills.join(", ")}</p>
                </div>
            )}
        </div>
    );
};

export default FileUpload;
