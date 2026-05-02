from typing import Any, Dict, Optional


PRODUCT_ENRICHMENT = {
    "1234567890": {
        "name": "Kendamil First Infant Milk",
        "brand": "Kendamil",
        "description": "First infant milk with whole milk fats and vitamins.",
        "category": "Baby & Toddler",
        "subcategory": "Formula Milk",
        "ingredients": "Whole milk, lactose, vegetable oils, demineralised whey powder, galacto-oligosaccharides, docosahexaenoic acid, vitamins, minerals",
        "allergens": ["milk"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "1111111111": {
        "name": "Aptamil First Infant Milk",
        "brand": "Aptamil",
        "description": "First infant milk suitable from birth.",
        "category": "Baby & Toddler",
        "subcategory": "Formula Milk",
        "ingredients": "Lactose, skimmed milk, vegetable oils, whey protein concentrate, fish oil, vitamins, minerals",
        "allergens": ["milk", "fish"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "2222222222": {
        "name": "SMA First Infant Milk",
        "brand": "SMA",
        "description": "First infant milk with DHA and vitamin D.",
        "category": "Baby & Toddler",
        "subcategory": "Formula Milk",
        "ingredients": "Lactose, skimmed milk, vegetable oils, whey protein, fish oil, vitamins, minerals",
        "allergens": ["milk", "fish"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "3333333333": {
        "name": "HiPP Organic First Infant Milk",
        "brand": "HiPP",
        "description": "Organic first infant milk.",
        "category": "Baby & Toddler",
        "subcategory": "Formula Milk",
        "ingredients": "Organic skimmed milk, organic lactose, organic vegetable oils, whey powder, fish oil, vitamins, minerals",
        "allergens": ["milk", "fish"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "4444444444": {
        "name": "Cow & Gate First Infant Milk",
        "brand": "Cow & Gate",
        "description": "First infant milk suitable from birth.",
        "category": "Baby & Toddler",
        "subcategory": "Formula Milk",
        "ingredients": "Lactose, skimmed milk, vegetable oils, whey protein, fish oil, vitamins, minerals",
        "allergens": ["milk", "fish"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "5555555555": {
        "name": "Kendamil Organic First Infant Milk",
        "brand": "Kendamil",
        "description": "Organic first infant milk.",
        "category": "Baby & Toddler",
        "subcategory": "Formula Milk",
        "ingredients": "Organic whole milk, organic lactose, organic vegetable oils, whey powder, vitamins, minerals",
        "allergens": ["milk"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "6666666666": {
        "name": "Cow & Gate Fruity Wholegrain Porridge",
        "brand": "Cow & Gate",
        "description": "Wholegrain baby porridge with fruit.",
        "category": "Baby & Toddler",
        "subcategory": "Porridge",
        "ingredients": "Wholegrain oat flour, skimmed milk powder, banana flakes, apple flakes, vitamins, minerals",
        "allergens": ["milk", "gluten"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "7777777777": {
        "name": "Aptamil Multigrain Porridge",
        "brand": "Aptamil",
        "description": "Baby porridge with oats and mixed grains.",
        "category": "Baby & Toddler",
        "subcategory": "Porridge",
        "ingredients": "Wholegrain oat flour, wheat flour, rice flour, skimmed milk powder, vitamins, minerals",
        "allergens": ["milk", "gluten", "wheat"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "8888888888": {
        "name": "HiPP Organic Baby Porridge",
        "brand": "HiPP",
        "description": "Organic baby porridge with oats.",
        "category": "Baby & Toddler",
        "subcategory": "Porridge",
        "ingredients": "Organic wholegrain oat flour, organic rice flour, vitamin B1",
        "allergens": ["gluten"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "9999999999": {
        "name": "Ella's Kitchen The Green One",
        "brand": "Ella's Kitchen",
        "description": "Fruit and vegetable baby puree pouch.",
        "category": "Baby & Toddler",
        "subcategory": "Fruit Puree",
        "ingredients": "Apple, pear, banana, kiwi",
        "allergens": [],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "1010101010": {
        "name": "Ella's Kitchen Bananas Bananas Bananas",
        "brand": "Ella's Kitchen",
        "description": "Banana baby puree pouch.",
        "category": "Baby & Toddler",
        "subcategory": "Fruit Puree",
        "ingredients": "Banana (100%)",
        "allergens": [],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "1212121212": {
        "name": "Heinz By Nature Pear Baby Food",
        "brand": "Heinz",
        "description": "Simple pear puree for babies.",
        "category": "Baby & Toddler",
        "subcategory": "Fruit Puree",
        "ingredients": "Pear (100%)",
        "allergens": [],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "1313131313": {
        "name": "Organix Melty Carrot Puffs",
        "brand": "Organix",
        "description": "Light baby snack made from maize and carrot.",
        "category": "Baby & Toddler",
        "subcategory": "Snacks",
        "ingredients": "Maize, sunflower oil, carrot powder, thiamin",
        "allergens": [],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "1414141414": {
        "name": "Organix Apple Rice Cakes",
        "brand": "Organix",
        "description": "Baby rice cakes with apple juice.",
        "category": "Baby & Toddler",
        "subcategory": "Snacks",
        "ingredients": "Rice, apple juice concentrate, cinnamon",
        "allergens": [],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "1515151515": {
        "name": "Kiddylicious Strawberry Wafers",
        "brand": "Kiddylicious",
        "description": "Strawberry flavoured wafer snack for toddlers.",
        "category": "Baby & Toddler",
        "subcategory": "Snacks",
        "ingredients": "Wheat flour, grape juice concentrate, strawberry powder, sunflower oil",
        "allergens": ["gluten", "wheat"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "1616161616": {
        "name": "Cow & Gate Banana Baby Food",
        "brand": "Cow & Gate",
        "description": "Smooth banana puree for babies.",
        "category": "Baby & Toddler",
        "subcategory": "Fruit Puree",
        "ingredients": "Banana (100%)",
        "allergens": [],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "1717171717": {
        "name": "Aptamil Toddler Milk 1-2 Years",
        "brand": "Aptamil",
        "description": "Toddler milk drink with vitamins and minerals.",
        "category": "Baby & Toddler",
        "subcategory": "Toddler Milk",
        "ingredients": "Skimmed milk, lactose, vegetable oils, galacto-oligosaccharides, fish oil, vitamins, minerals",
        "allergens": ["milk", "fish"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "1818181818": {
        "name": "Kendamil Toddler Milk",
        "brand": "Kendamil",
        "description": "Toddler milk made with whole milk fats.",
        "category": "Baby & Toddler",
        "subcategory": "Toddler Milk",
        "ingredients": "Whole milk, lactose, vegetable oils, vitamins, minerals",
        "allergens": ["milk"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
    "1919191919": {
        "name": "HiPP Organic Growing Up Milk",
        "brand": "HiPP",
        "description": "Organic growing up milk for toddlers.",
        "category": "Baby & Toddler",
        "subcategory": "Toddler Milk",
        "ingredients": "Organic skimmed milk, organic lactose, vegetable oils, fish oil, vitamins, minerals",
        "allergens": ["milk", "fish"],
        "source": "enrichment",
        "source_retailer": "SafeBite",
    },
}


def get_product_enrichment(barcode: Any) -> Optional[Dict[str, Any]]:
    if barcode is None:
        return None
    return PRODUCT_ENRICHMENT.get(str(barcode).strip())


def enrich_product_data(product: Dict[str, Any]) -> Dict[str, Any]:
    if not product:
        return product

    enriched = dict(product)
    barcode = str(enriched.get("barcode", "")).strip()
    extra = PRODUCT_ENRICHMENT.get(barcode)

    if not extra:
        return enriched

    for key, value in extra.items():
        current = enriched.get(key)

        if current is None:
            enriched[key] = value
            continue

        if isinstance(current, str) and not current.strip():
            enriched[key] = value
            continue

        if isinstance(current, list) and not current:
            enriched[key] = value
            continue

    return enriched
