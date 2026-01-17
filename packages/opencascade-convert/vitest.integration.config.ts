const config = {
  test: {
    environment: 'node',
    include: ['packages/opencascade-convert/src/**/__tests__/**/*.integration.test.ts'],
    testTimeout: 300_000,
    maxThreads: 1,
    minThreads: 1,
    poolOptions: {
      threads: {
        minThreads: 1,
        maxThreads: 1,
      },
    },
  },
};

export default config;
