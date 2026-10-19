"""
Debug de checksum para contratos específicos
Analisa endereços e verifica formato EIP-55
"""
import re
from web3 import Web3

# ETHEREUM RPC
ETH_RPC = "https://eth.llamarpc.com"
w3 = Web3(Web3.HTTPProvider(ETH_RPC))

# Selectors conhecidos
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
    "0x791ac947": "swapExactTokensForETHSupportingFeeOnTransferTokens",
    "0xad5c4648": "WETH()",
    "0xf305d719": "addLiquidityETH",
    "0x751039fc": "removeLimits()",
    "0xc9567bf9": "openTrading()",
    "0x49bd5a5e": "uniswapV2Pair()",
    "0x1694505e": "uniswapV2Router()",
}


def analyze_address_checksum(address: str):
    """Analisa o checksum EIP-55 de um endereço."""
    print(f"\n{'='*70}")
    print(f"ENDEREÇO ORIGINAL: {address}")
    print("="*70)
    
    # Checksum EIP-55
    try:
        checksum_addr = Web3.to_checksum_address(address)
        is_valid = address == checksum_addr
        
        print(f"Checksum EIP-55:   {checksum_addr}")
        print(f"Formato válido:    {'SIM' if is_valid else 'NAO'}")
        
        if not is_valid:
            print("\n[!] DIFERENÇAS DETECTADAS:")
            for i, (orig, check) in enumerate(zip(address[2:], checksum_addr[2:])):
                if orig != check:
                    pos = i + 2  # +2 para considerar o "0x"
                    print(f"    Posição {pos}: '{orig}' -> '{check}'")
        
        return checksum_addr
    except Exception as e:
        print(f"ERRO: {e}")
        return None


def analyze_contract(address: str):
    """Analisa o bytecode e selectors de um contrato."""
    try:
        addr = Web3.to_checksum_address(address)
        
        # Verificar se é contrato
        code = w3.eth.get_code(addr)
        
        if code == b'' or code.hex() == '0x':
            print(f"\n[!] ENDEREÇO NÃO É UM CONTRATO (EOA ou vazio)")
            balance = w3.eth.get_balance(addr)
            print(f"    Balance: {Web3.from_wei(balance, 'ether')} ETH")
            return None
        
        bytecode = code.hex()
        print(f"\n[CONTRATO DETECTADO]")
        print(f"Bytecode size: {len(bytecode)//2} bytes")
        
        # Extrair selectors
        all_sels = set()
        for m in re.findall(r'63([0-9a-fA-F]{8})', bytecode):
            all_sels.add(f"0x{m.lower()}")
        
        print(f"Total selectors PUSH4: {len(all_sels)}")
        
        # Calcular checksum dos selectors
        if all_sels:
            sorted_sels = sorted(list(all_sels))
            concat = "".join([s[2:] for s in sorted_sels])
            hash_bytes = Web3.keccak(hexstr=concat)
            selector_checksum = f"#{hash_bytes.hex()[:8]}"
        else:
            selector_checksum = "#00000000"
        
        print(f"Checksum selectors: {selector_checksum}")
        
        # Identificar funções conhecidas
        known = []
        unknown = []
        for sel in sorted(all_sels):
            if sel in KNOWN_SELECTORS:
                known.append((sel, KNOWN_SELECTORS[sel]))
            else:
                unknown.append(sel)
        
        print(f"\nFunções conhecidas ({len(known)}):")
        for sel, name in known:
            print(f"  {sel} -> {name}")
        
        if unknown:
            print(f"\nSelectors desconhecidos ({len(unknown)}):")
            for sel in unknown[:15]:  # Limitar para não poluir
                print(f"  {sel}")
            if len(unknown) > 15:
                print(f"  ... e mais {len(unknown)-15}")
        
        # Tentar obter nome/símbolo do token
        try:
            abi = [
                {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
            ]
            contract = w3.eth.contract(address=addr, abi=abi)
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            print(f"\nToken Info:")
            print(f"  Nome: {name}")
            print(f"  Símbolo: {symbol}")
        except:
            pass
        
        return {
            "address": addr,
            "bytecode_size": len(bytecode)//2,
            "selectors": all_sels,
            "checksum": selector_checksum
        }
        
    except Exception as e:
        print(f"\nERRO ao analisar contrato: {e}")
        return None


def main():
    # Endereços para debugar
    addresses = [
        "0x4904Ab74222459FF45908880F99507852f2714EF",
        "0x506D6c41548B6CD0F00C6610e9411468bb01609c",
        "0x4904ab74222459ff45908880f99507852f2714ef",
    ]
    
    print("="*70)
    print("DEBUG DE CHECKSUM - ANÁLISE DE CONTRATOS")
    print("="*70)
    
    results = []
    
    for addr in addresses:
        # Análise do checksum EIP-55
        checksum_addr = analyze_address_checksum(addr)
        
        if checksum_addr:
            # Análise do contrato
            result = analyze_contract(checksum_addr)
            if result:
                results.append(result)
    
    # Comparação se houver múltiplos contratos
    if len(results) >= 2:
        print("\n" + "="*70)
        print("COMPARAÇÃO DE CHECKSUMS DOS CONTRATOS")
        print("="*70)
        
        unique_contracts = {}
        for r in results:
            unique_contracts[r["address"]] = r
        
        for addr, data in unique_contracts.items():
            print(f"\n{addr}")
            print(f"  Checksum selectors: {data['checksum']}")
            print(f"  Total selectors: {len(data['selectors'])}")
        
        # Se houver 2+ contratos únicos, mostrar diferenças
        if len(unique_contracts) >= 2:
            addrs = list(unique_contracts.keys())
            sels1 = unique_contracts[addrs[0]]["selectors"]
            sels2 = unique_contracts[addrs[1]]["selectors"]
            
            common = sels1 & sels2
            only1 = sels1 - sels2
            only2 = sels2 - sels1
            
            print(f"\nSelectors em comum: {len(common)}")
            print(f"Apenas em {addrs[0][:10]}...: {len(only1)}")
            print(f"Apenas em {addrs[1][:10]}...: {len(only2)}")


if __name__ == "__main__":
    main()
