export default function MatchScore({ percentage }) {
  let color = 'text-red-600 bg-red-50 border-red-200';
  let ringColor = 'stroke-red-500';

  if (percentage >= 75) {
    color = 'text-green-600 bg-green-50 border-green-200';
    ringColor = 'stroke-green-500';
  } else if (percentage >= 50) {
    color = 'text-yellow-600 bg-yellow-50 border-yellow-200';
    ringColor = 'stroke-yellow-500';
  }

  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className={`flex flex-col items-center p-3 rounded-xl border ${color}`}>
      <svg className="w-20 h-20 -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          className={ringColor}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <span className="text-2xl font-bold -mt-14 mb-8">{Math.round(percentage)}%</span>
      <span className="text-xs font-medium">Match</span>
    </div>
  );
}
