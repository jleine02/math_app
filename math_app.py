from app import create_app, db
from app.models import User, Equation, Notification, Message

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Equation": Equation, "Message": Message, "Notification": Notification}
