module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: ['prettier'],
  plugins: ['prettier'],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'script',
  },
  rules: {
    'prettier/prettier': 'error',
    'no-unused-vars': 'error',
  },
};
