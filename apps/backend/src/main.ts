/**
 * This is not a production server yet!
 * This is only a minimal backend to get started.
 */

import { Logger, VersioningType } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NestFactory } from '@nestjs/core';
import { NestExpressApplication } from '@nestjs/platform-express';
import cookieParser from 'cookie-parser';
import csurf from 'csurf';
import type { NextFunction, Request, Response } from 'express';
import helmet from 'helmet';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './app/app.module';

type CsrfRequest = Request & {
  csrfToken?: () => string;
};

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);
  const config = app.get(ConfigService);
  const globalPrefix = config.get<string>('GLOBAL_PREFIX', 'api');
  const trustProxy = config.get<number>('TRUST_PROXY', 1);
  const corsOrigin = config.get<string>('CORS_ORIGIN', '*');
  const nodeEnv = config.get<string>('NODE_ENV', 'development');
  const apiVersion = config.get<string>('API_VERSION', '1');
  const swaggerEnabled = config.get<boolean>('SWAGGER_ENABLED', true);
  const swaggerPath = config.get<string>('SWAGGER_PATH', 'docs');
  const swaggerTitle = config.get<string>('SWAGGER_TITLE', 'Bunlar API');
  const swaggerDescription = config.get<string>(
    'SWAGGER_DESCRIPTION',
    'API documentation for Bunlar backend',
  );

  app.set('trust proxy', trustProxy);
  app.setGlobalPrefix(globalPrefix);
  app.enableVersioning({
    type: VersioningType.URI,
    defaultVersion: apiVersion,
  });

  app.use(
    helmet({
      contentSecurityPolicy: false,
      crossOriginEmbedderPolicy: false,
    }),
  );

  app.enableCors({
    origin:
      corsOrigin === '*'
        ? true
        : corsOrigin
            .split(',')
            .map((origin) => origin.trim())
            .filter(Boolean),
    credentials: true,
    methods: ['GET', 'HEAD', 'PUT', 'PATCH', 'POST', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-CSRF-Token'],
  });

  app.use(cookieParser());
  app.use(
    csurf({
      cookie: {
        httpOnly: true,
        sameSite: 'lax',
        secure: nodeEnv === 'production',
      },
      ignoreMethods: ['GET', 'HEAD', 'OPTIONS'],
    }),
  );
  app.use((req: CsrfRequest, res: Response, next: NextFunction) => {
    if (
      ['GET', 'HEAD', 'OPTIONS'].includes(req.method) &&
      typeof req.csrfToken === 'function'
    ) {
      res.setHeader('X-CSRF-Token', req.csrfToken());
    }
    next();
  });

  if (swaggerEnabled) {
    const swaggerConfig = new DocumentBuilder()
      .setTitle(swaggerTitle)
      .setDescription(swaggerDescription)
      .setVersion(apiVersion)
      .addBearerAuth()
      .build();
    const document = SwaggerModule.createDocument(app, swaggerConfig);
    SwaggerModule.setup(`${globalPrefix}/${swaggerPath}`, app, document);
  }

  const port = config.get<number>('PORT', 3000);
  await app.listen(port);
  Logger.log(
    `🚀 Application is running on: http://localhost:${port}/${globalPrefix}/v${apiVersion}`,
  );
  if (swaggerEnabled) {
    Logger.log(
      `📚 Swagger is available at: http://localhost:${port}/${globalPrefix}/${swaggerPath}`,
    );
  }
}

bootstrap();
