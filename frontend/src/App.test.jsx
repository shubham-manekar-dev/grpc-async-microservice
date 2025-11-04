import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import App from './App.jsx';
import * as api from './services/api.js';

vi.mock('./services/api.js');

describe('App', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders patients and allows selection', async () => {
    api.fetchPatients.mockResolvedValue([
      { id: 1, name: 'Test Patient', date_of_birth: '1990-01-01' },
    ]);
    api.submitIntake.mockResolvedValue({
      care_plan: {
        triage_level: 'routine',
        suggested_tests: ['CBC'],
        summary: 'Test summary',
      },
    });

    render(<App />);

    const patient = await screen.findByText('Test Patient');
    expect(patient).toBeInTheDocument();
  });
});
