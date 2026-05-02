from database import init_db, seed_products_from_json, seed_sample_offers


def run_seed():
    init_db()
    seed_products_from_json()
    seed_sample_offers()
    print("✅ Database created and seeded successfully.")


if __name__ == "__main__":
    run_seed()