from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import tempfile
import subprocess
import os

app = FastAPI(title="Resume PDF Compiler", version="1.0.0")


class ResumeRequest(BaseModel):
    latex: str


@app.get("/")
def health():
    return {"status": "ok", "service": "resume-pdf-compiler"}


@app.post("/compile")
async def compile_resume(data: ResumeRequest):
    try:
        temp_dir = tempfile.mkdtemp()

        tex_path = os.path.join(temp_dir, "resume.tex")

        latex_content = data.latex
        latex_content = latex_content.replace("\\n", "\n")
        latex_content = latex_content.replace("\\t", "\t")
        latex_content = latex_content.replace("```latex", "")
        latex_content = latex_content.replace("```", "")
        latex_content = latex_content.strip()

        print("=" * 80)
        print("TEMP DIR:", temp_dir)
        print("=" * 80)

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        print("FILE EXISTS:", os.path.exists(tex_path))

        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "resume.tex"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )

        pdf_path = os.path.join(temp_dir, "resume.pdf")

        if not os.path.exists(pdf_path):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )

        return FileResponse(
            path=pdf_path, media_type="application/pdf", filename="resume.pdf"
        )

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
