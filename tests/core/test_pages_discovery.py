#!/usr/bin/env python3

import dash
from dash import Dash

def test_pages_discovery():
    app = Dash(__name__, use_pages=True)
    print(f'Pages discovered: {len(dash.page_registry)}')
    
    if dash.page_registry:
        print('Registered pages:')
        for path, info in dash.page_registry.items():
            print(f'  {path}: {info.get("title", "No title")}')
    else:
        print('No pages discovered!')
        
    return app

if __name__ == "__main__":
    test_pages_discovery()
