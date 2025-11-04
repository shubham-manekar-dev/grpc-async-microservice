import { useEffect, useState } from 'react';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';

import PatientList from './components/PatientList.jsx';
import PatientIntake from './components/PatientIntake.jsx';
import { fetchPatients, submitIntake } from './services/api.js';

function App() {
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [carePlan, setCarePlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPatients().then(setPatients).catch(() => setPatients([]));
  }, []);

  const handlePatientSelect = (patientId) => {
    setSelectedPatientId(patientId);
    setCarePlan(null);
  };

  const handleIntakeSubmit = async (payload) => {
    if (!selectedPatientId) {
      setError('Please select a patient first.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const response = await submitIntake(selectedPatientId, payload);
      setCarePlan(response.care_plan);
    } catch (err) {
      setError(err.message || 'Failed to run intake.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        Healthcare AI Intake Assistant
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <PatientList
              patients={patients}
              onSelect={handlePatientSelect}
              selectedPatientId={selectedPatientId}
            />
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <PatientIntake
              onSubmit={handleIntakeSubmit}
              loading={loading}
              error={error}
              carePlan={carePlan}
            />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
