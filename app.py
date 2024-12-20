import streamlit as st
import google.generativeai as genai
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import re
import datetime
from markdown import Markdown

# Get API Key from environment variable
api_key = os.getenv("GEMINI_API_KEY")

# Check if the API key is found
if api_key is None:
    st.error("GEMINI_API_KEY environment variable not found.")
else:
    # Initialize the AI client
    genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat(
    history=[
        {"role": "user", "parts": "You are a programming assistant focused on providing \
                    accurate, clear, and concise answers to technical questions. \
                    Your goal is to help users solve programming problems efficiently, \
                    explain concepts clearly, and provide examples when appropriate. \
                    Use a professional yet approachable tone. Use explicit markdown \
                    format for code for all codes in the output."
        },
        {"role": "model", "parts": "Understood. Let me help you with that."},
    ]
)

def create_pdf(title, text_content):
    """
    Generates a PDF from the given text content with Markdown formatting using reportlab.

    Args:
        title (str): The title of the PDF.
        text_content (str): The Markdown-formatted text content to include in the PDF.

    Returns:
        io.BytesIO: A BytesIO object containing the generated PDF data.
    """
    # Create a buffer to hold the PDF data
    buffer = io.BytesIO()
    # Initialize the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Customize the Normal style
    normal_style = styles['Normal']
    normal_style.fontSize = 12
    normal_style.leading = 18
    normal_style.fontName = 'Helvetica'
    normal_style.alignment = 0

    # Create a custom style for code blocks
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=10,
        leading=14,
        backColor='#f0f0f0',
        borderColor='#d0d0d0',
        borderWidth=1,
        borderPadding=5,
        leftIndent=20,
        rightIndent=20,
        spaceBefore=10,
        spaceAfter=10
    )

    # Title style
    title_style = styles['Title']
    title_style.fontSize = 26
    title_style.fontName = 'Helvetica-Bold'
    title_style.spaceAfter = 20

    story = []

    # Add title
    story.append(Paragraph(title, title_style))

    # Convert markdown to HTML
    md = Markdown(extensions=['fenced_code', 'codehilite'])
    html = md.convert(text_content)
    
    # Remove problematic class attributes using regex
    html = re.sub(r'<(div|span) class="[^"]+">', r"<\1>", html) 

    # Split HTML into paragraphs and code blocks
    parts = html.split('```python')
    for part in parts:
        if part.strip().startswith('```python'):
            code_blocks = re.findall(r'```python(.*?)```', part, re.DOTALL)
            for code_content in code_blocks:
                story.append(Paragraph(code_content.strip(), code_style))
        else:
            paragraphs = part.split('</p>')
            for p in paragraphs:
                if p.strip():
                    paragraph_content = p.replace("<p>", "").strip()
                    paragraph_content = paragraph_content.replace("<strong>", "<b>").replace("</strong>", "</b>")
                    paragraph_content = paragraph_content.replace("<em>", "<i>").replace("</em>", "</i>")
                    story.append(Paragraph(paragraph_content, normal_style))
                    story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_ai_response(prompt):
    """Simulates generating a response from an AI model.

    Args:
    prompt: The prompt to send to the AI model.

    Returns:
    response from the AI model.
    """
    try:
        completion = chat.send_message(prompt, stream=True)

        # Extract and display the response
        response_container = st.empty()
        model_response=""
        for chunk in completion:
            if chunk.text is not None:
                model_response += chunk.text
                response_container.write(model_response)
            elif 'error' in chunk:
                st.error(f"Error occurred: {chunk['error']}")
                break        
        return model_response
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Define common programming tasks
programming_tasks = [
    "Write a function to reverse a string",
    "Create a class to represent a bank account",
    "Implement a binary search algorithm",
    "Write a script to scrape data from a website",
    "Create a function to validate an email address",
    "Implement a linked list data structure",
    "Write a program to find the factorial of a number",
    "Create a function to sort a list of numbers",
    "Implement a queue data structure",
    "Write a program to convert Celsius to Fahrenheit",
    "Create a recursive function to calculate Fibonacci numbers",
    "Write a function to check if a string is a palindrome",
    "Implement a stack data structure"
]

# Streamlit app
st.title("Gemini 1.5 Task Assistant")

# Task selection
selected_task = st.selectbox("Select a programming task:", programming_tasks)

# Task details input
task_details = st.text_area("Provide more details about the task (such as use Streamlit or Gradio):", height=150)

# Generate response button
if st.button("Get Response"):
    if not task_details:
        st.warning("Please provide details about the task.")
    else:
        # Construct the prompt
        prompt = f"Programming Task: {selected_task}\nDetails: {task_details}"

        with st.spinner("Thinking..."):
            response = generate_ai_response(prompt)

            # st.write(response)
        st.success("Response generated successfully.")

        if response:
            pdf_buffer = create_pdf(selected_task, response)

            # Generate filename with current timestamp
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output_{current_time}.pdf"

            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name=filename,
                mime="application/pdf"
            )
        else:
            st.warning("No data was passed to generate a PDF.")
