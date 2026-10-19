const ethers = require('ethers');

// Config
const WS_RPC = 'ws://localhost:7788';
const PANCAKE_V2_FACTORY = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73';
const PAIR_CREATED_TOPIC = '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9';

console.log('='.repeat(50));
console.log('TESTE DE CONEXAO');
console.log('='.repeat(50));
console.log(`RPC: ${WS_RPC}`);
console.log(`Factory: ${PANCAKE_V2_FACTORY}`);
console.log('='.repeat(50) + '\n');

async function test() {
    console.log('[1] Conectando ao WebSocket...');
    const provider = new ethers.WebSocketProvider(WS_RPC);
    console.log('[1] OK - Conectado!\n');

    console.log('[2] Buscando bloco atual...');
    const block = await provider.getBlockNumber();
    console.log(`[2] OK - Bloco: ${block}\n`);

    console.log('[3] Configurando listener para PairCreated...');
    provider.on({
        address: PANCAKE_V2_FACTORY,
        topics: [PAIR_CREATED_TOPIC]
    }, (log) => {
        console.log('\n>>> PAIR CREATED DETECTADO! <<<');
        console.log(`Block: ${log.blockNumber}`);
        console.log(`TX: ${log.transactionHash}`);
        console.log(`Token0: 0x${log.topics[1].slice(26)}`);
        console.log(`Token1: 0x${log.topics[2].slice(26)}`);
        console.log(`Pair: 0x${log.data.slice(26, 66)}`);
        console.log('');
    });
    console.log('[3] OK - Listener ativo!\n');

    console.log('[4] Aguardando eventos PairCreated...');
    console.log('    (Cada novo par no PancakeSwap V2 vai aparecer aqui)\n');
    console.log('    Pressione Ctrl+C para sair.\n');
}

test().catch(err => {
    console.error('ERRO:', err.message);
    process.exit(1);
});
