const config = {
  test: {
    environment: 'node',
    include: ['packages/opencascade-convert/src/**/__tests__/**/*.test.ts'],
    exclude: ['**/*.integration.test.ts'],
  },
};

export default config;
