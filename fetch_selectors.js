/**
 * Busca nomes das funções para cada selector usando 4byte.directory
 */
const { ethers, keccak256, getAddress } = require('ethers');
const axios = require('axios');

const BASE_RPC = "https://mainnet.base.org";
const provider = new ethers.JsonRpcProvider(BASE_RPC);

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

async function fetchFunctionName(selector) {
    try {
        // Tentar 4byte.directory
        const resp = await axios.get(`https://www.4byte.directory/api/v1/signatures/?hex_signature=${selector}`, {
            timeout: 5000
        });
        
        if (resp.data.results && resp.data.results.length > 0) {
            // Pegar a assinatura mais popular (primeira)
            return resp.data.results[0].text_signature;
        }
    } catch (e) {}
    
    try {
        // Tentar openchain
        const resp = await axios.get(`https://api.openchain.xyz/signature-database/v1/lookup?function=${selector}`, {
            timeout: 5000
        });
        
        if (resp.data.result && resp.data.result.function && resp.data.result.function[selector]) {
            return resp.data.result.function[selector][0].name;
        }
    } catch (e) {}
    
    return null;
}

async function getContractData(address) {
    const addr = getAddress(address);
    const code = await provider.getCode(addr);
    const selectors = extractSelectors(code);
    const checksum = calculateChecksum(selectors);
    
    // Info do token
    let tokenInfo = { name: 'Unknown', symbol: 'Unknown' };
    try {
        const abi = [
            "function name() view returns (string)",
            "function symbol() view returns (string)",
        ];
        const contract = new ethers.Contract(addr, abi, provider);
        tokenInfo.name = await contract.name().catch(() => 'Unknown');
        tokenInfo.symbol = await contract.symbol().catch(() => 'Unknown');
    } catch (e) {}
    
    return { address: addr, selectors, checksum, tokenInfo };
}

async function main() {
    const contracts = [
        { addr: "0x4904Ab74222459FF45908880F99507852f2714EF", name: "OPENVPP_1" },
        { addr: "0x506D6c41548B6CD0F00C6610e9411468bb01609c", name: "OPENVPP_2" }
    ];
    
    for (const { addr, name } of contracts) {
        console.log(`\n${'='.repeat(60)}`);
        console.log(`Processando ${name}: ${addr}`);
        console.log('='.repeat(60));
        
        const data = await getContractData(addr);
        
        console.log(`Checksum: ${data.checksum}`);
        console.log(`Selectors: ${data.selectors.size}`);
        console.log(`\nBuscando nomes das funções...`);
        
        const selectorMap = {};
        const sortedSels = Array.from(data.selectors).sort();
        
        for (let i = 0; i < sortedSels.length; i++) {
            const sel = sortedSels[i];
            process.stdout.write(`\r  [${i+1}/${sortedSels.length}] ${sel}`);
            
            const funcName = await fetchFunctionName(sel);
            selectorMap[sel] = funcName || `unknown_${sel.slice(2)}`;
            
            // Pequeno delay para não sobrecarregar API
            await new Promise(r => setTimeout(r, 200));
        }
        
        console.log(`\n\nResultados para ${name}:`);
        console.log(JSON.stringify(selectorMap, null, 2));
        
        // Criar JSON template
        const template = {
            name: "OPENVPP Template",
            symbol: "OPENVPP",
            checksum: data.checksum,
            reference_contract: addr,
            network: "base",
            selector_count: data.selectors.size,
            selectors: selectorMap
        };
        
        // Salvar arquivo
        const fs = require('fs');
        const filename = `openvpp_template_${name.split('_')[1]}.json`;
        fs.writeFileSync(filename, JSON.stringify(template, null, 4));
        console.log(`\nSalvo em: ${filename}`);
    }
}

main().catch(console.error);
