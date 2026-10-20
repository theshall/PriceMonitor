from src.products import list_products

products = list_products()

if not products:
    print("Nenhum produto encontrado.")
else:
    for product in products:
        print("-" * 40)
        print(f"ID: {product['id']}")
        print(f"Nome: {product['name']}")
        print(f"Marca: {product['brand']}")
        print(f"Modelo: {product['model']}")
