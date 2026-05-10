"""
Analisa contratos e calcula checksums (Method IDs Hash e Functions Hash)
para identificar padrões de deploy.
"""
from web3 import Web3
import re

# Conectar à BSC (Binance Smart Chain)
BSC_RPC = "https://bsc-dataseed.binance.org/"
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

print(f"Conectado à BSC: {w3.is_connected()}")


def get_bytecode(address: str) -> str:
    """Pega o bytecode de um contrato."""
    checksum_addr = Web3.to_checksum_address(address)
    bytecode = w3.eth.get_code(checksum_addr)
    return bytecode.hex()


def extract_function_selectors(bytecode: str) -> list[str]:
    """
    Extrai os function selectors (4 bytes) do bytecode.
    Os selectors aparecem após PUSH4 (opcode 0x63) no bytecode.
    """
    selectors = []
    
    # Remove '0x' se presente
    if bytecode.startswith('0x'):
        bytecode = bytecode[2:]
    
    # PUSH4 = 0x63, seguido de 4 bytes (8 caracteres hex)
    # Padrão: 63 XX XX XX XX (PUSH4 seguido de 4 bytes)
    pattern = r'63([0-9a-fA-F]{8})'
    matches = re.findall(pattern, bytecode)
    
    for match in matches:
        selector = f"0x{match.lower()}"
        if selector not in selectors:
            selectors.append(selector)
    
    return sorted(selectors)


def calculate_method_hash(selectors: list[str]) -> str:
    """
    Calcula o hash dos method IDs concatenados.
    Retorna os primeiros 4 bytes do hash.
    """
    if not selectors:
        return "#00000000"
    
    # Concatena todos os selectors (sem 0x)
    concat = "".join([s[2:] for s in selectors])
    
    # Calcula keccak256
    hash_bytes = Web3.keccak(hexstr=concat)
    
    # Retorna os primeiros 4 bytes
    return f"#{hash_bytes.hex()[:8]}"


def analyze_contract(address: str, name: str = ""):
    """Analisa um contrato e mostra seus checksums."""
    print(f"\n{'='*60}")
    print(f"Analisando: {name or address}")
    print(f"Endereço: {address}")
    print(f"{'='*60}")
    
    try:
        # 1. Pegar bytecode
        bytecode = get_bytecode(address)
        print(f"Bytecode size: {len(bytecode)//2} bytes")
        
        # 2. Extrair function selectors
        selectors = extract_function_selectors(bytecode)
        print(f"\nFunction Selectors encontrados ({len(selectors)}):")
        for sel in selectors[:10]:  # Mostra os 10 primeiros
            print(f"  {sel}")
        if len(selectors) > 10:
            print(f"  ... e mais {len(selectors) - 10}")
        
        # 3. Calcular method hash
        method_hash = calculate_method_hash(selectors)
        print(f"\n[METHOD] Method IDs Hash: {method_hash}")
        
        # 4. Calcular hash do bytecode completo (functions text)
        bytecode_hash = Web3.keccak(hexstr=bytecode[2:] if bytecode.startswith('0x') else bytecode)
        functions_hash = f"#{bytecode_hash.hex()[:8]}"
        print(f"[FUNCTIONS] Functions Hash (bytecode): {functions_hash}")
        
        return {
            "address": address,
            "bytecode_size": len(bytecode)//2,
            "selectors": selectors,
            "method_hash": method_hash,
            "functions_hash": functions_hash
        }
        
    except Exception as e:
        print(f"Erro: {e}")
        return None


if __name__ == "__main__":
    # Contratos para analisar (do mesmo dev)
    contracts = [
        ("0xf55bd605efafec54c14af96d3227640672921068", "Contrato 1"),
        ("0x863afe6ed8e226dee1b9e4f81bb93da04c082205", "Contrato 2"),
    ]
    
    results = []
    for addr, name in contracts:
        result = analyze_contract(addr, name)
        if result:
            results.append(result)
    
    # Comparar checksums
    if len(results) >= 2:
        print("\n" + "="*60)
        print("COMPARACAO DOS CHECKSUMS")
        print("="*60)
        
        same_method = results[0]["method_hash"] == results[1]["method_hash"]
        same_functions = results[0]["functions_hash"] == results[1]["functions_hash"]
        
        print(f"\nContrato 1 - Method Hash: {results[0]['method_hash']}")
        print(f"Contrato 2 - Method Hash: {results[1]['method_hash']}")
        print(f"-> Mesmo Method Hash: {'SIM' if same_method else 'NAO'}")
        
        print(f"\nContrato 1 - Functions Hash: {results[0]['functions_hash']}")
        print(f"Contrato 2 - Functions Hash: {results[1]['functions_hash']}")
        print(f"-> Mesmo Functions Hash: {'SIM' if same_functions else 'NAO'}")
        
        if same_method and same_functions:
            print("\n>>> CONCLUSAO: Os contratos usam o MESMO TEMPLATE!")
        elif same_method:
            print("\n>>> CONCLUSAO: Mesmas funcoes, mas bytecode diferente (pode ser mesma base com modificacoes)")
        else:
            print("\n>>> CONCLUSAO: Templates diferentes")
