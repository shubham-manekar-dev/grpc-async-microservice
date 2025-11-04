import PropTypes from 'prop-types';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';

function PatientList({ patients, selectedPatientId, onSelect }) {
  if (patients.length === 0) {
    return <Typography>No patients available.</Typography>;
  }

  return (
    <List>
      {patients.map((patient) => (
        <ListItem key={patient.id} disablePadding>
          <ListItemButton
            selected={patient.id === selectedPatientId}
            onClick={() => onSelect(patient.id)}
            data-testid={`patient-${patient.id}`}
          >
            <ListItemText primary={patient.name} secondary={patient.date_of_birth} />
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  );
}

PatientList.propTypes = {
  patients: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
      date_of_birth: PropTypes.string.isRequired,
    })
  ).isRequired,
  selectedPatientId: PropTypes.number,
  onSelect: PropTypes.func.isRequired,
};

export default PatientList;
