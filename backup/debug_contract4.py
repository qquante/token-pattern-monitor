"""
DEBUG: Analisa o contrato 4 em detalhe e compara com os outros 3
"""
from web3 import Web3
import re

BSC_RPC = "https://bsc-dataseed.binance.org/"
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

# Selectors do template alvo (28)
SELECTOR_CACHE = {
    "0x06fdde03", "0x095ea7b3", "0x18160ddd", "0x20800a00",
    "0x23b872dd", "0x2dc0562d", "0x313ce567", "0x4e487b71",
    "0x70a08231", "0x715018a6", "0x751039fc", "0x791ac947",
    "0x7d1db4a5", "0x8da5cb5b", "0x8f9a55c0", "0x95d89b41",
    "0xa9059cbb", "0xad5c4648", "0xbd460cdc", "0xc34c08e5",
    "0xc45a0155", "0xc9567bf9", "0xc9c65396", "0xccec3716",
    "0xd8454a82", "0xdd62ed3e", "0xf305d719", "0xffffffff"
}

def get_bytecode(address: str) -> str:
    checksum_addr = Web3.to_checksum_address(address)
    bytecode = w3.eth.get_code(checksum_addr)
    return bytecode.hex()

def extract_all_selectors(bytecode: str) -> list[str]:
    """Extrai TODOS os selectors via PUSH4 (0x63)."""
    if bytecode.startswith('0x'):
        bytecode = bytecode[2:]
    
    selectors = set()
    pattern = r'63([0-9a-fA-F]{8})'
    matches = re.findall(pattern, bytecode)
    
    for match in matches:
        selectors.add(f"0x{match.lower()}")
    
    return sorted(list(selectors))

def extract_cached_selectors(bytecode: str) -> set[str]:
    """Extrai apenas selectors que estão no cache."""
    if bytecode.startswith('0x'):
        bytecode = bytecode[2:]
    
    selectors = set()
    pattern = r'63([0-9a-fA-F]{8})'
    matches = re.findall(pattern, bytecode)
    
    for match in matches:
        sel = f"0x{match.lower()}"
        if sel in SELECTOR_CACHE:
            selectors.add(sel)
    
    return selectors

def calculate_checksum(selectors: set[str]) -> str:
    if not selectors:
        return "#00000000"
    sorted_sels = sorted(list(selectors))
    concat = "".join([s[2:] for s in sorted_sels])
    hash_bytes = Web3.keccak(hexstr=concat)
    return f"#{hash_bytes.hex()[:8]}"


if __name__ == "__main__":
    contracts = [
        ("0xf55bd605efafec54c14af96d3227640672921068", "Contrato 1 (OK)"),
        ("0x863afe6ed8e226dee1b9e4f81bb93da04c082205", "Contrato 2 (OK)"),
        ("0xbb58c8f8444cc5095e4bfd17d282a751c3b77240", "Contrato 3 (OK)"),
        ("0x85fd43a539a035f61f50441fd8a5f4b768ba749d", "Contrato 4 (FALHOU)"),
    ]
    
    all_data = {}
    
    for addr, name in contracts:
        print(f"\n{'='*70}")
        print(f"{name}")
        print(f"Endereco: {addr}")
        print(f"{'='*70}")
        
        bytecode = get_bytecode(addr)
        all_selectors = extract_all_selectors(bytecode)
        cached_selectors = extract_cached_selectors(bytecode)
        checksum = calculate_checksum(cached_selectors)
        
        all_data[addr] = {
            "name": name,
            "bytecode_size": len(bytecode) // 2,
            "all_selectors": set(all_selectors),
            "cached_selectors": cached_selectors,
            "checksum": checksum
        }
        
        print(f"Bytecode: {len(bytecode) // 2} bytes")
        print(f"Total selectors encontrados: {len(all_selectors)}")
        print(f"Selectors no cache: {len(cached_selectors)}")
        print(f"Checksum: {checksum}")
        
        if len(all_selectors) > 0:
            print(f"\nTODOS os selectors ({len(all_selectors)}):")
            for i, s in enumerate(all_selectors):
                in_cache = "*" if s in SELECTOR_CACHE else " "
                print(f"  [{in_cache}] {s}")
    
    # Comparação especial: Contrato 4 vs Contrato 1
    print("\n" + "="*70)
    print("COMPARACAO: Contrato 4 vs Contrato 1")
    print("="*70)
    
    c1_sels = all_data[contracts[0][0]]["all_selectors"]
    c4_sels = all_data[contracts[3][0]]["all_selectors"]
    
    common = c1_sels & c4_sels
    only_c1 = c1_sels - c4_sels
    only_c4 = c4_sels - c1_sels
    
    print(f"\nSelectors em COMUM: {len(common)}")
    print(f"Apenas no Contrato 1: {len(only_c1)}")
    print(f"Apenas no Contrato 4: {len(only_c4)}")
    
    if only_c1:
        print(f"\nApenas no Contrato 1:")
        for s in sorted(only_c1):
            print(f"  {s}")
    
    if only_c4:
        print(f"\nApenas no Contrato 4:")
        for s in sorted(only_c4):
            print(f"  {s}")
    
    # Verificar se é um proxy/contrato vazio
    print("\n" + "="*70)
    print("DIAGNOSTICO DO CONTRATO 4")
    print("="*70)
    
    c4_bytecode_size = all_data[contracts[3][0]]["bytecode_size"]
    c4_selectors = all_data[contracts[3][0]]["all_selectors"]
    
    if c4_bytecode_size < 100:
        print("⚠️  Bytecode muito pequeno - pode ser um PROXY!")
    elif len(c4_selectors) == 0:
        print("⚠️  Nenhum selector encontrado via PUSH4!")
        print("   O contrato pode usar um pattern diferente.")
    else:
        print(f"Bytecode: {c4_bytecode_size} bytes")
        print(f"Selectors: {len(c4_selectors)}")
