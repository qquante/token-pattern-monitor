"""
Analise COMPLETA - identifica TODAS as funcoes via 4byte.directory API
"""
from web3 import Web3
import re
import requests
import time

BSC_RPC = "https://bsc-dataseed.binance.org/"
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

# Cache para evitar requisicoes repetidas
selector_cache = {}


def get_bytecode(address: str) -> str:
    checksum_addr = Web3.to_checksum_address(address)
    bytecode = w3.eth.get_code(checksum_addr)
    return bytecode.hex()


def extract_selectors(bytecode: str) -> list[str]:
    """Extrai selectors via PUSH4 (0x63)."""
    if bytecode.startswith('0x'):
        bytecode = bytecode[2:]
    
    selectors = set()
    pattern = r'63([0-9a-fA-F]{8})'
    matches = re.findall(pattern, bytecode)
    
    for match in matches:
        selectors.add(f"0x{match.lower()}")
    
    return sorted(list(selectors))


def lookup_selector(selector: str) -> str:
    """Consulta 4byte.directory para identificar a funcao."""
    if selector in selector_cache:
        return selector_cache[selector]
    
    try:
        # API do 4byte.directory
        url = f"https://www.4byte.directory/api/v1/signatures/?hex_signature={selector}"
        resp = requests.get(url, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("results"):
                # Pega a primeira (mais comum)
                func_name = data["results"][0]["text_signature"]
                selector_cache[selector] = func_name
                return func_name
        
        selector_cache[selector] = None
        return None
        
    except Exception as e:
        selector_cache[selector] = None
        return None


def calculate_checksum(selectors: list[str]) -> str:
    """Hash dos selectors concatenados ordenados."""
    if not selectors:
        return "#00000000"
    sorted_sels = sorted(selectors)
    concat = "".join([s[2:] for s in sorted_sels])
    hash_bytes = Web3.keccak(hexstr=concat)
    return f"#{hash_bytes.hex()[:8]}"


def analyze_contract_full(address: str, name: str):
    """Analise completa com lookup de todas as funcoes."""
    print(f"\n{'='*70}")
    print(f"{name}")
    print(f"Endereco: {address}")
    print(f"{'='*70}")
    
    bytecode = get_bytecode(address)
    selectors = extract_selectors(bytecode)
    
    print(f"Bytecode: {len(bytecode)//2} bytes")
    print(f"Selectors extraidos: {len(selectors)}")
    
    # Identificar todas as funcoes
    print(f"\nIdentificando funcoes via 4byte.directory...")
    identified = {}
    unknown = []
    
    for i, sel in enumerate(selectors):
        func = lookup_selector(sel)
        if func:
            identified[sel] = func
        else:
            unknown.append(sel)
        
        # Progresso
        if (i + 1) % 10 == 0:
            print(f"  Processado {i+1}/{len(selectors)}...")
        
        time.sleep(0.1)  # Rate limit
    
    # Mostrar resultados
    print(f"\n--- FUNCOES IDENTIFICADAS ({len(identified)}) ---")
    for sel in sorted(identified.keys()):
        print(f"  {sel} -> {identified[sel]}")
    
    print(f"\n--- SELECTORS NAO IDENTIFICADOS ({len(unknown)}) ---")
    print("  (Podem ser constantes/dados, nao funcoes reais)")
    for sel in unknown:
        print(f"  {sel}")
    
    # Checksums
    all_checksum = calculate_checksum(selectors)
    identified_checksum = calculate_checksum(list(identified.keys()))
    
    print(f"\n--- CHECKSUMS ---")
    print(f"  Todos selectors:        {all_checksum}")
    print(f"  Apenas identificados:   {identified_checksum}")
    
    return {
        "address": address,
        "name": name,
        "selectors": selectors,
        "identified": identified,
        "unknown": unknown,
        "all_checksum": all_checksum,
        "identified_checksum": identified_checksum
    }


if __name__ == "__main__":
    contracts = [
        ("0xe655549794afa8817945de67994f39141d9b1529", "CONTRATO NOVO 1"),
        ("0x20d6015660b3fe52e6690a889b5c51f69902ce0e", "CONTRATO NOVO 2"),
    ]
    
    results = []
    for addr, name in contracts:
        result = analyze_contract_full(addr, name)
        results.append(result)
    
    # Comparacao final
    print("\n" + "="*70)
    print("COMPARACAO FINAL")
    print("="*70)
    
    # Checksums de todos
    print("\n--- CHECKSUMS DE TODOS OS CONTRATOS ---")
    print("\nChecksum TODOS selectors:")
    for r in results:
        print(f"  {r['name']}: {r['all_checksum']}")
    
    print("\nChecksum FUNCOES IDENTIFICADAS:")
    for r in results:
        print(f"  {r['name']}: {r['identified_checksum']}")
    
    # Verificar se todos os checksums de funcoes sao iguais
    all_identified_checksums = [r['identified_checksum'] for r in results]
    all_same = len(set(all_identified_checksums)) == 1
    
    print(f"\n>>> TODOS USAM MESMO TEMPLATE: {'SIM' if all_same else 'NAO'}")
    
    if all_same:
        print(f">>> CHECKSUM DO TEMPLATE: {all_identified_checksums[0]}")
    
    # Mostrar funcoes em comum entre todos
    if len(results) >= 2:
        common_funcs = set(results[0]['identified'].keys())
        for r in results[1:]:
            common_funcs &= set(r['identified'].keys())
        
        print(f"\nFuncoes em comum (todos {len(results)} contratos): {len(common_funcs)}")
        
        # Checksum das funcoes em comum
        common_checksum = calculate_checksum(sorted(list(common_funcs)))
        print(f"Checksum funcoes em comum: {common_checksum}")
