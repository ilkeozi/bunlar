type Env = {
  NODE_ENV: 'development' | 'test' | 'production';
  PORT: number;
  GLOBAL_PREFIX: string;
  CORS_ORIGIN: string;
  TRUST_PROXY: number;
  THROTTLE_TTL_MS: number;
  THROTTLE_LIMIT: number;
  CACHE_TTL_SECONDS: number;
  CACHE_MAX_ITEMS: number;
  DATABASE_URL: string;
  API_VERSION: string;
  SWAGGER_ENABLED: boolean;
  SWAGGER_PATH: string;
  SWAGGER_TITLE: string;
  SWAGGER_DESCRIPTION: string;
  REDIS_ENABLED: boolean;
  REDIS_HOST: string;
  REDIS_PORT: number;
  REDIS_PASSWORD: string;
  REDIS_DB: number;
};
type NodeEnv = Env['NODE_ENV'];

function getOptionalString(config: Record<string, unknown>, key: string): string | undefined {
  const value = config[key];
  if (value === undefined) return undefined;
  if (typeof value === 'string') return value;
  throw new Error(`Invalid ${key}: expected a string, got "${String(value)}"`);
}

function isNodeEnv(value: string): value is NodeEnv {
  return value === 'development' || value === 'test' || value === 'production';
}

function parseNumber(value: string | undefined, fallback: number, name: string): number {
  if (!value) return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    throw new Error(`Invalid ${name}: expected a number, got "${value}"`);
  }
  return parsed;
}

function parseBoolean(
  value: string | undefined,
  fallback: boolean,
  name: string,
): boolean {
  if (!value) return fallback;
  if (value === 'true') return true;
  if (value === 'false') return false;
  throw new Error(`Invalid ${name}: expected "true" or "false", got "${value}"`);
}

function requireString(
  value: string | undefined,
  name: string,
): string {
  if (!value) {
    throw new Error(`Invalid ${name}: value is required`);
  }
  return value;
}

export function validateEnv(config: Record<string, unknown>): Env {
  const nodeEnv = getOptionalString(config, 'NODE_ENV') ?? 'development';
  if (!isNodeEnv(nodeEnv)) {
    throw new Error(`Invalid NODE_ENV: ${nodeEnv}`);
  }

  return {
    NODE_ENV: nodeEnv,
    PORT: parseNumber(getOptionalString(config, 'PORT'), 3000, 'PORT'),
    GLOBAL_PREFIX: getOptionalString(config, 'GLOBAL_PREFIX') ?? 'api',
    CORS_ORIGIN: getOptionalString(config, 'CORS_ORIGIN') ?? '*',
    TRUST_PROXY: parseNumber(getOptionalString(config, 'TRUST_PROXY'), 1, 'TRUST_PROXY'),
    THROTTLE_TTL_MS: parseNumber(
      getOptionalString(config, 'THROTTLE_TTL_MS'),
      60000,
      'THROTTLE_TTL_MS',
    ),
    THROTTLE_LIMIT: parseNumber(
      getOptionalString(config, 'THROTTLE_LIMIT'),
      100,
      'THROTTLE_LIMIT',
    ),
    CACHE_TTL_SECONDS: parseNumber(
      getOptionalString(config, 'CACHE_TTL_SECONDS'),
      60,
      'CACHE_TTL_SECONDS',
    ),
    CACHE_MAX_ITEMS: parseNumber(
      getOptionalString(config, 'CACHE_MAX_ITEMS'),
      1000,
      'CACHE_MAX_ITEMS',
    ),
    DATABASE_URL: requireString(
      getOptionalString(config, 'DATABASE_URL'),
      'DATABASE_URL',
    ),
    API_VERSION: getOptionalString(config, 'API_VERSION') ?? '1',
    SWAGGER_ENABLED: parseBoolean(
      getOptionalString(config, 'SWAGGER_ENABLED'),
      true,
      'SWAGGER_ENABLED',
    ),
    SWAGGER_PATH: getOptionalString(config, 'SWAGGER_PATH') ?? 'docs',
    SWAGGER_TITLE: getOptionalString(config, 'SWAGGER_TITLE') ?? 'Bunlar API',
    SWAGGER_DESCRIPTION:
      getOptionalString(config, 'SWAGGER_DESCRIPTION') ??
      'API documentation for Bunlar backend',
    REDIS_ENABLED: parseBoolean(
      getOptionalString(config, 'REDIS_ENABLED'),
      false,
      'REDIS_ENABLED',
    ),
    REDIS_HOST: getOptionalString(config, 'REDIS_HOST') ?? 'localhost',
    REDIS_PORT: parseNumber(getOptionalString(config, 'REDIS_PORT'), 6379, 'REDIS_PORT'),
    REDIS_PASSWORD: getOptionalString(config, 'REDIS_PASSWORD') ?? '',
    REDIS_DB: parseNumber(getOptionalString(config, 'REDIS_DB'), 0, 'REDIS_DB'),
  };
}
