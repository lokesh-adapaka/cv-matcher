export default function SkillTag({ skill, type = 'default' }) {
  const colorMap = {
    default: 'bg-blue-100 text-blue-800',
    matched: 'bg-green-100 text-green-800',
    missing: 'bg-red-100 text-red-800',
  };

  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${colorMap[type] || colorMap.default}`}
    >
      {skill}
    </span>
  );
}
