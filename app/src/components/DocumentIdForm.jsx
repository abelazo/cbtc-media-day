
import React, { useState } from 'react';

export default function DocumentIdForm() {
    const [documentId, setDocumentId] = useState('');
    const [name, setName] = useState('');
    const [message, setMessage] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('Procesando...');

        try {
            const apiUrl = import.meta.env.VITE_API_URL || '';
            const credentials = `Basic ${btoa(`${documentId}:${name}`)}`;

            const response = await fetch(`${apiUrl}/content`, {
                headers: {
                    'Authorization': credentials
                }
            });

            if (response.ok) {
                // Response is a base64-encoded zip file
                const base64Content = await response.text();

                // Decode base64 to binary
                const binaryString = atob(base64Content);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }

                // Create blob and trigger download
                const blob = new Blob([bytes], { type: 'application/zip' });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'cbtc-media-day-2025.zip';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);

                setMessage('¡Descarga completada! Revisa tu carpeta de descargas.');
            } else if (response.status === 404) {
                setMessage('Error (' + response.status + ') : No hay fotos asociadas a este jugador');
            } else {
                setMessage('Error (' + response.status + ') :' + response.statusText);
            }
        } catch (error) {
            console.error(error);
            setMessage('No se puede verificar que exista relación entre el número de documento y el nombre proporcionado');
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="name" style={{ display: 'block', marginBottom: '0.5rem' }}>Nombre completo del jugador/a</label>
                <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    style={{ padding: '0.5rem', width: '100%' }}
                />
            </div>
            <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="documentId" style={{ display: 'block', marginBottom: '0.5rem' }}>Numero de Documento</label>
                <input
                    id="documentId"
                    type="text"
                    value={documentId}
                    onChange={(e) => setDocumentId(e.target.value)}
                    style={{ padding: '0.5rem', width: '100%' }}
                />
            </div>
            <button type="submit" style={{ padding: '0.5rem 1rem' }}>Enviar</button>
            {message && <div style={{ marginTop: '1rem' }}>{message}</div>}
        </form>
    );
}
