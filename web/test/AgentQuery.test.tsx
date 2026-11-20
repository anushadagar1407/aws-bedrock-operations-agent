import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import React from 'react';
import { AgentQuery } from '../components/AgentQuery';

test('renders the operations query form', () => {
  render(<AgentQuery />);
  expect(screen.getByRole('textbox', { name: /container question/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /check status/i })).toBeInTheDocument();
});
