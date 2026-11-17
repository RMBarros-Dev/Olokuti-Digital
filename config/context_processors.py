def csp_nonce(request):
    """Expose the per-request CSP script nonce to Django templates."""
    return {"csp_nonce": getattr(request, "csp_nonce", "")}
