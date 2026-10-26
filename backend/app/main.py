from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from .ai import AssessmentFailure, assess_blood_values
from .config import settings
from .database import Base, engine, get_db
from .models import Patient
from .schemas import PatientInput, PatientOutput

Base.metadata.create_all(bind=engine)
app = FastAPI(title="HealthPredict AI API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(RequestValidationError)
async def validation_error(_, exc):
    errors = [{"field": ".".join(str(part) for part in error["loc"] if part != "body"), "message": error["msg"], "input": jsonable_encoder(error.get("input"))} for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "Validation failed", "errors": errors})


def find_patient(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.get("/api/health")
async def health():
    return {"status": "ok", "ai_configured": bool(settings.ai_api_key)}


@app.post("/api/patients", response_model=PatientOutput, status_code=status.HTTP_201_CREATED)
async def create_patient(data: PatientInput, db: Session = Depends(get_db)):
    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@app.get("/api/patients", response_model=list[PatientOutput])
async def list_patients(db: Session = Depends(get_db)):
    return db.scalars(select(Patient).order_by(Patient.created_at.desc(), Patient.id.desc())).all()


@app.get("/api/patients/{patient_id}", response_model=PatientOutput)
async def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return find_patient(db, patient_id)


@app.put("/api/patients/{patient_id}", response_model=PatientOutput)
async def update_patient(patient_id: int, data: PatientInput, db: Session = Depends(get_db)):
    patient = find_patient(db, patient_id)
    new_values = data.model_dump()
    blood_changed = any(getattr(patient, key) != new_values[key] for key in ("glucose", "haemoglobin", "cholesterol"))
    for key, value in new_values.items():
        setattr(patient, key, value)
    if blood_changed:
        patient.ai_status = "pending"
        patient.ai_remarks = None
    db.commit()
    db.refresh(patient)
    return patient


@app.delete("/api/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    db.delete(find_patient(db, patient_id))
    db.commit()


@app.post("/api/patients/{patient_id}/assess", response_model=PatientOutput)
async def assess_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = find_patient(db, patient_id)
    patient.ai_remarks = None
    try:
        patient.ai_remarks = await assess_blood_values(patient.glucose, patient.haemoglobin, patient.cholesterol)
        patient.ai_status = "completed"
    except AssessmentFailure as exc:
        patient.ai_status = "failed"
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from None
    db.commit()
    db.refresh(patient)
    return patient
