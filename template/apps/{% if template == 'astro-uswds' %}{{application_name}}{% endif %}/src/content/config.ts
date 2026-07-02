import { z, defineCollection } from 'astro:content';
import { glob } from "astro/loaders";

const nav = defineCollection({
  loader: glob({ pattern: "**/*.yaml", base: "./src/content/nav" })
})


// Define types for content collections
const faqCollection = defineCollection({
  schema: z.object({
    title: z.string(),
    order: z.number(),
    description: z.string()
  }),
});

const about = defineCollection({})
const contact = defineCollection({})
const audits = defineCollection({})
const merchants = defineCollection({})
const smartBulletins = defineCollection({})
const howItWorks = defineCollection({})
const resources = defineCollection({})
const stakeholders = defineCollection({})
const publications = defineCollection({})

// Export only the collections that have corresponding directories
export const collections = {
  'faq': faqCollection,
  about,
  contact,
  audits,
  merchants,
  smartBulletins,
  howItWorks,
  resources,
  stakeholders,
  publications
};
