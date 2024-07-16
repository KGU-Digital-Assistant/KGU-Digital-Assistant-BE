from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Form, Header
from domain.user.phone_schema import PhoneNumberRequest, VerificationRequest
from domain.user.phone_service import send_verification_code, check_verification_code

router = APIRouter(
    prefix="/phone",
)


@router.post("/send-code/")
def send_code(request: PhoneNumberRequest):
    try:
        send_verification_code(request.phone_number)
        return {"message": "Verification code sent", "phone_number": request.phone_number}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-code/")
def verify_code(request: VerificationRequest):
    try:
        success, message = check_verification_code(request.phone_number, request.code)
        if success:
            return {"message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
