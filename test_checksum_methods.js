/**
 * Testa diferentes métodos de cálculo de checksum
 * Para descobrir como o sistema do usuário calcula #6575e88e
 */
const { keccak256, sha256, toUtf8Bytes } = require('ethers');
const crypto = require('crypto');

// 27 selectors do contrato 1 (da mensagem do usuário)
const SELECTORS = [
    "0x06fdde03", "0x095ea7b3", "0x16c2be6b", "0x18160ddd",
    "0x1dc61040", "0x23b872dd", "0x313ce567", "0x3852c326",
    "0x40c10f19", "0x42966c68", "0x70a08231", "0x715018a6",
    "0x79ba5097", "0x86a22eff", "0x8da5cb5b", "0x95d89b41",
    "0x99c8d556", "0xa9059cbb", "0xbd0932d0", "0xc2103825",
    "0xcd8de42c", "0xdd62ed3e", "0xe30c3978", "0xe5e31b13",
    "0xe6ef73d6", "0xee9a31a2", "0xf2fde38b"
];

const TARGET = '#6575e88e';

console.log('='.repeat(60));
console.log('TESTANDO MÉTODOS DE CHECKSUM');
console.log(`Target: ${TARGET}`);
console.log(`Selectors: ${SELECTORS.length}`);
console.log('='.repeat(60));

const sorted = [...SELECTORS].sort();

// Método 1: keccak256 da concatenação hex (sem 0x)
const concat1 = sorted.map(s => s.slice(2)).join('');
const hash1 = keccak256('0x' + concat1);
console.log(`\n1. keccak256(concat sem 0x): #${hash1.slice(2, 10)}`);

// Método 2: keccak256 da concatenação hex (com 0x)
const concat2 = sorted.join('');
const hash2 = keccak256('0x' + concat2.replace(/0x/g, ''));
console.log(`2. keccak256(concat com 0x): #${hash2.slice(2, 10)}`);

// Método 3: keccak256 como UTF-8 string
const concat3 = sorted.map(s => s.slice(2)).join('');
const hash3 = keccak256(toUtf8Bytes(concat3));
console.log(`3. keccak256(UTF8 string):   #${hash3.slice(2, 10)}`);

// Método 4: SHA256
const concat4 = sorted.map(s => s.slice(2)).join('');
const hash4 = crypto.createHash('sha256').update(concat4).digest('hex');
console.log(`4. SHA256(concat):           #${hash4.slice(0, 8)}`);

// Método 5: SHA256 do array JSON
const hash5 = crypto.createHash('sha256').update(JSON.stringify(sorted)).digest('hex');
console.log(`5. SHA256(JSON array):       #${hash5.slice(0, 8)}`);

// Método 6: MD5
const hash6 = crypto.createHash('md5').update(concat4).digest('hex');
console.log(`6. MD5(concat):              #${hash6.slice(0, 8)}`);

// Método 7: keccak256 sem ordenar
const unsorted = [...SELECTORS];
const concat7 = unsorted.map(s => s.slice(2)).join('');
const hash7 = keccak256('0x' + concat7);
console.log(`7. keccak256(não ordenado):  #${hash7.slice(2, 10)}`);

// Método 8: keccak256 com bytes direto (cada selector como 4 bytes)
const bytes8 = Buffer.concat(sorted.map(s => Buffer.from(s.slice(2), 'hex')));
const hash8 = keccak256(bytes8);
console.log(`8. keccak256(bytes direto):  #${hash8.slice(2, 10)}`);

// Método 9: ethers sha256
const hash9 = sha256('0x' + concat1);
console.log(`9. ethers sha256(hex):       #${hash9.slice(2, 10)}`);

// Método 10: XOR de todos os selectors
let xor = 0n;
for (const s of SELECTORS) {
    xor ^= BigInt(s);
}
const hash10 = xor.toString(16).padStart(8, '0');
console.log(`10. XOR de todos:            #${hash10.slice(0, 8)}`);

// Método 11: Soma de todos os selectors mod 2^32
let sum = 0n;
for (const s of SELECTORS) {
    sum += BigInt(s);
}
const hash11 = (sum % (2n ** 32n)).toString(16).padStart(8, '0');
console.log(`11. Soma mod 2^32:           #${hash11}`);

// Método 12: CRC32
const crc32 = (str) => {
    let crc = 0xFFFFFFFF;
    for (let i = 0; i < str.length; i++) {
        crc ^= str.charCodeAt(i);
        for (let j = 0; j < 8; j++) {
            crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0);
        }
    }
    return ((crc ^ 0xFFFFFFFF) >>> 0).toString(16).padStart(8, '0');
};
console.log(`12. CRC32(concat):           #${crc32(concat1)}`);

// Método 13: keccak256 dos selectors como string completa com vírgulas
const concat13 = sorted.join(',');
const hash13 = keccak256(toUtf8Bytes(concat13));
console.log(`13. keccak256(com vírgulas): #${hash13.slice(2, 10)}`);

// Método 14: SHA256 de bytes hex
const bytes14 = Buffer.from(concat1, 'hex');
const hash14 = crypto.createHash('sha256').update(bytes14).digest('hex');
console.log(`14. SHA256(bytes hex):       #${hash14.slice(0, 8)}`);

console.log('\n' + '='.repeat(60));
console.log('Nenhum método bateu? O sistema pode usar lógica customizada.');
console.log('='.repeat(60));
