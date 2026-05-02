# SafeBite Dashboard

Admin dashboard scaffold for the SafeBite FastAPI backend.

## Run

```bash
npm install
npm run dev
```

The dashboard uses `SAFEBITE_API_URL` on the server and falls back to `NEXT_PUBLIC_SAFEBITE_API_URL`.

Default API:

```text
http://127.0.0.1:8000
```

## Pages

- `/login`
- `/products`
- `/products/[barcode]`
- `/offers`
- `/import-review`

Current editor pages are read-oriented because the backend exposes read routes for products, offers, and alternatives but no admin write routes yet.
