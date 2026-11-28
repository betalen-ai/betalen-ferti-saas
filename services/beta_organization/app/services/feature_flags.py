from app.models.subscription import Subscription


PLAN_FEATURES = {
    "free": {
        "billing",
        "inventory",
        "farmers",
        "khata",
        "basicReports",
        "exports",
    },
    "multiUser": {"multiUser"},
    "whatsapp": {"whatsapp"},
    "multiBranch": {"multiBranch"},
    "advancedReports": {"advancedReports"},
}


def can_use(subscription: Subscription | None, feature: str) -> bool:
    if subscription is None:
        plan = "free"
    else:
        plan = subscription.plan.lower()
        if subscription.status != "active":
            return False
    return feature in PLAN_FEATURES.get(plan, PLAN_FEATURES["free"]) or feature in PLAN_FEATURES["free"]
