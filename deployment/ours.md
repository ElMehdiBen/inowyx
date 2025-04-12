
#  Force Rebuild + Restart the Stack
docker compose -f docker-compose.dev.yml build --no-cache --pull=false
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d


# start fresh
docker compose -f docker-compose.dev.yml down --volumes --remove-orphans