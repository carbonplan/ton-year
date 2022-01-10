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
        source: '/api',
        destination: '/api-reference',
      },
    ]
  },
})
