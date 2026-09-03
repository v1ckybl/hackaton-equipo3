import { grafoEjemplo } from './data';
import { simularCorte, detectarCaminosCriticos } from './graph';

console.log(simularCorte(grafoEjemplo, 'camino-1'));
console.log('---');
console.log(detectarCaminosCriticos(grafoEjemplo));