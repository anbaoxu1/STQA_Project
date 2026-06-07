Container image:

postgres.tar is the container image file. After extraction/import, it becomes the postgres:alpine image, which will be used for subsequent container creation.

Container creation command:

docker run -id --name=my-postgresql -v ./data:/var/lib/postgresql/data -p 1213:5432 -e POSTGRES_PASSWORD='123456' -e POSTGRES_USER='***' -e LANG=C.UTF-8 --restart=always postgres:alpine

Container startup/access command:

docker exec -it my-postgresql /bin/bash

Database creation/access command:

psql postgres ***
