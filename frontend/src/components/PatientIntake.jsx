import { useState } from 'react';
import PropTypes from 'prop-types';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

const initialVitals = {
  temperature_c: 36.6,
  heart_rate_bpm: 72,
  systolic_bp_mm_hg: 120,
  diastolic_bp_mm_hg: 80,
};

function PatientIntake({ onSubmit, loading, error, carePlan }) {
  const [symptoms, setSymptoms] = useState('');
  const [vitals, setVitals] = useState(initialVitals);

  const handleChange = (field) => (event) => {
    setVitals((prev) => ({ ...prev, [field]: event.target.valueAsNumber || 0 }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const payload = {
      symptoms: symptoms.split(',').map((item) => item.trim()).filter(Boolean),
      vitals: {
        ...vitals,
        temperature_c: Number(vitals.temperature_c),
        heart_rate_bpm: Number(vitals.heart_rate_bpm),
        systolic_bp_mm_hg: Number(vitals.systolic_bp_mm_hg),
        diastolic_bp_mm_hg: Number(vitals.diastolic_bp_mm_hg),
      },
    };
    onSubmit(payload);
  };

  return (
    <Stack spacing={2} component="form" onSubmit={handleSubmit}>
      <Typography variant="h5">AI Guided Intake</Typography>
      <TextField
        label="Symptoms"
        placeholder="chest pain, shortness of breath"
        value={symptoms}
        onChange={(event) => setSymptoms(event.target.value)}
        helperText="Comma separated"
      />
      <Box display="grid" gridTemplateColumns="repeat(2, minmax(0, 1fr))" gap={2}>
        <TextField
          label="Temperature (°C)"
          type="number"
          value={vitals.temperature_c}
          onChange={handleChange('temperature_c')}
          inputProps={{ step: 0.1 }}
        />
        <TextField
          label="Heart Rate (bpm)"
          type="number"
          value={vitals.heart_rate_bpm}
          onChange={handleChange('heart_rate_bpm')}
        />
        <TextField
          label="Systolic BP"
          type="number"
          value={vitals.systolic_bp_mm_hg}
          onChange={handleChange('systolic_bp_mm_hg')}
        />
        <TextField
          label="Diastolic BP"
          type="number"
          value={vitals.diastolic_bp_mm_hg}
          onChange={handleChange('diastolic_bp_mm_hg')}
        />
      </Box>
      {error && <Alert severity="error">{error}</Alert>}
      <Button type="submit" variant="contained" disabled={loading}>
        {loading ? <CircularProgress size={24} /> : 'Generate Care Plan'}
      </Button>
      {carePlan && (
        <Box>
          <Typography variant="h6">Triage Level: {carePlan.triage_level}</Typography>
          <Typography variant="subtitle1" gutterBottom>
            Suggested tests: {carePlan.suggested_tests.join(', ')}
          </Typography>
          <Typography>{carePlan.summary}</Typography>
        </Box>
      )}
    </Stack>
  );
}

PatientIntake.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  loading: PropTypes.bool,
  error: PropTypes.string,
  carePlan: PropTypes.shape({
    summary: PropTypes.string.isRequired,
    suggested_tests: PropTypes.arrayOf(PropTypes.string).isRequired,
    triage_level: PropTypes.string.isRequired,
  }),
};

export default PatientIntake;
