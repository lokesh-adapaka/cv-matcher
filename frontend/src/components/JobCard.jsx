import { useState } from 'react';
import MatchScore from './MatchScore';
import SkillTag from './SkillTag';
import { generateTailoredCV, downloadBlob } from '../services/api';

export default function JobCard({ match, cvId }) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      const blob = await generateTailoredCV(cvId, match.job_id);
      downloadBlob(blob, `tailored_cv_${match.job_title.replace(/\s+/g, '_')}.pdf`);
    } catch (err) {
      setError('Failed to generate CV. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-6">
      <div className="flex gap-6">
        {/* Match Score */}
        <div className="flex-shrink-0">
          <MatchScore percentage={match.match_percentage} />
        </div>

        {/* Job Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {match.job_title}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {match.company}
            {match.location && <span> &bull; {match.location}</span>}
          </p>
          {match.salary && (
            <p className="text-sm font-medium text-green-700 mt-1">{match.salary}</p>
          )}

          {/* Explanation */}
          <p className="text-sm text-gray-500 mt-3">{match.match_explanation}</p>

          {/* Skills */}
          <div className="mt-4 space-y-2">
            {match.matched_skills?.length > 0 && (
              <div>
                <span className="text-xs font-medium text-gray-500 mr-2">Matched:</span>
                <div className="inline-flex flex-wrap gap-1">
                  {match.matched_skills.map((skill) => (
                    <SkillTag key={skill} skill={skill} type="matched" />
                  ))}
                </div>
              </div>
            )}
            {match.missing_skills?.length > 0 && (
              <div>
                <span className="text-xs font-medium text-gray-500 mr-2">Missing:</span>
                <div className="inline-flex flex-wrap gap-1">
                  {match.missing_skills.map((skill) => (
                    <SkillTag key={skill} skill={skill} type="missing" />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {generating ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-2 h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Generating...
                </>
              ) : (
                'Generate Tailored CV'
              )}
            </button>
            {match.job_url && (
              <a
                href={match.job_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                View Job →
              </a>
            )}
          </div>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>
      </div>
    </div>
  );
}
