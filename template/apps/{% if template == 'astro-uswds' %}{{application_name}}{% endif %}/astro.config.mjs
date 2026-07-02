// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from "@astrojs/sitemap";
import process_anchors from "./src/plugins/process_anchors";
import process_image_urls from './src/plugins/process_image_urls';
import generateRedirects from './src/config/redirects';
import sitemapFilter from "./src/config/sitemapFilter";



const base = process.env.BASEURL ? (process.env.BASEURL.endsWith('/') ? process.env.BASEURL : `${process.env.BASEURL}/`) : '/'

// https://astro.build/config
export default defineConfig({
  site: 'https://TODO_VAR_site_name.com',
  base: base,
  integrations: [
    mdx(),
    sitemap({ filter: sitemapFilter }),
  ],
  outDir: '_site',
  markdown: {
    rehypePlugins: [
      [process_anchors, { baseURL: base }],
      [process_image_urls, { baseURL: base }]
    ],
  },
  redirects: generateRedirects(base),
  vite: {
    resolve: {
      alias: {
        '@assets': new URL('./src/assets', import.meta.url).pathname,
        '@components': '/src/components',
        '@layouts': '/src/layouts'
      },
    },
    publicDir: 'public',
  },
  // Enable legacy features to support the layout field in Markdown frontmatter
  legacy: {
    collections: true
  },
});

