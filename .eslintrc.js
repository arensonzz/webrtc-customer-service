module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: ["prettier"],
  plugins: ["html", "prettier"],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
  },
  rules: {
    "prettier/prettier": "error",
    "no-unused-vars": "error",
  },
};
