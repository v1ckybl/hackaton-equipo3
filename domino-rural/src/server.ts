import express from 'express';
import cors from 'cors';
import { grafoEjemplo } from './data';
import { simularCorte, detectarCaminosCriticos } from './graph';

const app = express();
const PUERTO = 3002;

app.use(cors());
app.use(express.json());

// GET /api/caminos-criticos
// Devuelve todos los caminos que, si se cortan, aíslan a alguien,
// ordenados por impacto (mayor cantidad de ganado primero).
app.get('/api/caminos-criticos', (req, res) => {
  const resultado = detectarCaminosCriticos(grafoEjemplo);
  res.json(resultado);
});

// POST /api/simular-corte
// body: { "idCamino": "camino-1" }
// Simula el corte de un camino puntual y devuelve el impacto.
app.post('/api/simular-corte', (req, res) => {
  const { idCamino } = req.body;

  if (!idCamino) {
    return res.status(400).json({ error: 'Falta el campo idCamino' });
  }

  const existe = grafoEjemplo.caminos.some((c) => c.id === idCamino);
  if (!existe) {
    return res.status(404).json({ error: `No existe el camino ${idCamino}` });
  }

  const resultado = simularCorte(grafoEjemplo, idCamino);
  res.json(resultado);
});

app.listen(PUERTO, () => {
  console.log(`Módulo Dominio Rural corriendo en http://localhost:${PUERTO}`);
});