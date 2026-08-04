import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

/** @type {import('next').NextConfig} */
const config = {
  output: 'export',
  // served at https://odoolings.ronit.io/ (custom domain, see public/CNAME),
  // root path, no basePath.
  trailingSlash: true,
  reactStrictMode: true,
};

export default withMDX(config);
