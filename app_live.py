import json
import dash
from dash import dcc, html, Input, Output, callback, dash_table, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import networkx as nx
from datetime import datetime
import threading
import time
from sparql_client import SPARQLClient

# Initialize SPARQL client
SPARQL_ENDPOINT = "https://api.kg.odissei.nl/datasets/odissei/odissei-kg-acceptance/services/odissei-kg-acceptance-virtuoso/sparql"
sparql_client = SPARQLClient(SPARQL_ENDPOINT)

# Global variable to store schema data
schema_data = {}
last_update_time = None

# Load initial data from file as fallback
try:
    with open('odissei_schema_processed.json', 'r') as f:
        schema_data = json.load(f)
        last_update_time = "Loaded from file"
except FileNotFoundError:
    # If no file, create empty structure
    schema_data = {
        "metadata": {"total_classes": 0, "total_predicates": 0, "domain_specific_classes": 0, "domain_specific_predicates": 0},
        "namespaces": {"odissei_namespaces": [], "dataverse_namespaces": []},
        "classes": {"all": [], "domain_specific": []},
        "predicates": {"all": [], "domain_specific": []}
    }

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "ODISSEI Schema Visualizer - Live Data"

# Define namespace colors
namespace_colors = {
    "https://portal.odissei.nl/schema/geospatial#": "#3B82F6",
    "https://portal.odissei.nl/schema/dansMetadata#": "#10B981",
    "https://portal.odissei.nl/schema/enrichments#": "#F59E0B",
    "https://portal.odissei.nl/schema/provenance#": "#EF4444",
    "https://portal.odissei.nl/schema/questionInformation#": "#8B5CF6",
    "https://portal.odissei.nl/schema/socialscience#": "#EC4899",
    "https://portal.odissei.nl/schema/variableInformation#": "#06B6D4",
    "https://dataverse.org/schema/citation/": "#F97316",
    "https://dataverse.org/schema/core#": "#84CC16",
    "https://w3id.org/nwo-research-fields#": "#6366F1",
    "https://w3id.org/research-technology-readiness-levels#": "#14B8A6",
    "https://w3id.org/software-types#": "#F43F5E",
    "http://rdf-vocabulary.ddialliance.org/discovery#": "#A855F7",
    "http://xmlns.com/foaf/0.1/": "#22C55E",
    "https://www.w3.org/TR/prov-o/#": "#64748B",
    "default": "#6B7280"
}

def get_namespace_from_uri(uri):
    if '#' in uri:
        return uri.split('#')[0] + '#'
    else:
        parts = uri.split('/')
        return '/'.join(parts[:-1]) + '/'

def get_color_for_namespace(namespace):
    return namespace_colors.get(namespace, namespace_colors["default"])

def get_namespace_short_name(namespace):
    return namespace.split('/')[-1].replace('#', '') or namespace.split('/')[-2]

def update_schema_data():
    """Update schema data from SPARQL endpoint"""
    global schema_data, last_update_time
    try:
        print("Fetching data from SPARQL endpoint...")
        new_data = sparql_client.fetch_schema_data()
        if new_data and new_data.get('classes', {}).get('all'):
            schema_data = new_data
            last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            schema_data['metadata']['last_updated'] = last_update_time
            print(f"Data updated successfully at {last_update_time}")
            
            # Save to file for backup
            with open('odissei_schema_live.json', 'w') as f:
                json.dump(schema_data, f, indent=2)
        else:
            print("Failed to fetch data or received empty data")
    except Exception as e:
        print(f"Error updating schema data: {e}")

def background_update():
    """Background thread to update data periodically"""
    while True:
        update_schema_data()
        time.sleep(300)  # Update every 5 minutes

# Start background update thread
update_thread = threading.Thread(target=background_update, daemon=True)
update_thread.start()

# Create network graph data
def create_network_graph(selected_group='all'):
    if not schema_data.get('classes', {}).get('all'):
        return nx.Graph()
        
    G = nx.Graph()
    
    # Filter data based on selection
    if selected_group == 'all':
        classes = schema_data['classes']['all'][:30]  # Limit for performance
        predicates = schema_data['predicates'].get('domain_specific', [])[:20]
    elif selected_group == 'domain_specific':
        classes = schema_data['classes'].get('domain_specific', [])
        predicates = schema_data['predicates'].get('domain_specific', [])[:15]
    else:
        # Filter by namespace
        classes = [cls for cls in schema_data['classes']['all'] 
                  if get_namespace_from_uri(cls['uri']) == selected_group][:20]
        predicates = [pred for pred in schema_data['predicates'].get('domain_specific', []) 
                     if get_namespace_from_uri(pred['uri']) == selected_group][:15]
    
    # Add nodes
    for cls in classes:
        G.add_node(cls['uri'], 
                  label=cls['local_name'], 
                  type='class',
                  namespace=get_namespace_from_uri(cls['uri']))
    
    for pred in predicates:
        G.add_node(pred['uri'], 
                  label=pred['local_name'], 
                  type='predicate',
                  namespace=get_namespace_from_uri(pred['uri']))
    
    # Add some sample edges
    nodes = list(G.nodes())
    for i in range(min(len(nodes) - 1, 25)):
        if i % 3 == 0:
            G.add_edge(nodes[i], nodes[i + 1])
    
    return G

def create_plotly_network(G):
    if not G.nodes():
        return []
        
    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=3, iterations=50)
    
    # Create edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(x=edge_x, y=edge_y,
                           line=dict(width=1, color='#E5E7EB'),
                           hoverinfo='none',
                           mode='lines')
    
    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    node_sizes = []
    node_info = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        node_data = G.nodes[node]
        node_text.append(node_data['label'])
        node_colors.append(get_color_for_namespace(node_data['namespace']))
        node_sizes.append(20 if node_data['type'] == 'class' else 15)
        
        # Create hover info
        namespace_short = get_namespace_short_name(node_data['namespace'])
        node_info.append(f"<b>{node_data['label']}</b><br>" +
                        f"Type: {node_data['type']}<br>" +
                        f"Namespace: {namespace_short}<br>" +
                        f"URI: {node}")
    
    node_trace = go.Scatter(x=node_x, y=node_y,
                           mode='markers+text',
                           hovertemplate='%{hovertext}<extra></extra>',
                           hovertext=node_info,
                           text=node_text,
                           textposition="top center",
                           marker=dict(size=node_sizes,
                                     color=node_colors,
                                     line=dict(width=2, color='white')))
    
    return [edge_trace, node_trace]

# App layout
app.layout = dbc.Container([
    # Interval component for live updates
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # Update every minute
        n_intervals=0
    ),
    
    dbc.Row([
        dbc.Col([
            html.H1("ODISSEI Knowledge Graph Schema Explorer", 
                   className="text-center mb-2"),
            html.P("Live data from SPARQL endpoint - Auto-updates every minute",
                   className="text-center text-muted mb-2"),
            html.P(id="last-update-info", className="text-center text-sm text-muted mb-4")
        ])
    ]),
    
    # Statistics cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="total-classes", className="card-title"),
                    html.P("Total Classes", className="card-text")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="total-predicates", className="card-title"),
                    html.P("Total Predicates", className="card-text")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="odissei-namespaces", className="card-title"),
                    html.P("ODISSEI Namespaces", className="card-text")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="domain-predicates", className="card-title"),
                    html.P("Domain Predicates", className="card-text")
                ])
            ])
        ], width=3)
    ], className="mb-4"),
    
    # Manual refresh button
    dbc.Row([
        dbc.Col([
            dbc.Button("🔄 Refresh Data Now", id="refresh-button", color="primary", size="sm")
        ], width=12, className="text-center mb-3")
    ]),
    
    # Tabs
    dbc.Tabs([
        dbc.Tab(label="Overview", tab_id="overview"),
        dbc.Tab(label="Classes", tab_id="classes"),
        dbc.Tab(label="Predicates", tab_id="predicates"),
        dbc.Tab(label="Visualization", tab_id="visualization")
    ], id="tabs", active_tab="overview"),
    
    html.Div(id="tab-content", className="mt-4")
], fluid=True)

# Callback to update statistics
@app.callback(
    [Output("total-classes", "children"),
     Output("total-predicates", "children"),
     Output("odissei-namespaces", "children"),
     Output("domain-predicates", "children"),
     Output("last-update-info", "children")],
    [Input("interval-component", "n_intervals"),
     Input("refresh-button", "n_clicks")]
)
def update_statistics(n_intervals, n_clicks):
    global schema_data, last_update_time
    
    # Manual refresh if button clicked
    if n_clicks:
        update_schema_data()
    
    metadata = schema_data.get('metadata', {})
    namespaces = schema_data.get('namespaces', {})
    
    update_info = f"Last updated: {last_update_time or 'Never'}"
    
    return (
        str(metadata.get('total_classes', 0)),
        str(metadata.get('total_predicates', 0)),
        str(len(namespaces.get('odissei_namespaces', []))),
        str(metadata.get('domain_specific_predicates', 0)),
        update_info
    )

# Callback for tab content
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "overview":
        return render_overview()
    elif active_tab == "classes":
        return render_classes()
    elif active_tab == "predicates":
        return render_predicates()
    elif active_tab == "visualization":
        return render_visualization()

def render_overview():
    namespaces = schema_data.get('namespaces', {})
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Schema Overview"),
                dbc.CardBody([
                    html.P("The ODISSEI Knowledge Graph schema encompasses social science research data, datasets, software, and metadata."),
                    dbc.Row([
                        dbc.Col([
                            html.H5("ODISSEI Namespaces"),
                            html.Ul([
                                html.Li([
                                    html.Span("●", style={"color": get_color_for_namespace(ns), "margin-right": "8px"}),
                                    get_namespace_short_name(ns)
                                ]) for ns in namespaces.get('odissei_namespaces', [])
                            ])
                        ], width=6),
                        dbc.Col([
                            html.H5("Dataverse Namespaces"),
                            html.Ul([
                                html.Li([
                                    html.Span("●", style={"color": get_color_for_namespace(ns), "margin-right": "8px"}),
                                    get_namespace_short_name(ns)
                                ]) for ns in namespaces.get('dataverse_namespaces', [])
                            ])
                        ], width=6)
                    ])
                ])
            ])
        ])
    ])

def render_classes():
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Classes Explorer"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Input(id="class-search", placeholder="Search classes...", type="text")
                        ], width=8),
                        dbc.Col([
                            dcc.Dropdown(
                                id="class-namespace-filter",
                                options=[{"label": "All Namespaces", "value": "all"}],
                                value="all"
                            )
                        ], width=4)
                    ], className="mb-3"),
                    html.Div(id="classes-table")
                ])
            ])
        ])
    ])

def render_predicates():
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Predicates Explorer"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Input(id="predicate-search", placeholder="Search predicates...", type="text")
                        ], width=8),
                        dbc.Col([
                            dcc.Dropdown(
                                id="predicate-namespace-filter",
                                options=[{"label": "All Namespaces", "value": "all"}],
                                value="all"
                            )
                        ], width=4)
                    ], className="mb-3"),
                    html.Div(id="predicates-table")
                ])
            ])
        ])
    ])

def render_visualization():
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Schema Visualization"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dcc.Dropdown(
                                id="viz-group-selector",
                                options=[
                                    {"label": "All Elements", "value": "all"},
                                    {"label": "Domain Specific", "value": "domain_specific"}
                                ],
                                value="all"
                            )
                        ], width=4)
                    ], className="mb-3"),
                    dcc.Graph(id="network-graph", style={"height": "600px"})
                ])
            ])
        ])
    ])

# Callbacks for filtering
@app.callback(
    Output("classes-table", "children"),
    [Input("class-search", "value"),
     Input("class-namespace-filter", "value"),
     Input("interval-component", "n_intervals")]
)
def update_classes_table(search_term, namespace_filter, n_intervals):
    classes = schema_data.get('classes', {}).get('all', [])
    if not classes:
        return html.P("No classes data available")
    
    classes_df = pd.DataFrame(classes)
    classes_df['namespace'] = classes_df['uri'].apply(get_namespace_from_uri)
    classes_df['namespace_short'] = classes_df['namespace'].apply(get_namespace_short_name)
    
    # Apply filters
    if search_term:
        mask = classes_df['local_name'].str.contains(search_term, case=False, na=False) | \
               classes_df['uri'].str.contains(search_term, case=False, na=False)
        classes_df = classes_df[mask]
    
    if namespace_filter and namespace_filter != "all":
        classes_df = classes_df[classes_df['namespace'] == namespace_filter]
    
    return dash_table.DataTable(
        data=classes_df[['local_name', 'namespace_short', 'uri']].to_dict('records'),
        columns=[
            {"name": "Class Name", "id": "local_name"},
            {"name": "Namespace", "id": "namespace_short"},
            {"name": "URI", "id": "uri"}
        ],
        style_cell={'textAlign': 'left', 'fontSize': '12px'},
        style_data={'whiteSpace': 'normal', 'height': 'auto'},
        page_size=20
    )

@app.callback(
    Output("predicates-table", "children"),
    [Input("predicate-search", "value"),
     Input("predicate-namespace-filter", "value"),
     Input("interval-component", "n_intervals")]
)
def update_predicates_table(search_term, namespace_filter, n_intervals):
    predicates = schema_data.get('predicates', {}).get('domain_specific', [])
    if not predicates:
        return html.P("No predicates data available")
    
    predicates_df = pd.DataFrame(predicates)
    predicates_df['namespace'] = predicates_df['uri'].apply(get_namespace_from_uri)
    predicates_df['namespace_short'] = predicates_df['namespace'].apply(get_namespace_short_name)
    
    # Apply filters
    if search_term:
        mask = predicates_df['local_name'].str.contains(search_term, case=False, na=False) | \
               predicates_df['uri'].str.contains(search_term, case=False, na=False)
        predicates_df = predicates_df[mask]
    
    if namespace_filter and namespace_filter != "all":
        predicates_df = predicates_df[predicates_df['namespace'] == namespace_filter]
    
    return dash_table.DataTable(
        data=predicates_df[['local_name', 'namespace_short', 'uri']].to_dict('records'),
        columns=[
            {"name": "Predicate Name", "id": "local_name"},
            {"name": "Namespace", "id": "namespace_short"},
            {"name": "URI", "id": "uri"}
        ],
        style_cell={'textAlign': 'left', 'fontSize': '12px'},
        style_data={'whiteSpace': 'normal', 'height': 'auto'},
        page_size=20
    )

@app.callback(
    Output("network-graph", "figure"),
    [Input("viz-group-selector", "value"),
     Input("interval-component", "n_intervals")]
)
def update_network_graph(selected_group, n_intervals):
    G = create_network_graph(selected_group)
    traces = create_plotly_network(G)
    
    fig = go.Figure(data=traces,
                   layout=go.Layout(
                       title=f"Schema Network - {selected_group.replace('_', ' ').title()}",
                       titlefont_size=16,
                       showlegend=False,
                       hovermode='closest',
                       margin=dict(b=20,l=5,r=5,t=40),
                       annotations=[ dict(
                           text="Live data from SPARQL endpoint - Click and drag to explore",
                           showarrow=False,
                           xref="paper", yref="paper",
                           x=0.005, y=-0.002,
                           xanchor="left", yanchor="bottom",
                           font=dict(color="#888", size=12)
                       )],
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       plot_bgcolor='white'
                   ))
    
    return fig

if __name__ == "__main__":
    # Initial data fetch
    print("Performing initial data fetch...")
    update_schema_data()
    
    print("Starting ODISSEI Schema Visualizer with live data...")
    print("Open your browser and go to: http://localhost:8052")
    app.run_server(debug=True, host='0.0.0.0', port=8052)

