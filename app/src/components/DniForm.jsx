
import React, { useState } from 'react';

export default function DniForm() {
    const [dni, setDni] = useState('');
    const [nombre, setNombre] = useState('');
    const [message, setMessage] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('Procesando...');

        try {
            const apiUrl = import.meta.env.VITE_API_URL || '';
            const credentials = `Basic ${btoa(`${dni}:${nombre}`)}`;

            const response = await fetch(`${apiUrl}/content`, {
                headers: {
                    'Authorization': credentials
                }
            });

            if (response.ok) {
                const data = await response.json();
                setMessage(data.message || 'OK');
            } else if (response.status === 404) {
                setMessage('Error (' + response.status + ') : No hay fotos asociadas a este jugador');
            } else {
                setMessage('Error (' + response.status + ') :' + response.statusText);
            }
        } catch (error) {
            console.error(error);
            setMessage('Error de red');
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="nombre" style={{ display: 'block', marginBottom: '0.5rem' }}>Nombre</label>
                <input
                    id="nombre"
                    type="text"
                    value={nombre}
                    onChange={(e) => setNombre(e.target.value)}
                    style={{ padding: '0.5rem', width: '100%' }}
                />
            </div>
            <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="dni" style={{ display: 'block', marginBottom: '0.5rem' }}>DNI</label>
                <input
                    id="dni"
                    type="text"
                    value={dni}
                    onChange={(e) => setDni(e.target.value)}
                    style={{ padding: '0.5rem', width: '100%' }}
                />
            </div>
            <button type="submit" style={{ padding: '0.5rem 1rem' }}>Enviar</button>
            {message && <div style={{ marginTop: '1rem' }}>{message}</div>}
        </form>
    );
}
