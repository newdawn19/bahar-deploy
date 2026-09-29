# 可选：构建自包含镜像（默认是挂载 jar 运行，无需构建）。
#
# 在 deploy/ 目录下执行（context 必须是 deploy/，JAR_FILE 相对该目录）：
#   docker build -f docker/Dockerfile --build-arg JAR_FILE=runtime/bahar-shop.jar -t bahar-shop .
FROM eclipse-temurin:11-jre

ARG JAR_FILE=runtime/bahar-shop.jar
ENV TZ=Asia/Shanghai
ENV JAVA_OPTS="-Xmx512m"

# logback-spring.xml 里 FILE appender 写 /data/log/bahar/server.log，目录需提前存在
RUN mkdir -p /data/oss /data/log/bahar

COPY ${JAR_FILE} /app.jar

EXPOSE 8080
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app.jar --server.port=${SERVER_PORT:-8080}"]
