"""
Deep Analysis - Ethereum Tokens
Usa 4byte.directory para identificar TODOS os selectors
"""
import re
import sys
import time
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
        # Se todos os bytes são printáveis ASCII, provavelmente é string
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


def get_creation_info(address: str) -> dict:
    """Busca info de criação via Etherscan."""
    try:
        url = f"https://api.etherscan.io/api?module=contract&action=getcontractcreation&contractaddresses={address}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data["status"] == "1" and data["result"]:
            return data["result"][0]
        return {}
    except:
        return {}


def analyze_token_deep(address: str) -> dict:
    """Análise profunda de um token."""
    addr = Web3.to_checksum_address(address)
    
    print(f"\n{'='*80}")
    print(f"DEEP ANALYSIS: {addr}")
    print("="*80)
    
    # Bytecode
    bytecode = w3.eth.get_code(addr).hex()
    print(f"Bytecode: {len(bytecode)//2} bytes")
    
    # Info básica
    try:
        abi = [
            {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
        ]
        contract = w3.eth.contract(address=addr, abi=abi)
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        print(f"Nome: {name}")
        print(f"Simbolo: {symbol}")
    except:
        name = "Unknown"
        symbol = "???"
    
    # Criação
    creation = get_creation_info(address)
    if creation:
        print(f"Criador: {creation.get('contractCreator')}")
        print(f"TX: {creation.get('txHash')}")
    
    # Extrair selectors
    all_selectors = extract_all_selectors(bytecode)
    print(f"\nTotal PUSH4: {len(all_selectors)}")
    
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
        # Rate limit
        if i % 10 == 0 and i > 0:
            print(f"  Processados: {i}/{len(valid_selectors)}")
            time.sleep(0.1)
    
    # Mostrar resultados
    print(f"\n{'='*80}")
    print(f"FUNCOES IDENTIFICADAS ({len(identified)})")
    print("="*80)
    for sel in sorted(identified.keys()):
        sigs = identified[sel]
        print(f"  {sel} -> {sigs[0]}")
        if len(sigs) > 1:
            for s in sigs[1:3]:
                print(f"           -> {s}")
    
    print(f"\n{'='*80}")
    print(f"SELECTORS NAO IDENTIFICADOS ({len(unidentified)})")
    print("="*80)
    for sel in sorted(unidentified):
        print(f"  {sel}")
    
    # Calcular checksum apenas dos identificados
    checksum_valid = calculate_checksum(valid_selectors)
    checksum_identified = calculate_checksum(set(identified.keys()))
    
    print(f"\n{'='*80}")
    print("CHECKSUMS")
    print("="*80)
    print(f"Todos os selectors validos: {checksum_valid}")
    print(f"Apenas identificados: {checksum_identified}")
    
    return {
        "address": address,
        "name": name,
        "symbol": symbol,
        "valid_selectors": valid_selectors,
        "identified": identified,
        "unidentified": unidentified,
        "checksum_valid": checksum_valid,
        "checksum_identified": checksum_identified,
    }


def compare_deep(results: list):
    """Compara tokens em profundidade."""
    print(f"\n{'='*80}")
    print("COMPARACAO DEEP")
    print("="*80)
    
    # Selectors validos em comum
    common_valid = results[0]["valid_selectors"] & results[1]["valid_selectors"]
    print(f"\nSelectors validos em COMUM: {len(common_valid)}")
    
    # Funções identificadas em comum
    common_funcs = set(results[0]["identified"].keys()) & set(results[1]["identified"].keys())
    print(f"Funcoes identificadas em COMUM: {len(common_funcs)}")
    
    for sel in sorted(common_funcs):
        sig = results[0]["identified"][sel][0]
        print(f"  {sel} -> {sig}")
    
    # Checksum comum
    checksum_common = calculate_checksum(common_valid)
    checksum_funcs = calculate_checksum(common_funcs)
    
    print(f"\nChecksum selectors comuns: {checksum_common}")
    print(f"Checksum funcoes comuns: {checksum_funcs}")
    
    return common_valid, common_funcs, checksum_funcs


if __name__ == "__main__":
    print("DEEP ANALYSIS - ETHEREUM TOKENS")
    print("Consultando 4byte.directory para identificar funcoes")
    print("="*80)
    
    results = []
    for token in TOKENS:
        result = analyze_token_deep(token)
        results.append(result)
    
    if len(results) == 2:
        common, funcs, checksum = compare_deep(results)
        
        print(f"\n{'='*80}")
        print("RESUMO FINAL")
        print("="*80)
        print(f"Token 1: {results[0]['symbol']}")
        print(f"  Checksum: {results[0]['checksum_valid']}")
        print(f"  Funcoes: {len(results[0]['identified'])}")
        print(f"Token 2: {results[1]['symbol']}")
        print(f"  Checksum: {results[1]['checksum_valid']}")
        print(f"  Funcoes: {len(results[1]['identified'])}")
        print(f"\nEm comum:")
        print(f"  Selectors: {len(common)}")
        print(f"  Funcoes: {len(funcs)}")
        print(f"  Checksum: {checksum}")
