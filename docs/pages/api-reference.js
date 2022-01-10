import React from 'react'
import { promises as fs } from 'fs'
import { Box, Themed } from 'theme-ui'
import Themify from '../components/themify'
import Section from '../components/section'

const APIReference = ({ body }) => {
  return (
    <Box>
      <Section name='API'>
        <Themed.h1>API Reference</Themed.h1>
        <Themify html={body} />
      </Section>
    </Box>
  )
}

export default APIReference

export async function getStaticProps({ params }) {
  const res = await fs.readFile('./_build/json/api.fjson', 'utf8')
  const contents = JSON.parse(res)
  return { props: contents }
}
