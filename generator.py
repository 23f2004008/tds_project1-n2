# generator.py
import os
import re
from openai import OpenAI

def generate_app_files(brief_text, output_folder):
    """
    Uses GPT to generate separate HTML, CSS, and JS files based on the given brief text.
    """

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    print("🧠 Generating code with GPT...")

    prompt = f"""
    You are a coding assistant that must output three distinct files for a minimal web app.
    Based on this user brief:

    {brief_text}

    Please return your answer in this exact format:

    <HTML>
    (contents of index.html)
    </HTML>

    <CSS>
    (contents of style.css)
    </CSS>

    <JS>
    (contents of script.js)
    </JS>

    Make sure the HTML links to style.css and script.js correctly.
    Do NOT include explanations, only the 3 file contents wrapped in these tags.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert web app generator that returns well-structured code."},
            {"role": "user", "content": prompt},
        ]
    )

    generated = response.choices[0].message.content

    # Extract sections
    html_match = re.search(r"<HTML>(.*?)</HTML>", generated, re.DOTALL | re.IGNORECASE)
    css_match  = re.search(r"<CSS>(.*?)</CSS>", generated, re.DOTALL | re.IGNORECASE)
    js_match   = re.search(r"<JS>(.*?)</JS>", generated, re.DOTALL | re.IGNORECASE)

    html_code = html_match.group(1).strip() if html_match else "<h1>Hello World</h1>"
    css_code  = css_match.group(1).strip() if css_match else "body { background: #f9f9f9; }"
    js_code   = js_match.group(1).strip() if js_match else "console.log('JS loaded');"

    # Save the files
    with open(os.path.join(output_folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_code)

    with open(os.path.join(output_folder, "style.css"), "w", encoding="utf-8") as f:
        f.write(css_code)

    with open(os.path.join(output_folder, "script.js"), "w", encoding="utf-8") as f:
        f.write(js_code)

    print("✅ index.html, style.css, and script.js created successfully in", output_folder)
