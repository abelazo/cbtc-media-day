
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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

    test('handles successful download', async () => {
        // Mock base64 content (simplified for testing)
        const base64Content = btoa('fake zip content');

        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            text: async () => base64Content
        });
        global.fetch = fetchMock;

        // Mock DOM APIs for download
        const createObjectURLMock = vi.fn().mockReturnValue('blob:mock-url');
        const revokeObjectURLMock = vi.fn();
        const originalCreateObjectURL = global.URL.createObjectURL;
        const originalRevokeObjectURL = global.URL.revokeObjectURL;
        global.URL.createObjectURL = createObjectURLMock;
        global.URL.revokeObjectURL = revokeObjectURLMock;

        const clickMock = vi.fn();
        const mockLink = document.createElement('a');
        mockLink.click = clickMock;

        const originalCreateElement = document.createElement.bind(document);
        document.createElement = vi.fn((tag) => {
            if (tag === 'a') {
                return mockLink;
            }
            return originalCreateElement(tag);
        });

        render(<DniForm />);

        fireEvent.change(screen.getByLabelText(/DNI/i), { target: { value: '123' } });
        fireEvent.change(screen.getByLabelText(/Nombre/i), { target: { value: 'User' } });
        fireEvent.click(screen.getByRole('button', { name: /Enviar/i }));

        // Wait for async operations and state updates
        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalled();
        });

        // Verify download flow
        await waitFor(() => {
            expect(document.createElement).toHaveBeenCalledWith('a');
            expect(mockLink.download).toBe('photos.zip');
            expect(clickMock).toHaveBeenCalled();
            expect(createObjectURLMock).toHaveBeenCalled();
            expect(revokeObjectURLMock).toHaveBeenCalled();
        });

        // Cleanup
        document.createElement = originalCreateElement;
        global.URL.createObjectURL = originalCreateObjectURL;
        global.URL.revokeObjectURL = originalRevokeObjectURL;
    });

    test('handles 404 error', async () => {
        const fetchMock = vi.fn().mockResolvedValue({
            ok: false,
            status: 404,
            text: async () => 'Not found'
        });
        global.fetch = fetchMock;

        render(<DniForm />);

        fireEvent.change(screen.getByLabelText(/DNI/i), { target: { value: '123' } });
        fireEvent.change(screen.getByLabelText(/Nombre/i), { target: { value: 'User' } });
        fireEvent.click(screen.getByRole('button', { name: /Enviar/i }));

        // Wait for async operations and state updates
        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalled();
            expect(screen.getByText(/No hay fotos asociadas a este jugador/i)).toBeTruthy();
        });
    });
});
