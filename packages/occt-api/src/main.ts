import "reflect-metadata";
import { NestFactory } from "@nestjs/core";
import { AppModule } from "./app.module";

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    logger: ["log", "warn", "error"]
  });
  app.enableCors({ origin: true });

  const port = Number(process.env.PORT || 3001);
  await app.listen(port, "0.0.0.0");
  console.log(`[occt-api] listening on ${port}`);
}

bootstrap();
