/**
 * Testa checksum baseado no bytecode
 */
const { ethers, keccak256, sha256 } = require('ethers');
const crypto = require('crypto');

const BASE_RPC = "https://mainnet.base.org";
const provider = new ethers.JsonRpcProvider(BASE_RPC);

const TARGET_CHECKSUM = '#6575e88e';
const TARGET_BYTECODE_HASH = '#0xca7eeaa123d43b46';
const TARGET_FUNCTIONS_HASH = '#0x020c149cbc647d1b';

async function main() {
    const address = "0x4904Ab74222459FF45908880F99507852f2714EF";
    
    console.log('='.repeat(60));
    console.log('TESTANDO CHECKSUM BASEADO NO BYTECODE');
    console.log(`Contrato: ${address}`);
    console.log('='.repeat(60));
    console.log(`\nTargets:`);
    console.log(`  Checksum:  ${TARGET_CHECKSUM}`);
    console.log(`  Bytecode:  ${TARGET_BYTECODE_HASH}`);
    console.log(`  Functions: ${TARGET_FUNCTIONS_HASH}`);
    
    const bytecode = await provider.getCode(address);
    console.log(`\nBytecode: ${bytecode.length} chars (${(bytecode.length-2)/2} bytes)`);
    
    // Método 1: keccak256 do bytecode completo
    const hash1 = keccak256(bytecode);
    console.log(`\n1. keccak256(bytecode): ${hash1.slice(0, 18)}`);
    console.log(`   Match bytecode hash: ${hash1.slice(0, 18) === TARGET_BYTECODE_HASH.slice(1) ? 'SIM!' : 'NAO'}`);
    
    // Método 2: primeiros 8 chars do keccak256
    console.log(`2. keccak256[2:10]:     #${hash1.slice(2, 10)}`);
    console.log(`   Match checksum:      ${`#${hash1.slice(2, 10)}` === TARGET_CHECKSUM ? 'SIM!' : 'NAO'}`);
    
    // Método 3: SHA256 do bytecode
    const hash3 = crypto.createHash('sha256').update(bytecode).digest('hex');
    console.log(`3. SHA256(bytecode):    #${hash3.slice(0, 8)}`);
    
    // Método 4: xxhash style (primeiros 16 chars do keccak)
    console.log(`4. keccak64:            #0x${hash1.slice(2, 18)}`);
    console.log(`   Match bytecode hash: ${`#0x${hash1.slice(2, 18)}` === TARGET_BYTECODE_HASH ? 'SIM!' : 'NAO'}`);
    
    // Método 5: Bytecode sem constructor (runtime code)
    // O runtime code começa após o constructor
    const runtimeStart = bytecode.indexOf('6080604052');
    if (runtimeStart > 2) {
        const runtimeCode = '0x' + bytecode.slice(runtimeStart);
        const hash5 = keccak256(runtimeCode);
        console.log(`5. keccak256(runtime):  #${hash5.slice(2, 10)}`);
    }
    
    // Método 6: Hash do deployed bytecode (sem 0x)
    const hash6 = keccak256('0x' + bytecode.slice(2));
    console.log(`6. keccak256(no 0x):    #${hash6.slice(2, 10)}`);
    
    // Método 7: Tentar diferentes offsets do hash
    console.log(`\n7. Tentando diferentes offsets do keccak256:`);
    for (let i = 0; i < 24; i += 2) {
        const slice = hash1.slice(2 + i, 10 + i);
        if (slice === TARGET_CHECKSUM.slice(1)) {
            console.log(`   MATCH! offset ${i}: #${slice}`);
        }
    }
    
    // Método 8: Combinação de hashes
    const funcHash = '#0x020c149cbc647d1b';
    const bytecodeHash = hash1;
    
    // XOR dos primeiros 4 bytes de cada
    const xor8 = (parseInt(bytecodeHash.slice(2, 10), 16) ^ parseInt(funcHash.slice(3, 11), 16)).toString(16).padStart(8, '0');
    console.log(`\n8. XOR(bytecode, func): #${xor8}`);
    
    // Método 9: Adicionar os hashes
    const sum9 = ((BigInt('0x' + bytecodeHash.slice(2, 10)) + BigInt('0x' + funcHash.slice(3, 11))) % (2n ** 32n)).toString(16).padStart(8, '0');
    console.log(`9. SUM(bytecode, func): #${sum9}`);
    
    // Método 10: Hash do code hash (duplo hash)
    const hash10 = keccak256(hash1);
    console.log(`10. keccak256(keccak):  #${hash10.slice(2, 10)}`);
    
    // Extrair selectors para testar outras combinações
    const selectors = [];
    const regex = /63([0-9a-fA-F]{8})/g;
    let match;
    const codeWithout0x = bytecode.slice(2);
    while ((match = regex.exec(codeWithout0x)) !== null) {
        selectors.push('0x' + match[1].toLowerCase());
    }
    
    // Apenas selectors únicos, ordenados
    const uniqueSelectors = [...new Set(selectors)].sort();
    console.log(`\nSelectors encontrados: ${uniqueSelectors.length}`);
    
    // Método 11: keccak256 de TODOS os selectors (não só funções)
    const concat11 = uniqueSelectors.map(s => s.slice(2)).join('');
    const hash11 = keccak256('0x' + concat11);
    console.log(`11. keccak256(ALL sels): #${hash11.slice(2, 10)}`);
    
    // Método 12: SHA256 de todos os selectors
    const hash12 = crypto.createHash('sha256').update(concat11).digest('hex');
    console.log(`12. SHA256(ALL sels):    #${hash12.slice(0, 8)}`);
    
    console.log('\n' + '='.repeat(60));
}

main().catch(console.error);
