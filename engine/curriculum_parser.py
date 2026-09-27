import io,pypdf
from engine.skill_utils import extract_skills
class CurriculumPDFParser:
    def parse(self,f):
        r=pypdf.PdfReader(io.BytesIO(f.read())); text="\n".join(p.extract_text() or "" for p in r.pages)
        return text,extract_skills(text)
