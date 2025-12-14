
import { render, screen, fireEvent } from '@testing-library/react';
import DniForm from './DniForm';
import { describe, test, expect, vi } from 'bun:test';

describe('DniForm', () => {
    test('renders form elements', () => {
        render(<DniForm />);

        // Use getByLabelText to encourage accessibility
        expect(screen.getByLabelText(/DNI/i)).toBeTruthy();
        expect(screen.getByLabelText(/Nombre/i)).toBeTruthy();
        expect(screen.getByRole('button', { name: /Enviar/i })).toBeTruthy();
    });

    test('updates values on change', () => {
        render(<DniForm />);

        const dniInput = screen.getByLabelText(/DNI/i);
        const nombreInput = screen.getByLabelText(/Nombre/i);

        fireEvent.change(dniInput, { target: { value: '12345678A' } });
        fireEvent.change(nombreInput, { target: { value: 'ValidUser' } });

        expect(dniInput.value).toBe('12345678A');
        expect(nombreInput.value).toBe('ValidUser');
    });

    test('calls API on submit', async () => {
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({ message: 'Hello, Test!' })
        });
        global.fetch = fetchMock;

        render(<DniForm />);

        fireEvent.change(screen.getByLabelText(/DNI/i), { target: { value: '123' } });
        fireEvent.change(screen.getByLabelText(/Nombre/i), { target: { value: 'User' } });
        fireEvent.click(screen.getByRole('button', { name: /Enviar/i }));

        // We expect fetch to be called. We can't easily check args without knowing exact env var
        expect(fetchMock).toHaveBeenCalled();
    });
});
