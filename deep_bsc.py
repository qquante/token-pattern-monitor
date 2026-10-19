"""
Deep Analysis - BSC Token
Usa 4byte.directory para identificar TODAS as funções
"""
import re
import sys
import time
import requests
from web3 import Web3

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# BSC RPC
BSC_RPC = "https://bsc-dataseed.binance.org/"
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

# Token para analisar
TOKEN = "0x67ad239f90e0b8024f4bb1022225071e0d95a50a"


def lookup_4byte(selector: str) -> list:
    """Consulta 4byte.directory para identificar função."""
    try:
        url = f"https://www.4byte.directory/api/v1/signatures/?hex_signature={selector}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data["count"] > 0:
                return [r["text_signature"] for r in data["results"]]
        return []
    except:
        return []


def extract_all_selectors(bytecode: str) -> set[str]:
    """Extrai TODOS os selectors PUSH4 do bytecode."""
    if bytecode.startswith('0x'):
        bytecode = bytecode[2:]
    
    selectors = set()
    for match in re.findall(r'63([0-9a-fA-F]{8})', bytecode):
        sel = f"0x{match.lower()}"
        selectors.add(sel)
    
    return selectors


def is_ascii_string(hex_str: str) -> bool:
    """Verifica se o hex parece ser string ASCII (falso positivo)."""
    try:
        bytes_data = bytes.fromhex(hex_str[2:])
        return all(32 <= b <= 126 for b in bytes_data)
    except:
        return False


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
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
        ]
        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
        return {
            "name": contract.functions.name().call(),
            "symbol": contract.functions.symbol().call(),
            "decimals": contract.functions.decimals().call(),
            "totalSupply": contract.functions.totalSupply().call(),
        }
    except Exception as e:
        return {"name": "Unknown", "symbol": "???", "decimals": 18, "totalSupply": 0, "error": str(e)}


def get_creation_tx(address: str) -> dict:
    """Busca transação de criação via BSCScan API."""
    try:
        url = f"https://api.bscscan.com/api?module=contract&action=getcontractcreation&contractaddresses={address}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data["status"] == "1" and data["result"]:
            return data["result"][0]
        return {}
    except:
        return {}


def analyze_token_deep(address: str) -> dict:
    """Análise profunda de um token BSC."""
    addr = Web3.to_checksum_address(address)
    
    print(f"\n{'='*80}")
    print(f"DEEP ANALYSIS BSC: {addr}")
    print("="*80)
    
    # Info básica
    info = get_token_info(address)
    print(f"Nome: {info.get('name', 'Unknown')}")
    print(f"Simbolo: {info.get('symbol', '???')}")
    print(f"Decimals: {info.get('decimals', 18)}")
    
    # Supply formatado
    supply = info.get('totalSupply', 0)
    decimals = info.get('decimals', 18)
    formatted_supply = supply / (10 ** decimals)
    print(f"Total Supply: {formatted_supply:,.0f}")
    
    # Criação
    creation = get_creation_tx(address)
    if creation:
        print(f"\nCriador: {creation.get('contractCreator')}")
        print(f"TX: {creation.get('txHash')}")
    
    # Bytecode
    bytecode = w3.eth.get_code(addr).hex()
    print(f"\nBytecode: {len(bytecode)//2} bytes")
    
    # Extrair selectors
    all_selectors = extract_all_selectors(bytecode)
    print(f"Total PUSH4: {len(all_selectors)}")
    
    # Filtrar falsos positivos (strings ASCII)
    valid_selectors = set()
    ascii_strings = set()
    for sel in all_selectors:
        if is_ascii_string(sel):
            ascii_strings.add(sel)
        else:
            valid_selectors.add(sel)
    
    print(f"Selectors validos: {len(valid_selectors)}")
    print(f"Strings ASCII (ignoradas): {len(ascii_strings)}")
    
    # Consultar 4byte para cada selector
    print(f"\nConsultando 4byte.directory...")
    identified = {}
    unidentified = set()
    
    for i, sel in enumerate(sorted(valid_selectors)):
        signatures = lookup_4byte(sel)
        if signatures:
            identified[sel] = signatures
        else:
            unidentified.add(sel)
        if i % 10 == 0 and i > 0:
            print(f"  Processados: {i}/{len(valid_selectors)}")
            time.sleep(0.1)
    
    # Mostrar resultados
    print(f"\n{'='*80}")
    print(f"FUNCOES IDENTIFICADAS ({len(identified)})")
    print("="*80)
    for sel in sorted(identified.keys()):
        sigs = identified[sel]
        # Mostrar a assinatura mais provável (última é geralmente a original)
        primary = sigs[-1] if len(sigs) > 1 else sigs[0]
        print(f"  {sel} -> {primary}")
    
    print(f"\n{'='*80}")
    print(f"SELECTORS NAO IDENTIFICADOS ({len(unidentified)})")
    print("="*80)
    for sel in sorted(unidentified):
        print(f"  {sel}")
    
    # Checksums
    checksum_all = calculate_checksum(all_selectors)
    checksum_valid = calculate_checksum(valid_selectors)
    checksum_identified = calculate_checksum(set(identified.keys()))
    
    print(f"\n{'='*80}")
    print("CHECKSUMS")
    print("="*80)
    print(f"Todos os PUSH4: {checksum_all}")
    print(f"Selectors validos: {checksum_valid}")
    print(f"Apenas identificados: {checksum_identified}")
    
    # Gerar cache de selectors para monitor
    print(f"\n{'='*80}")
    print("CACHE PARA MONITOR")
    print("="*80)
    print("const SELECTOR_CACHE = new Set([")
    for sel in sorted(identified.keys()):
        print(f"    '{sel}',")
    print("]);")
    
    return {
        "address": address,
        "name": info.get("name"),
        "symbol": info.get("symbol"),
        "creator": creation.get("contractCreator") if creation else None,
        "valid_selectors": valid_selectors,
        "identified": identified,
        "unidentified": unidentified,
        "checksum_all": checksum_all,
        "checksum_valid": checksum_valid,
        "checksum_identified": checksum_identified,
    }


if __name__ == "__main__":
    print("DEEP ANALYSIS - BSC TOKEN")
    print("Consultando 4byte.directory para identificar funcoes")
    print("="*80)
    
    result = analyze_token_deep(TOKEN)
    
    print(f"\n{'='*80}")
    print("RESUMO PARA MONITORAMENTO")
    print("="*80)
    print(f"Token: {result['name']} ({result['symbol']})")
    print(f"Address: {result['address']}")
    print(f"Creator: {result['creator']}")
    print(f"Funcoes identificadas: {len(result['identified'])}")
    print(f"\n>>> CHECKSUM PARA MONITOR: {result['checksum_identified']}")
    print(f"\nUse esse checksum no monitor.js para detectar tokens similares!")
