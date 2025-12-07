import os, re, json, xml.etree.ElementTree as ET
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from openai import OpenAI
# from dotenv import load_dotenv

#load_dotenv()

# ---------- Configuration ----------
app = Flask(__name__)
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Read the key from the environment variable (Render, Heroku, etc.)
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_KEY:
    # This check runs both locally (if not in .env) and on the server (if not set)
    print("ERROR: OPENAI_API_KEY not found in environment variables!")
    # Depending on how critical the key is, you might exit the app here:
    # exit(1) 
    
# Initialize the OpenAI client using the key from the environment
client = OpenAI(api_key=OPENAI_KEY)


MODEL_FOR_PLAN = "gpt-4o-mini"
MODEL_FOR_XML  = "gpt-4o-mini"

# ---------- Helpers ----------
def clean_model_xml(s: str) -> str:
    """Strip code fences and keep the first <mxfile>...</mxfile> block."""
    s = s.strip()
    # Remove any markdown code fences
    if '```' in s:
        s = re.sub(r'```(?:xml)?', '', s, flags=re.IGNORECASE)
        s = re.sub(r'```', '', s)
    # Remove any comments
    s = re.sub(r'<!--.*?-->', '', s, flags=re.DOTALL)
    s = s.strip()
    
    # Find the mxfile block
    start = s.find('<mxfile')
    end = s.find('</mxfile>')
    
    if start != -1 and end != -1:
        return s[start:end+9].strip()
    
    # If we still have what looks like valid XML, return it
    if s.startswith('<mxfile'):
        return s
    
    # Last resort - try regex
    m = re.search(r'<mxfile.*?</mxfile>', s, re.DOTALL)
    return m.group(0).strip() if m else s

def sanity_check_drawio(xml: str):
    """Basic validation to ensure XML structure is correct."""
    try:
        root = ET.fromstring(xml)
        if root.tag != "mxfile":
            raise ValueError("Root must be <mxfile>")
    except Exception as e:
        raise AssertionError(f"XML parse error: {e}")

def prompt_for_plan(instruction: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_FOR_PLAN,
        messages=[
            {"role": "system", "content": "You are an expert solution architect."},
            {"role": "user", "content": f"""Create a flowchart plan for: "{instruction}".
            
            Output ONLY this format:
            NODES:
            - [ID] Label (Type: Start, Process, Decision, or End)
            EDGES:
            - ID -> ID : Label
            
            Keep IDs short (A, B, C). Keep labels concise."""}
        ],
        temperature=0.2,
        max_tokens=1000,
    )
    return response.choices[0].message.content

def prompt_for_xml(plan_text: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_FOR_XML,
        messages=[
            {"role": "system", "content": "You are an expert at generating Draw.io XML. Output ONLY raw XML without any markdown or explanations."},
            {"role": "user", "content": f"""Generate a complete diagrams.net/draw.io XML for this flowchart plan:

{plan_text}

Strict requirements:
- Output ONLY one <mxfile>...</mxfile> string. No markdown, no commentary, no code fences.
- Use this skeleton (do not reorder the first two cells):
  <mxfile><diagram><mxGraphModel><root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- ADD ALL NODES AND EDGES HERE -->
  </root></mxGraphModel></diagram></mxfile>
  
- Each node (vertex) must look like:
  <mxCell id="A" value="Label" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#36393d;shadow=1;" vertex="1" parent="1">
    <mxGeometry x="[number]" y="[number]" width="120" height="50" as="geometry"/>
  </mxCell>
  
- **CRITICAL**: For **Decision** nodes (usually diamond shape and short label), use this style for contrast:
  <mxCell id="B" value="Decision" style="rhombus;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontColor=#36393d;shadow=1;" vertex="1" parent="1">
    <mxGeometry x="[number]" y="[number]" width="100" height="100" as="geometry"/>
  </mxCell>
  
- Each edge must look like (use thicker stroke and a clear arrow):
  <mxCell id="e1" value="yes" edge="1" parent="1" source="A" target="B" style="endArrow=block;strokeWidth=2;strokeColor=#404040;">
    <mxGeometry relative="1" as="geometry"/>
  </mxCell>
  
- All ids unique; every edge's source/target id must exist; escape &, <, > in labels.
- Layout for **Organization** and **Readability**: Arrange shapes in a clear, consistent flow (e.g., top-to-bottom or left-to-right) with adequate spacing. **Do not overlap components.**
- Position nodes: Start at x="350" y="20", increment y by 120 for each level
- IDs: Use the exact IDs from the plan (e.g., A, B, C) for nodes, and e1, e2, e3 for edges

OUTPUT ONLY THE XML STRING, NOTHING ELSE."""}
        ],
        temperature=0.15,
        max_tokens=4000,
    )
    return response.choices[0].message.content

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/static/css/main.css')
def serve_css():
    css_content = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    .app-container { display: flex; height: 100vh; }
    .sidebar { width: 350px; background: #f7f8fa; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; }
    .sidebar-header { padding: 20px; border-bottom: 1px solid #e0e0e0; }
    .brand { font-size: 18px; font-weight: 600; display: flex; align-items: center; }
    .dot { width: 10px; height: 10px; background: #10b981; border-radius: 50%; margin-right: 8px; }
    .sidebar-content { flex: 1; padding: 20px; overflow-y: auto; }
    .step { margin-bottom: 25px; }
    .step label { display: block; margin-bottom: 8px; font-weight: 500; color: #374151; }
    textarea { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; resize: vertical; }
    .mono { font-family: 'Courier New', monospace; font-size: 12px; }
    .btn-group { display: flex; gap: 10px; }
    .btn { padding: 10px 16px; border: none; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-primary { background: #3b82f6; color: white; }
    .btn-primary:hover:not(:disabled) { background: #2563eb; }
    .btn-secondary { background: #6b7280; color: white; }
    .btn-secondary:hover:not(:disabled) { background: #4b5563; }
    .btn-success { background: #10b981; color: white; }
    .btn-success:hover:not(:disabled) { background: #059669; }
    .status-bar { padding: 12px 20px; background: #1f2937; color: white; font-size: 13px; }
    .main-view { flex: 1; position: relative; background: #fff; }
    #drawio-frame { width: 100%; height: 100%; border: none; }
    .overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.9); display: none; align-items: center; justify-content: center; z-index: 100; }
    .overlay.active { display: flex; }
    .spinner { width: 40px; height: 40px; border: 4px solid #f3f4f6; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    """
    return Response(css_content, mimetype='text/css')

@app.route("/api/plan", methods=["POST"])
def api_plan():
    instruction = request.form.get("instruction", "").strip()
    if not instruction:
        return jsonify(error="Missing instruction"), 400
    try:
        plan = prompt_for_plan(instruction)
        return jsonify(plan=plan)
    except Exception as e:
        print(f"Error in api_plan: {str(e)}")
        return jsonify(error=str(e)), 500

@app.route("/api/xml", methods=["POST"])
def api_xml():
    plan = request.form.get("plan", "").strip()
    if not plan:
        return jsonify(error="Missing plan"), 400
    try:
        raw_xml = prompt_for_xml(plan)
        print(f"Raw XML from model: {raw_xml[:200]}...")  # Debug log
        clean_xml = clean_model_xml(raw_xml)
        print(f"Cleaned XML: {clean_xml[:200]}...")  # Debug log
        sanity_check_drawio(clean_xml)
        return jsonify(xml=clean_xml)
    except AssertionError as e:
        print(f"Validation error: {str(e)}")
        return jsonify(error=f"Validation failed: {e}"), 400
    except Exception as e:
        print(f"Error in api_xml: {str(e)}")
        return jsonify(error=str(e)), 500

@app.route("/download", methods=["POST"])
def download():
    xml = request.form.get("xml", "").strip()
    if not xml:
        return "No XML data provided", 400
    return Response(
        xml,
        mimetype="application/xml",
        headers={"Content-Disposition": 'attachment; filename="diagram.drawio"'},
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001)