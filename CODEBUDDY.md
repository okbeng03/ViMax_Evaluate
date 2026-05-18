<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan at:
specs/001-agent-image-evaluation/plan.md

## Active Feature

**Feature**: Agent图像评估系统
**Spec**: specs/001-agent-image-evaluation/spec.md
**Plan**: specs/001-agent-image-evaluation/plan.md

## Technology Stack

- **Backend**: Python 3.13 / FastAPI
- **Frontend**: React 18 + Ant Design 6
- **Database**: SQLite
- **CLIP**: open_clip_torch (apple/DFN2B-CLIP-ViT-L-14-39B)
- **LLM**: LangChain + OpenAI/Local LLM
- **Image Analysis**: ComfyUI Qwen VL workflow

## Key Paths

- Backend: `backend/`
- Frontend: `frontend/`
- Specs: `specs/001-agent-image-evaluation/`
- Database: `data/evaluations.db`
<!-- SPECKIT END -->
