/**
 * Debug de checksum para contratos específicos - Multi-Chain
 * Verifica em várias redes: Ethereum, BSC, Polygon, Arbitrum, Base
 */
const { ethers, keccak256, getAddress } = require('ethers');

// RPCs de várias redes
const CHAINS = {
    'Ethereum': 'https://eth.llamarpc.com',
    'BSC': 'https://bsc-dataseed.binance.org/',
    'Polygon': 'https://polygon-rpc.com/',
    'Arbitrum': 'https://arb1.arbitrum.io/rpc',
    'Base': 'https://mainnet.base.org',
    'Avalanche': 'https://api.avax.network/ext/bc/C/rpc',
    'Optimism': 'https://mainnet.optimism.io',
};

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
    "0xc45a0155": "factory()",
    "0xc9c65396": "createPair(address,address)",
    "0x4e487b71": "Panic(uint256)",
};

/**
 * Extrai todos os selectors PUSH4 do bytecode
 */
function extractSelectors(bytecode) {
    const selectors = new Set();
    const code = bytecode.startsWith('0x') ? bytecode.slice(2) : bytecode;
    
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
 * Verifica se um endereço é contrato em uma rede específica
 */
async function checkContract(address, chainName, rpcUrl) {
    try {
        const provider = new ethers.JsonRpcProvider(rpcUrl);
        const addr = getAddress(address);
        
        const code = await provider.getCode(addr);
        
        if (code !== '0x' && code !== '0x0' && code.length > 2) {
            const bytecodeSize = (code.length - 2) / 2;
            const selectors = extractSelectors(code);
            const checksum = calculateChecksum(selectors);
            
            // Tentar obter info do token
            let tokenInfo = null;
            try {
                const abi = [
                    "function name() view returns (string)",
                    "function symbol() view returns (string)",
                    "function decimals() view returns (uint8)",
                ];
                const contract = new ethers.Contract(addr, abi, provider);
                const [name, symbol, decimals] = await Promise.all([
                    contract.name(),
                    contract.symbol(),
                    contract.decimals(),
                ]);
                tokenInfo = { name, symbol, decimals };
            } catch (e) {}
            
            return {
                isContract: true,
                chainName,
                address: addr,
                bytecodeSize,
                selectors,
                checksum,
                tokenInfo
            };
        }
        
        return { isContract: false, chainName };
    } catch (e) {
        return { isContract: false, chainName, error: e.message };
    }
}

/**
 * Analisa um endereço em todas as redes
 */
async function analyzeAddress(address) {
    const checksumAddr = getAddress(address);
    const isValid = address === checksumAddr;
    
    console.log(`\n${'='.repeat(70)}`);
    console.log(`ENDEREÇO: ${address}`);
    console.log('='.repeat(70));
    console.log(`Checksum EIP-55: ${checksumAddr}`);
    console.log(`Formato válido: ${isValid ? 'SIM' : 'NAO'}`);
    
    if (!isValid) {
        console.log('\nDiferenças no checksum:');
        const orig = address.slice(2);
        const check = checksumAddr.slice(2);
        for (let i = 0; i < orig.length; i++) {
            if (orig[i] !== check[i]) {
                console.log(`  Pos ${i + 2}: '${orig[i]}' -> '${check[i]}'`);
            }
        }
    }
    
    console.log('\nVerificando em múltiplas redes...');
    
    // Verificar em todas as redes em paralelo
    const promises = Object.entries(CHAINS).map(([name, rpc]) => 
        checkContract(checksumAddr, name, rpc)
    );
    
    const results = await Promise.all(promises);
    
    const contracts = results.filter(r => r.isContract);
    const notContracts = results.filter(r => !r.isContract);
    
    if (contracts.length === 0) {
        console.log('\n[!] NÃO É CONTRATO EM NENHUMA REDE');
        console.log('Redes verificadas: ' + notContracts.map(r => r.chainName).join(', '));
    } else {
        for (const c of contracts) {
            console.log(`\n[CONTRATO ENCONTRADO - ${c.chainName}]`);
            console.log(`Bytecode: ${c.bytecodeSize} bytes`);
            console.log(`Selectors: ${c.selectors.size}`);
            console.log(`Checksum: ${c.checksum}`);
            
            if (c.tokenInfo) {
                console.log(`Token: ${c.tokenInfo.name} (${c.tokenInfo.symbol})`);
                console.log(`Decimals: ${c.tokenInfo.decimals}`);
            }
            
            // Mostrar selectors conhecidos
            const known = [];
            const unknown = [];
            for (const sel of c.selectors) {
                if (KNOWN_SELECTORS[sel]) {
                    known.push([sel, KNOWN_SELECTORS[sel]]);
                } else {
                    unknown.push(sel);
                }
            }
            
            console.log(`\nFunções conhecidas (${known.length}):`);
            for (const [sel, name] of known.sort()) {
                console.log(`  ${sel} -> ${name}`);
            }
            
            if (unknown.length > 0) {
                console.log(`\nSelectors desconhecidos (${unknown.length}):`);
                for (const sel of unknown.sort().slice(0, 15)) {
                    console.log(`  ${sel}`);
                }
                if (unknown.length > 15) {
                    console.log(`  ... e mais ${unknown.length - 15}`);
                }
            }
        }
    }
    
    return contracts;
}

async function main() {
    const addresses = [
        "0x4904Ab74222459FF45908880F99507852f2714EF",
        "0x506D6c41548B6CD0F00C6610e9411468bb01609c",
        "0x4904ab74222459ff45908880f99507852f2714ef",
    ];
    
    console.log('='.repeat(70));
    console.log('DEBUG DE CHECKSUM - MULTI-CHAIN');
    console.log('='.repeat(70));
    console.log('Redes: ' + Object.keys(CHAINS).join(', '));
    
    const allContracts = [];
    
    for (const addr of addresses) {
        const contracts = await analyzeAddress(addr);
        allContracts.push(...contracts);
    }
    
    // Resumo final
    console.log(`\n${'='.repeat(70)}`);
    console.log('RESUMO FINAL');
    console.log('='.repeat(70));
    
    if (allContracts.length === 0) {
        console.log('Nenhum contrato encontrado em nenhuma rede.');
    } else {
        for (const c of allContracts) {
            console.log(`${c.chainName}: ${c.address}`);
            console.log(`  Checksum: ${c.checksum}`);
            if (c.tokenInfo) {
                console.log(`  Token: ${c.tokenInfo.symbol}`);
            }
        }
    }
}

main().catch(console.error);
