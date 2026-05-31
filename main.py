from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
import subprocess
import os

app = FastAPI()

class ResumeRequest(BaseModel):
    latex: str

@app.post("/compile")
async def compile_resume(data: ResumeRequest):

    with tempfile.TemporaryDirectory() as temp_dir:

        tex_path = os.path.join(temp_dir, "resume.tex")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(data.latex)

        subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "resume.tex"
            ],
            cwd=temp_dir,
            capture_output=True
        )

        pdf_path = os.path.join(temp_dir, "resume.pdf")

        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "message": "PDF generation failed"
            }

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="resume.pdf"
        )