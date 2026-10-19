/**
 * Debug de checksum para contratos específicos - BSC
 * Analisa endereços e verifica formato EIP-55
 */
const { ethers, keccak256, getAddress } = require('ethers');

// BSC RPC
const BSC_RPC = "https://bsc-dataseed.binance.org/";
const provider = new ethers.JsonRpcProvider(BSC_RPC);

// Selectors conhecidos
const KNOWN_SELECTORS = {
    "0x06fdde03": "name()",
    "0x095ea7b3": "approve(address,uint256)",
    "0x18160ddd": "totalSupply()",
    "0x23b872dd": "transferFrom(address,address,uint256)",
    "0x313ce567": "decimals()",
    "0x70a08231": "balanceOf(address)",
    "0x715018a6": "renounceOwnership()",
    "0x8da5cb5b": "owner()",
    "0x95d89b41": "symbol()",
    "0xa9059cbb": "transfer(address,uint256)",
    "0xdd62ed3e": "allowance(address,address)",
    "0xf2fde38b": "transferOwnership(address)",
    "0x791ac947": "swapExactTokensForETHSupportingFeeOnTransferTokens",
    "0xad5c4648": "WETH()",
    "0xf305d719": "addLiquidityETH",
    "0x751039fc": "removeLimits()",
    "0xc9567bf9": "openTrading()",
    "0x49bd5a5e": "uniswapV2Pair()",
    "0x1694505e": "uniswapV2Router()",
    "0x20800a00": "???",
    "0x2dc0562d": "???",
    "0x7d1db4a5": "???",
    "0x8f9a55c0": "???",
    "0xbd460cdc": "???",
    "0xc34c08e5": "???",
    "0xc45a0155": "factory()",
    "0xc9c65396": "createPair(address,address)",
    "0xccec3716": "???",
    "0xd8454a82": "???",
    "0x4e487b71": "Panic(uint256)",
};

/**
 * Analisa o checksum EIP-55 de um endereço
 */
function analyzeAddressChecksum(address) {
    console.log(`\n${'='.repeat(70)}`);
    console.log(`ENDEREÇO ORIGINAL: ${address}`);
    console.log('='.repeat(70));
    
    try {
        const checksumAddr = getAddress(address);
        const isValid = address === checksumAddr;
        
        console.log(`Checksum EIP-55:   ${checksumAddr}`);
        console.log(`Formato válido:    ${isValid ? 'SIM' : 'NAO'}`);
        
        if (!isValid) {
            console.log('\n[!] DIFERENÇAS DETECTADAS:');
            const orig = address.slice(2);
            const check = checksumAddr.slice(2);
            for (let i = 0; i < orig.length; i++) {
                if (orig[i] !== check[i]) {
                    console.log(`    Posição ${i + 2}: '${orig[i]}' -> '${check[i]}'`);
                }
            }
        }
        
        return checksumAddr;
    } catch (e) {
        console.log(`ERRO: ${e.message}`);
        return null;
    }
}

/**
 * Extrai todos os selectors PUSH4 do bytecode
 */
function extractSelectors(bytecode) {
    const selectors = new Set();
    const code = bytecode.startsWith('0x') ? bytecode.slice(2) : bytecode;
    
    // PUSH4 = 0x63
    const regex = /63([0-9a-fA-F]{8})/g;
    let match;
    while ((match = regex.exec(code)) !== null) {
        selectors.add(`0x${match[1].toLowerCase()}`);
    }
    
    return selectors;
}

/**
 * Calcula checksum de um conjunto de selectors
 */
function calculateChecksum(selectors) {
    if (selectors.size === 0) return "#00000000";
    
    const sortedSels = Array.from(selectors).sort();
    const concat = sortedSels.map(s => s.slice(2)).join('');
    const hash = keccak256('0x' + concat);
    return `#${hash.slice(2, 10)}`;
}

/**
 * Analisa o bytecode e selectors de um contrato
 */
async function analyzeContract(address) {
    try {
        const addr = getAddress(address);
        
        // Buscar bytecode
        const code = await provider.getCode(addr);
        
        if (code === '0x' || code === '0x0') {
            console.log(`\n[!] ENDEREÇO NÃO É UM CONTRATO (EOA ou vazio)`);
            const balance = await provider.getBalance(addr);
            console.log(`    Balance: ${ethers.formatEther(balance)} BNB`);
            return null;
        }
        
        console.log(`\n[CONTRATO DETECTADO NA BSC]`);
        console.log(`Bytecode size: ${(code.length - 2) / 2} bytes`);
        
        // Extrair selectors
        const allSels = extractSelectors(code);
        console.log(`Total selectors PUSH4: ${allSels.size}`);
        
        // Calcular checksum dos selectors
        const selectorChecksum = calculateChecksum(allSels);
        console.log(`Checksum selectors: ${selectorChecksum}`);
        
        // Identificar funções conhecidas
        const known = [];
        const unknown = [];
        for (const sel of Array.from(allSels).sort()) {
            if (KNOWN_SELECTORS[sel]) {
                known.push([sel, KNOWN_SELECTORS[sel]]);
            } else {
                unknown.push(sel);
            }
        }
        
        console.log(`\nFunções conhecidas (${known.length}):`);
        for (const [sel, name] of known) {
            console.log(`  ${sel} -> ${name}`);
        }
        
        if (unknown.length > 0) {
            console.log(`\nSelectors desconhecidos (${unknown.length}):`);
            for (const sel of unknown.slice(0, 20)) {
                console.log(`  ${sel}`);
            }
            if (unknown.length > 20) {
                console.log(`  ... e mais ${unknown.length - 20}`);
            }
        }
        
        // Tentar obter nome/símbolo do token
        try {
            const abi = [
                "function name() view returns (string)",
                "function symbol() view returns (string)",
                "function decimals() view returns (uint8)",
                "function totalSupply() view returns (uint256)"
            ];
            const contract = new ethers.Contract(addr, abi, provider);
            const [name, symbol, decimals, totalSupply] = await Promise.all([
                contract.name(),
                contract.symbol(),
                contract.decimals(),
                contract.totalSupply()
            ]);
            console.log(`\nToken Info:`);
            console.log(`  Nome: ${name}`);
            console.log(`  Símbolo: ${symbol}`);
            console.log(`  Decimals: ${decimals}`);
            console.log(`  Total Supply: ${ethers.formatUnits(totalSupply, decimals)}`);
        } catch (e) {
            // Não é um token ERC20 ou não tem essas funções
        }
        
        return {
            address: addr,
            bytecodeSize: (code.length - 2) / 2,
            selectors: allSels,
            checksum: selectorChecksum
        };
        
    } catch (e) {
        console.log(`\nERRO ao analisar contrato: ${e.message}`);
        return null;
    }
}

async function main() {
    // Endereços para debugar
    const addresses = [
        "0x4904Ab74222459FF45908880F99507852f2714EF",
        "0x506D6c41548B6CD0F00C6610e9411468bb01609c",
        "0x4904ab74222459ff45908880f99507852f2714ef",
    ];
    
    console.log('='.repeat(70));
    console.log('DEBUG DE CHECKSUM - ANÁLISE DE CONTRATOS (BSC)');
    console.log('='.repeat(70));
    
    const results = [];
    
    for (const addr of addresses) {
        // Análise do checksum EIP-55
        const checksumAddr = analyzeAddressChecksum(addr);
        
        if (checksumAddr) {
            // Análise do contrato
            const result = await analyzeContract(checksumAddr);
            if (result) {
                results.push(result);
            }
        }
    }
    
    // Comparação se houver múltiplos contratos
    if (results.length >= 2) {
        console.log(`\n${'='.repeat(70)}`);
        console.log('COMPARAÇÃO DE CHECKSUMS DOS CONTRATOS');
        console.log('='.repeat(70));
        
        const uniqueContracts = new Map();
        for (const r of results) {
            uniqueContracts.set(r.address, r);
        }
        
        for (const [addr, data] of uniqueContracts) {
            console.log(`\n${addr}`);
            console.log(`  Checksum selectors: ${data.checksum}`);
            console.log(`  Total selectors: ${data.selectors.size}`);
        }
        
        // Se houver 2+ contratos únicos, mostrar diferenças
        if (uniqueContracts.size >= 2) {
            const addrs = Array.from(uniqueContracts.keys());
            const sels1 = uniqueContracts.get(addrs[0]).selectors;
            const sels2 = uniqueContracts.get(addrs[1]).selectors;
            
            const common = new Set([...sels1].filter(x => sels2.has(x)));
            const only1 = new Set([...sels1].filter(x => !sels2.has(x)));
            const only2 = new Set([...sels2].filter(x => !sels1.has(x)));
            
            console.log(`\nSelectors em comum: ${common.size}`);
            console.log(`Apenas em ${addrs[0].slice(0, 10)}...: ${only1.size}`);
            console.log(`Apenas em ${addrs[1].slice(0, 10)}...: ${only2.size}`);
            
            if (only1.size > 0) {
                console.log(`\nSelectors únicos de ${addrs[0].slice(0, 10)}...:`);
                for (const sel of Array.from(only1).sort().slice(0, 10)) {
                    console.log(`  ${sel}`);
                }
            }
            
            if (only2.size > 0) {
                console.log(`\nSelectors únicos de ${addrs[1].slice(0, 10)}...:`);
                for (const sel of Array.from(only2).sort().slice(0, 10)) {
                    console.log(`  ${sel}`);
                }
            }
        }
    }
    
    // Resumo final
    console.log(`\n${'='.repeat(70)}`);
    console.log('RESUMO');
    console.log('='.repeat(70));
    for (const r of results) {
        console.log(`${r.address}: ${r.checksum}`);
    }
}

main().catch(console.error);
