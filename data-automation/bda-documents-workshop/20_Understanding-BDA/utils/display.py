import ipywidgets as widgets
from IPython.display import display, HTML
from PIL import Image
import io
import pandas as pd


def get_summaries(custom_outputs):
    custom_output_summaries = []
    for custom_output in custom_outputs:
        custom_output_summary = {}
        if custom_output:
            custom_output_summary = {
                'page_indices': custom_output.get('split_document', {}).get('page_indices', None),
                'matched_blueprint_name': custom_output.get('matched_blueprint', {}).get('name', None),
                'confidence': custom_output.get('matched_blueprint', {}).get('confidence', None),
                'document_class_type': custom_output.get('document_class', {}).get('type', None),
                #'matched_blueprint_arn': custom_output.get('matched_blueprint', {}).get('arn', None)
            }
        else:
            custom_output_summary = {}
        custom_output_summaries += [custom_output_summary]
    return custom_output_summaries


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

def onclick_function():
    return """
        <script>
            function handleClick(event) {
                var row = event.target;
                if (!row) return;  // Click wasn't on a row

                // Get the bbox data from the row
                var bbox = row.getAttribute('data-bbox');
                if (!bbox) return;  // No bbox data found
                row.style.backgroundColor = '#ffe0e0';
                
                // Parse the bbox string back to array
                //bbox = JSON.parse(bbox);
                row.style.backgroundColor = '#fff0f0';

                // Send custom event to Python
                var event = new CustomEvent('bbox_click', { detail: bbox });
                document.dispatchEvent(event);
                row.style.backgroundColor = '#ffe0e0';
                
                
                // First, reset all rows to default background
                var rows = document.getElementsByClassName('kc-item');
                for(var i = 0; i < rows.length; i++) {
                    rows[i].style.backgroundColor = '#f8f8f8';
                }
                
                // Then highlight only the clicked row
                row.style.backgroundColor = '#e0e0e0';
            }
        </script>
    """

def create_form_view(forms_data):
    """Create a formatted view for key-value pairs with nested dictionary support"""
    html_content = """
    <style>
        .kv-container {
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin: 4px;
            width: 100%;
        }    
        .kv-box {
            border: 0px solid #e0e0e0;
            border-radius: 4px;
            padding: 4px;
            margin: 0;
            background-color: #f8f9fa;
            width: auto;
        }
        .kv-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2px;
        }
        .kc-item {
            background-color: #fff;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2px;
        }
        .key {
            font-weight: 600; 
            padding: 1px 4px;
            font-size: 0.85em; 
            color: #333;
        }
        .value {
            background-color: #fff;
            padding: 1px 4px;
            border-radius: 4px;
            font-size: 0.85em;
            color: #666;
            margin-top: 1px;
        }
        .confidence {
            padding: 1px 4px;
            border-radius: 4px;
            font-size: 0.85em;
            color: #2196F3;        
        }
        .nested-container {
            margin-left: 8px;
            margin-top: 4px;
            border-left: 2px solid #e0e0e0;
            padding-left: 4px;
        }
        .parent-key {
            color: #6a1b9a;
            font-size: 0.9em;
            font-weight: 600;
            margin-bottom: 2px;
        }
    </style>       
    """

    html_content += onclick_function()
    html_content += '<div class="kv-container">'

    def render_nested_dict(data, level=0):
        nested_html = ""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    confidence = value.get('confidence', 0) * 100
                    if 'value' in value:
                        # Handle standard key-value pair with confidence
                        nested_html += f"""
                            <div class='kv-box'>
                                <div class='kv-item'>
                                    <div class='key'>{key}</div>
                                </div>
                                <div class='kc-item' onclick=handleClick(event) data-bbox='(10,40,110,200)'>
                                    <div class="value" >{value['value']}</div>
                                    <div class='confidence'>{confidence:.1f}%</div>
                                </div>
                            </div>
                        """
                    else:
                        # Handle nested dictionary
                        nested_html += f"""
                            <div class='kv-box'>
                                <div class='kv-item'>
                                    <div class='key'>{key}</div>
                                </div>
                                <div class="nested-container">
                                    {render_nested_dict(value, level + 1)}
                                </div>
                            </div>
                        """
                else:
                    # Handle direct key-value pairs without confidence
                    nested_html += f"""
                        <div class='kv-box'>
                            <div class='kv-item'>
                                <div class='key'>{key}</div>
                            </div>
                            <div class="value">{value}</div>
                        </div>
                    """
        return nested_html

    html_content += render_nested_dict(forms_data)
    html_content += "</div>"
    
    return HTML(html_content)




def create_table_view(tables_data):
    """Create a formatted view for tables"""
    html_content = """
    <style>
        .table-container {
            margin: 20px;
        }
        .table-view {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
        }
        .table-view th {
            background-color: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-size: 0.85em;
            border: 1px solid #dee2e6;
        }
        .table-view td {
            padding: 12px;
            border: 1px solid #dee2e6;
            font-size: 0.8em;
        }
    </style>
    """
    
    for table_name, table_data in tables_data.items():
        if table_data:
            df = pd.DataFrame(table_data)
            html_content += f"""
            <div class="table-container">
                <h3>{table_name}</h3>
                {df.to_html(classes='table-view', index=False)}
            </div>
            """
    
    return HTML(html_content)


def segment_view(document_image_uri, inference_result):
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
            width='60%',
            flex='0 0 60%',
            min_width='300px',
            height='auto',
            display='flex',
            align_items='stretch',
            justify_content='center'
        )
    )
    
    
    # Create tabs for different views
    tab = widgets.Tab(
        layout=widgets.Layout(
            width='40%',
            flex='0 0 40%',
            min_width='300px',
            height='auto'
        )
    )
    form_view = widgets.Output()
    table_view = widgets.Output()
    
    with form_view:
        display(create_form_view(inference_result['forms']))
        
    with table_view:
        display(create_table_view(inference_result['tables']))
    
    tab.children = [form_view, table_view]
    tab.set_title(0, 'Key Value Pairs')
    tab.set_title(1, 'Tables')

    
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
        children=[image_container, tab],
        layout=main_hbox_layout
    )

    
    # Add the scrollable class to the right VBox
    main_layout.add_class('main-container')
    return main_layout


def display_multiple(views):
    main_tab = widgets.Tab()
    for i, view in enumerate(views):
        main_tab.children = (*main_tab.children, view)
        main_tab.set_title(i, f'Document {i}')
    display(main_tab)