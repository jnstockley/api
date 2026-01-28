import random

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

router = APIRouter(prefix="/valentines")

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def display_valentines_message(request: Request):
    """
    Renders the `templates/valentine.html` template.
    """
    messages = [
        "Roses are red, violets are blue, I hate poetry, but I'm into you <3",
        "Roses are red, violets are blue, sugar is sweet and so are you.",
        "Roses are red, violets are blue, I want to chill and watch Netflix with you 😏",
        "Roses are red, violets are blue, is it hot in here, or is it just you?",
        "Roses are red, violets are blue, nothing in this crazy world, could keep me from loving you!",
        "Roses are red, violets are blue, these everyday things, don't compare to you.",
        "Roses are red, rhyming's a habit, lets go to bed, and make it like rabbits",
    ]

    # pick a random message
    message = random.choice(messages)

    return templates.TemplateResponse(
        "valentine.html", {"request": request, "message": message}
    )
