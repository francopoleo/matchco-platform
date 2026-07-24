cd /
cd /app
echo "Running command '$*'"
exec /bin/bash -c "$*"