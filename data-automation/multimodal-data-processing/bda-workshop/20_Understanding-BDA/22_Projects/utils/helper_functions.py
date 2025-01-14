import time
import boto3
from urllib.parse import urlparse
import requests
import io
from PyPDF2 import PdfReader, PdfWriter
from botocore.exceptions import ClientError
from IPython.display import HTML


bda_client = boto3.client('bedrock-data-automation')
bda_runtime_client = boto3.client('bedrock-data-automation-runtime')


def get_bucket_and_key(s3_uri):
    parsed_uri = urlparse(s3_uri)
    bucket_name = parsed_uri.netloc
    object_key = parsed_uri.path.lstrip('/')
    return (bucket_name, object_key)


def wait_for_job_to_complete(invocationArn):
    get_status_response = bda_runtime_client.get_data_automation_status(
         invocationArn=invocationArn)
    status = get_status_response['status']
    job_id = invocationArn.split('/')[-1]
    max_iterations = 60
    iteration_count = 0
    while status not in ['Success', 'ServiceError', 'ClientError']:
        print(f'Waiting for Job to Complete. Current status is {status}')
        time.sleep(10)
        iteration_count += 1
        if iteration_count >= max_iterations:
            print(f"Maximum number of iterations ({max_iterations}) reached. Breaking the loop.")
            break
        get_status_response = bda_runtime_client.get_data_automation_status(
         invocationArn=invocationArn)
        status = get_status_response['status']
    if iteration_count >= max_iterations:
        raise Exception("Job did not complete within the expected time frame.")
    else:
        print(f"Invocation Job with id {job_id} completed. Status is {status}")
    return get_status_response


def read_s3_object(s3_uri):
    # Parse the S3 URI
    parsed_uri = urlparse(s3_uri)
    bucket_name = parsed_uri.netloc
    object_key = parsed_uri.path.lstrip('/')
    # Create an S3 client
    s3_client = boto3.client('s3')
    try:
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        
        # Read the content of the object
        content = response['Body'].read().decode('utf-8')
        return content
    except Exception as e:
        print(f"Error reading S3 object: {e}")
        return None


def create_sample_file(url, start_page_index, end_page_index, output_file_path):

    # Download the PDF
    response = requests.get(url)
    pdf_content = io.BytesIO(response.content)

    # Create a PDF reader object
    pdf_reader = PdfReader(pdf_content)

    # Create a PDF writer object
    pdf_writer = PdfWriter()

    start_page_index = max(start_page_index, 0)
    end_page_index = min(end_page_index, len(pdf_reader.pages)-1)

    # Specify the pages you want to extract (0-indexed)
    pages_to_extract = list(range(start_page_index, end_page_index))

    # Add the specified pages to the writer
    for page_num in pages_to_extract:
        page = pdf_reader.pages[page_num]
        pdf_writer.add_page(page)

    # Save the extracted pages to a new PDF
    with open(output_file_path, "wb") as output_file:
        pdf_writer.write(output_file)


def get_nested_value(data, path):
    """
    Retrieve a value from a nested dictionary using a dot-separated path.

    :param data: The dictionary to search
    :param path: A string representing the path to the value, e.g., "Job.Status"
    :return: The value at the specified path, or None if not found
    """
    keys = path.split('.')
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data


def display_html(data, root='root', expanded=True, bg_color='#f0f0f0'):
    html = f"""
        <div class="custom-json-output" style="background-color: {bg_color}; padding: 10px; border-radius: 5px;">
            <button class="toggle-btn" style="margin-bottom: 10px;">{'Collapse' if expanded else 'Expand'}</button>
            <pre class="json-content" style="display: {'block' if expanded else 'none'};">{data}</pre>
        </div>
        
        <script>
        (function() {{
            var toggleBtn = document.currentScript.previousElementSibling.querySelector('.toggle-btn');
            var jsonContent = document.currentScript.previousElementSibling.querySelector('.json-content');
            
            toggleBtn.addEventListener('click', function() {{
                if (jsonContent.style.display === 'none') {{
                    jsonContent.style.display = 'block';
                    toggleBtn.textContent = 'Collapse';
                }} else {{
                    jsonContent.style.display = 'none';
                    toggleBtn.textContent = 'Expand';
                }}
            }});
        }})();
        </script>
        """
    display(HTML(html))


def wait_for_completion(
    client,
    get_status_function,
    status_kwargs,
    status_path_in_response,
    completion_states,
    error_states,
    max_iterations=60,
    delay=10
):
    """
    Generic function to wait for a boto3 BDA operation to complete.

    :param client: boto3 client instance
    :param get_status_function: Function to call to get the status (e.g., get_job_status)
    :param resource_arn: ARN of the resource to check
    :param completion_states: List of states indicating successful completion
    :param error_states: List of states indicating an error
    :param max_iterations: Maximum number of status checks before giving up
    :param delay: Time in seconds to wait between status checks
    :return: The final status of the resource
    :raises: Exception if the operation fails or exceeds max_iterations
    """
    for _ in range(max_iterations):
        try:
            response = get_status_function(**status_kwargs)
            status = get_nested_value(response, status_path_in_response)

            if status in completion_states:
                print(f"Operation completed successfully with status: {status}")
                return response

            if status in error_states:
                raise Exception(f"Operation failed with status: {status}")

            print(f"Current status: {status}. Waiting...")
            time.sleep(delay)

        except ClientError as e:
            raise Exception(f"Error checking status: {str(e)}")

    raise Exception(f"Operation timed out after {max_iterations} iterations")
