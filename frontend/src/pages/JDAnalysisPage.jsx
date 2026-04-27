import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import MatchScore from '../components/MatchScore';
import SkillTag from '../components/SkillTag';
import { analyzeJobDescription } from '../services/api';

export default function JDAnalysisPage() {
  const { cvId } = useParams();
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (jobDescription.trim().length < 20) {
      setError('Please paste a complete job description (at least 20 characters).');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    try {
      const data = await analyzeJobDescription(cvId, jobDescription);
      setResult(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to analyze. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link to="/" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
          ← Back to Upload
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mt-1">
          Job Description Analyzer
        </h1>
        <p className="text-gray-500 text-sm">
          Paste a job description to see how well your CV matches and get specific improvement suggestions.
        </p>
      </div>

      {/* Input Area */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
        <label className="block text-sm font-semibold text-gray-700">
          Paste the full job description below
        </label>
        <textarea
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the entire job description here — including title, responsibilities, requirements, qualifications..."
          rows={10}
          className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y placeholder-gray-400"
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">
            {jobDescription.length} characters
          </span>
          <button
            onClick={handleAnalyze}
            disabled={loading || jobDescription.trim().length < 20}
            className="px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Analyzing...
              </span>
            ) : (
              'Analyze Match'
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          <p className="text-gray-500 text-sm">AI is analyzing the job description against your CV...</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Match Score + Assessment */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0">
                <MatchScore percentage={result.match_percentage} />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-gray-900">Match Assessment</h2>
                <p className="text-gray-600 mt-2">{result.overall_assessment}</p>
              </div>
            </div>
          </div>

          {/* Skills Comparison */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Skills Comparison</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.matched_skills?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-green-700 mb-2">
                    ✓ Matched Skills ({result.matched_skills.length})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.matched_skills.map((skill) => (
                      <SkillTag key={skill} skill={skill} type="matched" />
                    ))}
                  </div>
                </div>
              )}
              {result.missing_skills?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-red-700 mb-2">
                    ✗ Missing Skills ({result.missing_skills.length})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.missing_skills.map((skill) => (
                      <SkillTag key={skill} skill={skill} type="missing" />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Keyword Suggestions */}
          {result.keyword_suggestions?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Keywords to Add to Your CV
              </h3>
              <div className="space-y-3">
                {result.keyword_suggestions.map((kw, i) => (
                  <div key={i} className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-lg p-3">
                    <span className="text-amber-600 font-bold text-lg mt-0.5">+</span>
                    <div>
                      <p className="font-medium text-gray-900">
                        "{kw.keyword}"
                        <span className="ml-2 text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
                          {kw.where}
                        </span>
                      </p>
                      <p className="text-sm text-gray-600 mt-0.5">{kw.tip}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CV Improvement Suggestions */}
          {result.cv_improvement_suggestions?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">
                CV Improvement Suggestions
              </h3>
              <div className="space-y-4">
                {result.cv_improvement_suggestions.map((s, i) => (
                  <div key={i} className="border border-gray-200 rounded-lg p-4 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold uppercase bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                        {s.section}
                      </span>
                    </div>
                    {s.current && (
                      <div>
                        <p className="text-xs font-medium text-gray-400">Current:</p>
                        <p className="text-sm text-gray-500 line-through">{s.current}</p>
                      </div>
                    )}
                    <div>
                      <p className="text-xs font-medium text-green-600">Suggested:</p>
                      <p className="text-sm text-gray-800 font-medium">{s.suggested}</p>
                    </div>
                    <p className="text-xs text-gray-500 italic">{s.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Experience Rewrite Suggestions */}
          {result.experience_rewrite_suggestions?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Experience Rewrite Suggestions
              </h3>
              <p className="text-sm text-gray-500">
                Here's how to reword your experience to better match this job:
              </p>
              <div className="space-y-4">
                {result.experience_rewrite_suggestions.map((exp, i) => (
                  <div key={i} className="border-l-4 border-blue-400 pl-4 space-y-2">
                    <p className="font-semibold text-gray-800">{exp.original_title}</p>
                    {exp.original_description && (
                      <div className="bg-red-50 rounded p-2">
                        <p className="text-xs font-medium text-red-500 mb-1">Before:</p>
                        <p className="text-sm text-gray-600">{exp.original_description}</p>
                      </div>
                    )}
                    <div className="bg-green-50 rounded p-2">
                      <p className="text-xs font-medium text-green-600 mb-1">After:</p>
                      <p className="text-sm text-gray-800">{exp.suggested_description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ATS Tips */}
          {result.ats_tips?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-3">
              <h3 className="text-lg font-semibold text-gray-900">
                ATS Optimization Tips
              </h3>
              <ul className="space-y-2">
                {result.ats_tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="text-blue-500 mt-0.5">💡</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
