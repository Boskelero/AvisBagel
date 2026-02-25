from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import handle_stripe_webhook


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body.decode("utf-8")
    signature = request.headers.get("Stripe-Signature", "")
    response = handle_stripe_webhook(payload, signature)
    return JsonResponse(response, status=501)


def payment_methods(request):
    return JsonResponse(
        {
            "methods": [
                {"code": "pay_on_pickup", "label": "Pay on pickup"},
                {"code": "cash", "label": "Cash"},
            ]
        }
    )
