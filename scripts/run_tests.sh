
set +e
docker stop mongodb
set -e

docker run -d --rm -p 27017-27019:27017-27019 --name mongodb mongo:4.2

sleep 5

pytest

docker stop mongodb