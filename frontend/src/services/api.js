import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchPatients() {
  const response = await axios.get(`${API_BASE_URL}/patients`);
  return response.data;
}

export async function submitIntake(patientId, payload) {
  const response = await axios.post(`${API_BASE_URL}/intake/${patientId}`, payload);
  return response.data;
}
