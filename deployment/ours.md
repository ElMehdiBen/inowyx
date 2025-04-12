
#  Force Rebuild + Restart the Stack
docker compose -f docker-compose.dev.yml build --no-cache --pull=false
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d


# start fresh
docker compose -f docker-compose.dev.yml down --volumes --remove-orphans


 git config --global user.email "you@example.com"
  git config --global user.name "Your Name"