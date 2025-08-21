# ODISSEI Schema Visualizer - Python Edition

A Python-based interactive web application for exploring the ODISSEI Knowledge Graph RDF schema using Dash and Plotly.

## Features

- **Interactive Dashboard**: Overview of schema statistics and namespaces
- **Classes Explorer**: Browse and search through all RDF classes with filtering
- **Predicates Explorer**: Explore domain-specific predicates with namespace filtering
- **Network Visualization**: Interactive graph showing relationships between schema elements
- **Real-time Filtering**: Search and filter by namespace across all views

## Requirements

- Python 3.8+
- All dependencies listed in `requirements.txt`

## Installation & Setup

1. **Clone or download the project files**
   ```bash
   # If you have the files, navigate to the directory
   cd odissei-python-visualizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify data file**
   Make sure `odissei_schema_processed.json` is in the same directory as `app.py`

## Running the Application

### Method 1: Direct Python execution
```bash
python app.py
```

### Method 2: Using Python3 explicitly
```bash
python3 app.py
```

The application will start and display:
```
Dash is running on http://0.0.0.0:8050/

 * Serving Flask app 'app'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8050
 * Running on http://[your-ip]:8050
```

## Accessing the Application

1. **Local access**: Open your browser and go to `http://localhost:8050`
2. **Network access**: Use `http://[your-ip]:8050` to access from other devices on the same network

## Application Structure

```
odissei-python-visualizer/
├── app.py                          # Main Dash application
├── requirements.txt                # Python dependencies
├── odissei_schema_processed.json   # Schema data
└── README.md                       # This file
```

## Usage Guide

### Overview Tab
- View schema statistics (total classes, predicates, namespaces)
- See color-coded namespace organization
- Understand the structure of ODISSEI and Dataverse namespaces

### Classes Tab
- Browse all 72 RDF classes in the schema
- Use the search box to find specific classes
- Filter by namespace using the dropdown
- View full URIs and namespace information

### Predicates Tab
- Explore domain-specific predicates (relations)
- Search through predicate names and URIs
- Filter by namespace to focus on specific areas
- See detailed predicate information

### Visualization Tab
- Interactive network graph of schema relationships
- Select different groups to focus visualization:
  - **All Elements**: Shows a sample of all classes and predicates
  - **Domain Specific**: Shows only domain-specific elements
  - **Namespace-specific**: Filter by individual namespaces
- Hover over nodes to see detailed information
- Click and drag to explore the network

## Technical Details

### Built With
- **Dash**: Web application framework
- **Plotly**: Interactive visualizations
- **NetworkX**: Graph analysis and layout
- **Pandas**: Data manipulation
- **Bootstrap**: UI components

### Data Source
The application uses schema data extracted from the ODISSEI SPARQL endpoint:
`https://api.kg.odissei.nl/datasets/odissei/odissei-kg-acceptance/services/odissei-kg-acceptance-virtuoso/sparql`

### Performance Notes
- Network visualization is limited to subsets of data for performance
- Large namespace selections may take a moment to render
- The application is optimized for exploration rather than exhaustive display

## Customization

### Modifying Colors
Edit the `namespace_colors` dictionary in `app.py` to change namespace color schemes.

### Adjusting Graph Layout
Modify the NetworkX layout parameters in the `create_plotly_network()` function:
```python
pos = nx.spring_layout(G, k=3, iterations=50)  # Adjust k and iterations
```

### Adding More Data
Replace `odissei_schema_processed.json` with updated schema data following the same structure.

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```
   OSError: [Errno 98] Address already in use
   ```
   Solution: Change the port in `app.py`:
   ```python
   app.run_server(debug=True, host='0.0.0.0', port=8051)  # Use different port
   ```

2. **Missing data file**
   ```
   FileNotFoundError: [Errno 2] No such file or directory: 'odissei_schema_processed.json'
   ```
   Solution: Ensure the JSON data file is in the same directory as `app.py`

3. **Module not found errors**
   Solution: Install missing dependencies:
   ```bash
   pip install [missing-module-name]
   ```

### Debug Mode
The application runs in debug mode by default. To disable:
```python
app.run_server(debug=False, host='0.0.0.0', port=8050)
```

## Deployment

For production deployment, consider using:
- **Gunicorn**: `gunicorn app:server`
- **Docker**: Create a Dockerfile for containerized deployment
- **Cloud platforms**: Deploy to Heroku, AWS, or similar platforms

## License

This application is created for exploring the ODISSEI Knowledge Graph schema. Please refer to ODISSEI's terms of use for the underlying data.

