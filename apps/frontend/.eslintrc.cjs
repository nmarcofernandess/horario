module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
  },
  overrides: [
    {
      files: ['src/renderer/components/ui/**/*.tsx'],
      rules: { 'react-refresh/only-export-components': 'off' },
    },
    {
      files: ['src/renderer/components/theme-provider.tsx', 'src/renderer/components/tour.tsx'],
      rules: { 'react-refresh/only-export-components': 'off' },
    },
  ],
}
