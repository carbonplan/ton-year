const isDev =
  process.env.VERCEL_ENV === 'preview' || process.env.NODE_ENV === 'development'

const slug = require('rehype-slug')

const withMDX = require('@next/mdx')({
  extension: /\.mdx?$/,
  options: {
    rehypePlugins: [slug],
  },
})

module.exports = withMDX({
  pageExtensions: ['jsx', 'js', 'md', 'mdx'],
  async rewrites() {
    return [
      {
        source: '/ton-year/api',
        destination: '/ton-year/api-reference',
      },
    ]
  },
  assetPrefix: isDev ? '' : 'https://ton-year.docs.carbonplan.org',
})
