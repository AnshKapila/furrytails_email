'use client';

import { FormEvent, useState } from 'react';
import { Instagram } from 'lucide-react';

const images = [
  {
    src: 'https://static.kite.ai/image/upload/v1784993848/app/eaccac4c-a287-4e55-89be-8007fdbfaef1/iter3/pet-ritual-dog-window.png',
    alt: 'Dog resting in early sunlight beside a linen curtain',
  },
  {
    src: 'https://static.kite.ai/image/upload/v1784993846/app/eaccac4c-a287-4e55-89be-8007fdbfaef1/iter3/pet-ritual-cat-linen.png',
    alt: 'Tabby cat on soft linen',
  },
  {
    src: 'https://static.kite.ai/image/upload/v1784993847/app/eaccac4c-a287-4e55-89be-8007fdbfaef1/iter3/pet-ritual-dog-hands.png',
    alt: 'Dog receiving gentle care as part of a morning ritual',
  },
  {
    src: 'https://static.kite.ai/image/upload/v1784993847/app/eaccac4c-a287-4e55-89be-8007fdbfaef1/iter3/pet-ritual-cat-sun.png',
    alt: 'Cat stretching in soft morning sunlight',
  },
  {
    src: 'https://static.kite.ai/image/upload/v1784993846/app/eaccac4c-a287-4e55-89be-8007fdbfaef1/iter3/pet-ritual-dog-garden.png',
    alt: 'Dog among sage green garden leaves',
  },
];

export default function Home() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'sending' | 'complete' | 'error'>('idle');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim()) return;
    setStatus('sending');

    try {
      const response = await fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      });
      
      if (response.ok) {
        setStatus('complete');
        window.__kite && window.__kite.conversion('signup');
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  }

  return (
    <main className="landing" data-kite-page-id="home" data-kite-page-type="landing">
      <section className="hero" data-kite-surface="home.early-access" data-kite-surface-type="hero">
        <img
          className="brand-logo"
          src="https://static.kite.ai/image/upload/c_crop,x_0.000,y_0.000,w_1.000,h_1.000/v1785039071/app/eaccac4c-a287-4e55-89be-8007fdbfaef1/p40hxhe6ojzmmsib6v6z.png"
          alt="Furrytail"
        />

        <div className="hero-copy">
          <p className="eyebrow">Natural care, considered</p>
          <h1>A new morning ritual, <em>for you and your dog.</em></h1>
          <p className="intro">Early members get first access, founding pricing, and a first look at what we&apos;re building held to your standard, made for theirs.</p>

          {status === 'complete' ? (
            <div className="confirmation" aria-live="polite">
              <p className="confirmation-success">
                You&apos;re on the list. The ritual begins soon, and you&apos;ll be the first to know.
              </p>

              <a href="https://www.instagram.com/" target="_blank" rel="noreferrer" data-kite-cta-id="instagram-follow" data-kite-role="secondary" data-kite-event="instagram_opened">
                <Instagram aria-hidden="true" size={14} strokeWidth={1.25} />
                Follow along
              </a>
            </div>
          ) : (
            <form className="signup-form" onSubmit={submit} data-kite-form-type="early-access-signup" data-kite-conversion="signup" data-kite-event="signup_completed" data-kite-conversion-hook>
              <label className="sr-only" htmlFor="email">Email address</label>
              <input id="email" name="email" type="email" autoComplete="email" placeholder="Enter your email" value={email} onChange={(event) => setEmail(event.target.value)} required />
              <button type="submit" disabled={status === 'sending'} data-kite-cta-id="early-access-submit" data-kite-role="primary" data-kite-event="signup_started">
                <span className="btn-text">{status === 'sending' ? 'Joining the list' : 'Keep Me Close'}</span>
              </button>
              {status === 'error' && <p className="form-error" role="alert">Please try again in a moment.</p>}
              <p className="form-privacy">No spam, just first access</p>
            </form>
          )}
        </div>

        {/* Desktop photo row */}
        <div className="photo-row photo-row-desktop" aria-label="Furrytail rituals with dogs and cats">
          {images.map((image, index) => (
            <div className={`ritual-frame ritual-frame-${index + 1}`} key={image.src}>
              <img className={`ritual-image image-${index + 1}`} src={image.src} alt={image.alt} />
            </div>
          ))}
        </div>

        {/* Mobile photo row — infinite marquee */}
        <div className="photo-row photo-row-mobile" aria-label="Furrytail rituals with dogs and cats" aria-hidden="true">
          <div className="marquee-track">
            {[...images, ...images].map((image, index) => (
              <div className="mobile-frame" key={`${image.src}-${index}`}>
                <img className="mobile-image" src={image.src} alt={image.alt} />
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
