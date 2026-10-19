/**
 * Recalcula checksum usando apenas function selectors (não errors/events)
 * Igual ao sistema do usuário
 */
const { keccak256 } = require('ethers');

// Selectors de FUNÇÕES do contrato 1 (0x4904Ab74...)
// Extraídos da mensagem do usuário
const SELECTORS_CONTRACT_1 = [
    "0x06fdde03", // name()
    "0x095ea7b3", // approve(address,uint256)
    "0x16c2be6b", // isTaxExempt(address)
    "0x18160ddd", // totalSupply()
    "0x1dc61040", // setTaxExempt(address,bool)
    "0x23b872dd", // transferFrom(address,address,uint256)
    "0x313ce567", // decimals()
    "0x3852c326", // setTax(uint32)
    "0x40c10f19", // mint(address,uint256)
    "0x42966c68", // burn(uint256)
    "0x70a08231", // balanceOf(address)
    "0x715018a6", // renounceOwnership()
    "0x79ba5097", // acceptOwnership()
    "0x86a22eff", // setPair(address,bool)
    "0x8da5cb5b", // owner()
    "0x95d89b41", // symbol()
    "0x99c8d556", // tax()
    "0xa9059cbb", // transfer(address,uint256)
    "0xbd0932d0", // setTaxExemptBatch(address[],bool)
    "0xc2103825", // setPairBatch(address[],bool)
    "0xcd8de42c", // setTaxReceiver(address)
    "0xdd62ed3e", // allowance(address,address)
    "0xe30c3978", // pendingOwner()
    "0xe5e31b13", // isPair(address)
    "0xe6ef73d6", // taxReceiver()
    "0xee9a31a2", // BRIDGE()
    "0xf2fde38b", // transferOwnership(address)
];

function calculateChecksum(selectors) {
    const sortedSels = [...selectors].sort();
    const concat = sortedSels.map(s => s.slice(2)).join('');
    const hash = keccak256('0x' + concat);
    return `#${hash.slice(2, 10)}`;
}

console.log('='.repeat(60));
console.log('RECÁLCULO DE CHECKSUM - MÉTODO DO SISTEMA');
console.log('='.repeat(60));

console.log(`\nContrato 1: 0x4904Ab74222459FF45908880F99507852f2714EF`);
console.log(`Selectors: ${SELECTORS_CONTRACT_1.length}`);

const checksum1 = calculateChecksum(SELECTORS_CONTRACT_1);
console.log(`Checksum calculado: ${checksum1}`);
console.log(`Checksum esperado:  #6575e88e`);
console.log(`Match: ${checksum1 === '#6575e88e' ? 'SIM!' : 'NAO'}`);

// Mostrar os selectors ordenados
console.log('\nSelectors ordenados:');
const sorted = [...SELECTORS_CONTRACT_1].sort();
sorted.forEach(s => console.log(`  ${s}`));

// Concatenação
const concat = sorted.map(s => s.slice(2)).join('');
console.log(`\nConcatenação (primeiros 100 chars): ${concat.slice(0, 100)}...`);
console.log(`Tamanho total: ${concat.length} chars`);
