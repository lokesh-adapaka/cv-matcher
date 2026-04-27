import { useState, useEffect } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import JobCard from '../components/JobCard';
import { matchCV } from '../services/api';

export default function MatchResultsPage() {
  const { cvId } = useParams();
  const [searchParams] = useSearchParams();
  const jobTitles = searchParams.get('titles')?.split(',').filter(Boolean) || [];
  const [loading, setLoading] = useState(true);
  const [matchData, setMatchData] = useState(null);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('match');
  const [minScore, setMinScore] = useState(0);
  const [sources, setSources] = useState(['adzuna']);

  const availableSources = [
    { id: 'adzuna', label: 'Adzuna' },
    { id: 'linkedin', label: 'LinkedIn' },
    { id: 'stepstone', label: 'StepStone' },
  ];

  const toggleSource = (sourceId) => {
    setSources((prev) => {
      if (prev.includes(sourceId)) {
        if (prev.length === 1) return prev; // Keep at least one source
        return prev.filter((s) => s !== sourceId);
      }
      return [...prev, sourceId];
    });
  };

  useEffect(() => {
    let cancelled = false;

    async function runMatch() {
      setLoading(true);
      setError('');
      try {
        const data = await matchCV(cvId, 'Germany', 'de', sources, jobTitles);
        if (!cancelled) {
          setMatchData(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err.response?.data?.detail || 'Failed to match CV against jobs. Please try again.'
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    runMatch();
    return () => {
      cancelled = true;
    };
  }, [cvId, sources, searchParams.get('titles')]);

  const filteredMatches = (matchData?.matches || [])
    .filter((m) => m.match_percentage >= minScore)
    .sort((a, b) => {
      if (sortBy === 'match') return b.match_percentage - a.match_percentage;
      if (sortBy === 'company') return (a.company || '').localeCompare(b.company || '');
      return 0;
    });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <h2 className="text-xl font-semibold text-gray-700">Analyzing Job Matches...</h2>
        <p className="text-gray-500 text-sm max-w-md text-center">
          Our AI is comparing your skills and experience against available jobs. This may take
          30-60 seconds.
        </p>
        <div className="flex items-center space-x-2 text-sm text-gray-400">
          <svg className="animate-pulse w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <circle cx="10" cy="10" r="10" />
          </svg>
          <span>Fetching jobs from {sources.join(', ')}...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20 space-y-4">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-700">Something went wrong</h2>
        <p className="text-red-600">{error}</p>
        <Link
          to="/"
          className="inline-block mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          ← Upload Another CV
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Link to="/" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            ← Upload Another CV
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">
            Job Matches
          </h1>
          <p className="text-gray-500 text-sm">
            {matchData?.total_jobs_analyzed || 0} jobs analyzed &bull;{' '}
            {filteredMatches.length} shown
          </p>
          {jobTitles.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-1">
              <span className="text-xs text-gray-400">Filtering by:</span>
              {jobTitles.map((t) => (
                <span key={t} className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full border border-blue-200 font-medium">
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="text-xs font-medium text-gray-500 block mb-1">Sources</label>
            <div className="flex gap-1">
              {availableSources.map((src) => (
                <button
                  key={src.id}
                  onClick={() => toggleSource(src.id)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                    sources.includes(src.id)
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:border-gray-400'
                  }`}
                >
                  {src.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 block mb-1">Min Score</label>
            <select
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white"
            >
              <option value={0}>All</option>
              <option value={25}>25%+</option>
              <option value={50}>50%+</option>
              <option value={75}>75%+</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 block mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white"
            >
              <option value="match">Match %</option>
              <option value="company">Company</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results */}
      {filteredMatches.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 text-lg">No matching jobs found.</p>
          <p className="text-gray-400 text-sm mt-1">
            Try uploading a different CV or adjusting the minimum score filter.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredMatches.map((match) => (
            <JobCard key={match.job_id} match={match} cvId={cvId} />
          ))}
        </div>
      )}
    </div>
  );
}
