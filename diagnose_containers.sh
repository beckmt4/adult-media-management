#!/bin/bash
# Container Diagnostic Script for Unraid
# Generates a detailed inventory of all running containers with volume/network info
# Run on Unraid (SSH): bash diagnose_containers.sh

echo "=== UNRAID CONTAINER INVENTORY ==="
echo "Generated: $(date)"
echo ""

echo "## Container List (Name, Image, Status, Ports)"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | column -t -s $'\t'
echo ""

echo "## Container Memory & CPU Allocation"
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.CPUPerc}}" 2>/dev/null | head -40
echo ""

echo "## Volume Mounts (Container → Volume Path)"
docker inspect $(docker ps -q) --format='{{.Name}} → {{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}' 2>/dev/null | sed 's/^\/+//' | column -t -s '→'
echo ""

echo "## Network Connections (Ports Published)"
docker ps --format "table {{.Names}}\t{{.Ports}}" 2>/dev/null | grep -v "<none>" | column -t -s $'\t'
echo ""

echo "## Container Base Images (Sorted by Size)"
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | sort -k2 -rh | head -20
echo ""

echo "## Stash GraphQL Connectivity Check"
curl -s -X POST http://localhost:9999/graphql \
  -H "Authorization: Basic $(echo -n 'root:qlx9_adM' | base64)" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ version }"}' 2>/dev/null | jq '.data.version' || echo "Stash API unreachable"
echo ""

echo "## n8n Endpoint Status"
curl -s -I http://localhost:5678/api/v1 2>/dev/null | head -1 || echo "n8n unreachable on localhost:5678"
echo ""

echo "## Faster-Whisper Availability"
curl -s http://localhost:10300/healthz 2>/dev/null || echo "Faster-Whisper unreachable on localhost:10300"
echo ""

echo "Export this output and save as CONTAINER_INVENTORY_$(date +%Y-%m-%d).txt"
