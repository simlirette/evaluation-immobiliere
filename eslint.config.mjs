import nextConfig from 'eslint-config-next'

export default [
  ...nextConfig,
  {
    ignores: ['.next/**', 'node_modules/**'],
  },
  {
    rules: {
      // setLoading(true) before async in effects is correct and intentional
      'react-hooks/set-state-in-effect': 'off',
      // Unescaped entities in JSX — warn only, not block
      'react/no-unescaped-entities': 'warn',
    },
  },
]
