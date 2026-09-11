/**
 * Standard Schema.org JSON-LD Generators for Landing Pages.
 * Injects rich machine-readable metadata for Google Search, Perplexity, Gemini, and SearchGPT.
 */

export function generateSoftwareApplicationSchema({
  name,
  description,
  url,
  applicationCategory = 'BusinessApplication',
  operatingSystem = 'All',
  offers = { price: '0', priceCurrency: 'USD' },
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name,
    description,
    url,
    applicationCategory,
    operatingSystem,
    offers: {
      '@type': 'Offer',
      price: offers.price,
      priceCurrency: offers.priceCurrency,
    },
  };
}

export function generateOrganizationSchema({
  name,
  url,
  logo,
  sameAs = [],
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name,
    url,
    logo,
    sameAs,
  };
}

export function generateFAQPageSchema(faqs = []) {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  };
}
