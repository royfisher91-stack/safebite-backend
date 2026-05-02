# SafeBite Mobile

Shared Expo app shell for iOS and Android.

## Run

```bash
npm install
npm run start
```

The app reads the SafeBite FastAPI backend from `EXPO_PUBLIC_SAFEBITE_API_URL` when set.

Defaults:

- iOS simulator: `http://127.0.0.1:8000`
- Android emulator: `http://10.0.2.2:8000`

For a physical phone, set `EXPO_PUBLIC_SAFEBITE_API_URL` to the Mac's LAN address, for example:

```bash
EXPO_PUBLIC_SAFEBITE_API_URL=http://192.168.1.25:8000 npm run start
```

## Current mobile shell

- Home
- Search
- Scanner with camera and manual barcode fallback
- Product detail using `/products/barcode/{barcode}`
- Alternatives using `/alternatives/{barcode}`
- Health checks using the backend `allergen` and `conditions` query params
- Saved placeholder

Useful test barcodes:

- `5056000500825` - Kendamil Goat First Infant Milk Stage 1
- `5060107330214` - Ella's Kitchen Apples Carrots Plus Parsnips 120G
