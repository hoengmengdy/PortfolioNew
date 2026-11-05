import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router';
import { LogoMark } from '../components/ui/Logo';
import { useLanguage } from '../hooks/useLanguage';
import { useSeo } from '../hooks/useSeo';

export default function NotFound() {
  const { t } = useLanguage();
  const { notFound } = t;

  useSeo({ title: t.meta.notFoundTitle, description: notFound.body, path: '/404', noindex: true });

  return (
    <main className="relative isolate grid min-h-svh place-items-center overflow-hidden px-5 py-16 text-center">
      <div aria-hidden="true" className="hero-grid absolute inset-0 -z-10" />
      <div>
        <LogoMark className="mx-auto size-14" />
        <p className="eyebrow mt-10">{notFound.eyebrow}</p>
        <h1 className="mt-5 text-4xl font-medium md:text-6xl">{notFound.title}</h1>
        <p className="mt-5 text-lg text-muted">{notFound.body}</p>
        <Link to="/" className="btn btn-gold mt-9">
          <ArrowLeft aria-hidden="true" className="size-4" />
          {notFound.home}
        </Link>
      </div>
    </main>
  );
}
