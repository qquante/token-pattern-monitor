"""
Analisa transacoes de criacao para identificar qual DEX/protocolo foi usado.
"""
from web3 import Web3

BSC_RPC = "https://bsc-dataseed.binance.org/"
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

# Enderecos conhecidos
KNOWN_ADDRESSES = {
    "0xca143ce32fe78f1f7019d7d551a6402fc5350c73": "PancakeSwap V2 Factory",
    "0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865": "PancakeSwap V3 Factory",
    "0x10ed43c718714eb63d5aa57b78b54704e256024e": "PancakeSwap V2 Router",
    "0x13f4ea83d0bd40e75c8222255bc855a974568dd4": "PancakeSwap V3 Router",
    "0xdb1d10011ad0ff90774d0c6bb92e5c5c8b4461f7": "Uniswap V3 Factory",
    "0x46a15b0b27311cedf172ab29e4f4766fbe7f4364": "PancakeSwap V3 Position Manager",
    "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c": "WBNB",
}

# Topics conhecidos
KNOWN_TOPICS = {
    "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9": "PairCreated (V2)",
    "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118": "PoolCreated (V3)",
    "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f": "Mint (V2)",
    "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde": "Mint (V3)",
    "0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f": "IncreaseLiquidity (V3)",
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer (ERC20)",
}


def analyze_tx(tx_hash: str):
    """Analisa uma transacao em detalhes."""
    print(f"\n{'='*80}")
    print(f"TX: {tx_hash}")
    print("="*80)
    
    try:
        # Buscar dados da transacao
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        print(f"\n[TX INFO]")
        print(f"  From: {tx['from']}")
        print(f"  To: {tx['to'] or 'CONTRACT CREATION'}")
        print(f"  Value: {Web3.from_wei(tx['value'], 'ether')} BNB")
        print(f"  Block: {tx['blockNumber']}")
        print(f"  Gas Used: {receipt['gasUsed']}")
        print(f"  Status: {'SUCCESS' if receipt['status'] == 1 else 'FAILED'}")
        
        # Identificar o 'to' address
        if tx['to']:
            to_lower = tx['to'].lower()
            if to_lower in KNOWN_ADDRESSES:
                print(f"  To Identified: {KNOWN_ADDRESSES[to_lower]}")
        
        # Se criou contrato
        if receipt['contractAddress']:
            print(f"\n[CONTRACT CREATED]")
            print(f"  Address: {receipt['contractAddress']}")
        
        # Analisar logs (eventos)
        print(f"\n[LOGS] ({len(receipt['logs'])} eventos)")
        
        for i, log in enumerate(receipt['logs']):
            print(f"\n  --- Log {i} ---")
            addr = log['address'].lower()
            if addr in KNOWN_ADDRESSES:
                print(f"  Contract: {KNOWN_ADDRESSES[addr]}")
            else:
                print(f"  Contract: {log['address']}")
            
            # Identificar topic0 (tipo de evento)
            if log['topics']:
                topic0 = log['topics'][0].hex()
                if topic0 in KNOWN_TOPICS:
                    print(f"  Event: {KNOWN_TOPICS[topic0]}")
                else:
                    print(f"  Topic0: {topic0[:20]}...")
                
                # Para PairCreated, decodificar tokens
                if topic0 == "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9":
                    token0 = "0x" + log['topics'][1].hex()[26:]
                    token1 = "0x" + log['topics'][2].hex()[26:]
                    pair = "0x" + log['data'].hex()[26:66]
                    print(f"  Token0: {token0}")
                    print(f"  Token1: {token1}")
                    print(f"  Pair: {pair}")
                
                # Para PoolCreated (V3), decodificar
                if topic0 == "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118":
                    token0 = "0x" + log['topics'][1].hex()[26:]
                    token1 = "0x" + log['topics'][2].hex()[26:]
                    print(f"  Token0: {token0}")
                    print(f"  Token1: {token1}")
        
        # Identificar protocolo usado
        protocols = set()
        for log in receipt['logs']:
            addr = log['address'].lower()
            if addr in KNOWN_ADDRESSES:
                protocols.add(KNOWN_ADDRESSES[addr])
            if log['topics']:
                topic0 = log['topics'][0].hex()
                if "V2" in KNOWN_TOPICS.get(topic0, ""):
                    protocols.add("PancakeSwap V2")
                if "V3" in KNOWN_TOPICS.get(topic0, ""):
                    protocols.add("PancakeSwap V3")
        
        if protocols:
            print(f"\n[PROTOCOLO IDENTIFICADO]")
            for p in protocols:
                print(f"  >>> {p}")
        
        return protocols
        
    except Exception as e:
        print(f"Erro: {e}")
        return set()


if __name__ == "__main__":
    # Transacoes para analisar
    txs = [
        "0xd0301b41a1a3884798699b387ab71ee26ac7b5f6b688ae6fbce64b725010bdb9",
        "0x7a1e75d31076edc321c5dbe73a4b648570ab62773871b38d0d1d5c2833ea57a9",
        "0x0988052c1f477be889af837a9b628f20e3552ba86d37e42b760c641748f296fa",
        "0x8fde4af0a37298d0bcef3058e31e7430b2ed8aed667ec81a57239fac0ce0ae52",
        "0xee32606e6b832f854f8cdf1ac533e203f9a86dad955f294266ef658b7662280f",
        "0xe90072f88c191bcdc478ff3f49a99e9b53a2a1167860ed616c56cf0175b51963",
        "0xdecac59407b42198a11fabaf84c9497803950fe3ae68d1712aa81e6547e9325e",
        "0x943edffb7884ad9c8bdc252ac1413e7510755902a6e3388c5ce603662afe38f1",
        "0x74d0012cfa95526817e7446ae3d48de8ebe31b530f471a664128637054ea1167",
        "0x06c64e56e64ff96f16864699586404a45cb46757a723a584cb61e481170365a1",
        "0x2badad95d3daaf410843fc9e65983a0560e000289d690b64df5785de0bb58cb7",
        "0x7f03afeb10cebfaee6b37c6c79ac7f29a7a20fb658fe7b4a84f97acbc0fc8bd4",
    ]
    
    all_protocols = {}
    
    for tx_hash in txs:
        protocols = analyze_tx(tx_hash)
        all_protocols[tx_hash[:12]] = protocols
    
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    for tx, protocols in all_protocols.items():
        print(f"{tx}... : {protocols if protocols else 'Nao identificado'}")
