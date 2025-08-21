import json
import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import networkx as nx
from urllib.parse import urlparse
import math

# Load schema data
with open('odissei_schema_processed.json', 'r') as f:
    schema_data = json.load(f)

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "ODISSEI Schema Visualizer - Python Edition"

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

# Create network graph data
def create_network_graph(selected_group='all'):
    G = nx.Graph()
    
    # Filter data based on selection
    if selected_group == 'all':
        classes = schema_data['classes']['all'][:30]  # Limit for performance
        predicates = schema_data['predicates']['domain_specific'][:20]
    elif selected_group == 'domain_specific':
        classes = schema_data['classes']['domain_specific']
        predicates = schema_data['predicates']['domain_specific'][:15]
    else:
        # Filter by namespace
        classes = [cls for cls in schema_data['classes']['all'] 
                  if get_namespace_from_uri(cls['uri']) == selected_group][:20]
        predicates = [pred for pred in schema_data['predicates']['domain_specific'] 
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
    
    # Add some sample edges (in a real implementation, you'd query for actual relationships)
    nodes = list(G.nodes())
    for i in range(min(len(nodes) - 1, 25)):
        if i % 3 == 0:  # Add some edges
            G.add_edge(nodes[i], nodes[i + 1])
    
    return G

def create_plotly_network(G):
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
    dbc.Row([
        dbc.Col([
            html.H1("ODISSEI Knowledge Graph Schema Explorer", 
                   className="text-center mb-4"),
            html.P("Python-based interactive visualization of the RDF schema from the ODISSEI SPARQL endpoint.",
                   className="text-center text-muted mb-4")
        ])
    ]),
    
    # Statistics cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(str(schema_data['metadata']['total_classes']), className="card-title"),
                    html.P("Total Classes", className="card-text")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(str(schema_data['metadata']['total_predicates']), className="card-title"),
                    html.P("Total Predicates", className="card-text")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(str(len(schema_data['namespaces']['odissei_namespaces'])), className="card-title"),
                    html.P("ODISSEI Namespaces", className="card-text")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(str(schema_data['metadata']['domain_specific_predicates']), className="card-title"),
                    html.P("Domain Predicates", className="card-text")
                ])
            ])
        ], width=3)
    ], className="mb-4"),
    
    # Tabs
    dbc.Tabs([
        dbc.Tab(label="Overview", tab_id="overview"),
        dbc.Tab(label="Classes", tab_id="classes"),
        dbc.Tab(label="Predicates", tab_id="predicates"),
        dbc.Tab(label="Visualization", tab_id="visualization")
    ], id="tabs", active_tab="overview"),
    
    html.Div(id="tab-content", className="mt-4")
], fluid=True)

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
                                ]) for ns in schema_data['namespaces']['odissei_namespaces']
                            ])
                        ], width=6),
                        dbc.Col([
                            html.H5("Dataverse Namespaces"),
                            html.Ul([
                                html.Li([
                                    html.Span("●", style={"color": get_color_for_namespace(ns), "margin-right": "8px"}),
                                    get_namespace_short_name(ns)
                                ]) for ns in schema_data['namespaces']['dataverse_namespaces']
                            ])
                        ], width=6)
                    ])
                ])
            ])
        ])
    ])

def render_classes():
    # Create DataFrame for classes
    classes_df = pd.DataFrame(schema_data['classes']['all'])
    classes_df['namespace'] = classes_df['uri'].apply(get_namespace_from_uri)
    classes_df['namespace_short'] = classes_df['namespace'].apply(get_namespace_short_name)
    
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
                                options=[{"label": "All Namespaces", "value": "all"}] + 
                                       [{"label": get_namespace_short_name(ns), "value": ns} 
                                        for ns in set(classes_df['namespace'])],
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
    # Create DataFrame for predicates
    predicates_df = pd.DataFrame(schema_data['predicates']['domain_specific'])
    predicates_df['namespace'] = predicates_df['uri'].apply(get_namespace_from_uri)
    predicates_df['namespace_short'] = predicates_df['namespace'].apply(get_namespace_short_name)
    
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
                                options=[{"label": "All Namespaces", "value": "all"}] + 
                                       [{"label": get_namespace_short_name(ns), "value": ns} 
                                        for ns in set(predicates_df['namespace'])],
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
                                ] + [{"label": get_namespace_short_name(ns), "value": ns} 
                                     for ns in schema_data['namespaces']['odissei_namespaces'] + 
                                               schema_data['namespaces']['dataverse_namespaces']],
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
     Input("class-namespace-filter", "value")]
)
def update_classes_table(search_term, namespace_filter):
    classes_df = pd.DataFrame(schema_data['classes']['all'])
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
     Input("predicate-namespace-filter", "value")]
)
def update_predicates_table(search_term, namespace_filter):
    predicates_df = pd.DataFrame(schema_data['predicates']['domain_specific'])
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
    Input("viz-group-selector", "value")
)
def update_network_graph(selected_group):
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
                           text="Click and drag to explore the network",
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
    app.run_server(debug=True, host='0.0.0.0', port=8050)

