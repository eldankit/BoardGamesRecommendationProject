FROM postgres:latest
ENV POSTGRES_PASSWORD mypassword
ENV POSTGRES_USER postgres
ENV POSTGRES_DB postgres
COPY dump.sql /docker-entrypoint-initdb.d/
