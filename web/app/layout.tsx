import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';
import { Provider } from '@/components/provider';
import {
  GeistPixelCircle,
  GeistPixelGrid,
  GeistPixelLine,
  GeistPixelSquare,
  GeistPixelTriangle,
} from 'geist/font/pixel';
import { ProgressPill } from '@/components/progress-pill';
import {
  appDescription,
  appName,
  basePath,
  canonicalUrl,
  homeTitle,
  siteOrigin,
  socialCard,
} from '@/lib/shared';
import type { Metadata, Viewport } from 'next';
import './global.css';

export const viewport: Viewport = {
  colorScheme: 'light dark',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#f7fbfc' },
    { media: '(prefers-color-scheme: dark)', color: '#0f1f22' },
  ],
};

export const metadata: Metadata = {
  metadataBase: new URL(siteOrigin),
  title: {
    default: homeTitle,
    template: `%s | ${appName}`,
  },
  description: appDescription,
  applicationName: appName,
  creator: 'Ronit Jadhav',
  alternates: {
    canonical: canonicalUrl(),
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: canonicalUrl(),
    siteName: appName,
    title: homeTitle,
    description: appDescription,
    images: [
      {
        url: socialCard,
        width: 1200,
        height: 630,
        alt: `${appName}: free Odoo 19 development tutorial`,
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: homeTitle,
    description: appDescription,
    images: [socialCard],
  },
  icons: {
    icon: [
      {
        url: `${basePath}/brand/odoolings-avatar-paper.png`,
        type: 'image/png',
        sizes: '1024x1024',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: `${basePath}/brand/odoolings-avatar-ink.png`,
        type: 'image/png',
        sizes: '1024x1024',
        media: '(prefers-color-scheme: dark)',
      },
    ],
    apple: `${basePath}/brand/odoolings-avatar-paper.png`,
  },
  manifest: `${basePath}/manifest.webmanifest`,
};

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable} ${GeistPixelSquare.variable} ${GeistPixelGrid.variable} ${GeistPixelCircle.variable} ${GeistPixelTriangle.variable} ${GeistPixelLine.variable}`}
      suppressHydrationWarning
    >
      <body className="flex flex-col min-h-screen">
        <Provider>{children}</Provider>
        <ProgressPill />
      </body>
    </html>
  );
}
