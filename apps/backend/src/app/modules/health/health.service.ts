import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import {
  HealthCheckError,
  type HealthIndicatorResult,
} from '@nestjs/terminus';
import Redis from 'ioredis';
import { Client } from 'pg';

@Injectable()
export class HealthProbeService {
  constructor(private readonly config: ConfigService) {}

  async checkPostgres(): Promise<HealthIndicatorResult> {
    const connectionString = this.config.get<string>('DATABASE_URL', '');
    const client = new Client({ connectionString });

    try {
      await client.connect();
      await client.query('SELECT 1');
      return {
        database: { status: 'up' },
      };
    } catch (error) {
      throw new HealthCheckError('PostgreSQL check failed', {
        database: { status: 'down', message: this.toErrorMessage(error) },
      });
    } finally {
      await client.end().catch(() => undefined);
    }
  }

  async checkRedis(): Promise<HealthIndicatorResult> {
    const redisEnabled = this.config.get<boolean>('REDIS_ENABLED', false);
    if (!redisEnabled) {
      return { redis: { status: 'up', message: 'disabled' } };
    }

    const host = this.config.get<string>('REDIS_HOST', 'localhost');
    const port = this.config.get<number>('REDIS_PORT', 6379);
    const password = this.config.get<string>('REDIS_PASSWORD', '');
    const db = this.config.get<number>('REDIS_DB', 0);

    const redis = new Redis({
      host,
      port,
      password: password || undefined,
      db,
      maxRetriesPerRequest: 1,
      lazyConnect: true,
    });

    try {
      await redis.connect();
      const pong = await redis.ping();
      if (pong !== 'PONG') {
        throw new Error(`Unexpected ping response: ${pong}`);
      }
      return { redis: { status: 'up' } };
    } catch (error) {
      throw new HealthCheckError('Redis check failed', {
        redis: { status: 'down', message: this.toErrorMessage(error) },
      });
    } finally {
      redis.disconnect();
    }
  }

  private toErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      return error.message;
    }
    return 'Unknown error';
  }
}
