"""
Analise detalhada dos contratos - mostra TODOS os selectors
para comparar melhor os dois contratos.
"""
from web3 import Web3
import re

BSC_RPC = "https://bsc-dataseed.binance.org/"
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

def get_bytecode(address: str) -> str:
    checksum_addr = Web3.to_checksum_address(address)
    bytecode = w3.eth.get_code(checksum_addr)
    return bytecode.hex()

def extract_function_selectors(bytecode: str) -> list[str]:
    """Extrai selectors via PUSH4 (0x63)."""
    if bytecode.startswith('0x'):
        bytecode = bytecode[2:]
    
    selectors = set()
    pattern = r'63([0-9a-fA-F]{8})'
    matches = re.findall(pattern, bytecode)
    
    for match in matches:
        selectors.add(f"0x{match.lower()}")
    
    return sorted(list(selectors))

def calculate_checksum_v1(selectors: list[str]) -> str:
    """Hash dos selectors concatenados."""
    if not selectors:
        return "#00000000"
    concat = "".join([s[2:] for s in selectors])
    hash_bytes = Web3.keccak(hexstr=concat)
    return f"#{hash_bytes.hex()[:8]}"

def calculate_checksum_v2(selectors: list[str]) -> str:
    """Hash dos selectors ordenados e unidos."""
    if not selectors:
        return "#00000000"
    # Ordenar e juntar
    sorted_sels = sorted(selectors)
    concat = "".join(sorted_sels)  # Com 0x
    hash_bytes = Web3.keccak(text=concat)
    return f"#{hash_bytes.hex()[:8]}"


if __name__ == "__main__":
    contracts = [
        "0xf55bd605efafec54c14af96d3227640672921068",
        "0x863afe6ed8e226dee1b9e4f81bb93da04c082205",
    ]
    
    all_selectors = {}
    
    for addr in contracts:
        print(f"\n{'='*60}")
        print(f"Contrato: {addr}")
        print(f"{'='*60}")
        
        bytecode = get_bytecode(addr)
        selectors = extract_function_selectors(bytecode)
        all_selectors[addr] = set(selectors)
        
        print(f"Bytecode: {len(bytecode)//2} bytes")
        print(f"Selectors: {len(selectors)}")
        print(f"\nTodos os selectors:")
        for s in selectors:
            print(f"  {s}")
        
        print(f"\nChecksum v1: {calculate_checksum_v1(selectors)}")
        print(f"Checksum v2: {calculate_checksum_v2(selectors)}")
    
    # Comparar
    print("\n" + "="*60)
    print("ANALISE COMPARATIVA")
    print("="*60)
    
    set1 = all_selectors[contracts[0]]
    set2 = all_selectors[contracts[1]]
    
    common = set1 & set2
    only_in_1 = set1 - set2
    only_in_2 = set2 - set1
    
    print(f"\nSelectors em comum: {len(common)}")
    print(f"Apenas no Contrato 1: {len(only_in_1)}")
    print(f"Apenas no Contrato 2: {len(only_in_2)}")
    
    if only_in_1:
        print(f"\nApenas no Contrato 1:")
        for s in sorted(only_in_1):
            print(f"  {s}")
    
    if only_in_2:
        print(f"\nApenas no Contrato 2:")
        for s in sorted(only_in_2):
            print(f"  {s}")
    
    # Calcular checksum apenas dos selectors em comum
    common_list = sorted(list(common))
    print(f"\nChecksum dos selectors EM COMUM:")
    print(f"  {calculate_checksum_v1(common_list)}")
