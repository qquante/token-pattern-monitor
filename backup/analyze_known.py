"""
Filtra apenas os selectors que sao funcoes ERC20/padroes conhecidas.
Calcula checksum baseado apenas nas funcoes reais.
"""
from web3 import Web3
import re

BSC_RPC = "https://bsc-dataseed.binance.org/"
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

# Selectors conhecidos de funcoes ERC20 e comuns em tokens
KNOWN_SELECTORS = {
    "0x06fdde03": "name()",
    "0x095ea7b3": "approve(address,uint256)",
    "0x18160ddd": "totalSupply()",
    "0x23b872dd": "transferFrom(address,address,uint256)",
    "0x313ce567": "decimals()",
    "0x70a08231": "balanceOf(address)",
    "0x95d89b41": "symbol()",
    "0xa9059cbb": "transfer(address,uint256)",
    "0xdd62ed3e": "allowance(address,address)",
    "0x8da5cb5b": "owner()",
    "0x715018a6": "renounceOwnership()",
    "0xf2fde38b": "transferOwnership(address)",
    "0xc9567bf9": "openTrading()",
    "0x791ac947": "swapExactTokensForETHSupportingFeeOnTransferTokens(...)",
    "0xf305d719": "addLiquidityETH(...)",
    "0xad5c4648": "WETH()",
    "0xc45a0155": "factory()",
    "0xc9c65396": "createPair(address,address)",
    "0x4e487b71": "Panic(uint256)",  # Erro do Solidity
}


def get_bytecode(address: str) -> str:
    checksum_addr = Web3.to_checksum_address(address)
    bytecode = w3.eth.get_code(checksum_addr)
    return bytecode.hex()


def extract_all_selectors(bytecode: str) -> list[str]:
    """Extrai todos os PUSH4 do bytecode."""
    if bytecode.startswith('0x'):
        bytecode = bytecode[2:]
    
    selectors = set()
    pattern = r'63([0-9a-fA-F]{8})'
    matches = re.findall(pattern, bytecode)
    
    for match in matches:
        selectors.add(f"0x{match.lower()}")
    
    return sorted(list(selectors))


def filter_known_selectors(selectors: list[str]) -> dict:
    """Retorna apenas os selectors conhecidos."""
    known = {}
    unknown = []
    
    for sel in selectors:
        if sel in KNOWN_SELECTORS:
            known[sel] = KNOWN_SELECTORS[sel]
        else:
            unknown.append(sel)
    
    return {"known": known, "unknown": unknown}


def calculate_checksum(selectors: list[str]) -> str:
    """Hash dos selectors concatenados."""
    if not selectors:
        return "#00000000"
    sorted_sels = sorted(selectors)
    concat = "".join([s[2:] for s in sorted_sels])  # Remove 0x
    hash_bytes = Web3.keccak(hexstr=concat)
    return f"#{hash_bytes.hex()[:8]}"


if __name__ == "__main__":
    contracts = [
        ("0xf55bd605efafec54c14af96d3227640672921068", "Contrato 1"),
        ("0x863afe6ed8e226dee1b9e4f81bb93da04c082205", "Contrato 2"),
    ]
    
    results = []
    
    for addr, name in contracts:
        print(f"\n{'='*60}")
        print(f"{name}: {addr}")
        print(f"{'='*60}")
        
        bytecode = get_bytecode(addr)
        all_sels = extract_all_selectors(bytecode)
        filtered = filter_known_selectors(all_sels)
        
        print(f"\nBytecode: {len(bytecode)//2} bytes")
        print(f"Total selectors extraidos: {len(all_sels)}")
        print(f"Selectors conhecidos: {len(filtered['known'])}")
        
        print(f"\nFuncoes identificadas:")
        for sel, func in sorted(filtered['known'].items()):
            print(f"  {sel} -> {func}")
        
        # Calcular checksums
        all_checksum = calculate_checksum(all_sels)
        known_checksum = calculate_checksum(list(filtered['known'].keys()))
        
        print(f"\nChecksum (todos): {all_checksum}")
        print(f"Checksum (apenas conhecidos): {known_checksum}")
        
        results.append({
            "name": name,
            "addr": addr,
            "all_sels": all_sels,
            "known": filtered['known'],
            "all_checksum": all_checksum,
            "known_checksum": known_checksum
        })
    
    # Comparacao
    print("\n" + "="*60)
    print("COMPARACAO FINAL")
    print("="*60)
    
    if len(results) >= 2:
        same_all = results[0]["all_checksum"] == results[1]["all_checksum"]
        same_known = results[0]["known_checksum"] == results[1]["known_checksum"]
        
        print(f"\nChecksum TODOS os selectors:")
        print(f"  {results[0]['name']}: {results[0]['all_checksum']}")
        print(f"  {results[1]['name']}: {results[1]['all_checksum']}")
        print(f"  -> Iguais: {'SIM' if same_all else 'NAO'}")
        
        print(f"\nChecksum apenas selectors CONHECIDOS:")
        print(f"  {results[0]['name']}: {results[0]['known_checksum']}")
        print(f"  {results[1]['name']}: {results[1]['known_checksum']}")
        print(f"  -> Iguais: {'SIM' if same_known else 'NAO'}")
        
        # Funcoes em comum
        set1 = set(results[0]['known'].keys())
        set2 = set(results[1]['known'].keys())
        common = set1 & set2
        
        print(f"\nFuncoes conhecidas em comum: {len(common)}/{len(set1 | set2)}")
        
        if same_known:
            print("\n>>> MESMO TEMPLATE BASE (mesmas funcoes principais)!")
        else:
            print("\n>>> Templates diferentes ou modificados")
