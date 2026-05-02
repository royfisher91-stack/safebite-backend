from database import get_product_by_barcode, upsert_product


def main() -> None:
    barcode = "7622210449283"
    product = get_product_by_barcode(barcode)

    if not product:
        print(f"❌ Product not found: {barcode}")
        return

    product["category"] = "Baby Snacks"
    product["subcategory"] = "Baby Crisps & Puffs"

    upsert_product(product)

    print("✅ Updated category")
    print(f"   {barcode} | {product['name']} | {product['category']} | {product['subcategory']}")


if __name__ == "__main__":
    main()