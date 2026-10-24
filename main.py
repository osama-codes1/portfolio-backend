import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import engine, SessionLocal, Base
import models

load_dotenv()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://osama-al-bashari.vercel.app",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_admin(x_admin_password: str = Header(None)):
    if not ADMIN_PASSWORD or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")


class ContactMessage(BaseModel):
    name: str
    email: str
    message: str


class ProjectIn(BaseModel):
    title: str
    description: str = ""
    tech: str = ""
    github_link: str = ""


class SkillIn(BaseModel):
    category: str
    name: str


def project_to_dict(p):
    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "tech": p.tech.split(",") if p.tech else [],
        "github_link": p.github_link,
    }


def message_to_dict(m):
    return {
        "id": m.id,
        "name": m.name,
        "email": m.email,
        "message": m.message,
    }


def skill_to_dict(s):
    return {"id": s.id, "category": s.category, "name": s.name}


@app.get("/")
def home():
    return {"message": "welcome to portfolio API"}


@app.get("/api/projects")
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    return [project_to_dict(p) for p in projects]


@app.get("/api/projects/{id}")
def get_project(id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_to_dict(project)


@app.get("/api/skills")
def get_skills(db: Session = Depends(get_db)):
    skills = db.query(models.Skill).order_by(models.Skill.category, models.Skill.id).all()
    return [skill_to_dict(s) for s in skills]


@app.post("/api/contact")
def receive_message(msg: ContactMessage, db: Session = Depends(get_db)):
    new_message = models.ContactMessage(
        name=msg.name,
        email=msg.email,
        message=msg.message,
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return {
        "status": "success",
        "message": f"Thank you {msg.name}! Your message has been received."
    }


@app.post("/api/admin/login")
def admin_login(x_admin_password: str = Header(None)):
    verify_admin(x_admin_password)
    return {"status": "ok"}


@app.post("/api/admin/projects", dependencies=[Depends(verify_admin)])
def create_project(project: ProjectIn, db: Session = Depends(get_db)):
    new_project = models.Project(**project.model_dump())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return project_to_dict(new_project)


@app.put("/api/admin/projects/{id}", dependencies=[Depends(verify_admin)])
def update_project(id: int, project: ProjectIn, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in project.model_dump().items():
        setattr(db_project, key, value)
    db.commit()
    db.refresh(db_project)
    return project_to_dict(db_project)


@app.delete("/api/admin/projects/{id}", dependencies=[Depends(verify_admin)])
def delete_project(id: int, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(db_project)
    db.commit()
    return {"status": "deleted"}


@app.post("/api/admin/skills", dependencies=[Depends(verify_admin)])
def create_skill(skill: SkillIn, db: Session = Depends(get_db)):
    new_skill = models.Skill(**skill.model_dump())
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    return skill_to_dict(new_skill)


@app.delete("/api/admin/skills/{id}", dependencies=[Depends(verify_admin)])
def delete_skill(id: int, db: Session = Depends(get_db)):
    db_skill = db.query(models.Skill).filter(models.Skill.id == id).first()
    if not db_skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(db_skill)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/admin/messages", dependencies=[Depends(verify_admin)])
def get_messages(db: Session = Depends(get_db)):
    messages = (
        db.query(models.ContactMessage)
        .order_by(models.ContactMessage.id.desc())
        .all()
    )
    return [message_to_dict(m) for m in messages]


@app.delete("/api/admin/messages/{id}", dependencies=[Depends(verify_admin)])
def delete_message(id: int, db: Session = Depends(get_db)):
    db_message = (
        db.query(models.ContactMessage)
        .filter(models.ContactMessage.id == id)
        .first()
    )
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(db_message)
    db.commit()
    return {"status": "deleted"}