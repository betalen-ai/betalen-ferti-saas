from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_items():
    return {"items": [], "resource": "org_users"}