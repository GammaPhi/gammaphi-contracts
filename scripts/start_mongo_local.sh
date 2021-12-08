
set +e
docker stop mongodb
set -e

docker run --rm -p 27017-27019:27017-27019 --name mongodb mongo:4.2
