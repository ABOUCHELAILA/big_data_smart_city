# Grafana Dashboard Configuration
# This file contains the dashboard configuration for Smart City Traffic Analysis
# To use: Copy content to Grafana UI or use provisioning

Dashboard Title: Smart City - Analyse du Trafic Urbain

## Panels:

### 1. Trafic Moyen par Zone
- Type: Time Series (Bar Chart)
- Data Source: Traffic Data API
- Target: zone_metrics
- Visualization: Bars with 80% fill opacity

### 2. Taux de Congestion par Zone  
- Type: Gauge
- Data Source: Traffic Data API
- Target: congestion
- Thresholds: Green (0-50%), Yellow (50-70%), Red (70%+)

### 3. Vitesse Moyenne par Type de Route
- Type: Time Series (Line Chart)
- Data Source: Traffic Data API
- Target: road_metrics
- Unit: km/h
- Shows: Mean and Max values

### 4. Répartition du Trafic par Zone
- Type: Pie Chart (Donut)
- Data Source: Traffic Data API
- Target: zone_metrics
- Displays traffic distribution across zones

## Configuration Notes:
- Dashboard UID: smart-city-traffic
- Tags: smart-city, traffic, mobility
- Time Range: Last 6 hours
- Auto-refresh: Enabled
