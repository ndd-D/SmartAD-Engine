FROM openjdk:17-jdk-slim AS builder
WORKDIR /build
COPY . .
RUN ./mvnw clean package -DskipTests -q

FROM openjdk:17-jre-slim
WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "-Dspring.profiles.active=prod", "app.jar"]
