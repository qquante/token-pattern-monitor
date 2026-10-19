"""
Analisa contrato especifico - todos os selectors e checksum
"""
import re
from web3 import Web3

# ETHEREUM RPC
ETH_RPC = "https://eth.llamarpc.com"
w3 = Web3(Web3.HTTPProvider(ETH_RPC))

# Selectors conhecidos do template alvo
SELECTOR_CACHE = {
    "0x06fdde03", "0x095ea7b3", "0x18160ddd", "0x20800a00",
    "0x23b872dd", "0x2dc0562d", "0x313ce567", "0x4e487b71",
    "0x70a08231", "0x715018a6", "0x751039fc", "0x791ac947",
    "0x7d1db4a5", "0x8da5cb5b", "0x8f9a55c0", "0x95d89b41",
    "0xa9059cbb", "0xad5c4648", "0xbd460cdc", "0xc34c08e5",
    "0xc45a0155", "0xc9567bf9", "0xc9c65396", "0xccec3716",
    "0xd8454a82", "0xdd62ed3e", "0xf305d719", "0xffffffff"
}

TARGET_CHECKSUM = "#25171e80"

def analyze(addr):
    addr = Web3.to_checksum_address(addr)
    print(f"\nAnalisando: {addr}")
    print("="*60)
    
    bytecode = w3.eth.get_code(addr).hex()
    print(f"Bytecode size: {len(bytecode)//2} bytes")
    
    # Extrair TODOS os selectors
    all_sels = set()
    for m in re.findall(r'63([0-9a-fA-F]{8})', bytecode[2:]):
        all_sels.add(f"0x{m.lower()}")
    
    print(f"Total selectors encontrados: {len(all_sels)}")
    
    # Filtrar pelos conhecidos
    matched_sels = all_sels & SELECTOR_CACHE
    print(f"Selectors do cache: {len(matched_sels)}")
    
    # Calcular checksum
    if matched_sels:
        sorted_sels = sorted(list(matched_sels))
        concat = "".join([s[2:] for s in sorted_sels])
        hash_bytes = Web3.keccak(hexstr=concat)
        checksum = f"#{hash_bytes.hex()[:8]}"
    else:
        checksum = "#00000000"
    
    print(f"\nChecksum: {checksum}")
    print(f"Target: {TARGET_CHECKSUM}")
    print(f"Match: {'SIM!' if checksum == TARGET_CHECKSUM else 'NAO'}")
    
    print(f"\nSelectors encontrados no cache ({len(matched_sels)}):")
    for s in sorted(matched_sels):
        print(f"  {s}")
    
    print(f"\nTodos os selectors ({len(all_sels)}):")
    for s in sorted(all_sels):
        flag = " <-- no cache" if s in SELECTOR_CACHE else ""
        print(f"  {s}{flag}")

if __name__ == "__main__":
    analyze("0x98530b4eeab7487219020134ebed4851e780151d")
    analyze("0xd80a36ab1bd56182392b5a5e485eab8ea683837a")
