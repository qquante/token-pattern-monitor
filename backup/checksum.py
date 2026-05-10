from web3 import Web3


def to_checksum(address: str) -> str:
    """Converte um endereço para formato checksum EIP-55."""
    return Web3.to_checksum_address(address)


def is_valid_checksum(address: str) -> bool:
    """Verifica se o endereço já está no formato checksum correto."""
    try:
        return address == Web3.to_checksum_address(address)
    except:
        return False


if __name__ == "__main__":
    # Endereços para testar
    addresses = [
        "0xf55bd605efafec54c14af96d3227640672921068",
        "0x863afe6ed8e226dee1b9e4f81bb93da04c082205",
    ]
    
    print("=" * 70)
    print("CONVERSÃO DE ENDEREÇOS PARA CHECKSUM (EIP-55)")
    print("=" * 70)
    
    for addr in addresses:
        checksum = to_checksum(addr)
        is_valid = is_valid_checksum(addr)
        
        print(f"\nOriginal:    {addr}")
        print(f"Checksum:    {checksum}")
        print(f"Já válido:   {'Sim' if is_valid else 'Não'}")
        print("-" * 70)
