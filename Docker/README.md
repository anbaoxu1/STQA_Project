## PostgreSQL Container Setup

### Container Image

`postgres.tar` is the container image file. After extraction or import, it becomes the `postgres:alpine` image, which is used for subsequent container creation.

### Container Creation

Run the following command to create the PostgreSQL container:

```bash
docker run -id \
  --name=my-postgresql \
  -v ./data:/var/lib/postgresql/data \
  -p 1213:5432 \
  -e POSTGRES_PASSWORD='123456' \
  -e POSTGRES_USER='***' \
  -e LANG=C.UTF-8 \
  --restart=always \
  postgres:alpine
