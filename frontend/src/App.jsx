import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import MatchResultsPage from './pages/MatchResultsPage';
import JDAnalysisPage from './pages/JDAnalysisPage';
import './index.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <Link to="/" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">CV</span>
                </div>
                <span className="text-xl font-bold text-gray-900">AI CV Matcher</span>
              </Link>
              <div className="flex space-x-4">
                <Link
                  to="/"
                  className="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Upload CV
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/matches/:cvId" element={<MatchResultsPage />} />
            <Route path="/jd-analyze/:cvId" element={<JDAnalysisPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-auto">
          <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
            AI CV Matcher &mdash; Upload your CV, find matching jobs, generate tailored resumes.
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
