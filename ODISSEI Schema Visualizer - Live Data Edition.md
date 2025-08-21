# ODISSEI Schema Visualizer - Live Data Edition

A Python-based interactive web application for exploring the ODISSEI Knowledge Graph RDF schema with **live data updates** from the SPARQL endpoint.

## 🚀 New Features - Live Data Updates

- **Real-time Data Fetching**: Automatically queries the SPARQL endpoint every 5 minutes
- **Manual Refresh**: Click the "🔄 Refresh Data Now" button for immediate updates
- **Live Statistics**: All statistics update automatically with fresh data
- **Background Updates**: Data fetching happens in the background without interrupting user interaction
- **Fallback Support**: Uses cached data if the SPARQL endpoint is unavailable

## Features

- **Interactive Dashboard**: Overview of schema statistics and namespaces (live updated)
- **Classes Explorer**: Browse and search through all RDF classes with filtering (live data)
- **Predicates Explorer**: Explore domain-specific predicates with namespace filtering (live data)
- **Network Visualization**: Interactive graph showing relationships between schema elements (live data)
- **Real-time Filtering**: Search and filter by namespace across all views
- **Auto-refresh**: Visual indicators show when data was last updated

## Requirements

- Python 3.8+
- Internet connection (for SPARQL endpoint access)
- All dependencies listed in `requirements.txt`

## Installation & Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify files**
   Make sure these files are present:
   - `app_live.py` (main application with live updates)
   - `sparql_client.py` (SPARQL endpoint client)
   - `odissei_schema_processed.json` (fallback data)

## Running the Live Application

### Method 1: Live Data Version (Recommended)
```bash
python app_live.py
```

### Method 2: Static Data Version (Fallback)
```bash
python app.py
```

The live application will start and display:
```
Performing initial data fetch...
INFO:sparql_client:Fetching schema data from SPARQL endpoint...
INFO:sparql_client:Executing SPARQL query: SELECT DISTINCT ?p WHERE {?s ?p ?o} LIMIT 100...
INFO:sparql_client:Executing SPARQL query: SELECT DISTINCT ?type WHERE {?s a ?type} LIMIT 100...
Fetched X classes and Y predicates
Data updated successfully at 2024-XX-XX XX:XX:XX
Starting ODISSEI Schema Visualizer with live data...
Open your browser and go to: http://localhost:8052
```

## Accessing the Application

1. **Local access**: Open your browser and go to `http://localhost:8052`
2. **Network access**: Use `http://[your-ip]:8052` to access from other devices

## Live Data Features

### Automatic Updates
- **Background Thread**: Fetches new data every 5 minutes automatically
- **Non-blocking**: Updates happen in the background without interrupting user interaction
- **Error Handling**: Falls back to cached data if SPARQL endpoint is unavailable

### Manual Refresh
- Click the "🔄 Refresh Data Now" button to immediately fetch fresh data
- Useful when you know the data has changed and don't want to wait for automatic update

### Update Indicators
- **Last Updated**: Shows timestamp of the most recent data fetch
- **Live Status**: Interface indicates when data is being refreshed
- **Statistics**: All numbers update automatically with fresh data

## Application Structure

```
odissei-python-visualizer/
├── app_live.py                     # Main live application
├── app.py                          # Static version (fallback)
├── sparql_client.py                # SPARQL endpoint client
├── requirements.txt                # Python dependencies
├── odissei_schema_processed.json   # Fallback data
├── odissei_schema_live.json        # Live data cache (generated)
├── README_live.md                  # This file
└── README.md                       # Original README
```

## Usage Guide

### Overview Tab
- View live schema statistics (auto-updating)
- See color-coded namespace organization
- Real-time count of classes, predicates, and namespaces

### Classes Tab
- Browse all RDF classes from live SPARQL data
- Search and filter functionality with live data
- Namespace filtering based on current data

### Predicates Tab
- Explore domain-specific predicates from live endpoint
- Real-time search and filtering
- Up-to-date predicate information

### Visualization Tab
- Interactive network graph with live data
- Auto-updating relationships and nodes
- Group filtering based on current schema

## Technical Details

### SPARQL Integration
- **Endpoint**: `https://api.kg.odissei.nl/datasets/odissei/odissei-kg-acceptance/services/odissei-kg-acceptance-virtuoso/sparql`
- **Query Types**: Distinct classes and predicates
- **Error Handling**: Graceful fallback to cached data
- **Timeout**: 30-second timeout for SPARQL queries

### Update Mechanism
- **Background Thread**: Daemon thread for automatic updates
- **Threading**: Non-blocking updates using Python threading
- **Caching**: Saves fetched data to local JSON file
- **Fallback**: Uses static data if live fetch fails

### Performance Optimization
- **Selective Updates**: Only updates when new data is available
- **Caching**: Reduces SPARQL endpoint load
- **Lazy Loading**: Network visualization limits nodes for performance

## Configuration

### Update Frequency
Modify the update interval in `app_live.py`:
```python
time.sleep(300)  # Update every 5 minutes (300 seconds)
```

### SPARQL Timeout
Adjust timeout in `sparql_client.py`:
```python
response = self.session.get(url, timeout=30)  # 30 second timeout
```

### Data Limits
Control the amount of data fetched:
```python
predicates = client.get_distinct_predicates(100)  # Limit to 100 predicates
classes = client.get_distinct_classes(100)        # Limit to 100 classes
```

## Troubleshooting

### Common Issues

1. **SPARQL Endpoint Unavailable**
   - Application will use cached/fallback data
   - Check internet connection
   - Verify SPARQL endpoint URL is accessible

2. **Slow Initial Load**
   - First data fetch may take 30-60 seconds
   - Subsequent updates are faster due to caching

3. **Port Already in Use**
   ```
   OSError: [Errno 98] Address already in use
   ```
   Solution: Change port in `app_live.py`:
   ```python
   app.run_server(debug=True, host='0.0.0.0', port=8053)
   ```

4. **Threading Issues**
   - Background updates run in daemon threads
   - Threads automatically terminate when main application stops

### Debug Mode
The application runs in debug mode by default. To disable:
```python
app.run_server(debug=False, host='0.0.0.0', port=8052)
```

### Monitoring Updates
Check the console output for update status:
```
Fetching data from SPARQL endpoint...
Data updated successfully at 2024-XX-XX XX:XX:XX
```

## Data Sources

- **Live Data**: ODISSEI SPARQL endpoint (primary)
- **Fallback Data**: Local JSON file (backup)
- **Cache**: `odissei_schema_live.json` (auto-generated)

## Security Notes

- Application binds to `0.0.0.0` for network access
- No authentication required for SPARQL endpoint
- Data is read-only (no modifications to endpoint)

## License

This application is created for exploring the ODISSEI Knowledge Graph schema with live data capabilities. Please refer to ODISSEI's terms of use for the underlying data.

