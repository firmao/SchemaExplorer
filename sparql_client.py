import requests
import json
import logging
from typing import Dict, List, Optional
from urllib.parse import quote

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SPARQLClient:
    """Client for querying the ODISSEI SPARQL endpoint"""
    
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ODISSEI-Schema-Visualizer/1.0',
            'Accept': 'application/json'
        })
    
    def execute_query(self, query: str) -> Optional[Dict]:
        """Execute a SPARQL query and return the results"""
        try:
            # URL encode the query
            encoded_query = quote(query)
            url = f"{self.endpoint_url}?query={encoded_query}"
            
            logger.info(f"Executing SPARQL query: {query[:100]}...")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Try to parse as JSON
            try:
                return response.json()
            except json.JSONDecodeError:
                # If not JSON, return the text content
                logger.warning("Response is not valid JSON, returning text")
                return {"results": {"bindings": []}}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error executing SPARQL query: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def get_distinct_predicates(self, limit: int = 100) -> List[Dict[str, str]]:
        """Get distinct predicates from the endpoint"""
        query = f"SELECT DISTINCT ?p WHERE {{?s ?p ?o}} LIMIT {limit}"
        
        result = self.execute_query(query)
        if not result:
            return []
        
        predicates = []
        try:
            # Handle different response formats
            if isinstance(result, list):
                # Direct list format
                for item in result:
                    if 'p' in item:
                        predicates.append({
                            'uri': item['p'],
                            'local_name': self._extract_local_name(item['p'])
                        })
            elif isinstance(result, dict) and 'results' in result:
                # SPARQL JSON format
                for binding in result['results'].get('bindings', []):
                    if 'p' in binding:
                        uri = binding['p'].get('value', binding['p'])
                        predicates.append({
                            'uri': uri,
                            'local_name': self._extract_local_name(uri)
                        })
            else:
                logger.warning(f"Unexpected result format: {type(result)}")
                
        except Exception as e:
            logger.error(f"Error parsing predicates: {e}")
        
        return predicates
    
    def get_distinct_classes(self, limit: int = 100) -> List[Dict[str, str]]:
        """Get distinct classes from the endpoint"""
        query = f"SELECT DISTINCT ?type WHERE {{?s a ?type}} LIMIT {limit}"
        
        result = self.execute_query(query)
        if not result:
            return []
        
        classes = []
        try:
            # Handle different response formats
            if isinstance(result, list):
                # Direct list format
                for item in result:
                    if 'type' in item:
                        classes.append({
                            'uri': item['type'],
                            'local_name': self._extract_local_name(item['type'])
                        })
            elif isinstance(result, dict) and 'results' in result:
                # SPARQL JSON format
                for binding in result['results'].get('bindings', []):
                    if 'type' in binding:
                        uri = binding['type'].get('value', binding['type'])
                        classes.append({
                            'uri': uri,
                            'local_name': self._extract_local_name(uri)
                        })
            else:
                logger.warning(f"Unexpected result format: {type(result)}")
                
        except Exception as e:
            logger.error(f"Error parsing classes: {e}")
        
        return classes
    
    def _extract_local_name(self, uri: str) -> str:
        """Extract local name from URI"""
        if '#' in uri:
            return uri.split('#')[-1]
        else:
            return uri.split('/')[-1]
    
    def get_namespace_from_uri(self, uri: str) -> str:
        """Extract namespace from URI"""
        if '#' in uri:
            return uri.split('#')[0] + '#'
        else:
            parts = uri.split('/')
            return '/'.join(parts[:-1]) + '/'
    
    def fetch_schema_data(self) -> Dict:
        """Fetch complete schema data from the endpoint"""
        logger.info("Fetching schema data from SPARQL endpoint...")
        
        # Get predicates and classes
        predicates = self.get_distinct_predicates(100)
        classes = self.get_distinct_classes(100)
        
        # Process the data
        all_namespaces = set()
        odissei_namespaces = []
        dataverse_namespaces = []
        domain_specific_predicates = []
        domain_specific_classes = []
        
        # Process predicates
        for pred in predicates:
            namespace = self.get_namespace_from_uri(pred['uri'])
            all_namespaces.add(namespace)
            
            # Filter domain-specific predicates
            if any(domain in namespace.lower() for domain in ['odissei', 'dataverse']):
                domain_specific_predicates.append(pred)
                
                if 'odissei' in namespace.lower():
                    if namespace not in odissei_namespaces:
                        odissei_namespaces.append(namespace)
                elif 'dataverse' in namespace.lower():
                    if namespace not in dataverse_namespaces:
                        dataverse_namespaces.append(namespace)
        
        # Process classes
        for cls in classes:
            namespace = self.get_namespace_from_uri(cls['uri'])
            all_namespaces.add(namespace)
            
            # Filter domain-specific classes
            if any(domain in namespace.lower() for domain in ['odissei', 'dataverse', 'w3id.org', 'foaf']):
                domain_specific_classes.append(cls)
        
        # Create schema data structure
        schema_data = {
            "metadata": {
                "title": "ODISSEI Knowledge Graph Schema",
                "description": "RDF Schema extracted from the ODISSEI SPARQL endpoint",
                "endpoint": self.endpoint_url,
                "total_classes": len(classes),
                "total_predicates": len(predicates),
                "domain_specific_classes": len(domain_specific_classes),
                "domain_specific_predicates": len(domain_specific_predicates),
                "last_updated": None  # Will be set by the calling code
            },
            "namespaces": {
                "odissei_namespaces": odissei_namespaces,
                "dataverse_namespaces": dataverse_namespaces,
                "all_namespaces": list(all_namespaces)
            },
            "classes": {
                "all": classes,
                "domain_specific": domain_specific_classes
            },
            "predicates": {
                "all": predicates,
                "domain_specific": domain_specific_predicates
            }
        }
        
        logger.info(f"Fetched {len(classes)} classes and {len(predicates)} predicates")
        return schema_data

# Test the client
if __name__ == "__main__":
    client = SPARQLClient("https://api.kg.odissei.nl/datasets/odissei/odissei-kg-acceptance/services/odissei-kg-acceptance-virtuoso/sparql")
    
    # Test predicates query
    predicates = client.get_distinct_predicates(10)
    print(f"Found {len(predicates)} predicates")
    for pred in predicates[:5]:
        print(f"  - {pred['local_name']}: {pred['uri']}")
    
    # Test classes query
    classes = client.get_distinct_classes(10)
    print(f"Found {len(classes)} classes")
    for cls in classes[:5]:
        print(f"  - {cls['local_name']}: {cls['uri']}")

