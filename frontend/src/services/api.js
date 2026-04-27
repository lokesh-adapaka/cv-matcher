import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 min timeout for AI operations
});

export async function uploadCV(file) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/cv/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getCV(cvId) {
  const { data } = await api.get(`/cv/${cvId}`);
  return data;
}

export async function searchJobs(skills, location = 'Germany', country = 'de', page = 1, sources = ['adzuna']) {
  const { data } = await api.get('/jobs/search', {
    params: { skills: skills.join(','), location, country, page, sources: sources.join(',') },
  });
  return data;
}

export async function matchCV(cvId, location = 'Germany', country = 'de', sources = ['adzuna'], jobTitles = []) {
  const { data } = await api.post('/match', {
    cv_id: cvId,
    location,
    country,
    sources,
    job_titles: jobTitles,
  });
  return data;
}

export async function getMatchResults(cvId) {
  const { data } = await api.get(`/match/${cvId}`);
  return data;
}

export async function analyzeJobDescription(cvId, jobDescription) {
  const { data } = await api.post('/match/jd-analyze', {
    cv_id: cvId,
    job_description: jobDescription,
  });
  return data;
}

export async function generateTailoredCV(cvId, jobId) {
  const response = await api.post('/cv/generate', {
    cv_id: cvId,
    job_id: jobId,
  }, {
    responseType: 'blob',
  });
  return response.data;
}

export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}
