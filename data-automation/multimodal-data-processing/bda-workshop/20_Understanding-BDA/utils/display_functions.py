import ipywidgets as widgets
from IPython.display import display, HTML
import pandas as pd
from PIL import Image
import io
import boto3
import json


onclick_function = """
<script>
    function handleClick(event) {
    
        var row = event.target
        row.style.backgroundColor = '#e0e0e0';
        if (!row) return;  // Click wasn't on a row
        
        // Get the bbox data from the row
        var bbox = row.getAttribute('data-bbox');
        if (!bbox) return;  // No bbox data found
        
        // Parse the bbox string back to array
        bbox = JSON.parse(bbox);
        
        // Send custom event to Python
        var event = new CustomEvent('bbox_click', { detail: bbox });
        document.dispatchEvent(event);
        
        // Highlight the clicked row
        var rows = document.getElementsByClassName('bbox-row');
        for(var i = 0; i < rows.length; i++) {
            rows[i].style.backgroundColor = '#f8f8f8';
        }
        row.style.backgroundColor = '#e0e0e0';
    }
</script>
"""

def load_image(image_path):
    # Open the image
    img = Image.open(image_path)
    
    # Convert to JPEG if it's not already
    if img.format != 'JPEG':
        # Create a byte stream
        buf = io.BytesIO()
        # Save as JPEG to the byte stream
        img.save(buf, format='JPEG')
        # Get the byte value
        image_bytes = buf.getvalue()
    else:
        # If already JPEG, read directly
        with open(image_path, 'rb') as file:
            image_bytes = file.read()
    
    return image_bytes

def get_kv_html(kv_pairs):
    # Create key-value pairs display
    kv_html = onclick_function
    kv_html += """
    <div style="border: 0px solid #ddd; padding: 10px; margin: 1px; overflow-y: auto;">        
        <table style="width: 100%; border: 0px solid #888; border-collapse: separate; border-spacing: 1 1px;">
            <style>
                td {
                    padding: 2px 2px;
                    border: 0px solid #ddd; 
                }
            </style>
    """
    
    for i, (key, (value, confidence)) in enumerate(kv_pairs.items()):
        kv_html += '<tr onclick=handleClick(event) data-bbox=\'(10,40,110,200)\'><td width=100%>'
        kv_html += create_key_value_box(key, value, confidence)
        kv_html += '</td></tr>'
    kv_html += """
        </table>
    </div>
    """
    return kv_html

def create_key_value_box(key, value, confidence):
    html = f"""
       <div style="
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 2px;
            margin: 2px 1;
            background-color: #f8f9fa;
            width: 100%;
            max-width: 100%;
            font-family: sans-serif;"
        >
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0px;
        ">
            <div style="font-weight: 600; font-size: 0.9em; color: #333;">{key}</div>
            <div style="
                background-color: #fff;
                padding: 2px 4px;
                border-radius: 4px;
                font-size: 0.9em;
                color: #666;
            ">{confidence}</div>
        </div>
        <div style="color: #666; font-size: 0.9em">{value}</div>
    </div>
    """
    return html
    
def display_result(document_image_uri, kvpairs):
    # Create the layout with top alignment
    main_hbox_layout = widgets.Layout(
        width='100%',
        display='flex',
        flex_flow='row nowrap',
        align_items='stretch',
        margin='0'
    )

    image_widget = widgets.Image(
        value=b'',
        format='png',
        width='auto',
        height='auto'
    )
    image_widget.value = load_image(image_path=document_image_uri)
    image_container = widgets.Box(
        children=[image_widget],
        layout=widgets.Layout(
            border='1px solid #888',
            padding='1px',
            margin='2px',
            width='70%',
            flex='0 0 70%',
            min_width='300px',
            height='auto',
            display='flex',
            align_items='stretch',
            justify_content='center'
        )
    )
    kv_html = get_kv_html(kvpairs)
    # Add content to the Forms tab
    header_widget = widgets.HTML(
        value="<h3>Key Value Pairs</h3>",
        layout=widgets.Layout(
            width='100%',          # Set to 30% of available space
            border='1px solid #888',            
            padding='1px',
            margin='1px',
            min_width='300px',     # Minimum width
            justify_content='center'
        ))
    
    result_widget = widgets.HTML(
        value=kv_html,
        layout=widgets.Layout(
            border='0px solid #888',            
            width='100%', 
            height='10px',
            flex='0 0 100%',       # flex: grow shrink basis
            margin='5px',
            min_width='300px'
        )
    )
    result_container = widgets.VBox(
        children=[result_widget],
        layout=widgets.Layout(
            border='0px solid #888',
            padding='4px',
            margin='5px',
            width='30%',
            flex='0 0 30%',
            min_width='200px',
            justify_content='center'
        )
    )
    # Add custom CSS for scrollable container
    custom_style = """
    <style>
        .scrollable-vbox {
            max-height: 1000px;
            overflow-y: auto;
            overflow-x: hidden;
        }
        .main-container {
            display: flex;
            height: 1000px;  /* Match with max-height above */
        }
    </style>
    """
    display(HTML(custom_style))
    # Create the main layout
    main_layout = widgets.HBox(
        children=[image_container, result_container],
        layout=main_hbox_layout
    )
    # Add the scrollable class to the right VBox
    result_widget.add_class('scrollable-vbox')
    main_layout.add_class('main-container')
    # Display the main layout
    display(main_layout)