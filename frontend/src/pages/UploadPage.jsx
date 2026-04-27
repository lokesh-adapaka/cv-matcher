import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CVUploader from '../components/CVUploader';
import SkillTag from '../components/SkillTag';
import { uploadCV } from '../services/api';

export default function UploadPage() {
  const [loading, setLoading] = useState(false);
  const [parsedCV, setParsedCV] = useState(null);
  const [cvId, setCvId] = useState(null);
  const [error, setError] = useState('');
  const [jobTitles, setJobTitles] = useState([]);
  const [titleInput, setTitleInput] = useState('');
  const navigate = useNavigate();

  const addTitle = () => {
    const trimmed = titleInput.trim();
    if (trimmed && !jobTitles.includes(trimmed)) {
      setJobTitles((prev) => [...prev, trimmed]);
    }
    setTitleInput('');
  };

  const removeTitle = (title) => {
    setJobTitles((prev) => prev.filter((t) => t !== title));
  };

  const handleTitleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTitle();
    }
  };

  const handleUpload = async (file) => {
    setLoading(true);
    setError('');
    setParsedCV(null);
    try {
      const data = await uploadCV(file);
      setCvId(data.cv_id);
      setParsedCV(data.parsed_cv);
    } catch (err) {
      const msg =
        err.response?.data?.detail || 'Failed to upload and parse CV. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-bold text-gray-900">
          Find Your Perfect Job Match
        </h1>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto">
          Upload your CV and our AI will analyze your skills, find matching jobs, and
          generate tailored resumes that get you hired.
        </p>
      </div>

      {/* Upload Area */}
      <CVUploader onUpload={handleUpload} isLoading={loading} />

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Parsed CV Results */}
      {parsedCV && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">CV Analysis</h2>
            <span className="text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">
              Parsed Successfully
            </span>
          </div>

          {/* Name & Contact */}
          {parsedCV.name && (
            <div>
              <h3 className="text-lg font-semibold text-gray-800">{parsedCV.name}</h3>
              <p className="text-sm text-gray-500">
                {[parsedCV.email, parsedCV.phone].filter(Boolean).join(' • ')}
              </p>
            </div>
          )}

          {/* Summary */}
          {parsedCV.summary && (
            <div>
              <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Summary
              </h4>
              <p className="text-gray-700">{parsedCV.summary}</p>
            </div>
          )}

          {/* Skills */}
          {parsedCV.skills?.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Skills ({parsedCV.skills.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {parsedCV.skills.map((skill) => (
                  <SkillTag key={skill} skill={skill} />
                ))}
              </div>
            </div>
          )}

          {/* Experience */}
          {parsedCV.experience?.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Experience
              </h4>
              <div className="space-y-3">
                {parsedCV.experience.map((exp, i) => (
                  <div key={i} className="border-l-2 border-blue-200 pl-4">
                    <p className="font-medium text-gray-800">{exp.title}</p>
                    <p className="text-sm text-gray-500">
                      {exp.company}
                      {exp.duration && <span> • {exp.duration}</span>}
                    </p>
                    {exp.description && (
                      <p className="text-sm text-gray-600 mt-1">{exp.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Education */}
          {parsedCV.education?.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Education
              </h4>
              <div className="space-y-2">
                {parsedCV.education.map((edu, i) => (
                  <div key={i} className="border-l-2 border-purple-200 pl-4">
                    <p className="font-medium text-gray-800">{edu.degree}</p>
                    <p className="text-sm text-gray-500">
                      {edu.institution}
                      {edu.year && <span> • {edu.year}</span>}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Job Title Filter */}
          <div>
            <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Job Titles to Search For
            </h4>
            <p className="text-xs text-gray-400 mb-2">
              Add one or more job titles to focus your search (e.g. &quot;Software Engineer&quot;, &quot;Data Scientist&quot;). Press Enter or click Add.
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={titleInput}
                onChange={(e) => setTitleInput(e.target.value)}
                onKeyDown={handleTitleKeyDown}
                placeholder="e.g. Frontend Developer"
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={addTitle}
                className="px-4 py-2 bg-gray-800 text-white text-sm font-medium rounded-lg hover:bg-gray-900 transition-colors"
              >
                Add
              </button>
            </div>
            {jobTitles.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {jobTitles.map((title) => (
                  <span
                    key={title}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 text-sm font-medium rounded-full border border-blue-200"
                  >
                    {title}
                    <button
                      type="button"
                      onClick={() => removeTitle(title)}
                      className="ml-1 text-blue-400 hover:text-blue-700 font-bold"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="pt-4 border-t border-gray-100 space-y-3">
            <button
              onClick={() => {
                const params = new URLSearchParams();
                if (jobTitles.length > 0) params.set('titles', jobTitles.join(','));
                const query = params.toString();
                navigate(`/matches/${cvId}${query ? `?${query}` : ''}`);
              }}
              className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors text-lg"
            >
              Find Matching Jobs →
            </button>
            <button
              onClick={() => navigate(`/jd-analyze/${cvId}`)}
              className="w-full py-3 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 transition-colors text-lg"
            >
              Paste a Job Description & Analyze Match →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
