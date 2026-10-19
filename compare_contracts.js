/**
 * Comparação detalhada dos dois contratos na Base
 */
const { ethers, keccak256, getAddress } = require('ethers');

const BASE_RPC = "https://mainnet.base.org";
const provider = new ethers.JsonRpcProvider(BASE_RPC);

// Selectors conhecidos expandidos
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
    "0x4e487b71": "Panic(uint256)",
    "0x40c10f19": "mint(address,uint256)",
    "0x42966c68": "burn(uint256)",
    "0x118cdaa7": "OwnershipTransferred(address,address)",
    "0x8c5be1e5": "Approval(address,address,uint256)",
    "0xddf252ad": "Transfer(address,address,uint256)",
};

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

function calculateChecksum(selectors) {
    if (selectors.size === 0) return "#00000000";
    
    const sortedSels = Array.from(selectors).sort();
    const concat = sortedSels.map(s => s.slice(2)).join('');
    const hash = keccak256('0x' + concat);
    return `#${hash.slice(2, 10)}`;
}

async function getContractData(address) {
    const addr = getAddress(address);
    const code = await provider.getCode(addr);
    const bytecodeSize = (code.length - 2) / 2;
    const selectors = extractSelectors(code);
    const checksum = calculateChecksum(selectors);
    
    // Info do token
    let tokenInfo = null;
    try {
        const abi = [
            "function name() view returns (string)",
            "function symbol() view returns (string)",
            "function decimals() view returns (uint8)",
            "function totalSupply() view returns (uint256)",
            "function owner() view returns (address)"
        ];
        const contract = new ethers.Contract(addr, abi, provider);
        const [name, symbol, decimals, totalSupply, owner] = await Promise.all([
            contract.name().catch(() => 'N/A'),
            contract.symbol().catch(() => 'N/A'),
            contract.decimals().catch(() => 0),
            contract.totalSupply().catch(() => 0n),
            contract.owner().catch(() => 'N/A'),
        ]);
        tokenInfo = { name, symbol, decimals, totalSupply, owner };
    } catch (e) {}
    
    return {
        address: addr,
        bytecodeSize,
        selectors,
        checksum,
        tokenInfo,
        code
    };
}

async function main() {
    const addresses = [
        "0x4904Ab74222459FF45908880F99507852f2714EF",
        "0x506D6c41548B6CD0F00C6610e9411468bb01609c"
    ];
    
    console.log('='.repeat(70));
    console.log('COMPARAÇÃO DETALHADA DOS CONTRATOS (BASE)');
    console.log('='.repeat(70));
    
    const contracts = [];
    
    for (const addr of addresses) {
        console.log(`\nCarregando ${addr.slice(0, 15)}...`);
        const data = await getContractData(addr);
        contracts.push(data);
        
        console.log(`\n${'─'.repeat(70)}`);
        console.log(`CONTRATO: ${data.address}`);
        console.log('─'.repeat(70));
        console.log(`Bytecode: ${data.bytecodeSize} bytes`);
        console.log(`Total Selectors: ${data.selectors.size}`);
        console.log(`Checksum: ${data.checksum}`);
        
        if (data.tokenInfo) {
            console.log(`\nToken Info:`);
            console.log(`  Nome: ${data.tokenInfo.name}`);
            console.log(`  Símbolo: ${data.tokenInfo.symbol}`);
            console.log(`  Decimals: ${data.tokenInfo.decimals}`);
            console.log(`  Owner: ${data.tokenInfo.owner}`);
            if (data.tokenInfo.totalSupply > 0n) {
                console.log(`  Total Supply: ${ethers.formatUnits(data.tokenInfo.totalSupply, data.tokenInfo.decimals)}`);
            }
        }
        
        // Listar TODOS os selectors
        console.log(`\nTodos os selectors (${data.selectors.size}):`);
        for (const sel of Array.from(data.selectors).sort()) {
            const name = KNOWN_SELECTORS[sel] || '???';
            console.log(`  ${sel} -> ${name}`);
        }
    }
    
    // Comparação
    console.log(`\n${'='.repeat(70)}`);
    console.log('COMPARAÇÃO');
    console.log('='.repeat(70));
    
    const [c1, c2] = contracts;
    const sels1 = c1.selectors;
    const sels2 = c2.selectors;
    
    const common = new Set([...sels1].filter(x => sels2.has(x)));
    const only1 = new Set([...sels1].filter(x => !sels2.has(x)));
    const only2 = new Set([...sels2].filter(x => !sels1.has(x)));
    
    console.log(`\nSelectors em comum: ${common.size}`);
    console.log(`Apenas em ${c1.tokenInfo?.symbol || c1.address.slice(0,10)}: ${only1.size}`);
    console.log(`Apenas em ${c2.tokenInfo?.symbol || c2.address.slice(0,10)}: ${only2.size}`);
    
    // Checksum dos selectors em comum
    const commonChecksum = calculateChecksum(common);
    console.log(`\nChecksum dos selectors em comum: ${commonChecksum}`);
    
    // Selectors em comum
    console.log(`\nSelectors em COMUM (${common.size}):`);
    for (const sel of Array.from(common).sort()) {
        const name = KNOWN_SELECTORS[sel] || '???';
        console.log(`  ${sel} -> ${name}`);
    }
    
    // Selectors únicos
    if (only1.size > 0) {
        console.log(`\nApenas em ${c1.tokenInfo?.symbol || 'Contrato 1'} (${only1.size}):`);
        for (const sel of Array.from(only1).sort()) {
            const name = KNOWN_SELECTORS[sel] || '???';
            console.log(`  ${sel} -> ${name}`);
        }
    }
    
    if (only2.size > 0) {
        console.log(`\nApenas em ${c2.tokenInfo?.symbol || 'Contrato 2'} (${only2.size}):`);
        for (const sel of Array.from(only2).sort()) {
            const name = KNOWN_SELECTORS[sel] || '???';
            console.log(`  ${sel} -> ${name}`);
        }
    }
    
    // Comparação de bytecode
    console.log(`\n${'='.repeat(70)}`);
    console.log('RESUMO FINAL');
    console.log('='.repeat(70));
    console.log(`\nContrato 1: ${c1.address}`);
    console.log(`  Token: ${c1.tokenInfo?.symbol || 'N/A'}`);
    console.log(`  Checksum: ${c1.checksum}`);
    console.log(`  Selectors: ${c1.selectors.size}`);
    
    console.log(`\nContrato 2: ${c2.address}`);
    console.log(`  Token: ${c2.tokenInfo?.symbol || 'N/A'}`);
    console.log(`  Checksum: ${c2.checksum}`);
    console.log(`  Selectors: ${c2.selectors.size}`);
    
    const similarity = (common.size / Math.max(sels1.size, sels2.size) * 100).toFixed(1);
    console.log(`\nSimilaridade: ${similarity}%`);
    console.log(`Mesmos checksums: ${c1.checksum === c2.checksum ? 'SIM' : 'NÃO'}`);
}

main().catch(console.error);
