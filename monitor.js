const ethers = require('ethers');
const axios = require('axios');

// ==================== CONFIGURAÇÃO ====================
const WS_RPC = process.env.WS_RPC || "";
const WBNB_ADDRESS = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c';

// ==================== TELEGRAM CONFIG ====================
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "";
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || "";

// ==================== CHECKSUM CONFIG ====================
const TARGET_CHECKSUM = '#25171e80';

// Selectors conhecidos (28 do template alvo)
const SELECTOR_CACHE = new Set([
    '0x06fdde03', '0x095ea7b3', '0x18160ddd', '0x20800a00',
    '0x23b872dd', '0x2dc0562d', '0x313ce567', '0x4e487b71',
    '0x70a08231', '0x715018a6', '0x751039fc', '0x791ac947',
    '0x7d1db4a5', '0x8da5cb5b', '0x8f9a55c0', '0x95d89b41',
    '0xa9059cbb', '0xad5c4648', '0xbd460cdc', '0xc34c08e5',
    '0xc45a0155', '0xc9567bf9', '0xc9c65396', '0xccec3716',
    '0xd8454a82', '0xdd62ed3e', '0xf305d719', '0xffffffff'
]);

// ==================== ENDEREÇOS DOS CONTRATOS ====================
const CONTRACTS = {
    PANCAKE_V2_FACTORY: '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73',
};

// ==================== TOPICS ====================
const TOPICS = {
    PAIR_CREATED_V2: '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9',
};

// ==================== ABIs ====================
const ERC20_ABI = [
    'function name() external view returns (string)',
    'function symbol() external view returns (string)',
    'function decimals() external view returns (uint8)'
];

const TRANSFER_ABI = [
    'event Transfer(address indexed from, address indexed to, uint256 value)'
];

// ==================== CONEXÃO ====================
let provider;
let analyzedCount = 0;
let matchCount = 0;

// ==================== FUNÇÕES DE CHECKSUM ====================
function extractSelectors(bytecode) {
    if (bytecode.startsWith('0x')) {
        bytecode = bytecode.slice(2);
    }

    const selectors = new Set();
    const regex = /63([0-9a-fA-F]{8})/g;
    let match;

    while ((match = regex.exec(bytecode)) !== null) {
        const sel = '0x' + match[1].toLowerCase();
        if (SELECTOR_CACHE.has(sel)) {
            selectors.add(sel);
        }
    }

    return selectors;
}

function calculateChecksum(selectors) {
    if (selectors.size === 0) return '#00000000';

    const sortedSels = Array.from(selectors).sort();
    const concat = sortedSels.map(s => s.slice(2)).join('');
    const hash = ethers.keccak256('0x' + concat);
    return '#' + hash.slice(2, 10);
}

async function getTokenCreator(tokenAddress) {
    try {
        const currentBlock = await provider.getBlockNumber();
        const fromBlock = Math.max(0, currentBlock - 1000);

        const transferIface = new ethers.Interface(TRANSFER_ABI);
        const filter = {
            address: tokenAddress,
            topics: [
                transferIface.getEvent('Transfer').topicHash,
                '0x0000000000000000000000000000000000000000000000000000000000000000'
            ],
            fromBlock,
            toBlock: currentBlock
        };

        const logs = await provider.getLogs(filter);
        if (logs.length > 0) {
            const tx = await provider.getTransaction(logs[0].transactionHash);
            return tx.from;
        }
        return null;
    } catch (error) {
        return null;
    }
}

// ==================== ANÁLISE DE TOKEN ====================
async function analyzeToken(tokenAddress, pairAddress) {
    const startTime = Date.now();

    try {
        // Buscar bytecode
        const t1 = Date.now();
        const bytecode = await provider.getCode(tokenAddress);
        const t2 = Date.now();

        if (bytecode.length < 100) return null;

        // Extrair selectors e calcular checksum
        const selectors = extractSelectors(bytecode);
        const checksum = calculateChecksum(selectors);
        const t3 = Date.now();

        analyzedCount++;
        console.log(`[ANALYZED] ${tokenAddress.slice(0, 16)}... | ${checksum} | ${selectors.size} funcs | ${t2 - t1}ms getCode | ${t3 - t2}ms checksum`);

        if (checksum !== TARGET_CHECKSUM) {
            return null;
        }

        // MATCH! Buscar info adicional
        const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, provider);
        const [name, symbol, creator] = await Promise.all([
            tokenContract.name().catch(() => 'Unknown'),
            tokenContract.symbol().catch(() => 'UNKNOWN'),
            getTokenCreator(tokenAddress)
        ]);
        const t4 = Date.now();

        console.log(`[TIMING] Total: ${t4 - startTime}ms | getCode: ${t2 - t1}ms | checksum: ${t3 - t2}ms | info: ${t4 - t3}ms`);

        return {
            address: tokenAddress,
            pair: pairAddress,
            name,
            symbol,
            creator,
            bytecodeSize: bytecode.length / 2,
            selectorsCount: selectors.size,
            checksum,
            timestamp: new Date().toISOString()
        };
    } catch (error) {
        console.log(`[ERROR] analyzeToken: ${error.message}`);
        return null;
    }
}

// ==================== TELEGRAM ====================
async function sendTelegramMessage(info) {
    try {
        const ca = info.address;

        const message = `*[ BSC ] NEW DEPLOY - Checksum ${info.checksum}*

*${info.name} (${info.symbol})*

*CA:* \`${ca}\`

*DEV:* \`${info.creator || 'Unknown'}\`

*Pair:* \`${info.pair}\`

*Bytecode:* ${info.bytecodeSize} bytes | *Funcs:* ${info.selectorsCount}
*Time:* ${info.timestamp}`;

        const keyboard = {
            inline_keyboard: [[
                { text: 'BSCSCAN', url: `https://bscscan.com/token/${ca}` },
                { text: 'SIGMA', url: `https://t.me/SigmaTrading9_bot?start=xyodacalls-${ca}` },
                { text: 'VIP', url: `https://t.me/SigmaTradingVIP_bot?start=xyodacalls-${ca}` },
                { text: 'BASED', url: `https://t.me/based_eth_bot?start=b_${ca}` },
                { text: 'GMGN', url: `https://gmgn.ai/bsc/token/${ca}` }
            ]]
        };

        await axios.post(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
            chat_id: TELEGRAM_CHAT_ID,
            text: message,
            parse_mode: 'Markdown',
            disable_web_page_preview: true,
            reply_markup: keyboard
        }, { timeout: 10000 });

        console.log('[TELEGRAM] Mensagem enviada!');
    } catch (error) {
        console.error('[TELEGRAM] Erro:', error.message);
    }
}

// ==================== HANDLER: PAIR CREATED ====================
async function handlePairCreatedV2(log) {
    const startTime = Date.now();

    try {
        const token0 = ethers.getAddress('0x' + log.topics[1].slice(26));
        const token1 = ethers.getAddress('0x' + log.topics[2].slice(26));
        const pairAddress = ethers.getAddress('0x' + log.data.slice(26, 66));

        // Identificar novo token (não é WBNB)
        let newToken;
        if (token0.toLowerCase() === WBNB_ADDRESS.toLowerCase()) {
            newToken = token1;
        } else if (token1.toLowerCase() === WBNB_ADDRESS.toLowerCase()) {
            newToken = token0;
        } else {
            // Nenhum é WBNB, ignorar
            return;
        }

        console.log(`\n[PAIR CREATED] Block: ${log.blockNumber} | Token: ${newToken.slice(0, 16)}... | Pair: ${pairAddress.slice(0, 16)}...`);

        // Analisar token
        const info = await analyzeToken(newToken, pairAddress);

        if (info) {
            matchCount++;
            console.log('\n' + '='.repeat(60));
            console.log('!!! MATCH ENCONTRADO !!!');
            console.log(`Token: ${info.name} (${info.symbol})`);
            console.log(`CA: ${info.address}`);
            console.log(`DEV: ${info.creator}`);
            console.log(`Checksum: ${info.checksum}`);
            console.log('='.repeat(60) + '\n');

            // Enviar Telegram
            await sendTelegramMessage(info);
        }

        const totalTime = Date.now() - startTime;
        console.log(`[TIMING] handlePairCreated total: ${totalTime}ms`);

    } catch (error) {
        console.error('[ERROR] handlePairCreatedV2:', error.message);
    }
}

// ==================== SETUP ====================
function setupListeners() {
    // PancakeSwap V2 - PairCreated
    provider.on({
        address: CONTRACTS.PANCAKE_V2_FACTORY,
        topics: [TOPICS.PAIR_CREATED_V2]
    }, (log) => {
        handlePairCreatedV2(log);
    });

    console.log('[INFO] Listeners configurados!');
    console.log(`  - PancakeSwap V2 Factory: ${CONTRACTS.PANCAKE_V2_FACTORY}`);
    console.log(`  - Evento: PairCreated`);
    console.log(`  - Checksum alvo: ${TARGET_CHECKSUM}`);
    console.log(`  - Selectors no cache: ${SELECTOR_CACHE.size}\n`);
}

async function initialize() {
    console.log('='.repeat(60));
    console.log('CHECKSUM MONITOR - PancakeSwap V2');
    console.log('='.repeat(60));
    console.log(`[INFO] Conectando a: ${WS_RPC}`);

    provider = new ethers.WebSocketProvider(WS_RPC);

    console.log('[INFO] Conectado!');
    console.log('[INFO] Aguardando novos pares...\n');

    setupListeners();
}

// ==================== ERROR HANDLING ====================
process.on('unhandledRejection', (error) => {
    console.error('[ERROR] Unhandled rejection:', error);
});

process.on('SIGINT', () => {
    console.log('\n[INFO] Encerrando...');
    console.log(`[STATS] Analisados: ${analyzedCount} | Matches: ${matchCount}`);
    provider.destroy();
    process.exit(0);
});

// ==================== INICIAR ====================
initialize().catch((error) => {
    console.error('[FATAL] Falha ao inicializar:', error);
    process.exit(1);
});
