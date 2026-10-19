"""
Analisa tokens ETHEREUM - extrai TODOS os selectors e compara padrões
SEM cache - análise limpa
"""
import re
import sys
import requests
from web3 import Web3

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ETHEREUM RPC
ETH_RPC = "https://eth.llamarpc.com"
w3 = Web3(Web3.HTTPProvider(ETH_RPC))

# Tokens para analisar
TOKENS = [
    "0x98530b4eeab7487219020134ebed4851e780151d",
    "0xd80a36ab1bd56182392b5a5e485eab8ea683837a",
]

# Selectors conhecidos (função -> nome)
KNOWN_SELECTORS = {
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
    "0x791ac947": "swapExactTokensForETHSupportingFeeOnTransferTokens",
    "0xad5c4648": "WETH()",
    "0xf305d719": "addLiquidityETH",
    "0x751039fc": "removeLimits()",
    "0xc9567bf9": "openTrading()",
    "0xa457c2d7": "decreaseAllowance(address,uint256)",
    "0x39509351": "increaseAllowance(address,uint256)",
    "0x49bd5a5e": "uniswapV2Pair()",
    "0x1694505e": "uniswapV2Router()",
    "0xc0246668": "excludeFromFees(address,bool)",
    "0x4fbee193": "isExcludedFromFee(address)",
}


def extract_all_selectors(bytecode: str) -> set[str]:
    """Extrai TODOS os selectors PUSH4 do bytecode."""
    if bytecode.startswith('0x'):
        bytecode = bytecode[2:]
    
    selectors = set()
    # PUSH4 = 0x63
    for match in re.findall(r'63([0-9a-fA-F]{8})', bytecode):
        sel = f"0x{match.lower()}"
        # Filtrar selectors que parecem válidos (não são strings ASCII)
        # Selectors válidos geralmente não começam com 0x3 (exceto alguns)
        selectors.add(sel)
    
    return selectors


def calculate_checksum(selectors: set[str]) -> str:
    """Calcula checksum de um conjunto de selectors."""
    if not selectors:
        return "#00000000"
    sorted_sels = sorted(list(selectors))
    concat = "".join([s[2:] for s in sorted_sels])
    hash_bytes = Web3.keccak(hexstr=concat)
    return f"#{hash_bytes.hex()[:8]}"


def get_token_info(address: str) -> dict:
    """Busca nome e símbolo do token."""
    try:
        abi = [
            {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
        ]
        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        return {"name": name, "symbol": symbol}
    except:
        return {"name": "Unknown", "symbol": "???"}


def get_creation_tx(address: str) -> dict:
    """Busca transação de criação via Etherscan API."""
    try:
        url = f"https://api.etherscan.io/api?module=contract&action=getcontractcreation&contractaddresses={address}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data["status"] == "1" and data["result"]:
            return data["result"][0]
        return None
    except:
        return None


def analyze_token(address: str) -> dict:
    """Análise completa de um token."""
    addr = Web3.to_checksum_address(address)
    
    print(f"\n{'='*70}")
    print(f"ANALISANDO: {addr}")
    print("="*70)
    
    # Info básica
    info = get_token_info(address)
    print(f"Nome: {info['name']}")
    print(f"Símbolo: {info['symbol']}")
    
    # Bytecode
    bytecode = w3.eth.get_code(addr).hex()
    print(f"Bytecode: {len(bytecode)//2} bytes")
    
    # Extrair TODOS os selectors
    all_selectors = extract_all_selectors(bytecode)
    print(f"Total selectors PUSH4: {len(all_selectors)}")
    
    # Checksum de TODOS os selectors
    checksum_all = calculate_checksum(all_selectors)
    print(f"Checksum (todos): {checksum_all}")
    
    # Identificar selectors conhecidos
    known = {}
    unknown = set()
    for sel in all_selectors:
        if sel in KNOWN_SELECTORS:
            known[sel] = KNOWN_SELECTORS[sel]
        else:
            unknown.add(sel)
    
    print(f"\nSelectors conhecidos ({len(known)}):")
    for sel, name in sorted(known.items()):
        print(f"  {sel} -> {name}")
    
    print(f"\nSelectors desconhecidos ({len(unknown)}):")
    for sel in sorted(unknown):
        print(f"  {sel}")
    
    # Transação de criação
    creation = get_creation_tx(address)
    if creation:
        print(f"\nCriador: {creation.get('contractCreator', 'Unknown')}")
        print(f"TX: {creation.get('txHash', 'Unknown')}")
    
    return {
        "address": address,
        "name": info["name"],
        "symbol": info["symbol"],
        "bytecode_size": len(bytecode)//2,
        "all_selectors": all_selectors,
        "known_selectors": known,
        "unknown_selectors": unknown,
        "checksum_all": checksum_all,
        "creator": creation.get("contractCreator") if creation else None,
    }


def compare_tokens(results: list):
    """Compara os tokens para encontrar padrões em comum."""
    print("\n" + "="*70)
    print("COMPARAÇÃO DOS TOKENS")
    print("="*70)
    
    # Selectors em comum
    common = results[0]["all_selectors"] & results[1]["all_selectors"]
    print(f"\nSelectors em COMUM ({len(common)}):")
    for sel in sorted(common):
        name = KNOWN_SELECTORS.get(sel, "???")
        print(f"  {sel} -> {name}")
    
    # Calcular checksum dos selectors em comum
    checksum_common = calculate_checksum(common)
    print(f"\nChecksum dos selectors em comum: {checksum_common}")
    
    # Selectors únicos de cada um
    only_1 = results[0]["all_selectors"] - results[1]["all_selectors"]
    only_2 = results[1]["all_selectors"] - results[0]["all_selectors"]
    
    print(f"\nApenas em {results[0]['symbol']} ({len(only_1)}):")
    for sel in sorted(only_1)[:10]:
        name = KNOWN_SELECTORS.get(sel, "???")
        print(f"  {sel} -> {name}")
    if len(only_1) > 10:
        print(f"  ... e mais {len(only_1)-10}")
    
    print(f"\nApenas em {results[1]['symbol']} ({len(only_2)}):")
    for sel in sorted(only_2)[:10]:
        name = KNOWN_SELECTORS.get(sel, "???")
        print(f"  {sel} -> {name}")
    if len(only_2) > 10:
        print(f"  ... e mais {len(only_2)-10}")
    
    return common, checksum_common


if __name__ == "__main__":
    print("ANÁLISE DE TOKENS ETHEREUM")
    print("Sem relação com tokens BSC anteriores")
    print("="*70)
    
    results = []
    for token in TOKENS:
        result = analyze_token(token)
        results.append(result)
    
    if len(results) == 2:
        common, checksum = compare_tokens(results)
        
        print("\n" + "="*70)
        print("RESUMO")
        print("="*70)
        print(f"Token 1: {results[0]['symbol']} | Checksum: {results[0]['checksum_all']}")
        print(f"Token 2: {results[1]['symbol']} | Checksum: {results[1]['checksum_all']}")
        print(f"Selectors em comum: {len(common)}")
        print(f"Checksum comum: {checksum}")
