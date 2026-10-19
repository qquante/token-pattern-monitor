/**
 * Calcula checksum EXATAMENTE como nos scripts Python
 * Método: keccak256 de TODOS os PUSH4 concatenados
 */
const { ethers, keccak256 } = require('ethers');

const BASE_RPC = "https://mainnet.base.org";
const provider = new ethers.JsonRpcProvider(BASE_RPC);

function extractAllSelectors(bytecode) {
    // Remove 0x prefix
    const code = bytecode.startsWith('0x') ? bytecode.slice(2) : bytecode;
    
    const selectors = new Set();
    // PUSH4 = opcode 0x63 seguido de 4 bytes (8 hex chars)
    const regex = /63([0-9a-fA-F]{8})/g;
    let match;
    
    while ((match = regex.exec(code)) !== null) {
        selectors.add('0x' + match[1].toLowerCase());
    }
    
    return selectors;
}

function calculateChecksum(selectors) {
    if (selectors.size === 0) return "#00000000";
    
    // Ordenar
    const sortedSels = Array.from(selectors).sort();
    
    // Concatenar sem 0x
    const concat = sortedSels.map(s => s.slice(2)).join('');
    
    // keccak256 da string hex
    const hash = keccak256('0x' + concat);
    
    // Primeiros 8 caracteres
    return '#' + hash.slice(2, 10);
}

async function analyzeContract(address, name) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`${name}: ${address}`);
    console.log('='.repeat(60));
    
    const bytecode = await provider.getCode(address);
    console.log(`Bytecode: ${(bytecode.length - 2) / 2} bytes`);
    
    const selectors = extractAllSelectors(bytecode);
    console.log(`Total PUSH4 selectors: ${selectors.size}`);
    
    const checksum = calculateChecksum(selectors);
    console.log(`\nCHECKSUM: ${checksum}`);
    
    console.log(`\nTodos os selectors (${selectors.size}):`);
    for (const sel of Array.from(selectors).sort()) {
        console.log(`  ${sel}`);
    }
    
    return { address, selectors, checksum };
}

async function main() {
    console.log('CÁLCULO DE CHECKSUM - MÉTODO ORIGINAL');
    console.log('(Igual ao analyze_eth.py e deep_analysis.py)');
    
    const results = [];
    
    // Contrato 1
    const r1 = await analyzeContract(
        "0x4904Ab74222459FF45908880F99507852f2714EF",
        "OPENVPP_1"
    );
    results.push(r1);
    
    // Contrato 2
    const r2 = await analyzeContract(
        "0x506D6c41548B6CD0F00C6610e9411468bb01609c",
        "OPENVPP_2"
    );
    results.push(r2);
    
    // Resumo
    console.log(`\n${'='.repeat(60)}`);
    console.log('RESUMO FINAL');
    console.log('='.repeat(60));
    console.log(`\nOPENVPP_1: ${r1.checksum} (${r1.selectors.size} selectors)`);
    console.log(`OPENVPP_2: ${r2.checksum} (${r2.selectors.size} selectors)`);
    
    // Selectors em comum
    const common = new Set([...r1.selectors].filter(x => r2.selectors.has(x)));
    const commonChecksum = calculateChecksum(common);
    console.log(`\nEm comum: ${common.size} selectors`);
    console.log(`Checksum comum: ${commonChecksum}`);
}

main().catch(console.error);
