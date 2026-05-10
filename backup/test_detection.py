"""
TESTE DE DETECCAO - Verifica se os 3 contratos seriam detectados
"""
import re
from web3 import Web3

BSC_RPC = "https://bsc-dataseed.binance.org/"
TARGET_CHECKSUM = "#25171e80"

SELECTOR_CACHE = {
    "0x06fdde03", "0x095ea7b3", "0x18160ddd", "0x20800a00",
    "0x23b872dd", "0x2dc0562d", "0x313ce567", "0x4e487b71",
    "0x70a08231", "0x715018a6", "0x751039fc", "0x791ac947",
    "0x7d1db4a5", "0x8da5cb5b", "0x8f9a55c0", "0x95d89b41",
    "0xa9059cbb", "0xad5c4648", "0xbd460cdc", "0xc34c08e5",
    "0xc45a0155", "0xc9567bf9", "0xc9c65396", "0xccec3716",
    "0xd8454a82", "0xdd62ed3e", "0xf305d719", "0xffffffff"
}

w3 = Web3(Web3.HTTPProvider(BSC_RPC))


def extract_selectors(bytecode: str) -> set[str]:
    if bytecode.startswith('0x'):
        bytecode = bytecode[2:]
    selectors = set()
    for match in re.findall(r'63([0-9a-fA-F]{8})', bytecode):
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


def test_detection(address: str) -> bool:
    """Simula deteccao de um contrato."""
    bytecode = w3.eth.get_code(Web3.to_checksum_address(address)).hex()
    selectors = extract_selectors(bytecode)
    checksum = calculate_checksum(selectors)
    is_match = checksum == TARGET_CHECKSUM
    return checksum, len(selectors), is_match


if __name__ == "__main__":
    contracts = [
        ("0xf55bd605efafec54c14af96d3227640672921068", "Contrato 1"),
        ("0x863afe6ed8e226dee1b9e4f81bb93da04c082205", "Contrato 2"),
        ("0xbb58c8f8444cc5095e4bfd17d282a751c3b77240", "Contrato 3"),
        ("0xa324cea2b6cfdbada85d60f0d8ec65f12f8d0a81", "Novo Token"),
    ]
    
    print("="*60)
    print("TESTE DE DETECCAO")
    print(f"Checksum alvo: {TARGET_CHECKSUM}")
    print("="*60 + "\n")
    
    all_pass = True
    
    for addr, name in contracts:
        checksum, selectors, is_match = test_detection(addr)
        status = "DETECTADO!" if is_match else "NAO DETECTADO"
        
        print(f"{name}: {addr[:16]}...")
        print(f"  Checksum: {checksum}")
        print(f"  Selectors: {selectors}")
        print(f"  Resultado: {status}")
        print()
        
        if not is_match:
            all_pass = False
    
    print("="*60)
    if all_pass:
        print("SUCESSO! Todos os 4 contratos seriam detectados!")
    else:
        print("FALHA! Algum contrato nao seria detectado.")
    print("="*60)
