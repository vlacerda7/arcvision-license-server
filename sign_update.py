from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# carrega chave privada (só no servidor!)
with open("update_private.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

file_path = "files/ArcVision_1.1.0.exe"

# lê o arquivo de update
with open(file_path, "rb") as f:
    data = f.read()

# cria assinatura
signature = private_key.sign(
    data,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

# salva assinatura
with open(file_path + ".sig", "wb") as f:
    f.write(signature)

print("Update assinado com sucesso!")
