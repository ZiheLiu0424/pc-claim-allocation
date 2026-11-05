def result(valid, message, **details):
    return {"valid": valid, "score": float(valid), "message": message, "details": details}
