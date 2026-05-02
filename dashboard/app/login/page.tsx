import Image from 'next/image';
import Link from 'next/link';

export default function LoginPage() {
  return (
    <main className="login-shell">
      <section className="login-panel">
        <div className="login-brand">
          <Image
            alt="SafeBite"
            className="brand-logo"
            height={48}
            priority
            src="/safebite-logo.png"
            width={48}
          />
          <strong>SafeBite</strong>
        </div>

        <form action="/products" className="login-form">
          <div className="form-field">
            <label htmlFor="email">Email</label>
            <input className="input" id="email" name="email" type="email" />
          </div>
          <div className="form-field">
            <label htmlFor="password">Password</label>
            <input className="input" id="password" name="password" type="password" />
          </div>
          <button className="button" type="submit">
            Sign in
          </button>
          <Link className="button button-secondary" href="/products">
            Continue to products
          </Link>
        </form>
      </section>
    </main>
  );
}
