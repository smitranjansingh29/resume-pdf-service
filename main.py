from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import tempfile
import subprocess
import os

app = FastAPI(
title="Resume PDF Compiler",
version="1.0.0"
)

class ResumeRequest(BaseModel):
    latex: str

@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "resume-pdf-compiler"
    }

@app.post("/compile")
async def compile_resume(data: ResumeRequest):

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            tex_path = os.path.join(temp_dir, "resume.tex")

        latex_content = data.latex

        # Fix escaped characters coming from n8n/Groq
        latex_content = latex_content.replace("\\n", "\n")
        latex_content = latex_content.replace("\\t", "\t")

        # Remove markdown code fences if AI accidentally returns them
        latex_content = latex_content.replace("```latex", "")
        latex_content = latex_content.replace("```", "")
        latex_content = latex_content.strip()

        print("=" * 80)
        print("LATEX RECEIVED")
        print("=" * 80)
        print(latex_content[:5000])
        print("=" * 80)

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        # First pass
        result1 = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "resume.tex"
            ],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )

        # Second pass
        result2 = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "resume.tex"
            ],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )

        pdf_path = os.path.join(temp_dir, "resume.pdf")

        if not os.path.exists(pdf_path):

            log_file = os.path.join(temp_dir, "resume.log")

            latex_log = ""

            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    latex_log = f.read()

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "PDF generation failed",
                    "stdout_first_pass": result1.stdout[-5000:],
                    "stderr_first_pass": result1.stderr[-5000:],
                    "stdout_second_pass": result2.stdout[-5000:],
                    "stderr_second_pass": result2.stderr[-5000:],
                    "latex_log": latex_log[-10000:]
                }
            )

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="resume.pdf"
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": str(e)
            }
        )